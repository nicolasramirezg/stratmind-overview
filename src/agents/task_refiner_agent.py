import os
from openai import OpenAI
from typing import Any
import re

from src.utils.prompt_loader import load_prompt

class TaskRefiner:
    """
    Evaluates whether a subtask should be refined and, if so, generates more specific subtasks.
    Output: dict with structure:
    {
        "original": "Original subtask",
        "refined": ["Subtask 1", "Subtask 2", ...]  # empty if no refinement needed
    }
    """

    def __init__(self, model: str = "gpt-3.5-turbo", debug: bool = False):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        self.model = model
        self.client = OpenAI(api_key=api_key)
        self.debug = debug

    @staticmethod
    def _parse_response(response: Any, debug: bool = False) -> dict:
        content = response.choices[0].message.content.strip()

        # Si no hay refinamiento, el modelo responde con "NO_REFINEMENT_NEEDED"
        if content == "NO_REFINEMENT_NEEDED":
            if debug:
                print("No refinement needed for this subtask.")
            return {
                "original": "",
                "refined": []
            }

        # Extrae bloques entre ---
        blocks = re.findall(
            r"---\s*Title:\s*(.+?)\s*Description:\s*(.+?)\s*Execution_type:\s*(.+?)\s*Expected_output:\s*(.+?)\s*Dependencies:\s*(.+?)\s*---",
            content,
            re.DOTALL | re.IGNORECASE
        )
        refined = []
        for title, description, execution_type, expected_output, dependencies in blocks:
            refined.append({
                "title": title.strip(),
                "description": description.strip(),
                "execution_type": execution_type.strip().lower(),
                "expected_output": expected_output.strip(),
                "dependencies": [d.strip() for d in dependencies.split(",")] if dependencies.strip().lower() != "none" else []
            })

        if debug:
            print("Parsed result:", {"original": "", "refined": refined})

        return {
            "original": "",
            "refined": refined
        }

    def refine(
        self,
        area_name: str,
        global_task: str,
        subtask: str,
        area_description: str = "",
        parent_task_title: str = "",
        existing_sibling_titles: list = None,
        return_prompt_and_response: bool = False
    ) -> dict:
        variables = {
            "root_task_title": global_task,
            "root_task_description": "",
            "area_name": area_name,
            "area_description": area_description,
            "parent_task_title": parent_task_title,
            "subtask": subtask,
            "existing_sibling_titles": ", ".join(existing_sibling_titles) if existing_sibling_titles else "None",
            "parent_info": ""  # Or add any extra context you want here
        }

        prompt = load_prompt("prompts/refiner_agent/user.txt", variables)
        system_prompt = load_prompt("prompts/refiner_agent/system.txt", {})

        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.5
        )

        parsed_result = self._parse_response(response, debug=self.debug)
        if return_prompt_and_response:
            return parsed_result, prompt, response.choices[0].message.content.strip()
        return parsed_result


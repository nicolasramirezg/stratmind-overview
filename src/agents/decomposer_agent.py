import os
from openai import OpenAI
import re
from src.utils.prompt_loader import load_prompt

class Decomposer:
    """
    Decomposer agent that breaks down a complex task into 3 to 9 main functional areas.

    Output format:
        {
            "intro": (str) General reasoning summary,
            "subtasks": [
                {
                    "area": (str) Name of the functional area,
                    "description": (str) Objective of that area,
                    "expected_output": (str) Expected result for that area,
                    "responsibilities": [(str)] List of key actions or responsibilities
                },
                ...
            ]
        }
    """

    def __init__(self, model: str = "gpt-3.5-turbo"):
        """
        Initialize the Decomposer agent with the specified OpenAI model.
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        self.model = model
        self.client = OpenAI(api_key=api_key)

    @staticmethod
    def parse_llm_decomposition(text: str, debug: bool = False) -> dict:
        """
        Parse the LLM output into an introduction and a list of area subtasks.

        Args:
            text (str): The raw output from the LLM.
            debug (bool): If True, prints parsing errors.

        Returns:
            dict: {
                "intro": <introduction string>,
                "subtasks": [ {area, description, expected_output, responsibilities}, ... ]
            }
        """
        try:
            # Split into INTRO and SUBTASKS sections
            parts = re.split(r"###\s*SUBTASKS\s*###", text, maxsplit=1)
            if len(parts) != 2:
                if debug:
                    print("Both sections (INTRO and SUBTASKS) were not found.")
                return {"intro": "", "subtasks": [{"raw": text.strip()}]}

            intro_block = parts[0].replace("### INTRODUCTION ###", "").strip()
            subtasks_block = parts[1].strip()

            # Split subtasks by blocks starting with "Area:"
            raw_subtasks = re.split(r"\n(?:\d+\.\s*)?Area:", subtasks_block)
            parsed_subtasks = []

            for block in raw_subtasks:
                block = "Area:" + block.strip()
                lines = block.splitlines()
                subtask = {
                    "area": "",
                    "description": "",
                    "expected_output": "",
                    "responsibilities": []
                }

                for line in lines:
                    line = line.strip()
                    if line.startswith("Area:"):
                        subtask["area"] = line.replace("Area:", "").strip()
                    elif line.startswith("Description:"):
                        subtask["description"] = line.replace("Description:", "").strip()
                    elif line.startswith("Expected_output:"):
                        subtask["expected_output"] = line.replace("Expected_output:", "").strip()
                    elif line.startswith("-"):
                        subtask["responsibilities"].append(line.lstrip("- ").strip())

                if subtask["area"] and subtask["description"]:
                    parsed_subtasks.append(subtask)

            return {
                "intro": intro_block,
                "subtasks": parsed_subtasks
            }

        except Exception as e:
            if debug:
                print("Error while parsing:", e)
            return {"intro": "", "subtasks": [{"raw": text.strip()}]}

    def decompose(
            self,
            task_description: str,
            expected_output: str,
            debug: bool = True) -> dict:
        """
        Decompose a complex task into main functional areas using the LLM.

        Args:
            task_description (str): The main task description.
            expected_output (str): The expected output for the main task.
            debug (bool): If True, prints parsing errors.

        Returns:
            dict: Decomposition result with intro and subtasks.
        """
        messages = [
            {
                "role": "system",
                "content": load_prompt(
                    "prompts/decomposer_agent/system.txt",
                    {}
                )
            },
            {
                "role": "user",
                "content": load_prompt(
                    "prompts/decomposer_agent/user_with_expectedoutput.txt",
                    {
                        "task_description": task_description,
                        "expected_output": expected_output
                    }
                )
            }
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3
        )

        content = response.choices[0].message.content.strip()
        result = self.parse_llm_decomposition(content, debug=True)
        return result
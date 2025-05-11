from openai import OpenAI
from typing import Any
import json

class TaskRefiner:

    """
    Evalúa si una subtarea debe refinarse y, en su caso, genera nuevas subtareas más específicas.

    Output: dict con estructura:
    {
        "original": "Subtarea original",
        "refined": ["Subtarea 1", "Subtarea 2", ...]  # vacío si no necesita refinamiento
    }
    """

    def __init__(self, model: str = "gpt-3.5-turbo"):
        self.model = model
        self.client = OpenAI()

    @staticmethod
    def _parse_response(response: Any) -> dict:
        content = response.choices[0].message.content.strip()

        try:
            data = json.loads(content)

            if isinstance(data, dict) and "original" in data and "refined" in data:
                original = data["original"]
                refined = data["refined"]

                if isinstance(original, str) and isinstance(refined, list):
                    refined_clean = [s.strip() for s in refined if isinstance(s, str) and s.strip()]
                    return {
                        "original": original.strip(),
                        "refined": refined_clean
                    }

            # Fallback si estructura incorrecta
            return {
                "original": content,
                "refined": []
            }

        except json.JSONDecodeError:
            fallback_lines = []
            for line in content.splitlines():
                line = line.strip()
                if line:
                    fallback_lines.append(line.lstrip("-• "))

            return {
                "original": content,
                "refined": fallback_lines
            }

    # devuelve: {"original": str, "refined": list[str] or []}
    def refine(self, area_name: str, global_task: str, subtask: str) -> dict:

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert agent in analyzing and refining subtasks within a multi-agent system.\n\n"
                    "Your role is to evaluate whether a specific subtask, assigned to a functional area, is clear and focused enough "
                    "to be executed by a specialized agent, or if it should be broken down into smaller steps.\n\n"
                    "You should only decompose the subtask if ALL of the following conditions are met:\n"
                    "- The subtask is ambiguous, overly broad, or involves multiple distinct decisions.\n"
                    "- It cannot reasonably be performed by a single autonomous agent.\n"
                    "- Its execution requires multiple clearly distinguishable phases.\n\n"
                    "Do not decompose a subtask simply because it is logically divisible. Only refine it if doing so is necessary "
                    "for an agent to effectively and autonomously execute it.\n\n"
                    "Your output must be a JSON object with the following structure:\n\n"
                    "{\n"
                    "  \"original\": \"The full original subtask\",\n"
                    "  \"refined\": [\"Smaller subtask 1\", \"Smaller subtask 2\", ...]\n"
                    "}\n\n"
                    "If you believe the subtask is already clear and actionable, return:\n\n"
                    "{\n"
                    "  \"original\": \"The full original subtask\",\n"
                    "  \"refined\": []\n"
                    "}\n\n"
                    "Do not include any explanation, comments, or text outside of the JSON object."
                )
            }
            ,
            {
                "role": "user",
                "content": (
                    f"You are evaluating a subtask within the functional area: '{area_name}', "
                    f"which is part of the broader task: '{global_task}'.\n\n"
                    f"The subtask to evaluate is:\n"
                    f"\"{subtask}\"\n\n"
                    "Determine whether this subtask should be further decomposed following the criteria previously described. "
                    "Return your output strictly in the required JSON format."
                )
            }
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.4
        )

        parsed_result = self._parse_response(response)
        return parsed_result


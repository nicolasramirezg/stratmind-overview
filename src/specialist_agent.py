from openai import OpenAI
from typing import Any
import json



class SpecialistAgent:

    """
    Genera subtareas específicas y ejecutables para cada área funcional
    a partir de una descomposición inicial de una tarea compleja.

    Output: dict con el nombre de cada área como clave, y una lista de strings como subtareas:
    {
        "Marketing Strategy": [
            "Define target audience",
            "Choose distribution channels"
        ],
        ...
    }
    """

    def __init__(self, model: str = "gpt-3.5-turbo"):
        self.model = model
        self.client = OpenAI()

    @staticmethod
    def _parse_response(response: Any, area_name: str) -> list[str]:
        content = response.choices[0].message.content.strip()

        try:
            data = json.loads(content)

            if isinstance(data, dict) and "area" in data and "subtasks" in data:
                subtasks_raw = data["subtasks"]

                if isinstance(subtasks_raw, list):
                    valid_subtasks = []
                    for s in subtasks_raw:
                        if isinstance(s, str) and s.strip():
                            valid_subtasks.append(s.strip())
                    return valid_subtasks

            return [content.strip()]

        except json.JSONDecodeError:
            fallback_subtasks = []
            for line in content.splitlines():
                line = line.strip()
                if line:
                    fallback_subtasks.append(line.lstrip("-• "))
            return fallback_subtasks

    def plan_subtasks(self, decomposition: dict, global_task: str) -> dict:
        result = {}

        for area in decomposition["subtasks"]:
            area_name = area["area"]
            description = area["description"]
            responsibilities = area.get("responsibilities", [])

            messages = [
                {
                    "role": "system",
                    "content": (
                        f"You are a specialized expert agent assigned to the area of '{area_name}'.\n\n"
                        f"Your role is to analyze this functional area within the broader context of the overall task:\n"
                        f"'{global_task}'\n\n"
                        f"The goal of this area is:\n'{description}'\n\n"
                        f"Some of the responsibilities associated with this area may include:\n"
                        f"{json.dumps(responsibilities, indent=2)}\n\n"
                        "Your task is to generate **3 to 7 concrete and well-defined subtasks** required to successfully fulfill this functional area.\n\n"
                        "Each subtask must:\n"
                        "- Be written in clear, executable natural language.\n"
                        "- Include enough context to be actionable by an autonomous agent.\n"
                        "- Be directly related to the description and the responsibilities of the area.\n\n"
                        "You must strictly return a **JSON object** with the following structure:\n\n"
                        "{\n"
                        f"  \"area\": \"{area_name}\",\n"
                        "  \"subtasks\": [\n"
                        "    \"First executable subtask\",\n"
                        "    \"Second executable subtask\",\n"
                        "    ...\n"
                        "  ]\n"
                        "}\n\n"
                        "Do not include any explanation, introduction, or text outside this JSON object."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Area name: {area_name}\n\n"
                        f"Overall task: {global_task}\n\n"
                        f"Responsibilities:\n{json.dumps(responsibilities, indent=2)}\n\n"
                        "Please return a structured plan as described above."
                    )
                }
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.4
            )

            parsed_subtasks = self._parse_response(response, area_name)
            result[area_name] = parsed_subtasks

        return result
from openai import OpenAI
from typing import Dict, List
import json
import re


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
    def _parse_specialist_output(text: str, debug: bool = False) -> Dict[str, List[str]]:
        try:
            parts = re.split(r"###\s*SUBTASKS\s*###", text, maxsplit=1)
            if len(parts) != 2:
                if debug:
                    print("❌ No se encontraron ambas secciones (AREA y SUBTASKS)")
                return {"area": "", "subtasks": [text.strip()]}

            area_block = parts[0]
            subtasks_block = parts[1]

            # Extraer nombre del área ignorando encabezados
            area_lines = [
                line.strip() for line in area_block.splitlines()
                if line.strip() and not line.strip().startswith("###")
            ]
            area_name = area_lines[0] if area_lines else ""

            # Extraer subtareas válidas, sin encabezados ni repeticiones del nombre
            subtasks = [
                line.lstrip("- ").strip()
                for line in subtasks_block.splitlines()
                if line.strip()
                   and not line.strip().startswith("###")
                   and line.strip() != area_name
            ]

            return {
                "area": area_name,
                "subtasks": subtasks
            }

        except Exception as e:
            if debug:
                print("❌ Error al parsear especialista:", e)
            return {"area": "", "subtasks": [text.strip()]}

    def plan_subtasks(self, decomposition: dict, global_task: str) -> list:
        result = []

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
                        f"Some responsibilities associated with this area may include:\n"
                        f"{json.dumps(responsibilities, indent=2)}\n\n"
                        "You must generate a concrete, well-structured plan of executable subtasks for this area."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Your task is to generate **3 to 7 concrete and well-defined subtasks** required to successfully fulfill the area of: '{area_name}'.\n\n"
                        f"The plan must:\n"
                        f"- Contain subtasks written in clear, executable natural language.\n"
                        f"- Include enough context to be actionable by an autonomous agent.\n"
                        f"- Be directly related to the area’s description and responsibilities.\n\n"
                        f"Your response must strictly follow **this format**:\n\n"
                        f"### AREA ###\n"
                        f"{area_name}\n\n"
                        f"### SUBTASKS ###\n"
                        f"- First executable subtask\n"
                        f"- Second executable subtask\n"
                        f"- ... (between 3 and 7 total)\n\n"
                        f"Do NOT include any explanations, comments, extra formatting, markdown, or sections beyond those specified."
                    )
                }

            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.4
            )



            content = response.choices[0].message.content.strip()
            # print('### LLM RESPONSE ###')
            # print(content)

            parsed = self._parse_specialist_output(content)
            result.append(parsed)

        return result
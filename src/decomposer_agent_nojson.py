from openai import OpenAI
import re


class Decomposer:

    """
    Descompone una tarea compleja en entre 3 y 9 áreas funcionales principales.

    Output: dict con claves:
    {
        "intro": "Resumen del razonamiento general",
        "subtasks": [
            {
                "area": "Nombre del área",
                "description": "Objetivo de esa área",
                "expected_output": "Respuesta que se espera"
                "responsibilities": ["Acción 1", "Acción 2"]
            },
            ...
        ]
    }
    """

    def __init__(self, model: str = "gpt-3.5-turbo"):
        self.model = model
        self.client = OpenAI()

    @staticmethod
    def parse_llm_decomposition(text: str, debug: bool = False) -> dict:
        try:
            # Separar en dos secciones: INTRO y SUBTASKS
            parts = re.split(r"###\s*SUBTASKS\s*###", text, maxsplit=1)
            if len(parts) != 2:
                if debug:
                    print("❌ No se encontraron ambas secciones (INTRO y SUBTASKS)")
                return {"intro": "", "subtasks": [{"raw": text.strip()}]}

            intro_block = parts[0].replace("### INTRODUCTION ###", "").strip()
            subtasks_block = parts[1].strip()

            # Separar subtareas por bloques que empiezan por "Area:"
            raw_subtasks = re.split(r"\n(?:\d+\.\s*)?Area:", subtasks_block)
            parsed_subtasks = []

            for block in raw_subtasks:
                block = "Area:" + block.strip()
                lines = block.splitlines()
                subtask = {
                    "area": "",
                    "description": "",
                    "expected_output": "",  # <-- Añadido
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
                print("❌ Error al parsear:", e)
            return {"intro": "", "subtasks": [{"raw": text.strip()}]}

    def decompose(self, task_description: str, expected_output: str, debug: bool = True) -> dict:

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert agent in analyzing and decomposing complex tasks.\n\n"
                    "Your goal is to break down a task into a set of meaningful, well-structured\n"
                    "functional areas. Each area should represent a distinct responsibility that\n"
                    "could be delegated to a specialized agent.\n\n"
                    "The number of areas should typically range between 3 and 9, but only include\n"
                    "as many as are logically justified by the nature of the task.\n\n"
                    "Avoid artificial segmentation. Do not invent areas just to reach a number.\n"
                    "Group related responsibilities under coherent domains where appropriate.\n\n"
                    "Use your expert judgment to ensure the division is practical and efficient.\n"
                    "Return your output using a strict textual format to ensure correct parsing."
                )
            },
            {
                "role": "user",
                "content": (
                    "Analyze the following task and divide it into a practical number of\n"
                    "functional areas of specialization.\n\n"
                    f"{task_description}\n\n"
                    "The expecpetected output of the task is:\n"
                    f"{expected_output}\n\n"
                    "Your response must follow **exactly** this structure:\n\n"
                    "### INTRODUCTION ###\n"
                    "A short paragraph explaining how you approached the decomposition.\n"
                    "Justify the number of areas you identified and the logic behind them.\n\n"
                    "### SUBTASKS ###\n"
                    "Area: <short name>\n"
                    "Description: <what this area is responsible for>\n"
                    "Expected_output: <what you expect from this area>\n"
                    "Responsibilities:\n"
                    "- <first key responsibility>\n"
                    "- <second key responsibility>\n"
                    "- <...>\n\n"
                    "Repeat this block for each functional area (between 3 and 9 total).\n\n"
                    "Do not include JSON, markdown, or any extra formatting beyond this."
                )
            }

        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3
        )

        content = response.choices[0].message.content.strip()
        # print("🧾 RAW LLM content:\n", content)

        result = self.parse_llm_decomposition(content, debug=True)
        return result
        # print(result["intro"])
        # for s in result["subtasks"]:
        #     print("-", s["area"])





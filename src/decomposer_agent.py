from openai import OpenAI
import re

from src.utils.prompt_loader import load_prompt


class Decomposer:

    """
    Descompone una tarea compleja en entre 3 y 9 áreas funcionales principales.

    Output:
        {
            "intro": (str) Resumen del razonamiento general,
            "subtasks": [
                {
                    "area": (str) Nombre del área funcional,
                    "description": (str) Objetivo de esa área,
                    "expected_output": (str) Resultado esperado de esa área,
                    "responsibilities": [(str)] Lista de acciones o responsabilidades clave
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

    def decompose(
            self,
            task_description: str,
            expected_output: str,
            debug: bool = True) -> dict:

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
        # print("🧾 RAW LLM content:\n", content)

        result = self.parse_llm_decomposition(content, debug=True)
        return result
        # print(result["intro"])
        # for s in result["subtasks"]:
        #     print("-", s["area"])





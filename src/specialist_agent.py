from openai import OpenAI
import re
from src.utils.prompt_loader import load_prompt


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
    def _parse_specialist_output(text: str, debug: bool = False) -> dict:
        try:
            parts = re.split(r"###\s*SUBTASKS\s*###", text, maxsplit=1)
            if len(parts) != 2:
                if debug:
                    print("❌ No se encontraron ambas secciones (AREA y SUBTASKS)")
                return {"area": "", "subtasks": []}

            area_block = parts[0]
            subtasks_block = parts[1]

            # Extraer nombre del área ignorando encabezados
            area_lines = [
                line.strip() for line in area_block.splitlines()
                if line.strip() and not line.strip().startswith("###")
            ]
            area_name = area_lines[0] if area_lines else ""

            # Parsear subtareas en dicts
            subtask_blocks = re.split(r"Subtask:\s*", subtasks_block)
            subtasks = []
            for block in subtask_blocks:
                if not block.strip():
                    continue
                title = re.search(r"Title:\s*(.+)", block)
                description = re.search(r"Description:\s*(.+)", block)
                expected_output = re.search(r"Expected_output:\s*(.+)", block)
                dependencies = re.search(r"Dependencies:\s*(.+)", block)
                if not (title and description and expected_output and dependencies):
                    if debug:
                        print(f"❌ Formato incorrecto en bloque:\n{block}")
                    continue
                subtasks.append({
                    "title": title.group(1).strip(),
                    "description": description.group(1).strip(),
                    "expected_output": expected_output.group(1).strip(),
                    "dependencies": [d.strip() for d in dependencies.group(1).split(",")] if dependencies and dependencies.group(1).strip().lower() != "none" else []
                })

            return {
                "area": area_name,
                "subtasks": subtasks
            }

        except Exception as e:
            if debug:
                print("❌ Error al parsear especialista:", e)
                print("Contenido recibido:\n", text)
            return {"area": "", "subtasks": []}

    def plan_subtasks(self, decomposition: dict, global_task: str) -> list:
        result = []

        for area in decomposition["subtasks"]:
            area_name = area["area"]
            description = area["description"]
            responsibilities = area.get("responsibilities", [])
            expected_output = area.get("expected_output", "")

            # Preparamos las variables para interpolación en los .txt
            variables = {
                "area_name": area_name,
                "global_task": global_task,
                "description": description,
                "expected_output": expected_output,
                "responsibilities": "\n".join(f"- {r}" for r in responsibilities)
            }

            messages = [
                {
                    "role": "system",
                    "content": load_prompt(
                        "prompts/specialist_agent/system.txt",
                        variables)
                },
                {
                    "role": "user",
                    "content": load_prompt(
                        "prompts/specialist_agent/user.txt",
                        variables)
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
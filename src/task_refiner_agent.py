from openai import OpenAI
from typing import Any
import re

from src.utils.prompt_loader import load_prompt

class TaskRefiner:

    """
    Evalúa si una subtarea debe refinarse y, en su caso, genera nuevas subtareas más específicas.

    Output: dict con estructura:
    {
        "original": "Subtarea original",
        "refined": ["Subtarea 1", "Subtarea 2", ...]  # vacío si no necesita refinamiento
    }
    """

    def __init__(self, model: str = "gpt-3.5-turbo", debug: bool = False):
        self.model = model
        self.client = OpenAI()
        self. debug = debug

    @staticmethod
    def _parse_response(response: Any, debug: bool = False) -> dict:
        content = response.choices[0].message.content.strip()

        try:
            sections = content.split("###")
            section_dict = {}

            if debug:
                print("🧩 Secciones detectadas:", [s.strip() for s in sections if s.strip()])

            for i in range(1, len(sections), 2):
                # Convertimos a mayúsculas para robustez, ya que esperamos etiquetas como 'ORIGINAL', 'REFINED'
                key = sections[i].strip().upper()
                value = sections[i + 1].strip() if i + 1 < len(sections) else ""
                section_dict[key] = value

            original = section_dict.get("ORIGINAL", "").strip()
            refined_raw = section_dict.get("REFINED", "").strip()

            if not original:
                if debug:
                    print("❌ No se encontró sección ORIGINAL")

            if debug and refined_raw:
                print("📄 Sección REFINED bruta:\n", refined_raw)

            refined = []
            subtask_blocks = re.split(r"Subtask:", refined_raw)
            for block in subtask_blocks:
                if not block.strip():
                    continue
                title = re.search(r"Title:\s*(.+)", block)
                description = re.search(r"Description:\s*(.+)", block)
                expected_output = re.search(r"Expected_output:\s*(.+)", block)
                execution_type = re.search(r"Execution_type:\s*(.+)", block)  # <-- Añadido
                dependencies = re.search(r"Dependencies:\s*(.+)", block)
                refined.append({
                    "title": title.group(1).strip() if title else block.strip(),
                    "description": description.group(1).strip() if description else "",
                    "expected_output": expected_output.group(1).strip() if expected_output else "",
                    "execution_type": execution_type.lower().strip() if execution_type else "llm",  # <-- Añadido
                    "dependencies": [d.strip() for d in dependencies.group(1).split(",")] if dependencies and dependencies.group(1).strip().lower() != "none" else []
                })

            if debug:
                print("✅ Resultado parseado:", {"original": original, "refined": refined})

            return {
                "original": original,
                "refined": refined
            }

        except Exception as e:
            if debug:
                print("❌ Error al parsear la respuesta del refinador:", e)
            return {
                "original": content,
                "refined": []
            }

    def refine(
        self,
        area_name: str,
        global_task: str,
        subtask: str,
        area_description: str = "",
        root_task_title: str = "",
        root_task_description: str = "",
        parent_task: dict = None,
        parent_dependencies: list = None
    ) -> dict:
        parent_info = ""
        if parent_task:
            parent_info += f"\nParent Task Title: {parent_task.get('title', '')}"
            parent_info += f"\nParent Description: {parent_task.get('description', '')}"
            parent_info += f"\nParent Expected Output: {parent_task.get('expected_output', '')}"
            if parent_dependencies:
                parent_info += (
                    "\nParent Dependencies: " +
                    ", ".join(
                        dep.title if hasattr(dep, "title") else str(dep)
                        for dep in parent_dependencies
                    )
                )
        variables = {
            "root_task_title": root_task_title,
            "root_task_description": root_task_description,
            "area_name": area_name,
            "area_description": area_description,
            "parent_info": parent_info,  # Esto debe ser un string ya formateado
            "subtask": subtask  # Puede ser str o subtask["title"]
        }

        messages = [
            {
                "role": "system",
                "content": load_prompt("prompts/refiner_agent/system.txt", {})
            },
            {
                "role": "user",
                "content": load_prompt("prompts/refiner_agent/user.txt", variables)
            }
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.4
        )

        parsed_result = self._parse_response(response, debug=self.debug)
        return parsed_result


from openai import OpenAI
from typing import Any
import re

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
                refined.append({
                    "title": title.group(1).strip() if title else block.strip(),
                    "description": description.group(1).strip() if description else "",
                    "expected_output": expected_output.group(1).strip() if expected_output else ""
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
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert agent in analyzing and refining subtasks in a multi-agent system.\n\n"
                    "Your task is to determine whether a given subtask, assigned to a functional area, is clear and focused enough to be executed by an autonomous agent, or if it needs to be decomposed into smaller, more actionable steps.\n\n"
                    "Only refine the subtask if all of the following conditions are met:\n"
                    "- The subtask is ambiguous, overly broad, or involves multiple distinct decisions.\n"
                    "- It cannot be reasonably executed by a single autonomous agent as is.\n"
                    "- Its execution requires multiple clearly distinguishable phases.\n\n"
                    "Do not refine a subtask merely because it is logically divisible; only do so when necessary for effective execution."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Root Task Title: {root_task_title}\n"
                    f"Root Task Description: {root_task_description}\n"
                    f"Area: {area_name}\n"
                    f"Area Description: {area_description}\n"
                    f"{parent_info}\n\n"
                    f"Subtask:\n\"{subtask}\"\n\n"
                    "Return your analysis using exactly the following format:\n\n"
                    "### ORIGINAL ###\n"
                    "Copy the original subtask exactly as received above.\n\n"
                    "### REFINED ###\n"
                    "Subtask:\n"
                    "Title: <short title>\n"
                    "Description: <description>\n"
                    "Expected_output: <expected output>\n"
                    "Subtask:\n"
                    "Title: <short title>\n"
                    "Description: <description>\n"
                    "Expected_output: <expected output>\n"
                    "... (repeat for each refined subtask)\n\n"
                    "If the subtask is already actionable, leave the '### REFINED ###' section empty.\n"
                    "Do not include any explanations, comments, or extra text beyond these two sections."
                )
            }
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.4
        )

        parsed_result = self._parse_response(response, debug=self.debug)
        return parsed_result


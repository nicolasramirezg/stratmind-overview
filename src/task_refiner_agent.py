from openai import OpenAI
from typing import Any

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
            for line in refined_raw.splitlines():
                line = line.strip()
                if line.startswith("- "):
                    item = line[2:].strip()
                    if item:
                        refined.append(item)

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

    # devuelve: {"original": str, "refined": list[str] or []}
    def refine(self, area_name: str, global_task: str, subtask: str) -> dict:

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
            }
            ,
            {
                "role": "user",
                "content": (
                    f"Evaluate the following subtask for the functional area: '{area_name}',\n"
                    f"which is part of the overall task: '{global_task}'.\n\n"
                    f"Subtask:\n\"{subtask}\"\n\n"
                    "Return your analysis using exactly the following format:\n\n"
                    "### ORIGINAL ###\n"
                    "Copy the original subtask exactly as received above.\n\n"
                    "### REFINED ###\n"
                    "- First refined subtask (if applicable)\n"
                    "- Second refined subtask (if applicable)\n"
                    "- ...\n\n"
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


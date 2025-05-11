from openai import OpenAI
import json

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
                "responsibilities": ["Acción 1", "Acción 2"]
            },
            ...
        ]
    }
    """

    def __init__(self, model: str = "gpt-3.5-turbo"):
        self.model = model
        self.client = OpenAI()

    def decompose(self, task_description: str) -> dict:
        """
        Usa un LLM para descomponer una tarea compleja en subtareas específicas y secuenciales.
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert agent in analyzing and decomposing complex tasks.\n\n"
                    "Your goal is to analyze a general task and break it down into **3 to 9** major functional subtasks. "
                    "Each subtask should represent a clear area of responsibility, similar to what a specialized team member would handle.\n\n"
                    "Assess the complexity of the task and estimate how many distinct areas of specialization are required to solve it, choosing between 6 and 9 depending on scope.\n\n"
                    "Return strictly a **JSON list with exactly two elements**, in this order:\n"
                    "1. A string with a brief introduction explaining your general reasoning for how you chose the functional areas.\n"
                    "2. A list of functional subtasks, where each subtask is an object with the following fields:\n"
                    "   - 'area': a short title for the subtask or area.\n"
                    "   - 'description': a clear explanation of the goal of that area within the overall task.\n"
                    "   - 'responsibilities': a list of key actions or decisions that an agent responsible for this area would need to handle.\n\n"
                    "Output format must be: **a JSON list with [introduction, list_of_subtasks]**.\n"
                    "Do not include any additional text, titles, explanations, or markdown outside of the JSON list."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Analyze the following task and return its functional decomposition into distinct areas of specialization:\n\n"
                    f"{task_description}\n\n"
                    f"Your output must be a JSON list with exactly two elements:\n"
                    f"1. A short introductory string explaining your reasoning.\n"
                    f"2. A list of 3 to 9 functional subtasks as described.\n\n"
                    f"Do not include anything outside this JSON list. No comments, explanations, or formatting."
                )
            }
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3
        )

        # Parseamos el contenido como lista de subtareas
        content = response.choices[0].message.content.strip()

        try:
            data = json.loads(content)

            # Comprobamos que sea una lista con dos elementos: [intro, list_of_subtasks]
            if isinstance(data, list) and len(data) == 2:
                intro = data[0]
                subtasks_raw = data[1]

                # Validamos que la introducción sea texto y la lista contenga diccionarios
                if isinstance(intro, str) and isinstance(subtasks_raw, list):
                    valid_subtasks = []
                    for s in subtasks_raw:
                        if isinstance(s, dict):
                            valid_subtasks.append(s)

                    return {
                        "intro": intro,
                        "subtasks": valid_subtasks
                    }

            # Si la estructura no es válida, devolvemos el contenido como texto plano para revisión
            return {
                "intro": "",
                "subtasks": [{"raw": content.strip()}] if content.strip() else []
            }

        except json.JSONDecodeError:
            # Fallback manual línea por línea si el JSON está roto
            fallback_subtasks = []
            for line in content.splitlines():
                line = line.strip()
                if line:
                    fallback_subtasks.append({"raw": line.lstrip("-• ")})

            return {
                "intro": "",
                "subtasks": fallback_subtasks
            }
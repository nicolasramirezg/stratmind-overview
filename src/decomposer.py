from openai import OpenAI
import json

class Decomposer:
    def __init__(self, model: str = "gpt-3.5-turbo"):
        self.model = model
        self.client = OpenAI()

    def decompose(self, task_description: str) -> list[str]:
        """
        Usa un LLM para descomponer una tarea compleja en subtareas específicas y secuenciales.
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "Eres un agente que descompone tareas complejas en subtareas claras, específicas y ejecutables. "
                    "Cada subtarea debe:\n"
                    "- Representar una única acción concreta.\n"
                    "- Ser escrita en lenguaje natural claro y sencillo.\n"
                    "- Ser útil para ser directamente procesada por un modelo LLM.\n\n"
                    "Devuelve exclusivamente una lista JSON de subtareas, sin explicaciones ni texto adicional."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Descompón la siguiente tarea en subtareas independientes y ordenadas:\n\n"
                    f"{task_description}\n\n"
                    f"Recuerda: solo quiero la lista en formato JSON, sin explicaciones, ejemplos ni texto extra."
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

        # En caso de que lo devuelva en formato JSON de lista
        try:
            subtasks = json.loads(content)
            if isinstance(subtasks, list):
                # Validamos que cada elemento sea string y no esté vacío
                subtasks = [s.strip() for s in subtasks if isinstance(s, str) and s.strip()]
                return subtasks
            else:
                # Fallback si no es lista: devolver contenido en una lista
                return [content.strip()] if content.strip() else []
        except json.JSONDecodeError:
            # Fallback manual si falla el JSON
            return [line.strip("-• ") for line in content.splitlines() if line.strip()]


from openai import OpenAI
import json

class TaskAnalyzer:
    def __init__(self, model: str = "gpt-3.5-turbo"):
        self.model = model
        self.client = OpenAI()

    def analyze_task(self, prompt: str) -> dict:
        """
        Analiza un prompt para determinar si la tarea es simple o compleja.
        Devuelve un diccionario con la clasificación y un breve razonamiento.
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "Eres un analizador de tareas experto en organización y planificación."
                    "Tu tarea es analizar un enunciado y determinar:"
                    "- Si es 'simple' (una instrucción directa, resoluble en un solo paso)."
                    "- O 'complex' (requiere varias acciones, planificación o integración de muchos aspectos)."
                    "Devuelve exclusivamente un objeto JSON con dos campos: "
                    "'complexity' ('simple' o 'complex') y 'reasoning' (una frase breve de hasta 30 palabras)."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Analiza el siguiente enunciado:\n\n"
                    f"{prompt}"
                )
            }
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.0,
            n=1
        )

        content = response.choices[0].message.content.strip()

        # Intentamos parsear el contenido como JSON
        try:
            result = json.loads(content)
            return result
        except json.JSONDecodeError:
            # fallback: respuesta básica por si falla el parseo
            return {"complexity": "unknown", "reasoning": "No se pudo analizar correctamente."}
from openai import OpenAI

class RefinerAPE:
    def __init__(self, model: str, params: dict):
        self.model = model
        self.client = OpenAI()
        self.params = params  # TODO: trabajar siempre leyendo de aquí

    def refine(self, prompt: str) -> tuple[str, list[dict]]:
        """
        Realiza el refinamiento iterativo de un prompt utilizando generación, evaluación y resampleo.
        """
        # Paso 1: Generar candidatos iniciales
        candidates = self.generate_candidates(prompt, temperature=self.params.get('temperature_generate', 0.7),
                                              n=self.params.get('num_candidates_initial', 3))

        rounds_log = []   # lista para guardar la evolución

        # Paso 2: Iterar refinamientos
        for iteration in range(self.params.get('max_iterations', 3)):
            # Evaluar candidatos
            scored_candidates = self.score_candidates(candidates)

            # Guardar los candidatos y scores de esta iteración
            rounds_log.append({
                "iteración": iteration + 1,
                "candidatos": [{"prompt": c, "score": s} for c, s in scored_candidates]
            })

            # Seleccionar top-k%
            top_candidates = self.select_top_candidates(scored_candidates)

            # Resamplear alrededor de los mejores
            candidates = self.resample_candidates(top_candidates)

            # Opcional: log info si debug_mode está activo
            if self.params.get('debug_mode', False):
                print(f"Iteración {iteration + 1}: {len(candidates)} prompts generados tras resampleo")

        # Paso 3: Evaluar candidatos finales
        final_scored = self.score_candidates(candidates)

        # Devolver el mejor prompt
        best_prompt = max(final_scored, key=lambda x: x[1])[0]
        return best_prompt, rounds_log

    def generate_candidates(self, prompt: str, temperature: float, n: int) -> list[str]:
        """
        Genera 'n' variantes refinadas de un prompt inicial a una cierta temperatura.
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "Eres un experto en ingeniería de prompts. Dada una instrucción genérica, "
                    "genera múltiples versiones alternativas mejoradas, manteniendo el significado "
                    "pero optimizando la claridad, la precisión y la efectividad."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Genera {n} variantes refinadas del siguiente prompt:\n\n"
                    f"'{prompt}'\n\n"
                    f"Entrega únicamente la lista, una variante por línea."
                )
            }
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            n=1  # Solo una llamada que devuelve todas las variantes en texto
        )

        content = response.choices[0].message.content.strip()

        # Parseamos el contenido en una lista
        candidates = [line.strip("-• ") for line in content.splitlines() if line.strip()]
        return candidates

    def score_candidates(self, candidates: list[str]) -> list[tuple[str, float]]:
        """
        Evalúa una lista de prompts candidatos y les asigna una puntuación de calidad.
        """
        scored_candidates = []

        for prompt in candidates:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Eres un crítico experto en prompts para LLMs. "
                        "Tu tarea es evaluar la calidad de un prompt "
                        "considerando claridad, especificidad y utilidad para obtener buenas respuestas."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Evalúa este prompt del 0 al 10, siendo 10 excelente y 0 muy malo:\n\n"
                        f"'{prompt}'\n\n"
                        "Devuelve únicamente un número, sin texto adicional."
                    )
                }
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.params.get('temperature_score', 0.0),
                n=1
            )

            score_text = response.choices[0].message.content.strip()

            # Intentamos convertir el resultado en un número flotante
            try:
                score = float(score_text.split()[0])  # Coge el primer número que aparezca
            except ValueError:
                score = 0.0  # Si no se puede convertir, puntuamos como 0

            scored_candidates.append((prompt, score))

        return scored_candidates

    def select_top_candidates(self, scored_candidates: list[tuple[str, float]]) -> list[str]:
        """
        Selecciona el top-k% de prompts candidatos basándose en la puntuación.
        """
        # Ordenamos los candidatos de mayor a menor puntuación
        sorted_candidates = sorted(scored_candidates, key=lambda x: x[1], reverse=True)

        # Calculamos cuántos prompts seleccionar
        k_percent = self.params.get('top_k_percent', 40) / 100  # Convertimos a decimal
        top_k = max(1, int(len(sorted_candidates) * k_percent))  # Siempre al menos 1

        # Seleccionamos los mejores
        top_candidates = [prompt for prompt, _ in sorted_candidates[:top_k]]

        return top_candidates

    def resample_candidates(self, top_candidates: list[str]) -> list[str]:
        """
        Genera nuevas variantes refinadas a partir de los mejores prompts.
        """
        resampled_prompts = []

        # Número de variantes a generar por prompt
        resamples_per_prompt = self.params.get('resamples_per_prompt', 2)

        for prompt in top_candidates:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Eres un experto en reformular prompts para mantener su significado "
                        "pero mejorar su claridad, especificidad y efectividad."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Genera {resamples_per_prompt} variantes de este prompt manteniendo el significado pero reformulándolo:\n\n"
                        f"'{prompt}'\n\n"
                        f"Entrega únicamente la lista, una variante por línea."
                    )
                }
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.params.get('temperature_resample', 0.6),
                n=1
            )

            content = response.choices[0].message.content.strip()

            # Parseamos la respuesta
            new_variants = [line.strip("-• ") for line in content.splitlines() if line.strip()]
            resampled_prompts.extend(new_variants)

        return resampled_prompts


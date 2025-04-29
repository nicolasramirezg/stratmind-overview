class RecursiveDecomposer:
    def __init__(self, analyzer, decomposer, max_depth: int = 2, verbose: bool = True):
        """
        analyzer: instancia de TaskAnalyzer
        decomposer: instancia de Decomposer
        max_depth: nivel máximo de recursividad permitido
        """
        self.analyzer = analyzer
        self.decomposer = decomposer
        self.max_depth = max_depth
        self.verbose = verbose  # Nuevo parámetro para controlar si queremos logs

    def decompose(self, task: str, depth: int = 0) -> list[dict]:   # list[str]
        if self.verbose:
            print(f"\n{'-' * 40}\nAnalizando tarea en profundidad {depth}:\n{task}\n{'-' * 40}")

        if depth > self.max_depth:
            if self.verbose:
                print(f"Profundidad máxima alcanzada ({depth}). No subdividir más.\n")
            return [{"task": task, "depth": depth, "type": "max_depth"}]
            # return [task]

        analysis = self.analyzer.analyze_task(task)

        if self.verbose:
            print(f"Resultado del análisis: {analysis['complexity']} — {analysis['reasoning']}")

        task_node = {
            "task": task,
            "depth": depth,
            "type": analysis["complexity"]
        }

        if analysis["complexity"] == "simple":
            if self.verbose:
                print(f"Tarea considerada simple. Se añade directamente.\n")
            return  [task_node]

        else:
            if self.verbose:
                print(f"Tarea compleja detectada. Subdividiendo...\n")
            subtasks = self.decomposer.decompose(task) # llamamos a Decomposer.decompose()

            final_subtasks = []
            for idx, subtask in enumerate(subtasks, 1):
                if self.verbose:
                    print(f"  ➔ Subtarea {idx}: {subtask}")
                decomposed = self.decompose(subtask, depth=depth + 1) #Recursive.decompose
                final_subtasks.extend(decomposed)

            return [task_node] + final_subtasks


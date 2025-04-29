from datetime import datetime
from src.refiner_ape import RefinerAPE
from src.task_analyzer import TaskAnalyzer
from src.decomposer import Decomposer
from src.recursive_decomposer import RecursiveDecomposer
from src.utils.run_logger import save_run

from dotenv import load_dotenv

load_dotenv()  # Solo esto, para cargar el .env

def main():
    prompt = "prepara un viaje a cuenca de 3 días"

    params = {
        "num_candidates_initial": 3,
        "resamples_per_prompt": 1,
        "top_k_percent": 30,
        "max_iterations": 3,
        "temperature_generate": 0.7,
        "temperature_resample": 0.6,
        "temperature_score": 0.0,
        "scoring_mode": "simple",
        "debug_mode": True,  # --> Este no lo usa nadie todavía, pero no rompe nada
    }

    refiner = RefinerAPE(model="gpt-3.5-turbo",params=params)
    refined_prompt, rounds_log = refiner.refine(prompt)

    print("Prompt refinado:")
    print(refined_prompt)

    # # Analizar la complejidad de la tarea
    analyzer = TaskAnalyzer(model="gpt-3.5-turbo")
    analysis = analyzer.analyze_task(refined_prompt)
    print(analysis)

    decomposer = Decomposer(model="gpt-3.5-turbo")
    analyzer = TaskAnalyzer(model="gpt-3.5-turbo")
    recursive_decomposer = RecursiveDecomposer(
        analyzer=analyzer,
        decomposer=decomposer,
        max_depth=2,
        verbose=True
    )

    all_task_nodes  = recursive_decomposer.decompose(refined_prompt)

    # Subtareas finales (solo las 'simple')
    final_subtasks = [
        {"task": node["task"], "depth": node["depth"]}
        for node in all_task_nodes
        if node["type"] in ["simple", "max_depth"]
    ]

    # Registro completo (todos los task_nodes)
    generated_tasks = all_task_nodes

    print("\n Subtareas generadas:")
    for idx, subtask in enumerate(final_subtasks, 1):
        print(f"{idx}. {subtask}")

    # ---- Construimos el log completo
    log_data = {
        "prompt_inicial": prompt,
        "prompt_refinado": refined_prompt,
        "refiner_intermedio": rounds_log,
        "análisis": {
            "complexity": analysis["complexity"],
            "reasoning": analysis.get("reasoning", "")
        },
        "tareas_generadas": generated_tasks,
        "subtareas_finales": final_subtasks,
        "metadata": {
            "modelo": "gpt-3.5-turbo",
            "timestamp": datetime.now().isoformat()
        }
    }

    # ---- Guardamos
    save_run(log_data)

if __name__ == "__main__":
    main()

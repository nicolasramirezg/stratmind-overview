from src.decomposer_agent import Decomposer
from src.specialist_agent import SpecialistAgent
from src.task_refiner_agent import TaskRefiner
from src.recursive_refiner import refine_recursively

from src.utils.run_logger import save_run

from dotenv import load_dotenv

load_dotenv()  # Solo esto, para cargar el .env

def print_refined_tree(refined_tree: dict):
    for area, subtasks in refined_tree.items():
        print(f"\nArea: {area}")
        for i, item in enumerate(subtasks, 1):
            print(f"  {i}. {item['original']}")
            if item["refined"]:
                for j, refined in enumerate(item["refined"], 1):
                    print(f"     {i}.{j} {refined}")
            else:
                print(f"     {i}.✓ No refinement needed")

def main():
    task_description = ("organiza un evento de charlas ted de 1 día")

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

    # 1. Descomponer la tarea en áreas funcionales
    decomposer = Decomposer()

    area_divisions = decomposer.decompose(task_description)

    print("Intro:\n", area_divisions["intro"])

    # Mostrar cada subtarea de forma legible
    for i, subtask in enumerate(area_divisions["subtasks"], 1):
        print(f"\nSubtarea {i}:")
        for key, value in subtask.items():
            print(f"  {key}: {value}")

    # 2. Generar subtareas concretas para cada área
    specialist = SpecialistAgent()
    subtasks_by_area = specialist.plan_subtasks(area_divisions, task_description)

    for area, subtasks in subtasks_by_area.items():
        print(f"\nArea: {area}")
        for i, subtask in enumerate(subtasks, 1):
            print(f"  {i}. {subtask}")

    # 3. Subdividimos las tareas de manera recursiva
    task_refiner = TaskRefiner()
    refined_tree = {}

    for area_name, subtasks in subtasks_by_area.items():
        refined_tree[area_name] = []

        for subtask in subtasks:
            result = refine_recursively(
                subtask=subtask,
                area_name=area_name,
                global_task=task_description,
                refiner=task_refiner ,
                max_depth=3
            )
            refined_tree[area_name].append(result)

    print_refined_tree(refined_tree)

    save_run(task_description, area_divisions, refined_tree, "output")

if __name__ == "__main__":
    main()

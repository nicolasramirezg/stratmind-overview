from src.decomposer_agent_nojson import Decomposer
from src.specialist_agent import SpecialistAgent
from src.task_refiner_agent import TaskRefiner
from src.recursive_refiner_parent_subtask import refine_recursively
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

    task_description = "Diseña una arquitectura que permita la operar con criptomonedas"

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

    for area_data in subtasks_by_area:
        area = area_data["area"]
        subtasks = area_data["subtasks"]

        print(f"\nArea: {area}")
        for i, subtask in enumerate(subtasks, 1):
            print(f"  {i}. {subtask}")

    # 3. Subdividimos las tareas de manera recursiva
    task_refiner = TaskRefiner()
    refined_tree = {}

    for area_data in subtasks_by_area:
        area_name = area_data["area"]
        subtasks = area_data["subtasks"]

        refined_tree[area_name] = []

        for subtask in subtasks:
            result = refine_recursively(
                subtask=subtask,
                area_name=area_name,
                global_task=task_description,
                refiner=task_refiner,
                max_depth=3,
                parent_subtask=None  # <- Añadido para raíz
            )
            refined_tree[area_name].append(result)

    print_refined_tree(refined_tree)

    save_run(task_description, area_divisions, refined_tree, "output")


if __name__ == "__main__":
    main()

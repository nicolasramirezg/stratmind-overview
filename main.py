# Módulos estándar
import json
import os
from datetime import datetime

# Paquetes externos
from dotenv import load_dotenv

# Módulos locales
from src.class_task import TaskManager, create_and_link_subtasks
from src.decomposer_agent import Decomposer
from src.executor_agent import execute_tasks_postorder
from src.recursive_refiner_parent_subtask import refine_recursively
from src.specialist_agent import SpecialistAgent
from src.task_refiner_agent import TaskRefiner
from src.utils.task_exporter import export_task_tree
from src.utils.task_to_dict import task_to_dict


load_dotenv()  # Solo esto, para cargar el .env

def main():
    print("Iniciando main()")
    
    task_description = "Haz un plan de viaje a Bogotá, Colombia, incluyendo actividades, lugares turísticos, gastronomía y cultura local."

    task_manager = TaskManager()
    print("Creando tarea raíz...")

    ### añadir refinamiento aquí de la tarea inicial que genere un prompt elaborado?

    # Tarea raíz
    root_task = task_manager.create_task(
        title=f"Tarea principal: {task_description}",
        description=task_description,
        expected_output="Un plan de viaje detallado"
    )

    # 1. Descomponer la tarea en áreas funcionales
    print("Descomponiendo en áreas funcionales...")
    decomposer = Decomposer()
    area_divisions = decomposer.decompose(
        root_task.description,
        root_task.expected_output
    )

    # Guardar la introducción generada por el LLM en la tarea raíz
    root_task.intro = area_divisions["intro"]

    print("Intro:\n", area_divisions["intro"])

    # Crear subtareas de área como hijas del root_task
    print("Creando tareas de área...")
    for subtask in area_divisions["subtasks"]:
        print(f"  - Área: {subtask['area']}")
        task_manager.create_task(
            title=subtask["area"],
            description=subtask["description"],
            expected_output=subtask["expected_output"], 
            area=subtask["area"],
            responsibilities=subtask["responsibilities"],
            parent_id=root_task.task_id,
            execution_type=subtask.get("execution_type", "llm")
        )

    print("Preparando áreas para SpecialistAgent...")

    # 2. Generar subtareas concretas para cada área
    # Obtener las áreas funcionales desde el árbol de tareas
    areas = [t for t in task_manager.tasks.values() if t.parent == root_task]


    # Preparar la estructura esperada por SpecialistAgent
    area_divisions_from_tasks = {
        "subtasks": [
            {
                "area": area.area,
                "description": area.description,
                "expected_output": area.expected_output,
                "responsibilities": getattr(area, "responsibilities", [])
            }
            for area in areas
        ]
    }
    print("Llamando a SpecialistAgent...")
    specialist = SpecialistAgent()
    subtasks_by_area = specialist.plan_subtasks(area_divisions_from_tasks, task_description)

    print("Creando subtareas concretas y resolviendo dependencias...")
    # Almacenar subtareas concretas como hijas de cada área y resolver dependencias
    for area_data in subtasks_by_area:
        area = area_data["area"]
        subtasks = area_data["subtasks"]
        print(f"  - Área: {area}, {len(subtasks)} subtareas")
        area_task = next(
            (t for t in task_manager.tasks.values()
            if t.area == area and t.parent == root_task),
            None
        )
        if not area_task:
            print(f"    ⚠️ No se encontró tarea de área para {area}")
            continue
        # Usa la función utilitaria
        create_and_link_subtasks(subtasks, area, area_task, task_manager)


    # 3. Subdividimos las tareas de manera recursiva
    print("Iniciando refinamiento recursivo...")
    task_refiner = TaskRefiner()

    # Recorre áreas funcionales desde el árbol real
    for area_task in [t for t in task_manager.tasks.values() if t.parent == root_task]:
        area_name = area_task.area
        print(f"  Refinando área: {area_name}")
        for subtask_task in [t for t in task_manager.tasks.values() if t.parent == area_task]:
            print(f"    Refinando subtask: {subtask_task.title}")
            subtask_dict = {
                "title": subtask_task.title,
                "description": subtask_task.description,
                "expected_output": subtask_task.expected_output
            }

            refine_recursively(
                subtask=subtask_dict,
                area_name=area_name,
                global_task=task_description,
                refiner=task_refiner,
                task_manager=task_manager,
                max_depth=3,
                parent_subtask=subtask_task
            )
    print("Fin del refinamiento recursivo.")

    print("Executing all tasks with LLM or simulation as needed...")
    execute_tasks_postorder(root_task)

    # Exportar con nombre personalizado
    export_task_tree(root_task, task_manager, out_name="task_tree_bogota")

if __name__ == "__main__":
    main()


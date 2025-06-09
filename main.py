from src.decomposer_agent_nojson import Decomposer
from src.specialist_agent import SpecialistAgent
from src.task_refiner_agent import TaskRefiner
from src.recursive_refiner_parent_subtask import refine_recursively
from src.utils.run_logger import save_run
from src.class_task import Task, TaskManager
import os
import json

from dotenv import load_dotenv

load_dotenv()  # Solo esto, para cargar el .env


def main():
    print("Iniciando main()")
    
    task_manager = TaskManager()
    task_description = "Planea un viaje a Colombia para 1 semana"
    print("Creando tarea raíz...")
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

    print("Intro:\n", area_divisions["intro"])

    #Crear subtareas de área como hijas del root_task
    print("Creando tareas de área...")
    for subtask in area_divisions["subtasks"]:
        print(f"  - Área: {subtask['area']}")
        task_manager.create_task(
            title=subtask["area"],
            description=subtask["description"],
            expected_output=subtask["expected_output"], 
            area=subtask["area"],
            responsibilities=subtask["responsibilities"],
            parent_id=root_task.task_id
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
    subtasks_by_area = specialist.plan_subtasks(
        area_divisions_from_tasks,
        task_description
    )

    print("Creando subtareas concretas y resolviendo dependencias...")
    # Almacenar subtareas concretas como hijas de cada área y resolver dependencias
    for area_data in subtasks_by_area:
        area = area_data["area"]
        subtasks = area_data["subtasks"]
        print(f"  - Área: {area}, {len(subtasks)} subtareas")
        # Buscar la tarea de área correspondiente
        area_task = next(
            (t for t in task_manager.tasks.values()
             if t.area == area and t.parent == root_task),
            None
        )
        if not area_task:
            print(f"    ⚠️ No se encontró tarea de área para {area}")
            continue

        # Primero, crea todas las subtareas y guárdalas en un dict temporal por título
        subtask_objs = {}
        for subtask in subtasks:
            print(f"    Creando subtask: {subtask.get('title', subtask)}")
            st = task_manager.create_task(
                title=subtask["title"],
                description=subtask["description"],
                expected_output=subtask["expected_output"],
                area=area,
                parent_id=area_task.task_id
            )
            subtask_objs[subtask["title"]] = st

        # Luego, resuelve dependencias usando los títulos
        for subtask in subtasks:
            if subtask["dependencies"]:
                for dep_title in subtask["dependencies"]:
                    dep_task = subtask_objs.get(dep_title)
                    if dep_task:
                        subtask_objs[subtask["title"]].add_dependency(dep_task)
        

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
    print("Fin de main()")


    def task_to_dict(task, task_manager):
        return {
            "task_id": task.task_id,
            "title": task.title,
            "description": task.description,
            "expected_output": task.expected_output,
            "area": task.area,
            "responsibilities": getattr(task, "responsibilities", []),
            "parent": task.parent.task_id if task.parent else None,
            "dependencies": [dep.task_id for dep in getattr(
                task,
                "dependencies",
                set())],
            "subtasks": [
                task_to_dict(child, task_manager)
                for child in task_manager.tasks.values()
                if child.parent == task
            ]
        }

    # Al final de tu main():
    output_dir = os.path.join(os.getcwd(), "output")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "task_tree.json")

    tree_json = task_to_dict(root_task, task_manager)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(tree_json, f, indent=2, ensure_ascii=False)

    print(f"\nÁrbol de tareas exportado a: {output_path}")
    

if __name__ == "__main__":
    main()


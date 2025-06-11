from src.decomposer_agent import Decomposer
from src.specialist_agent import SpecialistAgent
from src.task_refiner_agent import TaskRefiner
from src.recursive_refiner_parent_subtask import refine_recursively
from src.utils.task_exporter import export_task_tree
from src.utils.task_exporter_txt import export_task_tree_txt
from src.class_task import TaskManager
from dotenv import load_dotenv

load_dotenv()  # Solo esto, para cargar el .env


def main():
    print("Iniciando main()")
    
    task_description = "Planea un viaje a cuenca de un fin de semana"

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
            parent_id=root_task.task_id
        )

    print("Preparando áreas para SpecialistAgent...")

    # 2. Generar subtareas concretas para cada área
    # Obtener las áreas funcionales desde el árbol de tareas
    areas = []
    for task_id, task_obj in task_manager.tasks.items():
        if task_obj.parent == root_task:
            areas.append(task_obj)

    # Preparar la estructura esperada por SpecialistAgent
    area_divisions_from_tasks = {
        "subtasks": []
    }

    for area in areas:
        area_data = {
            "area": area.area,
            "description": area.description,
            "expected_output": area.expected_output,
            "responsibilities": area.responsibilities if area.responsibilities else []
        }
        area_divisions_from_tasks["subtasks"].append(area_data)

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

        area_task = next(
            (t for t in task_manager.tasks.values()
             if t.area == area and t.parent == root_task),
            None
        )

        if not area_task:
            print(f"⚠️  Área ignorada (no encontrada en árbol): {area}")
            continue

        # Crear subtareas
        subtask_objs = {}
        for subtask in subtasks:
            st = task_manager.create_task(
                title=subtask["title"],
                description=subtask["description"],
                expected_output=subtask["expected_output"],
                area=area,
                parent_id=area_task.task_id
            )
            subtask_objs[subtask["title"]] = st

        print(f"\n🧩 Área '{area}': {len(subtasks)} subtareas creadas")

        # Resolver dependencias
        dep_count = 0
        for subtask in subtasks:
            if subtask["dependencies"]:
                for dep_title in subtask["dependencies"]:
                    dep_task = subtask_objs.get(dep_title)
                    if dep_task:
                        subtask_objs[subtask["title"]].add_dependency(dep_task)
                        dep_count += 1

        if dep_count > 0:
            print(f"🔗 {dep_count} dependencias establecidas en subtareas de '{area}'")

    # 3. Subdividimos las tareas de manera recursiva
    print("\n🚀 Iniciando refinamiento recursivo...")
    task_refiner = TaskRefiner()
    refined_total = 0

    for area_task in [t for t in task_manager.tasks.values() if t.parent == root_task]:
        area_name = area_task.area
        print(f"\n🔍 Refinando área: {area_name}")

        subtasks = []

        for t in task_manager.tasks.values():
            if t.parent == area_task:
                subtasks.append(t)

        for subtask in subtasks:
            print(f"   ↳ Subtarea: {subtask.title}")
            subtask_dict = {
                "title": subtask.title,
                "description": subtask.description,
                "expected_output": subtask.expected_output
            }

            new_tasks = refine_recursively(
                subtask=subtask_dict,
                area_name=area_name,
                global_task=task_description,
                refiner=task_refiner,
                task_manager=task_manager,
                max_depth=1,
                parent_subtask=subtask
            )
            refined_total += len(new_tasks) if isinstance(new_tasks, list) else 0

    print(f"\n✅ Refinamiento completo. Total de nuevas subtareas generadas: {refined_total}")

    export_task_tree(root_task, task_manager)

if __name__ == "__main__":
    main()


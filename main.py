from dotenv import load_dotenv
# Local modules
from src.utils.class_task import TaskManager, create_and_link_subtasks
from src.agents.decomposer_agent import Decomposer
from src.agents.executor_agent import execute_tasks_postorder
from src.utils.recursive_refiner_parent_subtask import refine_recursively
from src.agents.specialist_agent import SpecialistAgent, get_other_areas_subtasks
from src.agents.task_refiner_agent import TaskRefiner
from src.utils.task_exporter import export_task_tree

load_dotenv()

def create_root_task(task_manager, task_description, expected_output):
    """
    Create the root task for the project.
    """
    return task_manager.create_task(
        title=task_description,
        description=task_description,
        expected_output=expected_output
    )

def decompose_into_areas(root_task, decomposer):
    """
    Decompose the root task into functional areas.
    """
    area_divisions = decomposer.decompose(
        root_task.description,
        root_task.expected_output
    )
    root_task.intro = area_divisions["intro"]
    print("Intro:\n", area_divisions["intro"])
    return area_divisions

def create_area_tasks(task_manager, root_task, area_divisions):
    """
    Create area tasks under the root task.
    """
    for subtask in area_divisions["subtasks"]:
        print(f"  - Area: {subtask['area']}")
        task_manager.create_task(
            title=subtask["area"],
            description=subtask["description"],
            expected_output=subtask["expected_output"], 
            area=subtask["area"],
            responsibilities=subtask["responsibilities"],
            parent_id=root_task.task_id,
            execution_type=subtask.get("execution_type", "llm")
        )

def plan_area_subtasks(task_manager, root_task, specialist, task_description):
    """
    Generate concrete subtasks for each area and resolve dependencies.
    """
    areas = [t for t in task_manager.tasks.values() if t.parent == root_task]
    all_area_names = [area.area for area in areas]
    for area in areas:
        other_area_subtasks = get_other_areas_subtasks(task_manager, area, root_task)
        area_division = {
            "area": area.area,
            "description": area.description,
            "expected_output": area.expected_output,
            "responsibilities": getattr(area, "responsibilities", []),
            "other_area_subtasks": other_area_subtasks,
            "all_area_names": all_area_names
        }
        subtasks_by_area = specialist.plan_subtasks({"subtasks": [area_division]}, task_description)
        print("Creating concrete subtasks and resolving dependencies...")
        for area_data in subtasks_by_area:
            area_name = area_data["area"]
            subtasks = area_data["subtasks"]
            print(f"  - Area: {area_name}, {len(subtasks)} subtasks")
            area_task = next(
                (t for t in task_manager.tasks.values()
                if t.area == area_name and t.parent == root_task),
                None
            )
            if not area_task:
                print(f"!! Area task not found for {area_name}")
                continue
            create_and_link_subtasks(subtasks, area_name, area_task, task_manager)

def refine_all_subtasks(task_manager, root_task, task_refiner, task_description, max_depth=2):
    """
    Recursively refine ALL subtasks of each area, including all levels.
    """
    for area_task in [t for t in task_manager.tasks.values() if t.parent == root_task]:
        area_name = area_task.area
        print(f"  Refining area: {area_name}")
        def refine_subtree(task, depth=0):
            print(f"    Refining subtask: {task.title}")
            refine_recursively(
                subtask=task,
                area_name=area_name,
                global_task=task_description,
                refiner=task_refiner,
                task_manager=task_manager,
                depth=depth,
                max_depth=max_depth
            )
            for child in task.subtasks:
                refine_subtree(child, depth=depth+1)
        for subtask_task in area_task.subtasks:
            refine_subtree(subtask_task, depth=0)

def print_task_tree(task, level=0):
    print("  " * level + f"- {task.title} (id: {task.task_id})")
    for sub in getattr(task, "subtasks", []):
        print_task_tree(sub, level + 1)

def main():
    print("Starting main()")
    task_description = "Crea un plan de viaje a Bogotá"
    expected_output = "Un plan de viaje detallado."
    task_manager = TaskManager()

    print("Creating root task...")
    root_task = create_root_task(task_manager, task_description, expected_output)

    print("Decomposing into functional areas...")
    decomposer = Decomposer()
    area_divisions = decompose_into_areas(root_task, decomposer)

    print("Creating area tasks...")
    create_area_tasks(task_manager, root_task, area_divisions)

    print("Preparing areas for SpecialistAgent...")
    specialist = SpecialistAgent()
    plan_area_subtasks(task_manager, root_task, specialist, task_description)

    print("Starting recursive refinement...")
    task_refiner = TaskRefiner()
    refine_all_subtasks(task_manager, root_task, task_refiner, task_description)

    print("Executing all tasks with LLM or simulation as needed...")
    execute_tasks_postorder(root_task)

    export_task_tree(root_task, task_manager, out_name="task_tree")

    print("\n=== TASK TREE IN MEMORY BEFORE EXPORT ===")
    print_task_tree(root_task)

if __name__ == "__main__":
    main()
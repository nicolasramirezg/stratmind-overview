from dotenv import load_dotenv
# Local modules
from src.utils.class_task import TaskManager, create_and_link_subtasks
from src.agents.decomposer_agent import Decomposer
from src.agents.executor_agent import execute_tasks_postorder
from src.utils.recursive_refiner_parent_subtask import refine_recursively
from src.agents.specialist_agent import SpecialistAgent, get_other_areas_subtasks
from src.agents.task_refiner_agent import TaskRefiner
from src.utils.task_exporter import export_task_tree
from src.agents.specify_agent import SpecifyAgent
from src.agents.synthesize_agent import SynthesizeAgent


load_dotenv()

def create_root_task(task_manager, task_description, expected_output):
    """
    Create the root task for the project.

    Args:
        task_manager (TaskManager): The task manager instance.
        task_description (str): The clarified task description.
        expected_output (str): The expected output for the root task.

    Returns:
        Task: The created root task.
    """
    return task_manager.create_task(
        title=task_description,
        description=task_description,
        expected_output=expected_output
    )

def decompose_into_areas(root_task, decomposer):
    """
    Decompose the root task into functional areas using the decomposer agent.

    Args:
        root_task (Task): The root task object.
        decomposer (Decomposer): The decomposer agent.

    Returns:
        dict: Area divisions as returned by the decomposer.
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

    Args:
        task_manager (TaskManager): The task manager instance.
        root_task (Task): The root task object.
        area_divisions (dict): The area divisions from the decomposer.
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

    Args:
        task_manager (TaskManager): The task manager instance.
        root_task (Task): The root task object.
        specialist (SpecialistAgent): The specialist agent.
        task_description (str): The clarified task description.
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

    Args:
        task_manager (TaskManager): The task manager instance.
        root_task (Task): The root task object.
        task_refiner (TaskRefiner): The task refiner agent.
        task_description (str): The clarified task description.
        max_depth (int): Maximum recursion depth for refinement.
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
    """
    Recursively prints the task tree to the console.

    Args:
        task (Task): The current task to print.
        level (int): The current depth in the tree (for indentation).
    """
    print("  " * level + f"- {task.title} (id: {task.task_id})")
    for sub in getattr(task, "subtasks", []):
        print_task_tree(sub, level + 1)

def main():
    """
    Main entry point for the CLI workflow.
    Guides the user through clarification, synthesis, decomposition,
    subtask planning, refinement, execution, and export.
    """
    print("Starting main()")

    # Step 1: Interactive clarification
    specify_agent = SpecifyAgent()
    history = specify_agent.interactive_specification()

    # Step 2: Synthesize clarified task and expected output
    synthesize_agent = SynthesizeAgent()
    spec = synthesize_agent.synthesize(history)
    task_description = spec["description"]
    expected_output = spec["expected_output"]

    print("\nFinal clarified task:")
    print("Task:", task_description)
    print("Expected Output:", expected_output)

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

    export_task_tree(
        root_task,
        task_manager,
        out_name="task_tree",
        metadata={
            "clarified_description": task_description,
            "expected_output": expected_output
        }
    )

if __name__ == "__main__":
    main()
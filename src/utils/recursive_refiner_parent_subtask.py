from src.utils.class_task import create_and_link_subtasks
from src.utils.class_task import Task

def refine_recursively(
    subtask: Task,
    area_name: str,
    global_task: str,
    refiner,
    task_manager,
    depth: int = 0,
    max_depth: int = 1,
):
    """
    Recursively refines a subtask using the refiner agent and stores everything in the TaskManager.
    Does not return anything, only updates the TaskManager.
    """
    # Get sibling subtasks titles (excluding the current one)
    siblings = [t for t in task_manager.tasks.values() if t.parent == subtask.parent and t != subtask]
    sibling_titles = [t.title.strip().lower() for t in siblings]

    # Prepare variables for the prompt
    prompt_variables = {
        "area_name": area_name,
        "global_task": global_task,
        "subtask": subtask.title,
        "area_description": subtask.description,
        "parent_task_title": getattr(subtask.parent, "title", "") if subtask.parent else "",
        "existing_sibling_titles": sibling_titles
    }

    # Call the refiner with the appropriate context
    result, raw_prompt, raw_llm_response = refiner.refine(
        **prompt_variables,
        return_prompt_and_response=True 
    )

    # Solo crea hijos si hay refinamiento y no se ha alcanzado la profundidad máxima
    if result["refined"] and depth < max_depth:
        # Crea y enlaza los hijos refinados como subtareas de 'subtask'
        child_tasks = create_and_link_subtasks(
            result["refined"], area_name, subtask, task_manager
        )

        # Llama recursivamente para cada subtask refinada
        for child_subtask in result["refined"]:
            child_task = child_tasks[child_subtask["title"].strip().lower()]
            refine_recursively(
                subtask=child_task,
                area_name=area_name,
                global_task=global_task,
                refiner=refiner,
                task_manager=task_manager,
                depth=depth + 1,
                max_depth=max_depth
            )
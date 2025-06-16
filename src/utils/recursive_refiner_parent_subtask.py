from src.utils.class_task import create_and_link_subtasks

def refine_recursively(
    subtask: dict,
    area_name: str,
    global_task: str,
    refiner,
    task_manager,
    depth: int = 0,
    max_depth: int = 1,
    parent_subtask=None
):
    """
    Refina una subtarea aplicando recursivamente el refiner y almacena todo en el árbol de tareas.
    No devuelve nada, solo almacena en el TaskManager.
    """
    # Llama al refinador con el contexto adecuado
    result = refiner.refine(
        area_name=area_name,
        global_task=global_task,
        subtask=subtask["title"] if isinstance(subtask, dict) else subtask,
        area_description=subtask.get("description", "") if isinstance(subtask, dict) else "",
        root_task_title=getattr(parent_subtask, "root_task_title", "") if parent_subtask else "",
        root_task_description=getattr(parent_subtask, "root_task_description", "") if parent_subtask else "",
        parent_task={
            "title": getattr(parent_subtask, "title", ""),
            "description": getattr(parent_subtask, "description", ""),
            "expected_output": getattr(parent_subtask, "expected_output", "")
        } if parent_subtask else None,
        parent_dependencies=getattr(parent_subtask, "dependencies", []) if parent_subtask else None
    )

    if result["refined"] and depth < max_depth and parent_subtask:
        # Crea y enlaza las subtareas refinadas como hijas del parent_subtask
        child_tasks = create_and_link_subtasks(
            result["refined"], area_name, parent_subtask, task_manager
        )

        # Llama recursivamente para cada subtarea refinada
        for child_subtask in result["refined"]:
            child_task = child_tasks[child_subtask["title"].strip().lower()]
            refine_recursively(
                subtask=child_subtask,
                area_name=area_name,
                global_task=global_task,
                refiner=refiner,
                task_manager=task_manager,
                depth=depth + 1,
                max_depth=max_depth,
                parent_subtask=child_task
            )
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

    # Si hay refinamientos y no hemos alcanzado la profundidad máxima
    if result["refined"] and depth < max_depth and parent_subtask:
        for child_subtask in result["refined"]:
            # Almacena como hija en el árbol real
            child_task = task_manager.create_task(
                title=child_subtask.get("title", child_subtask),
                description=child_subtask.get("description", ""),
                expected_output=child_subtask.get("expected_output", ""),
                area=area_name,
                parent_id=parent_subtask.task_id
            )
            # Recursividad profunda
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
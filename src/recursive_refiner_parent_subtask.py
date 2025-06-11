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
    # 1. Determinar el título y descripción de la subtarea según su tipo
    if isinstance(subtask, dict):
        subtask_title = subtask["title"]
        area_description = subtask.get("description", "")
    else:
        subtask_title = subtask
        area_description = ""

    # 2. Extraer información del parent_subtask si existe
    if parent_subtask:
        root_task_title = getattr(parent_subtask, "root_task_title", "")
        root_task_description = getattr(parent_subtask, "root_task_description", "")

        parent_task = {
            "title": getattr(parent_subtask, "title", ""),
            "description": getattr(parent_subtask, "description", ""),
            "expected_output": getattr(parent_subtask, "expected_output", "")
        }

        parent_dependencies = getattr(parent_subtask, "dependencies", [])
    else:
        root_task_title = ""
        root_task_description = ""
        parent_task = None
        parent_dependencies = None

    # 3. Llamada limpia al refiner con contexto completo
    result = refiner.refine(
        area_name=area_name,
        global_task=global_task,
        subtask=subtask_title,
        area_description=area_description,
        root_task_title=root_task_title,
        root_task_description=root_task_description,
        parent_task=parent_task,
        parent_dependencies=parent_dependencies
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
def refine_recursively(
    subtask: str,
    area_name: str,
    global_task: str,
    refiner,
    depth: int = 0,
    max_depth: int = 3,
    parent_subtask: str = None
) -> dict:
    """
    Refina una subtarea aplicando recursivamente el refiner si es necesario.

    Output: nodo enriquecido con contexto jerárquico:
    {
        "original": "Subtarea original",
        "refined": [...],
        "area": "Nombre del área funcional",
        "global_task": "Tarea principal original",
        "parent_subtask": "Subtarea padre"  # None si es raíz
    }
    """

    # Aplicamos el refinamiento inicial
    result = refiner.refine(area_name, global_task, subtask)

    # Preparamos el nodo con contexto completo
    node = {
        "original": subtask,
        "refined": [],
        "area": area_name,
        "global_task": global_task,
        "parent_subtask": parent_subtask
    }

    # Si hay subtareas y no hemos alcanzado la profundidad máxima
    if result["refined"] and depth < max_depth:
        for child_subtask in result["refined"]:
            child_node = refine_recursively(
                subtask=child_subtask,
                area_name=area_name,
                global_task=global_task,
                refiner=refiner,
                depth=depth + 1,
                max_depth=max_depth,
                parent_subtask=subtask  # esta subtarea actual pasa a ser la padre
            )
            node["refined"].append(child_node)

    return node

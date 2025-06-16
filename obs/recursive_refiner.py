def refine_recursively(
    subtask: str,
    area_name: str,
    global_task: str,
    refiner,
    depth: int = 0,
    max_depth: int = 3,
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

    result = refiner.refine(area_name, global_task, subtask)

    # Verificamos si el resultado tiene subtareas refinadas
    # y si aún no hemos alcanzado la profundidad máxima
    if result["refined"] and depth < max_depth:

        # Creamos una lista vacía para almacenar los resultados refinados
        refined_children = []

        # Recorremos cada sub-subtarea generada por la llamada anterior al modelo
        for child_subtask in result["refined"]:
            # Aplicamos recursivamente el refinamiento sobre esa subtarea
            refined_result = refine_recursively(
                subtask=child_subtask,  # la nueva subtarea a evaluar
                area_name=area_name,  # el área funcional sigue siendo la misma
                global_task=global_task,  # el contexto global original no cambia
                refiner=refiner,  # el objeto que contiene el metodo .refine()
                depth=depth + 1,  # aumentamos el nivel de profundidad
                max_depth=max_depth  # límite de profundidad
            )

            # Guardamos el resultado (que también puede contener más niveles)
            refined_children.append(refined_result)

        # Sustituimos la lista de subtareas originales por las refinadas completas
        result["refined"] = refined_children

    return result

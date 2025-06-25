def task_to_dict(task, task_manager=None):
    """
    Recursively serializes a Task object and its subtasks into a dictionary.

    Args:
        task: The Task object to serialize.
        task_manager: (Optional) The TaskManager instance, not used in this function.

    Returns:
        dict: A dictionary representation of the task and its subtasks.
    """
    data = {
        "task_id": task.task_id,
        "title": task.title,
        "description": task.description,
        "expected_output": task.expected_output,
        "area": task.area,
        "responsibilities": getattr(task, "responsibilities", []),
        "execution_type": getattr(task, "execution_type", "llm"),
        "parent": task.parent.task_id if task.parent else None,
        "dependencies": [dep.task_id for dep in getattr(task, "dependencies", set())],
        "subtasks": [task_to_dict(child) for child in getattr(task, "subtasks", [])]
    }

    # Determine the level (depth) of the task in the tree
    level = 0
    parent = task.parent
    while parent:
        level += 1
        parent = parent.parent

    # Export prompt and result for ALL tasks except root and areas (level > 1)
    if level >= 2:
        data["prompt"] = getattr(task, "prompt", None)
        data["result"] = getattr(task, "result", None)
    else:
        data["result"] = getattr(task, "result", None)
    return data
def task_to_dict(task, task_manager=None):
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
    # Export prompt and result for ALL tasks except root and areas (nivel > 1)
    level = 0
    parent = task.parent
    while parent:
        level += 1
        parent = parent.parent
    if level >= 2:
        data["prompt"] = getattr(task, "prompt", None)
        data["result"] = getattr(task, "result", None)
    else:
        data["result"] = getattr(task, "result", None)
    return data
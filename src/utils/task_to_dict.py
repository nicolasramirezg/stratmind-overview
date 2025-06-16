def task_to_dict(task, task_manager):
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
        "subtasks": [
            task_to_dict(child, task_manager)
            for child in task_manager.tasks.values()
            if child.parent == task
        ]
    }
    # Solo exporta prompt y result si no es área
    if not [t for t in task_manager.tasks.values() if t.parent == task]:
        data["prompt"] = getattr(task, "prompt", None)
        data["result"] = getattr(task, "result", None)
    else:
        data["result"] = getattr(task, "result", None)
    return data

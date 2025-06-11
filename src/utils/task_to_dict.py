def task_to_dict(task, manager):
    return {
        "task_id": task.task_id,
        "title": task.title,
        "description": task.description,
        "expected_output": task.expected_output,
        "intro": getattr(task, "intro", None),  # ⬅️ NUEVO
        "area": task.area,
        "responsibilities": getattr(task, "responsibilities", []),
        "parent": task.parent.task_id if task.parent else None,
        "dependencies": [dep.task_id for dep in getattr(task, "dependencies", set())],
        "subtasks": [
            task_to_dict(child, manager)
            for child in manager.tasks.values()
            if child.parent == task
        ]
    }

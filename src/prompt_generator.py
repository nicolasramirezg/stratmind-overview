from src.class_task import Task, TaskManager
from openai import OpenAI

def build_system_prompt(task: Task) -> str:
    """
    Returns the system prompt for the LLM agent, emphasizing its role in a larger project.
    """
    return (
        "You are an expert autonomous agent collaborating in a multi-step project. "
        "You must resolve your assigned task using all available context and previous results. "
        "Be decisive, avoid repetition, and always act as a responsible project agent."
    )

def build_user_prompt(
    task: Task,
    project_title: str = "",
    max_subtasks: int = 3,
    max_chars_per_result: int = 800
) -> str:
    """
    Returns a structured, generic user prompt for the LLM agent.
    Only includes results of direct children (not grandchildren).
    """
    prompt_parts = []
    if project_title:
        prompt_parts.append(f"=== PROJECT ===\nTitle: {project_title}\n")

    # Include area if the parent is not the root
    if task.parent and task.parent.parent is not None:
        prompt_parts.append(f"=== AREA ===\nTitle: {task.parent.title}")
        if getattr(task.parent, "description", None):
            prompt_parts.append(f"Description: {task.parent.description}")
        prompt_parts.append("")

    dependencies = getattr(task, "dependencies", set())
    if dependencies:
        prompt_parts.append("=== DEPENDENCY RESULTS ===")
        prompt_parts.append("The following tasks must be completed before this one. Their results are provided for your reference:\n")
        for dep in dependencies:
            if hasattr(dep, "result") and dep.result:
                dep_result = str(dep.result)
                if len(dep_result) > max_chars_per_result:
                    dep_result = dep_result[:max_chars_per_result] + "\n...[truncated]..."
                prompt_parts.append(f"- Dependency: {dep.title}\n  Description: {dep.description}\n  Result: {dep_result}\n")
        prompt_parts.append("")

    prompt_parts.append("=== CURRENT TASK ===")
    prompt_parts.append(f"Title: {task.title}")
    prompt_parts.append(f"Description: {task.description}")
    prompt_parts.append(f"Expected Output: {task.expected_output}\n")

    # Only include direct children's results (not grandchildren)
    subtasks = [t for t in task.manager.tasks.values() if t.parent == task]
    if subtasks:
        prompt_parts.append("=== SUBTASK RESULTS ===")
        for sub in subtasks[:max_subtasks]:
            if hasattr(sub, "result") and sub.result:
                if isinstance(sub.result, dict):
                    prompt_parts.append(f"- {sub.title}: [Has {len(sub.result)} subtasks. See details in their own context.]")
                else:
                    result_text = str(sub.result)
                    if len(result_text) > max_chars_per_result:
                        result_text = result_text[:max_chars_per_result] + "\n...[truncated]..."
                    prompt_parts.append(f"- {sub.title}: {result_text}")
        prompt_parts.append("")

    prompt_parts.append(
        "=== INSTRUCTION ===\n"
        "You are responsible for completing the current task as part of the overall project. "
        "Use all available context, including dependency and previous results, but present your answer as your own expert recommendation or decision. "
        "Do NOT use phrases like 'Based on previous research' or 'According to earlier results'. "
        "Be direct, decisive, and act as an autonomous agent: provide your output as if you are the main expert responsible for this part of the project. "
        "If the task requires an external system or manual intervention, specify this clearly."
    )
    return "\n".join(prompt_parts)

def call_llm(system_prompt: str, user_prompt: str, model: str = "gpt-3.5-turbo") -> str:
    """
    Calls the real LLM (OpenAI) to get a response for the given prompts.
    """
    client = OpenAI()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[LLM ERROR]: {str(e)}"

def simulate_external_response(prompt: str, task: Task) -> str:
    """
    Simulates a generic response for tasks requiring external execution.
    """
    return (
        f"Simulation: The task '{task.title}' has been marked as completed by an external system or manual process.\n"
        f"Details: {task.description}\n"
        f"Expected Output: {task.expected_output}\n"
        f"(Prompt used: {prompt[:100]}...)"
    )

def execute_tasks_postorder(task: Task, prompts_and_responses=None, model: str = "gpt-3.5-turbo", level: int = 0):
    """
    Executes tasks in post-order (from leaves to root), respecting dependencies and project context.
    - Root (level 0) and areas (level 1) only aggregate results, no prompt/result.
    - Subtasks (level >= 2) generate prompt/result, using direct child results as context if present.
    """
    if prompts_and_responses is None:
        prompts_and_responses = []

    subtasks = [t for t in task.manager.tasks.values() if t.parent == task]
    for sub in subtasks:
        execute_tasks_postorder(sub, prompts_and_responses, model=model, level=level+1)

    # Root and areas: only aggregate results, no prompt/result
    if level == 0 or level == 1:
        if subtasks:
            task.result = {sub.title: sub.result for sub in subtasks}
        task.prompt = None
        return prompts_and_responses

    # For subtasks (level >= 2): build prompt including direct child results (if any)
    system_prompt = build_system_prompt(task)
    user_prompt = build_user_prompt(task, project_title=task.manager.tasks[task.manager.root_task_id].title)
    full_prompt = {"system": system_prompt, "user": user_prompt}

    execution_type = getattr(task, "execution_type", "llm")
    if execution_type == "llm":
        response = call_llm(system_prompt, user_prompt, model=model)
    else:
        response = simulate_external_response(user_prompt, task)

    task.prompt = full_prompt
    task.result = response
    prompts_and_responses.append({
        "task_id": task.task_id,
        "prompt": full_prompt,
        "response": response
    })
    return prompts_and_responses

# Example usage:
# from src.class_task import TaskManager
# task_manager = TaskManager()
# ... (build your task tree, setting execution_type as needed) ...
# prompts_responses = execute_tasks_postorder(task_manager.root_task)
# for item in prompts_responses:
#     print(item["prompt"])
#     print(item["response"])
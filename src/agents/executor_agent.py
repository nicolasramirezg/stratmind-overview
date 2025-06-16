from src.utils.class_task import Task
from openai import OpenAI
from src.utils.prompt_loader import load_prompt
import os

PROMPT_DIR = os.path.join("prompts", "executor_agent")

def build_system_prompt(task: Task) -> str:
    """
    Loads the system prompt for the LLM agent from an external .txt file.
    """
    prompt_path = os.path.join(PROMPT_DIR, "system.txt")
    return load_prompt(prompt_path, variables={})  # <-- FIXED

def build_user_prompt(
    task: Task,
    project_title: str = "",
    max_subtasks: int = 3,
    max_chars_per_result: int = 800
) -> str:
    """
    Loads and formats the user prompt for the LLM agent from an external .txt file.
    """
    prompt_path = os.path.join(PROMPT_DIR, "user.txt")

    # Build dynamic sections
    area_section = ""
    if task.parent and task.parent.parent is not None:
        area_section = f"=== AREA ===\nTitle: {task.parent.title}\nDescription: {getattr(task.parent, 'description', '')}\n"
    dependency_section = ""
    dependencies = getattr(task, "dependencies", set())
    if dependencies:
        dep_lines = []
        for dep in dependencies:
            dep_result = str(dep.result)[:max_chars_per_result] if hasattr(dep, "result") and dep.result else ""
            dep_lines.append(f"- Dependency: {dep.title}\n  Description: {dep.description}\n  Result: {dep_result}\n")
        dependency_section = "=== DEPENDENCY RESULTS ===\n" + "\n".join(dep_lines)
    subtask_section = ""
    subtasks = [t for t in task.manager.tasks.values() if t.parent == task]
    if subtasks:
        sub_lines = []
        for sub in subtasks[:max_subtasks]:
            if hasattr(sub, "result") and sub.result:
                if isinstance(sub.result, dict):
                    sub_lines.append(f"- {sub.title}: [Has {len(sub.result)} subtasks. See details in their own context.]")
                else:
                    result_text = str(sub.result)
                    if len(result_text) > max_chars_per_result:
                        result_text = result_text[:max_chars_per_result] + "\n...[truncated]..."
                    sub_lines.append(f"- {sub.title}: {result_text}")
        subtask_section = "=== SUBTASK RESULTS ===\n" + "\n".join(sub_lines)

    variables = {
        "project_title": project_title,
        "area_section": area_section,
        "dependency_section": dependency_section,
        "task_title": task.title,
        "task_description": task.description,
        "expected_output": task.expected_output,
        "subtask_section": subtask_section
    }

    return load_prompt(prompt_path, variables)

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

from src.utils.class_task import Task
from openai import OpenAI
from src.utils.prompt_loader import load_prompt
import os

# Directory where the executor agent's prompt templates are stored
PROMPT_DIR = os.path.join("prompts", "executor_agent")

def build_system_prompt(task: Task) -> str:
    """
    Loads the system prompt for the LLM agent from an external .txt file.

    Args:
        task (Task): The task for which the prompt is being built.

    Returns:
        str: The system prompt string.
    """
    prompt_path = os.path.join(PROMPT_DIR, "system.txt")
    return load_prompt(prompt_path, variables={})

def build_user_prompt(
    task: Task,
    project_title: str = "",
    max_subtasks: int = 3,
    max_chars_per_result: int = 800
) -> str:
    """
    Loads and formats the user prompt for the LLM agent from an external .txt file.
    Dynamically fills in sections for area, dependencies, and subtask results.

    Args:
        task (Task): The task for which the prompt is being built.
        project_title (str): The title of the overall project/root task.
        max_subtasks (int): Maximum number of subtask results to include.
        max_chars_per_result (int): Maximum characters per subtask result.

    Returns:
        str: The formatted user prompt string.
    """
    prompt_path = os.path.join(PROMPT_DIR, "user.txt")

    # Build area section if this is a subtask within an area
    area_section = ""
    if task.parent and task.parent.parent is not None:
        area_section = f"=== AREA ===\nTitle: {task.parent.title}\nDescription: {getattr(task.parent, 'description', '')}\n"

    # Build dependency section if there are dependencies
    dependency_section = ""
    dependencies = getattr(task, "dependencies", set())
    if dependencies:
        dep_lines = []
        for dep in dependencies:
            dep_result = str(dep.result)[:max_chars_per_result] if hasattr(dep, "result") and dep.result else ""
            dep_lines.append(f"- Dependency: {dep.title}\n  Description: {dep.description}\n  Result: {dep_result}\n")
        dependency_section = "=== DEPENDENCY RESULTS ===\n" + "\n".join(dep_lines)

    # Build subtask section if there are subtasks with results
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

    # Prepare variables for prompt template
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
    Calls the OpenAI LLM to get a response for the given prompts.

    Args:
        system_prompt (str): The system prompt for the LLM.
        user_prompt (str): The user prompt for the LLM.
        model (str): The OpenAI model to use.

    Returns:
        str: The LLM's response, or an error message if the call fails.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "[LLM ERROR]: OPENAI_API_KEY environment variable not set"
    client = OpenAI(api_key=api_key)
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
    Simulates a generic response for tasks that require external execution.

    Args:
        prompt (str): The prompt that would be sent to the LLM.
        task (Task): The task being executed.

    Returns:
        str: The simulated result (usually the expected output or a generic message).
    """
    return task.expected_output or f"[Simulated result for: {task.title}]"

def execute_tasks_postorder(task: Task, prompts_and_responses=None, model: str = "gpt-3.5-turbo", level: int = 0):
    """
    Recursively executes all subtasks in post-order (children before parent).
    For root and area tasks (levels 0 and 1), aggregates results from subtasks.
    For deeper levels, generates prompts and executes via LLM or simulation.

    Args:
        task (Task): The current task to execute.
        prompts_and_responses (list): Accumulates prompts and responses for logging/export.
        model (str): The LLM model to use.
        level (int): Current depth in the task tree.

    Returns:
        list: List of dicts with task_id, prompt, and response for each executed task.
    """
    if prompts_and_responses is None:
        prompts_and_responses = []

    # Recursively execute all subtasks first
    subtasks = [t for t in task.manager.tasks.values() if t.parent == task]
    for sub in subtasks:
        execute_tasks_postorder(sub, prompts_and_responses, model=model, level=level+1)

    # Root and area tasks only aggregate results, do not generate their own prompt
    if level <= 1:
        if subtasks:
            task.result = {sub.title: sub.result for sub in subtasks}
        task.prompt = None
        return prompts_and_responses

    # Subtasks and refinements (level 2+): always generate their own prompt and result
    system_prompt = build_system_prompt(task)
    user_prompt = build_user_prompt(
        task,
        project_title=task.manager.tasks[task.manager.root_task_id].title
    )
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

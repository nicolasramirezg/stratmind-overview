from openai import OpenAI
import re
from src.utils.prompt_loader import load_prompt


class SpecialistAgent:
    """
    Generates specific, actionable subtasks for each functional area
    from an initial decomposition of a complex task.

    Output: A dict with the area name as key and a list of subtask dicts:
    {
        "Marketing Strategy": [
            {
                "title": "Define target audience",
                "description": "...",
                "expected_output": "...",
                "dependencies": [...]
            },
            ...
        ],
        ...
    }
    """

    def __init__(self, model: str = "gpt-3.5-turbo"):
        """
        Initialize the SpecialistAgent with a given OpenAI model.
        """
        self.model = model
        self.client = OpenAI()

    @staticmethod
    def _parse_specialist_output(text: str, debug: bool = False) -> dict:
        """
        Parse the LLM output for area and subtasks.

        Args:
            text (str): The raw output from the LLM.
            debug (bool): If True, prints parsing errors.

        Returns:
            dict: {
                "area": <area_name>,
                "subtasks": [ {title, description, expected_output, dependencies}, ... ]
            }
        """
        try:
            parts = re.split(r"###\s*SUBTASKS\s*###", text, maxsplit=1)
            if len(parts) != 2:
                if debug:
                    print("Both sections (AREA and SUBTASKS) not found")
                return {"area": "", "subtasks": []}

            area_block = parts[0]
            subtasks_block = parts[1]

            # Extract area name, ignoring headers
            area_lines = [
                line.strip() for line in area_block.splitlines()
                if line.strip() and not line.strip().startswith("###")
            ]
            area_name = area_lines[0] if area_lines else ""

            # Parse subtasks into dicts
            subtask_blocks = re.split(r"Subtask:\s*", subtasks_block)
            subtasks = []
            for block in subtask_blocks:
                if not block.strip():
                    continue
                title = re.search(r"Title:\s*(.+)", block)
                description = re.search(r"Description:\s*(.+)", block)
                expected_output = re.search(r"Expected_output:\s*(.+)", block)
                dependencies = re.search(r"Dependencies:\s*(.+)", block)
                if not (title and description and expected_output and dependencies):
                    if debug:
                        print(f"Incorrect format in block:\n{block}")
                    continue
                subtasks.append({
                    "title": title.group(1).strip(),
                    "description": description.group(1).strip(),
                    "expected_output": expected_output.group(1).strip(),
                    "dependencies": [d.strip() for d in dependencies.group(1).split(",")] if dependencies and dependencies.group(1).strip().lower() != "none" else []
                })

            return {
                "area": area_name,
                "subtasks": subtasks
            }

        except Exception as e:
            if debug:
                print("Error parsing specialist output:", e)
                print("Received content:\n", text)
            return {"area": "", "subtasks": []}

    def plan_subtasks(self, decomposition: dict, global_task: str) -> list:
        """
        Generate concrete subtasks for each area using the LLM.

        Args:
            decomposition (dict): The decomposition with area info.
            global_task (str): The main project description.

        Returns:
            list: List of dicts, each with area and its subtasks.
        """
        result = []

        for area in decomposition["subtasks"]:
            area_name = area["area"]
            description = area["description"]
            responsibilities = area.get("responsibilities", [])
            expected_output = area.get("expected_output", "")

            # Prepare variables for prompt interpolation
            variables = {
                "area_name": area_name,
                "global_task": global_task,
                "description": description,
                "expected_output": expected_output,
                "responsibilities": "\n".join(f"- {r}" for r in responsibilities),
                "other_area_subtasks": area.get("other_area_subtasks", ""),
                "all_area_names": "\n".join(f"- {name}" for name in area.get("all_area_names", [])),
            }

            messages = [
                {
                    "role": "system",
                    "content": load_prompt(
                        "prompts/specialist_agent/system.txt",
                        variables)
                },
                {
                    "role": "user",
                    "content": load_prompt(
                        "prompts/specialist_agent/user.txt",
                        variables)
                }
            ]

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.4
            )

            content = response.choices[0].message.content.strip()

            parsed = self._parse_specialist_output(content)
            result.append(parsed)

        return result

def get_other_areas_subtasks(task_manager, current_area_task, root_task):
    """
    Collects the titles of subtasks already planned in other areas.

    Args:
        task_manager (TaskManager): The task manager instance.
        current_area_task (Task): The area currently being processed.
        root_task (Task): The root task.

    Returns:
        str: A formatted string listing other areas and their subtasks.
    """
    other_areas = [
        t for t in task_manager.tasks.values()
        if t.parent == root_task and t != current_area_task
    ]
    area_subtasks = []
    for area in other_areas:
        subtasks = [sub.title for sub in task_manager.tasks.values() if sub.parent == area]
        if subtasks:
            area_subtasks.append(f"- {area.title}: {', '.join(subtasks)}")
    return "\n".join(area_subtasks) if area_subtasks else "None"
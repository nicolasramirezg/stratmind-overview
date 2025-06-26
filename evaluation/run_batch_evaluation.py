import json
import os
from dotenv import load_dotenv
from datetime import datetime

from src.utils.class_task import TaskManager, create_and_link_subtasks
from src.agents.decomposer_agent import Decomposer
from src.agents.executor_agent import execute_tasks_postorder
from src.utils.recursive_refiner_parent_subtask import refine_recursively
from src.agents.specialist_agent import SpecialistAgent, get_other_areas_subtasks
from src.agents.task_refiner_agent import TaskRefiner
from src.utils.task_exporter import export_task_tree

load_dotenv()

def create_root_task(task_manager, task_description, expected_output):
    return task_manager.create_task(
        title=task_description,
        description=task_description,
        expected_output=expected_output
    )

def decompose_into_areas(root_task, decomposer):
    area_divisions = decomposer.decompose(
        root_task.description,
        root_task.expected_output
    )
    root_task.intro = area_divisions["intro"]
    return area_divisions

def create_area_tasks(task_manager, root_task, area_divisions):
    for subtask in area_divisions["subtasks"]:
        task_manager.create_task(
            title=subtask["area"],
            description=subtask["description"],
            expected_output=subtask["expected_output"], 
            area=subtask["area"],
            responsibilities=subtask["responsibilities"],
            parent_id=root_task.task_id,
            execution_type=subtask.get("execution_type", "llm")
        )

def plan_area_subtasks(task_manager, root_task, specialist, task_description):
    areas = [t for t in task_manager.tasks.values() if t.parent == root_task]
    all_area_names = [area.area for area in areas]
    for area in areas:
        other_area_subtasks = get_other_areas_subtasks(task_manager, area, root_task)
        area_division = {
            "area": area.area,
            "description": area.description,
            "expected_output": area.expected_output,
            "responsibilities": getattr(area, "responsibilities", []),
            "other_area_subtasks": other_area_subtasks,
            "all_area_names": all_area_names
        }
        subtasks_by_area = specialist.plan_subtasks({"subtasks": [area_division]}, task_description)
        for area_data in subtasks_by_area:
            area_name = area_data["area"]
            subtasks = area_data["subtasks"]
            area_task = next(
                (t for t in task_manager.tasks.values()
                if t.area == area_name and t.parent == root_task),
                None
            )
            if not area_task:
                continue
            create_and_link_subtasks(subtasks, area_name, area_task, task_manager)

def refine_all_subtasks(task_manager, root_task, task_refiner, task_description, max_depth=2):
    for area_task in [t for t in task_manager.tasks.values() if t.parent == root_task]:
        area_name = area_task.area
        def refine_subtree(task, depth=0):
            refine_recursively(
                subtask=task,
                area_name=area_name,
                global_task=task_description,
                refiner=task_refiner,
                task_manager=task_manager,
                depth=depth,
                max_depth=max_depth
            )
            for child in task.subtasks:
                refine_subtree(child, depth=depth+1)
        for subtask_task in area_task.subtasks:
            refine_subtree(subtask_task, depth=0)

def run_test_case(case):
    task_description = case["description"]
    expected_output = case["expected_output"]
    task_manager = TaskManager()

    root_task = create_root_task(task_manager, task_description, expected_output)
    decomposer = Decomposer()
    area_divisions = decompose_into_areas(root_task, decomposer)
    create_area_tasks(task_manager, root_task, area_divisions)

    specialist = SpecialistAgent()
    plan_area_subtasks(task_manager, root_task, specialist, task_description)

    task_refiner = TaskRefiner()
    refine_all_subtasks(task_manager, root_task, task_refiner, task_description)

    execute_tasks_postorder(root_task)

    # Export task tree with metadata
    export_task_tree(
        root_task,
        task_manager,
        out_name=f"{case['id']}_task_tree",
        metadata={
            "clarified_description": task_description,
            "expected_output": expected_output,
            "case_id": case["id"],
            "timestamp": datetime.now().isoformat()
        }
    )

def main():
    #with open("evaluation/test_cases.json", "r", encoding="utf-8") as f:
    with open("evaluation/test_cases_robustness.json", "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    for case in test_cases:
        print(f"\n🔹 Running test case: {case['id']} - {case['description'][:50]}...")
        run_test_case(case)

if __name__ == "__main__":
    main()

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from src.agents.specify_agent import SpecifyAgent
from src.agents.synthesize_agent import SynthesizeAgent
from src.agents.decomposer_agent import Decomposer
from src.agents.specialist_agent import SpecialistAgent, get_other_areas_subtasks
from src.agents.task_refiner_agent import TaskRefiner
from src.agents.executor_agent import execute_tasks_postorder
from src.utils.class_task import TaskManager, create_and_link_subtasks
from src.utils.recursive_refiner_parent_subtask import refine_recursively
from src.utils.task_exporter import export_task_tree
from main import (
    create_root_task, decompose_into_areas, create_area_tasks,
    plan_area_subtasks, refine_all_subtasks, print_task_tree
)
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://7e64aab1-e35a-4556-a06e-ae3a83f8a9af.lovableproject.com",
        "https://58b77832-a85f-4c06-b9b0-c0b284d922e2.lovableproject.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SESSION = {}

@app.post("/clarify")
async def clarify(request: Request):
    data = await request.json()
    session_id = data.get("session_id", "default")
    history = data.get("history", [])
    user_input = data.get("user_input", "")

    # Si el historial está vacío, usa el método del agente para construirlo
    if not history:
        history = SpecifyAgent.initial_history(user_input)
        user_input = None  # Ya está en el historial

    elif user_input:
        history.append({"role": "user", "content": user_input})

    specify_agent = SpecifyAgent()
    agent_response = specify_agent.get_response(history)
    history.append({"role": "assistant", "content": agent_response})
    finished = "fully specified" in agent_response.lower() or (user_input and user_input.lower() == "finish")
    SESSION[session_id] = {"history": history}
    return {"history": history, "agent_response": agent_response, "finished": finished}

@app.post("/synthesize")
async def synthesize(request: Request):
    data = await request.json()
    session_id = data.get("session_id", "default")
    history = SESSION.get(session_id, {}).get("history", [])
    if not history:
        raise HTTPException(status_code=400, detail="Clarification step not completed.")
    synthesize_agent = SynthesizeAgent()
    spec = synthesize_agent.synthesize(history)
    SESSION[session_id]["spec"] = spec
    return spec

@app.post("/decompose")
async def decompose(request: Request):
    data = await request.json()
    session_id = data.get("session_id", "default")
    spec = SESSION.get(session_id, {}).get("spec")
    if not spec:
        raise HTTPException(status_code=400, detail="Synthesis step not completed.")
    task_manager = TaskManager()
    root_task = create_root_task(task_manager, spec["description"], spec["expected_output"])
    decomposer = Decomposer()
    area_divisions = decompose_into_areas(root_task, decomposer)
    SESSION[session_id].update({
        "task_manager": task_manager,
        "root_task": root_task,
        "area_divisions": area_divisions
    })
    return {"areas": area_divisions["subtasks"]}

@app.post("/create_area_tasks")
async def create_area_tasks_endpoint(request: Request):
    data = await request.json()
    session_id = data.get("session_id", "default")
    tm = SESSION.get(session_id, {}).get("task_manager")
    root_task = SESSION.get(session_id, {}).get("root_task")
    area_divisions = SESSION.get(session_id, {}).get("area_divisions")
    if not (tm and root_task and area_divisions):
        raise HTTPException(status_code=400, detail="Decomposition step not completed.")
    create_area_tasks(tm, root_task, area_divisions)
    return {"status": "area tasks created"}

@app.post("/plan_subtasks")
async def plan_subtasks_endpoint(request: Request):
    data = await request.json()
    session_id = data.get("session_id", "default")
    tm = SESSION.get(session_id, {}).get("task_manager")
    root_task = SESSION.get(session_id, {}).get("root_task")
    spec = SESSION.get(session_id, {}).get("spec")
    if not (tm and root_task and spec):
        raise HTTPException(status_code=400, detail="Previous steps not completed.")
    specialist = SpecialistAgent()
    plan_area_subtasks(tm, root_task, specialist, spec["description"])
    return {"tree": root_task.to_dict()}

@app.post("/refine")
async def refine_endpoint(request: Request):
    data = await request.json()
    session_id = data.get("session_id", "default")
    tm = SESSION.get(session_id, {}).get("task_manager")
    root_task = SESSION.get(session_id, {}).get("root_task")
    spec = SESSION.get(session_id, {}).get("spec")
    if not (tm and root_task and spec):
        raise HTTPException(status_code=400, detail="Previous steps not completed.")
    task_refiner = TaskRefiner()
    refine_all_subtasks(tm, root_task, task_refiner, spec["description"])
    return {"tree": root_task.to_dict()}

@app.post("/execute")
async def execute_endpoint(request: Request):
    data = await request.json()
    session_id = data.get("session_id", "default")
    tm = SESSION.get(session_id, {}).get("task_manager")
    root_task = SESSION.get(session_id, {}).get("root_task")
    if not (tm and root_task):
        raise HTTPException(status_code=400, detail="Previous steps not completed.")
    execute_tasks_postorder(root_task)
    export_task_tree(root_task, tm, out_name=f"task_tree_{session_id}")
    return {"tree": root_task.to_dict()}

@app.post("/get_tree")
async def get_tree(request: Request):
    data = await request.json()
    session_id = data.get("session_id", "default")
    root_task = SESSION.get(session_id, {}).get("root_task")
    if not root_task:
        raise HTTPException(status_code=404, detail="No tree found for this session.")
    return {"tree": root_task.to_dict()}

@app.post("/print_tree")
async def print_tree(request: Request):
    data = await request.json()
    session_id = data.get("session_id", "default")
    root_task = SESSION.get(session_id, {}).get("root_task")
    if not root_task:
        raise HTTPException(status_code=404, detail="No tree found for this session.")
    print_task_tree(root_task)
    return {"status": "printed"}


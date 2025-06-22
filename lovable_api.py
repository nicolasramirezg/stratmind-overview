from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware  # <-- Añadido para CORS
from src.agents.specify_agent import SpecifyAgent
from src.agents.synthesize_agent import SynthesizeAgent
from src.agents.decomposer_agent import Decomposer
from src.agents.specialist_agent import SpecialistAgent
from src.agents.task_refiner_agent import TaskRefiner
from src.agents.executor_agent import execute_tasks_postorder
from src.utils.class_task import TaskManager
from src.utils.recursive_refiner_parent_subtask import refine_recursively
from src.utils.task_exporter import export_task_tree
import uvicorn

app = FastAPI()

# --- CORS Middleware: permite peticiones desde tu frontend ---
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
    specify_agent = SpecifyAgent()
    if user_input:
        history.append({"role": "user", "content": user_input})
    agent_response = specify_agent.get_response(history)
    history.append({"role": "assistant", "content": agent_response})
    finished = "fully specified" in agent_response.lower() or user_input.lower() == "finish"
    SESSION[session_id] = {"history": history}
    return {"history": history, "agent_response": agent_response, "finished": finished}

@app.post("/synthesize")
async def synthesize(request: Request):
    data = await request.json()
    session_id = data.get("session_id", "default")
    history = data.get("history", [])
    synthesize_agent = SynthesizeAgent()
    spec = synthesize_agent.synthesize(history)
    SESSION[session_id]["spec"] = spec
    return spec

@app.post("/decompose")
async def decompose(request: Request):
    data = await request.json()
    session_id = data.get("session_id", "default")
    spec = SESSION[session_id]["spec"]
    task_manager = TaskManager()
    from main import create_root_task, decompose_into_areas, create_area_tasks
    root_task = create_root_task(task_manager, spec["description"], spec["expected_output"])
    decomposer = Decomposer()
    area_divisions = decompose_into_areas(root_task, decomposer)
    create_area_tasks(task_manager, root_task, area_divisions)
    SESSION[session_id]["task_manager"] = task_manager
    SESSION[session_id]["root_task"] = root_task
    SESSION[session_id]["area_divisions"] = area_divisions
    return {"areas": area_divisions["subtasks"]}

@app.post("/plan_subtasks")
async def plan_subtasks(request: Request):
    data = await request.json()
    session_id = data.get("session_id", "default")
    from main import plan_area_subtasks
    specialist = SpecialistAgent()
    task_manager = SESSION[session_id]["task_manager"]
    root_task = SESSION[session_id]["root_task"]
    spec = SESSION[session_id]["spec"]
    plan_area_subtasks(task_manager, root_task, specialist, spec["description"])
    return {"tree": root_task.to_dict()}

@app.post("/refine")
async def refine(request: Request):
    data = await request.json()
    session_id = data.get("session_id", "default")
    from main import refine_all_subtasks
    task_refiner = TaskRefiner()
    task_manager = SESSION[session_id]["task_manager"]
    root_task = SESSION[session_id]["root_task"]
    spec = SESSION[session_id]["spec"]
    refine_all_subtasks(task_manager, root_task, task_refiner, spec["description"])
    return {"tree": root_task.to_dict()}

@app.post("/execute")
async def execute(request: Request):
    data = await request.json()
    session_id = data.get("session_id", "default")
    task_manager = SESSION[session_id]["task_manager"]
    root_task = SESSION[session_id]["root_task"]
    execute_tasks_postorder(root_task)
    export_task_tree(root_task, task_manager, out_name=f"task_tree_{session_id}")
    return {"tree": root_task.to_dict()}

@app.post("/get_tree")
async def get_tree(request: Request):
    data = await request.json()
    session_id = data.get("session_id", "default")
    root_task = SESSION[session_id]["root_task"]
    return {"tree": root_task.to_dict()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
# RESTful API for Task Management Agent
from fastapi import FastAPI, HTTPException
from schemas import Task
from firestore_interface import FirestoreTaskInterface
from task_management_agent import TaskManagementAgent
from typing import List

app = FastAPI()
db_interface = FirestoreTaskInterface()
agent = TaskManagementAgent(db_interface)

@app.post("/tasks/")
def create_task(client_id: str, description: str, breakdown_steps: List[str]):
    result = agent.create_and_breakdown_task(client_id, description, breakdown_steps)
    return result

@app.post("/tasks/{task_id}/assign/")
def assign_task(task_id: str, handyman_resource_id: str):
    success = agent.assign_task(task_id, handyman_resource_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found or not assignable")
    return {"assigned": True}

@app.post("/tasks/{task_id}/status/")
def update_status(task_id: str, status: str):
    success = agent.update_task_status(task_id, status)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"updated": True}

@app.get("/tasks/{parent_task_id}/progress/")
def get_progress(parent_task_id: str):
    return agent.get_task_progress(parent_task_id)

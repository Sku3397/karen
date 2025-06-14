from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from src.schemas.task import Task, TaskCreate, TaskUpdate
from src.security.auth import get_current_user

router = APIRouter()

tasks_db = {}

def get_task_or_404(task_id: str):
    task = tasks_db.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.post("/", response_model=Task, status_code=201)
def create_task(task: TaskCreate, current_user=Depends(get_current_user)):
    task_id = str(len(tasks_db) + 1)
    task_data = task.dict()
    task_data["id"] = task_id
    tasks_db[task_id] = task_data
    return Task(**task_data)

@router.get("/", response_model=List[Task])
def list_tasks(current_user=Depends(get_current_user)):
    return [Task(**data) for data in tasks_db.values()]

@router.get("/{task_id}", response_model=Task)
def get_task(task_id: str, current_user=Depends(get_current_user)):
    return Task(**get_task_or_404(task_id))

@router.put("/{task_id}", response_model=Task)
def update_task(task_id: str, update: TaskUpdate, current_user=Depends(get_current_user)):
    task = get_task_or_404(task_id)
    task.update(update.dict(exclude_unset=True))
    tasks_db[task_id] = task
    return Task(**task)

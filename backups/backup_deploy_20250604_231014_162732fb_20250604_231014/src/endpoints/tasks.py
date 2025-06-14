"""
Tasks API endpoint for the AI Handyman Secretary Assistant.
Provides CRUD operations for task management.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

# Import models
from ..models import User

router = APIRouter()

# Pydantic models for tasks
class TaskCreate(BaseModel):
    title: str
    description: str
    priority: str = "medium"
    estimated_duration: Optional[int] = None
    required_skills: Optional[List[str]] = None
    location: Optional[str] = None
    assigned_to: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    estimated_duration: Optional[int] = None
    required_skills: Optional[List[str]] = None
    location: Optional[str] = None
    assigned_to: Optional[str] = None

class TaskResponse(BaseModel):
    id: str
    title: str
    description: str
    priority: str
    status: str
    estimated_duration: Optional[int]
    required_skills: Optional[List[str]]
    location: Optional[str]
    assigned_to: Optional[str]
    created_at: str
    updated_at: str

# In-memory storage (would be replaced with database in production)
tasks_db = {}

@router.post("/tasks/", response_model=TaskResponse)
async def create_task(task: TaskCreate):
    """Create a new task."""
    task_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    task_data = {
        "id": task_id,
        "title": task.title,
        "description": task.description,
        "priority": task.priority,
        "status": "created",
        "estimated_duration": task.estimated_duration,
        "required_skills": task.required_skills or [],
        "location": task.location,
        "assigned_to": task.assigned_to,
        "created_at": now,
        "updated_at": now
    }
    
    tasks_db[task_id] = task_data
    return TaskResponse(**task_data)

@router.get("/tasks/", response_model=List[TaskResponse])
async def list_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to: Optional[str] = None
):
    """List all tasks with optional filtering."""
    tasks = list(tasks_db.values())
    
    # Apply filters
    if status:
        tasks = [t for t in tasks if t["status"] == status]
    if priority:
        tasks = [t for t in tasks if t["priority"] == priority]
    if assigned_to:
        tasks = [t for t in tasks if t["assigned_to"] == assigned_to]
    
    return [TaskResponse(**task) for task in tasks]

@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """Get a specific task by ID."""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskResponse(**tasks_db[task_id])

@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, task_update: TaskUpdate):
    """Update a task."""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_data = tasks_db[task_id]
    
    # Update fields that are provided
    update_data = task_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        task_data[field] = value
    
    task_data["updated_at"] = datetime.now().isoformat()
    tasks_db[task_id] = task_data
    
    return TaskResponse(**task_data)

@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete a task."""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    
    del tasks_db[task_id]
    return {"message": "Task deleted successfully"}

@router.post("/tasks/{task_id}/assign")
async def assign_task(task_id: str, assignee: str):
    """Assign a task to a user."""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    
    tasks_db[task_id]["assigned_to"] = assignee
    tasks_db[task_id]["status"] = "assigned"
    tasks_db[task_id]["updated_at"] = datetime.now().isoformat()
    
    return {"message": f"Task assigned to {assignee}"}

@router.post("/tasks/{task_id}/complete")
async def complete_task(task_id: str):
    """Mark a task as completed."""
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    
    tasks_db[task_id]["status"] = "completed"
    tasks_db[task_id]["updated_at"] = datetime.now().isoformat()
    
    return {"message": "Task marked as completed"}
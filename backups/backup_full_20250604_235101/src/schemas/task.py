from pydantic import BaseModel, Field
from typing import Optional, List

# New schema for task details to be nested
class TaskDetailsSchema(BaseModel):
    description: str
    estimated_duration: Optional[int] = None
    required_skills: Optional[List[str]] = []
    location: Optional[str] = None

class TaskBase(BaseModel):
    details: TaskDetailsSchema # Changed from dict to TaskDetailsSchema
    status: str = "created" # Default status
    priority: str = "medium" # Added priority, assuming it's common
    created_by: Optional[str] = None # Added created_by
    assignments: Optional[List[str]] = []
    history: Optional[List[dict]] = []

class TaskCreateSchema(BaseModel): # Renamed from TaskCreate for clarity, similar to CreateTaskRequest
    details: TaskDetailsSchema
    priority: str = "medium"
    created_by: str # creator is mandatory

class TaskUpdateSchema(BaseModel): # Renamed from TaskUpdate
    details: Optional[TaskDetailsSchema] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assignments: Optional[List[str]] = None
    history: Optional[List[dict]] = None # History update might be complex

class TaskResponseSchema(BaseModel): # For wrapping responses
    id: str
    details: TaskDetailsSchema
    status: str
    priority: str
    created_by: Optional[str]
    assignments: Optional[List[str]]
    # Add other fields as needed from the internal Task model, e.g., created_at, updated_at
    created_at: Optional[str] = None 
    updated_at: Optional[str] = None
    message: Optional[str] = None # For status messages

class TaskSchema(TaskBase): # This was 'Task', renamed to align with pattern
    id: str
    # Timestamps can be added here too if they are part of the core Task model visible externally
    created_at: Optional[str] = None 
    updated_at: Optional[str] = None

    class Config:
        orm_mode = True # If you ever map this to an ORM model directly

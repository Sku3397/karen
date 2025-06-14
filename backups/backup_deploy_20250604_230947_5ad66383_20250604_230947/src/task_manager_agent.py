"""
TaskManagerAgent - Handles task management operations for the AI Handyman Secretary Assistant.
Provides FastAPI endpoints for creating, assigning, and managing tasks.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel

# Import new schemas
from .schemas.task import (
    TaskCreateSchema,
    TaskResponseSchema,
    TaskDetailsSchema,
    TaskSchema
)
from .llm_client import LLMClient

logger = logging.getLogger(__name__)

# Pydantic models for request/response
class TaskDetails(BaseModel):
    description: str
    estimated_duration: Optional[int] = None
    required_skills: Optional[List[str]] = None
    location: Optional[str] = None

class CreateTaskRequest(BaseModel):
    details: TaskDetails
    priority: str = "medium"
    created_by: str

class TaskResponse(BaseModel):
    status: str
    task_id: Optional[str] = None
    message: Optional[str] = None

# The internal Task data class - this is how tasks are stored in memory by this agent.
# It should align with the fields exposed by TaskSchema or TaskResponseSchema.
class Task:
    """Task data model (internal representation)"""
    def __init__(self, task_id: str, details: TaskDetailsSchema, priority: str, created_by: str):
        self.id = task_id
        self.details = details
        self.priority = priority
        self.created_by = created_by
        self.status = "created"
        self.assigned_to: Optional[str] = None
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.llm_suggestion: Optional[str] = None

class TaskManagerAgent:
    """
    Task management agent that handles task lifecycle operations.
    """
    
    def __init__(self):
        """Initialize the TaskManagerAgent."""
        self.tasks: Dict[str, Task] = {}
        self.resources: Dict[str, Any] = {}
        try:
            self.llm_client = LLMClient()
            logger.info("LLMClient initialized successfully within TaskManagerAgent.")
        except ValueError as e:
            logger.error(f"Failed to initialize LLMClient in TaskManagerAgent: {e}")
            self.llm_client = None
        logger.info("TaskManagerAgent initialized successfully")
    
    def create_task(self, request: TaskCreateSchema) -> TaskResponseSchema:
        """
        Create a new task.
        
        Args:
            request: Task creation request using TaskCreateSchema
            
        Returns:
            TaskResponseSchema with creation status
        """
        try:
            task_id = str(uuid.uuid4())
            task = Task(
                task_id=task_id, 
                details=request.details, 
                priority=request.priority, 
                created_by=request.created_by
            )
            self.tasks[task_id] = task
            
            logger.info(f"Created task {task_id} for user {request.created_by}")
            
            return TaskResponseSchema(
                id=task.id,
                details=task.details,
                status=task.status,
                priority=task.priority,
                created_by=task.created_by,
                assignments=([task.assigned_to] if task.assigned_to else []),
                created_at=task.created_at,
                updated_at=task.updated_at,
                message=f"Task created successfully with ID {task_id}"
            )
            
        except Exception as e:
            logger.error(f"Failed to create task: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")
    
    def assign_task(self, task_id: str, assignee: str) -> TaskResponse:
        """
        Assign a task to a user.
        
        Args:
            task_id: ID of the task to assign
            assignee: User to assign the task to
            
        Returns:
            TaskResponse with assignment status
        """
        try:
            if task_id not in self.tasks:
                return TaskResponse(
                    status="error",
                    message=f"Task {task_id} not found"
                )
            
            task = self.tasks[task_id]
            task.assigned_to = assignee
            task.status = "assigned"
            task.updated_at = datetime.now().isoformat()
            
            logger.info(f"Assigned task {task_id} to {assignee}")
            
            return TaskResponse(
                status="assigned",
                task_id=task_id,
                message=f"Task assigned to {assignee}"
            )
            
        except Exception as e:
            logger.error(f"Failed to assign task {task_id}: {str(e)}")
            return TaskResponse(
                status="error",
                message=f"Failed to assign task: {str(e)}"
            )
    
    def update_task_status(self, task_id: str, new_status: str) -> TaskResponse:
        """
        Update the status of a task.
        
        Args:
            task_id: ID of the task to update
            new_status: New status for the task
            
        Returns:
            TaskResponse with update status
        """
        try:
            if task_id not in self.tasks:
                return TaskResponse(
                    status="error",
                    message=f"Task {task_id} not found"
                )
            
            task = self.tasks[task_id]
            old_status = task.status
            task.status = new_status
            task.updated_at = datetime.now().isoformat()
            
            logger.info(f"Updated task {task_id} status from {old_status} to {new_status}")
            
            return TaskResponse(
                status="updated",
                task_id=task_id,
                message=f"Task status updated to {new_status}"
            )
            
        except Exception as e:
            logger.error(f"Failed to update task {task_id} status: {str(e)}")
            return TaskResponse(
                status="error",
                message=f"Failed to update task status: {str(e)}"
            )
    
    def allocate_resources(self, task_id: str, resources: Dict[str, Any]) -> TaskResponse:
        """
        Allocate resources to a task.
        
        Args:
            task_id: ID of the task
            resources: Resources to allocate
            
        Returns:
            TaskResponse with allocation status
        """
        try:
            if task_id not in self.tasks:
                return TaskResponse(
                    status="error",
                    message=f"Task {task_id} not found"
                )
            
            # Store resource allocation
            self.resources[task_id] = resources
            
            logger.info(f"Allocated resources to task {task_id}: {resources}")
            
            return TaskResponse(
                status="allocated",
                task_id=task_id,
                message="Resources allocated successfully"
            )
            
        except Exception as e:
            logger.error(f"Failed to allocate resources to task {task_id}: {str(e)}")
            return TaskResponse(
                status="error",
                message=f"Failed to allocate resources: {str(e)}"
            )
    
    def verify_evidence(self, task_id: str, evidence: Dict[str, Any]) -> TaskResponse:
        """
        Verify evidence for task completion.
        
        Args:
            task_id: ID of the task
            evidence: Evidence data to verify
            
        Returns:
            TaskResponse with verification status
        """
        try:
            if task_id not in self.tasks:
                return TaskResponse(
                    status="error",
                    message=f"Task {task_id} not found"
                )
            
            # Simple evidence verification (would be more complex in reality)
            is_valid = evidence.get("photos") or evidence.get("description")
            
            if is_valid:
                task = self.tasks[task_id]
                task.status = "completed"
                task.updated_at = datetime.now().isoformat()
                
                logger.info(f"Evidence verified for task {task_id}")
                
                return TaskResponse(
                    status="verified",
                    task_id=task_id,
                    message="Evidence verified and task marked as completed"
                )
            else:
                return TaskResponse(
                    status="error",
                    message="Invalid evidence provided"
                )
            
        except Exception as e:
            logger.error(f"Failed to verify evidence for task {task_id}: {str(e)}")
            return TaskResponse(
                status="error",
                message=f"Failed to verify evidence: {str(e)}"
            )

    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> List[TaskResponseSchema]:
        """
        Retrieve all tasks.
        
        Returns:
            A list of all tasks formatted with TaskResponseSchema.
        """
        all_tasks_response = []
        for task_id, task in self.tasks.items():
            all_tasks_response.append(
                TaskResponseSchema(
                    id=task.id,
                    details=task.details,
                    status=task.status,
                    priority=task.priority,
                    created_by=task.created_by,
                    assignments=([task.assigned_to] if task.assigned_to else []),
                    created_at=task.created_at,
                    updated_at=task.updated_at,
                    message=None # No specific message for list items
                )
            )
        return all_tasks_response

    def generate_llm_suggestion_for_task(self, task_id: str) -> Optional[str]:
        """
        Generates an LLM suggestion for a given task and stores it.

        Args:
            task_id: The ID of the task.

        Returns:
            The generated LLM suggestion string, or None if an error occurred
            or the task was not found.
        """
        logger.debug(f"Attempting to generate LLM suggestion for task ID: {task_id}")
        if not self.llm_client:
            logger.warning("LLMClient not available in TaskManagerAgent. Cannot generate suggestion.")
            return None

        task = self.get_task_by_id(task_id)
        if not task:
            logger.warning(f"Task {task_id} not found. Cannot generate LLM suggestion.")
            return None

        if not task.details or not task.details.description:
            logger.warning(f"Task {task_id} has no description. Cannot generate LLM suggestion.")
            return None

        prompt = f"Based on the following handyman task, provide a concise summary and suggest one primary actionable next step. Keep the total response under 100 words. Task: {task.details.description}"
        
        logger.debug(f"Prompt for LLM suggestion for task {task_id}: '{prompt}'")
        
        try:
            suggestion = self.llm_client.generate_text(prompt)
            if suggestion and not suggestion.startswith("Error:"):
                task.llm_suggestion = suggestion
                task.updated_at = datetime.now().isoformat()
                logger.info(f"LLM suggestion generated and stored for task {task_id}: '{suggestion[:100]}...'")
                return suggestion
            else:
                logger.error(f"Failed to generate valid LLM suggestion for task {task_id}. LLMClient returned: {suggestion}")
                task.llm_suggestion = f"LLM suggestion generation failed: {suggestion}"
                return None
        except Exception as e:
            logger.error(f"Exception while generating LLM suggestion for task {task_id}: {e}", exc_info=True)
            task.llm_suggestion = f"LLM suggestion generation failed due to exception: {str(e)}"
            return None

# Initialize the agent
task_manager = TaskManagerAgent()

# Create FastAPI app
router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.post("/create", response_model=TaskResponseSchema)
async def create_task_endpoint(request: TaskCreateSchema):
    return task_manager.create_task(request)

@router.get("/", response_model=List[TaskResponseSchema], summary="List all tasks")
async def list_tasks_endpoint():
    """Retrieve all tasks."""
    return task_manager.get_all_tasks()

@router.post("/{task_id}/assign", response_model=TaskResponseSchema)
async def assign_task(task_id: str, assignee: str):
    """Assign a task to a user."""
    return task_manager.assign_task(task_id, assignee)

@router.put("/{task_id}/status", response_model=TaskResponseSchema)
async def update_task_status(task_id: str, new_status: str):
    """Update task status."""
    return task_manager.update_task_status(task_id, new_status)

@router.post("/{task_id}/resources", response_model=TaskResponseSchema)
async def allocate_resources(task_id: str, resources: Dict[str, Any]):
    """Allocate resources to a task."""
    return task_manager.allocate_resources(task_id, resources)

@router.post("/{task_id}/evidence", response_model=TaskResponseSchema)
async def verify_evidence(task_id: str, evidence: Dict[str, Any]):
    """Verify evidence for task completion."""
    return task_manager.verify_evidence(task_id, evidence)

@router.get("/health_check", tags=["Health"])
async def health_check():
    return {"status": "TaskManagerAgent is healthy"}
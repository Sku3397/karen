# Task Management Agent for AI Handyman Secretary Assistant
from firestore_interface import FirestoreTaskInterface
from schemas import Task, TaskStatus
from typing import List, Dict, Optional
import uuid
import datetime
from .agent_activity_logger import AgentActivityLogger

activity_logger = AgentActivityLogger()

class TaskManagementAgent:
    def __init__(self, firestore_interface: FirestoreTaskInterface):
        self.db = firestore_interface
        
        # Log initialization
        activity_logger.log_activity(
            agent_name="task_management_agent",
            activity_type="initialization",
            details={
                "firestore_interface": "initialized",
                "timestamp": datetime.datetime.now().isoformat()
            }
        )

    def create_and_breakdown_task(self, client_id: str, description: str, breakdown_steps: List[str]) -> Dict:
        # Create a parent task and its breakdown
        parent_task_id = str(uuid.uuid4())
        now = datetime.datetime.utcnow().isoformat()
        parent_task = Task(
            task_id=parent_task_id,
            client_id=client_id,
            description=description,
            status=TaskStatus.PENDING,
            created_at=now,
            updated_at=now,
            assigned_to=None,
            parent_task_id=None,
            steps=[],
        )
        self.db.add_task(parent_task)
        step_task_ids = []
        for step in breakdown_steps:
            step_task_id = str(uuid.uuid4())
            step_task = Task(
                task_id=step_task_id,
                client_id=client_id,
                description=step,
                status=TaskStatus.PENDING,
                created_at=now,
                updated_at=now,
                assigned_to=None,
                parent_task_id=parent_task_id,
                steps=[],
            )
            self.db.add_task(step_task)
            step_task_ids.append(step_task_id)
        self.db.update_task_steps(parent_task_id, step_task_ids)
        return {"parent_task_id": parent_task_id, "step_task_ids": step_task_ids}

    def assign_task(self, task_id: str, handyman_resource_id: str) -> bool:
        task = self.db.get_task(task_id)
        if not task or task.status != TaskStatus.PENDING:
            return False
        self.db.update_task_assignment(task_id, handyman_resource_id)
        # Optionally: Publish assignment event to Pub/Sub here
        return True

    def update_task_status(self, task_id: str, status: str) -> bool:
        task = self.db.get_task(task_id)
        if not task:
            return False
        self.db.update_task_status(task_id, status)
        # Optionally: Publish status update event here
        return True

    def get_task_progress(self, parent_task_id: str) -> Dict:
        parent_task = self.db.get_task(parent_task_id)
        if not parent_task:
            return {"error": "Parent task not found"}
        step_tasks = self.db.get_subtasks(parent_task_id)
        completed = sum(1 for t in step_tasks if t.status == TaskStatus.COMPLETED)
        total = len(step_tasks)
        progress = completed / total if total > 0 else 0.0
        return {
            "parent_task_id": parent_task_id,
            "progress": progress,
            "completed_steps": completed,
            "total_steps": total,
            "steps": [{"task_id": t.task_id, "status": t.status} for t in step_tasks],
        }

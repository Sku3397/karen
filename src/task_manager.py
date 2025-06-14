# Task Manager & Dependency Tracker Logic
from typing import List, Dict, Optional
from google.cloud import firestore
from .firestore_models import create_task, update_task_status, assign_task, get_task
import uuid

class TaskManager:
    def __init__(self, db):
        self.db = db # db will likely be None or an unconfigured Firestore client if passed from main

    def breakdown_handyman_task(self, main_task_title: str, main_task_description: str, subtasks: List[Dict]) -> str:
        """
        Create a parent task and its dependent subtasks in Firestore.
        Each subtask dict: {title, description, dependencies (optional)}
        Returns parent task ID.
        """
        # Create parent task
        parent_task_id = create_task(self.db, main_task_title, main_task_description)
        subtask_ids = []
        # Create subtasks
        for sub in subtasks:
            dep_ids = sub.get('dependencies', [])
            sub_id = create_task(self.db, sub['title'], sub['description'], dependencies=dep_ids)
            subtask_ids.append(sub_id)
        # Optionally, update parent with subtask IDs as dependencies
        self.db.collection('tasks').document(parent_task_id).update({'dependencies': subtask_ids})
        return parent_task_id

    def assign_tasks(self, agent_assignments: Dict[str, List[str]]):
        """
        Assign tasks to simulated handyman agents.
        agent_assignments: {agent_id: [task_id, ...]}
        """
        for agent_id, task_ids in agent_assignments.items():
            for task_id in task_ids:
                assign_task(self.db, task_id, agent_id)

    def get_ready_tasks(self) -> List[Dict]:
        """
        Return all tasks that are pending and have all dependencies completed.
        """
        pending_tasks = self.db.collection('tasks').where('status', '==', 'pending').stream()
        ready_tasks = []
        for doc in pending_tasks:
            task = doc.to_dict()
            task['id'] = doc.id  # Add document ID to task data
            deps = task.get('dependencies', [])
            if not deps:
                ready_tasks.append(task)
            else:
                # Check if all dependencies are completed
                if all(self.db.collection('tasks').document(dep_id).get().to_dict().get('status') == 'completed' for dep_id in deps):
                    ready_tasks.append(task)
        return ready_tasks

    def monitor_progress(self) -> Dict[str, List[Dict]]:
        """
        Return tasks grouped by status.
        """
        statuses = ['pending', 'in_progress', 'blocked', 'completed', 'failed']
        result = {status: [] for status in statuses}
        for status in statuses:
            tasks = []
            for doc in self.db.collection('tasks').where('status', '==', status).stream():
                task_data = doc.to_dict()
                task_data['id'] = doc.id
                tasks.append(task_data)
            result[status] = tasks
        return result

    def mark_task_in_progress(self, task_id: str):
        update_task_status(self.db, task_id, 'in_progress')

    def mark_task_completed(self, task_id: str):
        update_task_status(self.db, task_id, 'completed')
        # Optionally, unblock dependent tasks
        self._unblock_dependents(task_id)

    def _unblock_dependents(self, completed_task_id: str):
        # Find tasks where this task is a dependency
        dependents = self.db.collection('tasks').where('dependencies', 'array_contains', completed_task_id).stream()
        for doc in dependents:
            task = doc.to_dict()
            # If all dependencies completed, mark as pending if previously blocked
            if all(self.db.collection('tasks').document(dep_id).get().to_dict().get('status') == 'completed' for dep_id in task['dependencies']):
                if task['status'] == 'blocked':
                    update_task_status(self.db, doc.id, 'pending')

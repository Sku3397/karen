# Interface to Firestore for task storage
from google.cloud import firestore
from schemas import Task
from typing import Optional, List

class FirestoreTaskInterface:
    def __init__(self):
        self.client = firestore.Client()
        self.collection = self.client.collection('tasks')

    def add_task(self, task: Task):
        self.collection.document(task.task_id).set(task.dict())

    def get_task(self, task_id: str) -> Optional[Task]:
        doc = self.collection.document(task_id).get()
        if doc.exists:
            return Task(**doc.to_dict())
        return None

    def update_task_assignment(self, task_id: str, handyman_resource_id: str):
        self.collection.document(task_id).update({"assigned_to": handyman_resource_id, "updated_at": firestore.SERVER_TIMESTAMP})

    def update_task_status(self, task_id: str, status: str):
        self.collection.document(task_id).update({"status": status, "updated_at": firestore.SERVER_TIMESTAMP})

    def update_task_steps(self, task_id: str, step_task_ids: List[str]):
        self.collection.document(task_id).update({"steps": step_task_ids, "updated_at": firestore.SERVER_TIMESTAMP})

    def get_subtasks(self, parent_task_id: str) -> List[Task]:
        query = self.collection.where('parent_task_id', '==', parent_task_id).stream()
        return [Task(**doc.to_dict()) for doc in query]

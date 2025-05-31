# Firestore data models for Task Manager & Dependency Tracker
from typing import Optional, List, Dict
from google.cloud import firestore

# Task document structure
# Collection: tasks
# Fields:
#   id: str (Firestore doc id)
#   title: str
#   description: str
#   status: str (pending, in_progress, blocked, completed, failed)
#   assigned_agent_id: Optional[str]
#   dependencies: List[str] (List of dependent task IDs)
#   created_at: timestamp
#   updated_at: timestamp
#   metadata: Dict

def create_task(db, title: str, description: str, dependencies: Optional[List[str]] = None, metadata: Optional[Dict] = None) -> str:
    task_ref = db.collection('tasks').document()
    task_data = {
        'title': title,
        'description': description,
        'status': 'pending',
        'assigned_agent_id': None,
        'dependencies': dependencies or [],
        'created_at': firestore.SERVER_TIMESTAMP,
        'updated_at': firestore.SERVER_TIMESTAMP,
        'metadata': metadata or {}
    }
    task_ref.set(task_data)
    return task_ref.id

def update_task_status(db, task_id: str, status: str):
    task_ref = db.collection('tasks').document(task_id)
    task_ref.update({
        'status': status,
        'updated_at': firestore.SERVER_TIMESTAMP
    })

def assign_task(db, task_id: str, agent_id: str):
    task_ref = db.collection('tasks').document(task_id)
    task_ref.update({
        'assigned_agent_id': agent_id,
        'updated_at': firestore.SERVER_TIMESTAMP
    })

def get_task(db, task_id: str):
    return db.collection('tasks').document(task_id).get().to_dict()

def get_tasks_by_status(db, status: str):
    return [doc.to_dict() for doc in db.collection('tasks').where('status', '==', status).stream()]
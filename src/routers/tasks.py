from fastapi import APIRouter

router = APIRouter()

@router.post('/tasks/')
def create_task(task: Task):
    pass

@router.get('/tasks/')
def list_tasks():
    pass
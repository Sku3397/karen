from fastapi import APIRouter

router = APIRouter()

@router.post('/users/')
def create_user(user: User):
    pass

@router.get('/users/{user_id}')
def read_user(user_id: str):
    pass
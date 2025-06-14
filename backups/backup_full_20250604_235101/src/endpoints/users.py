from fastapi import APIRouter
from ..models import User

router = APIRouter()

@router.post('/users/')
def create_user(user: User):
    # Logic to add user to Firestore
    return {'id': user.id, 'name': user.name, 'email': user.email}
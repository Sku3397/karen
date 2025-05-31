from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from src.schemas.user import User, UserCreate, UserUpdate
from src.security.auth import get_current_user

router = APIRouter()

# Dummy in-memory storage for demonstration
users_db = {}

@router.post("/", response_model=User, status_code=201)
def create_user(user: UserCreate):
    if user.email in users_db:
        raise HTTPException(status_code=400, detail="Email already registered")
    users_db[user.email] = user.dict()
    return User(**users_db[user.email])

@router.get("/me", response_model=User)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/", response_model=List[User])
def list_users(current_user: User = Depends(get_current_user)):
    return [User(**data) for data in users_db.values()]

@router.put("/{email}", response_model=User)
def update_user(email: str, update: UserUpdate, current_user: User = Depends(get_current_user)):
    if email not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    users_db[email].update(update.dict(exclude_unset=True))
    return User(**users_db[email])

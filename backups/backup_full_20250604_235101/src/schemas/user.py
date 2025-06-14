from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List

class UserBase(BaseModel):
    email: EmailStr
    profile: dict
    preferences: Optional[dict] = {}
    permissions: Optional[List[str]] = []

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    profile: Optional[dict] = None
    preferences: Optional[dict] = None
    permissions: Optional[List[str]] = None

class User(UserBase):
    pass

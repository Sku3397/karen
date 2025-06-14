# Define Pydantic models for Firestore collections
from pydantic import BaseModel
from typing import List, Dict, Any

class User(BaseModel):
    id: str
    name: str
    email: str

class Procedure(BaseModel):
    id: str
    name: str
    description: str
    estimated_time_minutes: int
    required_tools: List[str]
    price: float

class FAQ(BaseModel):
    id: str
    question: str
    answer: str
    category: str = "general"

class ClientHistory(BaseModel):
    client_id: str
    interactions: List[Dict[str, Any]]

class Pricing(BaseModel):
    service_id: str
    base_price: float
    hourly_rate: float

# Define other models following the same structure for tasks, appointments, etc.
"""
Appointments API endpoint for the AI Handyman Secretary Assistant.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

router = APIRouter()

class AppointmentCreate(BaseModel):
    title: str
    description: str
    start_time: str
    end_time: str
    client_id: str
    location: Optional[str] = None

class AppointmentResponse(BaseModel):
    id: str
    title: str
    description: str
    start_time: str
    end_time: str
    client_id: str
    location: Optional[str]
    status: str
    created_at: str

# In-memory storage
appointments_db = {}

@router.post("/appointments/", response_model=AppointmentResponse)
async def create_appointment(appointment: AppointmentCreate):
    """Create a new appointment."""
    appointment_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    appointment_data = {
        "id": appointment_id,
        "title": appointment.title,
        "description": appointment.description,
        "start_time": appointment.start_time,
        "end_time": appointment.end_time,
        "client_id": appointment.client_id,
        "location": appointment.location,
        "status": "scheduled",
        "created_at": now
    }
    
    appointments_db[appointment_id] = appointment_data
    return AppointmentResponse(**appointment_data)

@router.get("/appointments/", response_model=List[AppointmentResponse])
async def list_appointments():
    """List all appointments."""
    return [AppointmentResponse(**apt) for apt in appointments_db.values()]

@router.get("/appointments/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(appointment_id: str):
    """Get a specific appointment."""
    if appointment_id not in appointments_db:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    return AppointmentResponse(**appointments_db[appointment_id])
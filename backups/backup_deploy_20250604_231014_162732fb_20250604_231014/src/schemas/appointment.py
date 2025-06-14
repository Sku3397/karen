from pydantic import BaseModel, Field
from typing import Optional, List

class AppointmentBase(BaseModel):
    schedule: dict
    participants: Optional[List[str]] = []
    location: Optional[str] = None
    notes: Optional[str] = None

class AppointmentCreate(AppointmentBase):
    pass

class AppointmentUpdate(BaseModel):
    schedule: Optional[dict] = None
    participants: Optional[List[str]] = None
    location: Optional[str] = None
    notes: Optional[str] = None

class Appointment(AppointmentBase):
    id: str

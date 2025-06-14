from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from src.schemas.appointment import Appointment, AppointmentCreate, AppointmentUpdate
from src.security.auth import get_current_user

router = APIRouter()

appointments_db = {}

def get_appointment_or_404(appointment_id: str):
    appt = appointments_db.get(appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appt

@router.post("/", response_model=Appointment, status_code=201)
def create_appointment(appt: AppointmentCreate, current_user=Depends(get_current_user)):
    appt_id = str(len(appointments_db) + 1)
    appt_data = appt.dict()
    appt_data["id"] = appt_id
    appointments_db[appt_id] = appt_data
    return Appointment(**appt_data)

@router.get("/", response_model=List[Appointment])
def list_appointments(current_user=Depends(get_current_user)):
    return [Appointment(**data) for data in appointments_db.values()]

@router.get("/{appointment_id}", response_model=Appointment)
def get_appointment(appointment_id: str, current_user=Depends(get_current_user)):
    return Appointment(**get_appointment_or_404(appointment_id))

@router.put("/{appointment_id}", response_model=Appointment)
def update_appointment(appointment_id: str, update: AppointmentUpdate, current_user=Depends(get_current_user)):
    appt = get_appointment_or_404(appointment_id)
    appt.update(update.dict(exclude_unset=True))
    appointments_db[appointment_id] = appt
    return Appointment(**appt)

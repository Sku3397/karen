from fastapi import APIRouter

router = APIRouter()

@router.post('/appointments/')
def schedule_appointment(appointment: Appointment):
    pass

@router.get('/appointments/')
def list_appointments():
    pass
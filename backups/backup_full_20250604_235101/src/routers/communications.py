from fastapi import APIRouter

router = APIRouter()

@router.post('/communications/send')
def send_communication(communication: Communication):
    pass
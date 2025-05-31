# Example usage of authentication, role checks, and input validation
from fastapi import APIRouter, Depends, HTTPException
from src.auth.middleware import require_role
from src.validators.input_validators import EmailInput, VoiceInput, CalendarEventInput

router = APIRouter()

@router.post("/email/process")
def process_email(input: EmailInput, user = Depends(require_role(["admin", "agent"]))):
    # Process validated email input
    return {"status": "Email processed", "user": user["role"]}

@router.post("/voice/process")
def process_voice(input: VoiceInput, user = Depends(require_role(["admin", "agent"]))):
    # Process validated voice transcript
    return {"status": "Voice processed", "user": user["role"]}

@router.post("/calendar/event")
def create_calendar_event(event: CalendarEventInput, user = Depends(require_role(["admin", "agent"]))):
    # Process validated calendar event
    return {"status": "Event created", "user": user["role"]}

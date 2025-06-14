"""
Communications API endpoint for the AI Handyman Secretary Assistant.
Handles email, SMS, and voice communications through the CommunicatorAgent.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime
import uuid

router = APIRouter()

# Pydantic models for communications
class EmailRequest(BaseModel):
    to_email: EmailStr
    subject: str
    body: str
    lang: str = "en"

class SMSRequest(BaseModel):
    phone_number: str
    message: str
    lang: str = "en"

class CallTranscriptionRequest(BaseModel):
    audio_url: str

class CommunicationResponse(BaseModel):
    id: str
    type: str  # email, sms, call
    status: str
    message: str
    timestamp: str

class CommunicationHistory(BaseModel):
    id: str
    type: str
    contact: str
    content: str
    status: str
    timestamp: str

# In-memory storage for communication history
communications_db = {}

@router.post("/communications/email", response_model=CommunicationResponse)
async def send_email(email_request: EmailRequest):
    """Send an email."""
    try:
        # In a real implementation, this would use the CommunicatorAgent
        # For now, simulate the email sending
        comm_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        # Simulate email sending logic
        success = True  # Would be actual result from CommunicatorAgent
        
        communication_record = {
            "id": comm_id,
            "type": "email",
            "contact": email_request.to_email,
            "content": f"Subject: {email_request.subject}\nBody: {email_request.body}",
            "status": "sent" if success else "failed",
            "timestamp": now
        }
        
        communications_db[comm_id] = communication_record
        
        return CommunicationResponse(
            id=comm_id,
            type="email",
            status="sent" if success else "failed",
            message=f"Email {'sent successfully' if success else 'failed to send'} to {email_request.to_email}",
            timestamp=now
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

@router.post("/communications/sms", response_model=CommunicationResponse)
async def send_sms(sms_request: SMSRequest):
    """Send an SMS."""
    try:
        comm_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        # Simulate SMS sending logic
        success = True  # Would be actual result from CommunicatorAgent
        
        communication_record = {
            "id": comm_id,
            "type": "sms",
            "contact": sms_request.phone_number,
            "content": sms_request.message,
            "status": "sent" if success else "failed",
            "timestamp": now
        }
        
        communications_db[comm_id] = communication_record
        
        return CommunicationResponse(
            id=comm_id,
            type="sms",
            status="sent" if success else "failed",
            message=f"SMS {'sent successfully' if success else 'failed to send'} to {sms_request.phone_number}",
            timestamp=now
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send SMS: {str(e)}")

@router.post("/communications/transcribe", response_model=CommunicationResponse)
async def transcribe_call(transcription_request: CallTranscriptionRequest):
    """Transcribe an incoming call."""
    try:
        comm_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        # Simulate call transcription logic
        transcript = "Mock transcription of the call"  # Would be actual result from CommunicatorAgent
        
        communication_record = {
            "id": comm_id,
            "type": "call",
            "contact": "unknown",  # Would extract from audio metadata
            "content": transcript,
            "status": "transcribed",
            "timestamp": now
        }
        
        communications_db[comm_id] = communication_record
        
        return CommunicationResponse(
            id=comm_id,
            type="call",
            status="transcribed",
            message=f"Call transcribed successfully: {transcript[:50]}...",
            timestamp=now
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to transcribe call: {str(e)}")

@router.get("/communications/history", response_model=List[CommunicationHistory])
async def get_communication_history(
    contact: Optional[str] = None,
    type: Optional[str] = None,
    limit: int = 50
):
    """Get communication history with optional filtering."""
    communications = list(communications_db.values())
    
    # Apply filters
    if contact:
        communications = [c for c in communications if contact.lower() in c["contact"].lower()]
    if type:
        communications = [c for c in communications if c["type"] == type]
    
    # Sort by timestamp (newest first) and limit
    communications.sort(key=lambda x: x["timestamp"], reverse=True)
    communications = communications[:limit]
    
    return [CommunicationHistory(**comm) for comm in communications]

@router.get("/communications/{comm_id}", response_model=CommunicationHistory)
async def get_communication(comm_id: str):
    """Get a specific communication record."""
    if comm_id not in communications_db:
        raise HTTPException(status_code=404, detail="Communication record not found")
    
    return CommunicationHistory(**communications_db[comm_id])

@router.get("/communications/stats/summary")
async def get_communication_stats():
    """Get communication statistics summary."""
    communications = list(communications_db.values())
    
    stats = {
        "total_communications": len(communications),
        "by_type": {},
        "by_status": {},
        "recent_activity": len([c for c in communications if 
                               (datetime.now() - datetime.fromisoformat(c["timestamp"])).days <= 7])
    }
    
    # Count by type
    for comm in communications:
        comm_type = comm["type"]
        stats["by_type"][comm_type] = stats["by_type"].get(comm_type, 0) + 1
    
    # Count by status
    for comm in communications:
        status = comm["status"]
        stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
    
    return stats
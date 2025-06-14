# Input Validators for Email, Voice, and Calendar Data
import re
from typing import Any, Dict
from pydantic import BaseModel, validator, EmailStr, ValidationError

class EmailInput(BaseModel):
    email: EmailStr
    subject: str
    body: str

    @validator('subject', 'body')
    def no_malicious_content(cls, v):
        if re.search(r'<script|javascript:|onerror=', v, re.IGNORECASE):
            raise ValueError("Potential XSS detected in input.")
        return v

class VoiceInput(BaseModel):
    transcript: str
    @validator('transcript')
    def validate_transcript(cls, v):
        if not v or len(v) > 2048:
            raise ValueError("Transcript empty or too long.")
        if re.search(r'[<>]|script|javascript:', v, re.IGNORECASE):
            raise ValueError("Potential XSS or code injection detected.")
        return v

class CalendarEventInput(BaseModel):
    title: str
    description: str
    start_time: str
    end_time: str
    attendees: list[EmailStr]

    @validator('title', 'description')
    def safe_text(cls, v):
        if re.search(r'<script|javascript:|onerror=', v, re.IGNORECASE):
            raise ValueError("Potential XSS detected in event data.")
        return v

    @validator('start_time', 'end_time')
    def valid_datetime_format(cls, v):
        # Expecting ISO 8601 format
        iso8601_regex = r"^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}(:\\d{2})?(\\.\\d+)?(Z|[+-]\\d{2}:\\d{2})$"
        if not re.match(iso8601_regex, v):
            raise ValueError("Invalid datetime format; must be ISO 8601.")
        return v

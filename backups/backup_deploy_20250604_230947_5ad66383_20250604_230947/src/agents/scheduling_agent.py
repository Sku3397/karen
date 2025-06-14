# Scheduling Agent core logic
import datetime
from typing import List, Optional, Dict
from src.agents.calendar.google_calendar import GoogleCalendarClient
from src.agents.calendar.outlook_calendar import OutlookCalendarClient
from src.agents.reminders import schedule_reminder
from google.cloud import firestore

class SchedulingAgent:
    def __init__(self, db=None):
        self.db = db or firestore.Client()
        self.gc_client = GoogleCalendarClient()
        self.outlook_client = OutlookCalendarClient()

    def schedule_event(self, user_id: str, provider: str, event_data: dict) -> dict:
        if provider == 'google':
            event = self.gc_client.create_event(user_id, event_data)
        elif provider == 'outlook':
            event = self.outlook_client.create_event(user_id, event_data)
        else:
            raise ValueError("Unsupported provider")
        # Persist to Firestore
        self.db.collection('scheduled_events').add({
            'user_id': user_id,
            'provider': provider,
            'event_id': event['id'],
            'event_data': event,
            'created_at': datetime.datetime.utcnow().isoformat()
        })
        # Schedule reminder if requested
        if event_data.get('reminder_minutes_before'):
            schedule_reminder(user_id, event['id'], provider, event_data['start'], event_data['reminder_minutes_before'])
        return event

    def list_events(self, user_id: str, provider: str, date_range: dict) -> List[dict]:
        if provider == 'google':
            return self.gc_client.list_events(user_id, date_range)
        elif provider == 'outlook':
            return self.outlook_client.list_events(user_id, date_range)
        else:
            raise ValueError("Unsupported provider")

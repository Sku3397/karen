# Google Calendar integration utilities
import os
import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from src.utils.oauth import get_google_credentials

class GoogleCalendarClient:
    def __init__(self):
        pass

    def create_event(self, user_id: str, event_data: dict) -> dict:
        creds = get_google_credentials(user_id)
        service = build('calendar', 'v3', credentials=creds)
        event_body = {
            'summary': event_data['summary'],
            'start': {'dateTime': event_data['start'], 'timeZone': event_data.get('timezone', 'UTC')},
            'end': {'dateTime': event_data['end'], 'timeZone': event_data.get('timezone', 'UTC')}
        }
        if event_data.get('description'):
            event_body['description'] = event_data['description']
        event = service.events().insert(calendarId='primary', body=event_body).execute()
        return event

    def list_events(self, user_id: str, date_range: dict):
        creds = get_google_credentials(user_id)
        service = build('calendar', 'v3', credentials=creds)
        events_result = service.events().list(
            calendarId='primary',
            timeMin=date_range['start'],
            timeMax=date_range['end'],
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        return events_result.get('items', [])

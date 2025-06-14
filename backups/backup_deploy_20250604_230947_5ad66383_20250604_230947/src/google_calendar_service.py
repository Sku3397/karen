# Google Calendar API integration. Assumes OAuth2 setup for user.
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import datetime

class GoogleCalendarService:
    def __init__(self, user_id):
        self.creds = self._load_user_credentials(user_id)
        self.service = build('calendar', 'v3', credentials=self.creds)

    def _load_user_credentials(self, user_id):
        # Pseudocode: Load from secure storage
        # For real deployment, integrate with Google Identity Platform
        return Credentials(token='user-access-token')

    def create_event(self, details):
        event_body = {
            'summary': details['title'],
            'location': details.get('location', ''),
            'description': details.get('notes', ''),
            'start': {'dateTime': details['start'].isoformat(), 'timeZone': 'UTC'},
            'end': {'dateTime': details['end'].isoformat(), 'timeZone': 'UTC'},
            'attendees': [{'email': e} for e in details.get('participants', [])],
        }
        event = self.service.events().insert(calendarId='primary', body=event_body).execute()
        return event

    def list_events(self, start_time, end_time):
        events_result = self.service.events().list(
            calendarId='primary',
            timeMin=start_time.isoformat() + 'Z',
            timeMax=end_time.isoformat() + 'Z',
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])
        # Normalize event dicts for conflict check
        normalized = []
        for e in events:
            normalized.append({
                'id': e['id'],
                'start': datetime.datetime.fromisoformat(e['start']['dateTime'].replace('Z', '+00:00')),
                'end': datetime.datetime.fromisoformat(e['end']['dateTime'].replace('Z', '+00:00')),
                'summary': e.get('summary', '')
            })
        return normalized

    def update_event(self, event_id, details):
        event = self.service.events().get(calendarId='primary', eventId=event_id).execute()
        if 'title' in details:
            event['summary'] = details['title']
        if 'location' in details:
            event['location'] = details['location']
        if 'notes' in details:
            event['description'] = details['notes']
        if 'start' in details:
            event['start']['dateTime'] = details['start'].isoformat()
        if 'end' in details:
            event['end']['dateTime'] = details['end'].isoformat()
        updated_event = self.service.events().update(calendarId='primary', eventId=event_id, body=event).execute()
        return updated_event

    def delete_event(self, event_id):
        self.service.events().delete(calendarId='primary', eventId=event_id).execute()

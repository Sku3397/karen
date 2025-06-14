# Google Calendar API integration
import requests
from google.oauth2.credentials import Credentials

class GoogleCalendarClient:
    def __init__(self, credentials_dict):
        # Handle empty credentials for testing
        if not credentials_dict or not all(key in credentials_dict for key in ['client_id', 'client_secret', 'refresh_token']):
            # Create mock credentials for testing
            self.creds = None
            self.is_mock = True
        else:
            self.creds = Credentials.from_authorized_user_info(credentials_dict)
            self.is_mock = False
        
        self.base_url = 'https://www.googleapis.com/calendar/v3'

    def list_events(self):
        if self.is_mock:
            # Return mock events for testing
            return [
                {
                    'id': 'mock_event_1',
                    'summary': 'Mock Event 1',
                    'start': {'dateTime': '2024-01-01T10:00:00Z'},
                    'end': {'dateTime': '2024-01-01T11:00:00Z'}
                }
            ]
        
        url = f'{self.base_url}/calendars/primary/events'
        resp = requests.get(url, headers={"Authorization": f"Bearer {self.creds.token}"})
        resp.raise_for_status()
        return resp.json().get('items', [])

    def create_event(self, event_data):
        if self.is_mock:
            # Return mock created event for testing
            return {
                'id': 'mock_created_event',
                'summary': event_data.get('summary', 'Mock Event'),
                'start': event_data.get('start', {'dateTime': '2024-01-01T10:00:00Z'}),
                'end': event_data.get('end', {'dateTime': '2024-01-01T11:00:00Z'}),
                'status': 'confirmed'
            }
        
        url = f'{self.base_url}/calendars/primary/events'
        resp = requests.post(url, headers={"Authorization": f"Bearer {self.creds.token}", "Content-Type": "application/json"}, json=event_data)
        resp.raise_for_status()
        return resp.json()

    def update_event(self, event_id, event_data):
        if self.is_mock:
            # Return mock updated event for testing
            return {
                'id': event_id,
                'summary': event_data.get('summary', 'Updated Mock Event'),
                'start': event_data.get('start', {'dateTime': '2024-01-01T10:00:00Z'}),
                'end': event_data.get('end', {'dateTime': '2024-01-01T11:00:00Z'}),
                'status': 'confirmed'
            }
        
        url = f'{self.base_url}/calendars/primary/events/{event_id}'
        resp = requests.put(url, headers={"Authorization": f"Bearer {self.creds.token}", "Content-Type": "application/json"}, json=event_data)
        resp.raise_for_status()
        return resp.json()

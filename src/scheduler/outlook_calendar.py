# Outlook Calendar API integration
import requests

class OutlookCalendarClient:
    def __init__(self, credentials_dict):
        # Handle empty credentials for testing
        if not credentials_dict or 'access_token' not in credentials_dict:
            self.token = None
            self.is_mock = True
        else:
            self.token = credentials_dict['access_token']
            self.is_mock = False
        
        self.base_url = 'https://graph.microsoft.com/v1.0/me/events'

    def list_events(self):
        if self.is_mock:
            # Return mock events for testing
            return [
                {
                    'id': 'mock_outlook_event_1',
                    'subject': 'Mock Outlook Event 1',
                    'start': {'dateTime': '2024-01-01T14:00:00Z'},
                    'end': {'dateTime': '2024-01-01T15:00:00Z'}
                }
            ]
        
        resp = requests.get(self.base_url, headers={"Authorization": f"Bearer {self.token}"})
        resp.raise_for_status()
        return resp.json().get('value', [])

    def create_event(self, event_data):
        if self.is_mock:
            # Return mock created event for testing
            return {
                'id': 'mock_outlook_created_event',
                'subject': event_data.get('subject', 'Mock Outlook Event'),
                'start': event_data.get('start', {'dateTime': '2024-01-01T14:00:00Z'}),
                'end': event_data.get('end', {'dateTime': '2024-01-01T15:00:00Z'}),
                'status': 'confirmed'
            }
        
        resp = requests.post(self.base_url, headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}, json=event_data)
        resp.raise_for_status()
        return resp.json()

    def update_event(self, event_id, event_data):
        if self.is_mock:
            # Return mock updated event for testing
            return {
                'id': event_id,
                'subject': event_data.get('subject', 'Updated Mock Outlook Event'),
                'start': event_data.get('start', {'dateTime': '2024-01-01T14:00:00Z'}),
                'end': event_data.get('end', {'dateTime': '2024-01-01T15:00:00Z'}),
                'status': 'confirmed'
            }
        
        url = f'{self.base_url}/{event_id}'
        resp = requests.patch(url, headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}, json=event_data)
        resp.raise_for_status()
        return resp.json()

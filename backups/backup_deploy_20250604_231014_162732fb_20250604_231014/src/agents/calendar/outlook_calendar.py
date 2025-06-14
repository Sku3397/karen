# Outlook Calendar integration utilities
import requests
from src.utils.oauth import get_outlook_access_token

class OutlookCalendarClient:
    def __init__(self):
        self.base_url = 'https://graph.microsoft.com/v1.0/me/events'

    def create_event(self, user_id: str, event_data: dict) -> dict:
        token = get_outlook_access_token(user_id)
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        body = {
            'subject': event_data['summary'],
            'start': {'dateTime': event_data['start'], 'timeZone': event_data.get('timezone', 'UTC')},
            'end': {'dateTime': event_data['end'], 'timeZone': event_data.get('timezone', 'UTC')},
        }
        if event_data.get('description'):
            body['body'] = {'contentType': 'text', 'content': event_data['description']}
        response = requests.post(self.base_url, headers=headers, json=body)
        response.raise_for_status()
        return response.json()

    def list_events(self, user_id: str, date_range: dict):
        token = get_outlook_access_token(user_id)
        headers = {'Authorization': f'Bearer {token}'}
        params = {
            'startDateTime': date_range['start'],
            'endDateTime': date_range['end']
        }
        response = requests.get(self.base_url, headers=headers, params=params)
        response.raise_for_status()
        return response.json().get('value', [])

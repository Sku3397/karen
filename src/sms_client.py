# SMSClient: Handles sending and receiving SMS via Twilio
from twilio.rest import Client
from typing import Optional

class SMSClient:
    def __init__(self, account_sid, auth_token, from_phone):
        self.client = Client(account_sid, auth_token)
        self.from_phone = from_phone

    def send_sms(self, to: str, body: str) -> bool:
        try:
            message = self.client.messages.create(
                body=body,
                from_=self.from_phone,
                to=to
            )
            return message.sid is not None
        except Exception as e:
            print(f"SMS send failed: {e}")
            return False

    def fetch_sms(self, from_: Optional[str] = None):
        try:
            messages = self.client.messages.list(from_=from_)
            return [{
                'from': msg.from_,
                'to': msg.to,
                'body': msg.body,
                'date_sent': str(msg.date_sent)
            } for msg in messages]
        except Exception as e:
            print(f"SMS fetch failed: {e}")
            return []

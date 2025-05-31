from twilio.rest import Client
from typing import Optional

class SMSHandler:
    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        self.client = Client(account_sid, auth_token)
        self.from_number = from_number

    def send_sms(self, to_number: str, message: str) -> Optional[str]:
        try:
            msg = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )
            return msg.sid
        except Exception as e:
            print(f"SMSHandler: Failed to send SMS - {e}")
            return None

# TwilioClient: Handles SMS and call functionality via Twilio API
from twilio.rest import Client

class TwilioClient:
    def __init__(self, creds):
        self.client = Client(creds['account_sid'], creds['auth_token'])
        self.from_number = creds['from_number']

    def send_sms(self, to, message):
        msg = self.client.messages.create(
            body=message,
            from_=self.from_number,
            to=to
        )
        return msg.sid

    def fetch_sms(self):
        messages = self.client.messages.list()
        return [
            {
                'from': m.from_,
                'to': m.to,
                'body': m.body,
                'date_sent': m.date_sent
            } for m in messages
        ]

    def initiate_call(self, to, twiml_url):
        call = self.client.calls.create(
            to=to,
            from_=self.from_number,
            url=twiml_url
        )
        return call.sid

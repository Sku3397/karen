# GmailClient: Handles sending and receiving emails via Gmail API
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64

class GmailClient:
    def __init__(self, creds):
        self.service = build('gmail', 'v1', credentials=creds)

    def send_email(self, to, subject, body):
        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject
        create_message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}
        sent = self.service.users().messages().send(userId='me', body=create_message).execute()
        return sent

    def fetch_emails(self, query=None):
        results = self.service.users().messages().list(userId='me', q=query).execute()
        messages = results.get('messages', [])
        emails = []
        for msg in messages:
            msg_data = self.service.users().messages().get(userId='me', id=msg['id']).execute()
            emails.append(msg_data)
        return emails

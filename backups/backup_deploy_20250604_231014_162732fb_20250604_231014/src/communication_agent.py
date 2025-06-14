# CommunicationAgent: Facade for email, SMS, and voice processing
from src.email_client import EmailClient
from src.sms_client import SMSClient
from src.voice_client import VoiceClient

class CommunicationAgent:
    def __init__(self, email_config, sms_config, gcp_config):
        self.email_client = EmailClient(**email_config)
        self.sms_client = SMSClient(**sms_config)
        self.voice_client = VoiceClient(**gcp_config)

    # Email methods
    def send_email(self, to, subject, body, attachments=None):
        return self.email_client.send_email(to, subject, body, attachments)

    def fetch_emails(self, folder='INBOX', search_criteria=None):
        return self.email_client.fetch_emails(folder, search_criteria)

    # SMS methods
    def send_sms(self, to, body):
        return self.sms_client.send_sms(to, body)

    def fetch_sms(self, from_=None):
        return self.sms_client.fetch_sms(from_)

    # Voice methods
    def transcribe_audio(self, audio_file_path, language_code="en-US"):
        return self.voice_client.transcribe(audio_file_path, language_code)

    def synthesize_speech(self, text, output_audio_file, language_code="en-US"):
        return self.voice_client.synthesize(text, output_audio_file, language_code)

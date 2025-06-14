# CommunicationAgent: Facade for email, SMS, and voice processing
from datetime import datetime
from src.email_client import EmailClient
from src.sms_client import SMSClient
from src.voice_client import VoiceClient
from src.agent_activity_logger import AgentActivityLogger

activity_logger = AgentActivityLogger()

class CommunicationAgent:
    def __init__(self, email_config, sms_config, gcp_config):
        self.email_client = EmailClient(**email_config)
        self.sms_client = SMSClient(**sms_config)
        self.voice_client = VoiceClient(**gcp_config)
        
        # Log initialization
        activity_logger.log_activity(
            agent_name="communication_agent",
            activity_type="initialization",
            details={
                "email_client": "initialized",
                "sms_client": "initialized", 
                "voice_client": "initialized",
                "timestamp": datetime.now().isoformat()
            }
        )

    # Email methods
    def send_email(self, to, subject, body, attachments=None):
        result = self.email_client.send_email(to, subject, body, attachments)
        
        # Log email sending activity
        activity_logger.log_activity(
            agent_name="communication_agent",
            activity_type="email_sent",
            details={
                "to": to,
                "subject": subject,
                "body_length": len(body) if body else 0,
                "has_attachments": attachments is not None,
                "success": result is not None,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        return result

    def fetch_emails(self, folder='INBOX', search_criteria=None):
        return self.email_client.fetch_emails(folder, search_criteria)

    # SMS methods
    def send_sms(self, to, body):
        result = self.sms_client.send_sms(to, body)
        
        # Log SMS sending activity
        activity_logger.log_activity(
            agent_name="communication_agent",
            activity_type="sms_sent",
            details={
                "to": to,
                "body_length": len(body) if body else 0,
                "success": result,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        return result

    def fetch_sms(self, from_=None):
        return self.sms_client.fetch_sms(from_)

    # Voice methods
    def transcribe_audio(self, audio_file_path, language_code="en-US"):
        return self.voice_client.transcribe(audio_file_path, language_code)

    def synthesize_speech(self, text, output_audio_file, language_code="en-US"):
        return self.voice_client.synthesize(text, output_audio_file, language_code)

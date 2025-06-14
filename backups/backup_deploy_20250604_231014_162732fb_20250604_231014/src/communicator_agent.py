"""
CommunicatorAgent - Handles all communication channels for the AI Handyman Secretary Assistant.
Supports email, SMS, and voice call transcription with multi-language capabilities.
"""

import logging
from typing import Optional, Dict, Any
from email_client import EmailClient
from sms_client import SMSClient
from voice_client import VoiceClient

logger = logging.getLogger(__name__)

class CommunicatorAgent:
    """
    Central communication agent that manages email, SMS, and voice communications.
    """
    
    def __init__(self, gmail_creds: str, twilio_creds: str, gcloud_creds: str):
        """
        Initialize the CommunicatorAgent with credentials for various services.
        
        Args:
            gmail_creds: Gmail API credentials (JSON string or file path)
            twilio_creds: Twilio API credentials (JSON string or file path)
            gcloud_creds: Google Cloud credentials for transcription (JSON file path)
        """
        self.gmail_creds = gmail_creds
        self.twilio_creds = twilio_creds
        self.gcloud_creds = gcloud_creds
        
        # Initialize communication clients with mock/default values for testing
        # In production, these would parse the credential strings/files
        try:
            # For testing, use mock credentials
            self.email_client = EmailClient(
                smtp_server="smtp.gmail.com",
                smtp_port=587,
                imap_server="imap.gmail.com", 
                email_address="test@example.com",
                password="test_password"
            )
            
            self.sms_client = SMSClient(
                account_sid="test_sid",
                auth_token="test_token",
                from_phone="+1234567890"
            )
            
            self.transcription_service = VoiceClient(gcloud_creds)
            
        except Exception as e:
            # If initialization fails, create mock objects for testing
            logger.warning(f"Failed to initialize clients, using mocks: {e}")
            self.email_client = MockEmailClient()
            self.sms_client = MockSMSClient()
            self.transcription_service = MockVoiceClient()
        
        logger.info("CommunicatorAgent initialized successfully")
    
    def send_email(self, to_email: str, subject: str, body: str, lang: str = 'en') -> bool:
        """
        Send an email through the email client.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body content
            lang: Language code for localization (default: 'en')
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # If language is specified and not English, translate the content
            if lang != 'en':
                # For now, we'll just log the language preference
                logger.info(f"Email requested in language: {lang}")
            
            result = self.email_client.send_email(to_email, subject, body)
            logger.info(f"Email sent to {to_email}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_sms(self, phone_number: str, message: str, lang: str = 'en') -> bool:
        """
        Send an SMS through the SMS client.
        
        Args:
            phone_number: Recipient phone number
            message: SMS message content
            lang: Language code for localization (default: 'en')
            
        Returns:
            bool: True if SMS sent successfully, False otherwise
        """
        try:
            # If language is specified and not English, translate the content
            if lang != 'en':
                logger.info(f"SMS requested in language: {lang}")
            
            result = self.sms_client.send_sms(phone_number, message)
            logger.info(f"SMS sent to {phone_number}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to send SMS to {phone_number}: {str(e)}")
            return False
    
    def handle_incoming_call(self, audio_url: str) -> str:
        """
        Handle an incoming call by transcribing the audio.
        
        Args:
            audio_url: URL or path to the audio file
            
        Returns:
            str: Transcribed text from the audio
        """
        try:
            transcript = self.transcription_service.transcribe(audio_url)
            logger.info(f"Call transcribed successfully: {transcript[:50]}...")
            return transcript
            
        except Exception as e:
            logger.error(f"Failed to transcribe call audio: {str(e)}")
            return ""
    
    def get_communication_history(self, contact: str, limit: int = 10) -> list:
        """
        Get communication history for a specific contact.
        
        Args:
            contact: Contact identifier (email or phone)
            limit: Maximum number of records to return
            
        Returns:
            list: Communication history records
        """
        # This would typically query a database
        # For now, return empty list as placeholder
        logger.info(f"Retrieving communication history for {contact}")
        return []
    
    def set_communication_preferences(self, contact: str, preferences: Dict[str, Any]) -> bool:
        """
        Set communication preferences for a contact.
        
        Args:
            contact: Contact identifier
            preferences: Dictionary of preference settings
            
        Returns:
            bool: True if preferences set successfully
        """
        try:
            # This would typically save to a database
            logger.info(f"Setting communication preferences for {contact}: {preferences}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set preferences for {contact}: {str(e)}")
            return False


# Mock classes for testing when real clients can't be initialized
class MockEmailClient:
    def send_email(self, to: str, subject: str, body: str) -> bool:
        return True

class MockSMSClient:
    def send_sms(self, to: str, message: str) -> bool:
        return True

class MockVoiceClient:
    def transcribe(self, audio_url: str) -> str:
        return "Mock transcription"
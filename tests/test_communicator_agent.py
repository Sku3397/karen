# Unit tests for CommunicatorAgent (mocking external services)
import unittest
from unittest.mock import MagicMock
from src.communicator_agent import CommunicatorAgent

class TestCommunicatorAgent(unittest.TestCase):
    def setUp(self):
        self.agent = CommunicatorAgent('gmail_creds', 'twilio_creds', 'gcloud_creds')
        self.agent.email_client.send_email = MagicMock(return_value=True)
        self.agent.sms_client.send_sms = MagicMock(return_value=True)
        self.agent.transcription_service.transcribe = MagicMock(return_value="Hello World")

    def test_send_email(self):
        self.assertTrue(self.agent.send_email('test@example.com', 'Hi', 'Body'))
    
    def test_send_sms(self):
        self.assertTrue(self.agent.send_sms('+11234567890', 'Test message'))

    def test_handle_incoming_call(self):
        transcript = self.agent.handle_incoming_call('audio_url')
        self.assertEqual(transcript, "Hello World")

    def test_multilang_response(self):
        self.agent.email_client.send_email = MagicMock(return_value=True)
        result = self.agent.send_email('test@example.com', 'Hi', 'Hello', lang='es')
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()

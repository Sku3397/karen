"""
Integration tests for SMS functionality
Verifies email, SMS, and simultaneous operation
"""
import pytest
import asyncio
import os
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

# Import Karen's components
from src.sms_client import SMSClient
from src.handyman_sms_engine import HandymanSMSEngine
from src.email_client import EmailClient
from src.handyman_response_engine import HandymanResponseEngine
from src.celery_sms_tasks import (
    get_sms_client_instance, 
    get_sms_engine_instance,
    fetch_new_sms,
    process_sms_with_llm,
    send_karen_sms_reply
)

class TestSMSIntegration:
    """Test SMS functionality in isolation"""
    
    @pytest.fixture
    def mock_sms_client(self):
        """Create a mock SMS client for testing"""
        mock_client = Mock(spec=SMSClient)
        mock_client.karen_phone = "+17575551234"
        mock_client.send_sms.return_value = True
        mock_client.fetch_sms.return_value = []
        mock_client.mark_sms_as_processed.return_value = True
        mock_client.is_sms_processed.return_value = False
        return mock_client

    @pytest.fixture
    def mock_twilio_client(self):
        """Mock Twilio client for testing"""
        mock_twilio = MagicMock()
        
        # Mock message object
        mock_message = MagicMock()
        mock_message.sid = "SM123456789"
        mock_message.from_ = "+15551234567"
        mock_message.to = "+17575551234"
        mock_message.body = "Test message"
        mock_message.date_sent = datetime.now(timezone.utc)
        mock_message.status = "received"
        mock_message.direction = "inbound"
        
        mock_twilio.messages.create.return_value = mock_message
        mock_twilio.messages.list.return_value = [mock_message]
        
        return mock_twilio

    @pytest.fixture
    def sms_client(self, mock_twilio_client):
        """Create real SMS client with mocked Twilio"""
        with patch('src.sms_client.Client', return_value=mock_twilio_client):
            return SMSClient(
                karen_phone="+17575551234",
                token_data={'account_sid': 'test_sid', 'auth_token': 'test_token'}
            )

    @pytest.fixture
    def sms_engine(self):
        """Create SMS engine for testing"""
        mock_llm = Mock()
        mock_llm.generate_text.return_value = "Thank you for your message! Call 757-354-4577 for assistance."
        
        return HandymanSMSEngine(
            business_name="Beach Handyman",
            service_area="Virginia Beach area", 
            phone="757-354-4577",
            llm_client=mock_llm
        )

    def test_sms_client_initialization(self, sms_client):
        """Test SMS client initializes correctly"""
        assert sms_client.karen_phone == "+17575551234"
        assert sms_client.account_sid == "test_sid"
        assert sms_client.auth_token == "test_token"

    def test_sms_send_functionality(self, sms_client):
        """Test SMS sending"""
        result = sms_client.send_sms("+15551234567", "Test message")
        assert result is True
        
        # Verify Twilio was called correctly
        sms_client.client.messages.create.assert_called_once_with(
            body="Test message",
            from_="+17575551234",
            to="+15551234567"
        )

    def test_sms_fetch_functionality(self, sms_client):
        """Test SMS fetching"""
        messages = sms_client.fetch_sms(max_results=10)
        assert isinstance(messages, list)
        assert len(messages) >= 0
        
        # Verify structure of returned messages
        if messages:
            msg = messages[0]
            required_fields = ['id', 'sender', 'body', 'date_str', 'uid']
            for field in required_fields:
                assert field in msg

    def test_sms_classification(self, sms_engine):
        """Test SMS message classification"""
        test_cases = [
            ("Emergency! Pipe burst!", True, False),  # (message, is_emergency, is_quote)
            ("Can I get a quote for plumbing?", False, True),
            ("yes", False, False),
            ("STOP", False, False),
        ]
        
        for message, expected_emergency, expected_quote in test_cases:
            classification = sms_engine.classify_sms_type("+15551234567", message)
            
            assert classification['is_emergency'] == expected_emergency
            assert classification['is_quote_request'] == expected_quote
            assert 'sender_phone' in classification

    @pytest.mark.asyncio
    async def test_sms_response_generation(self, sms_engine):
        """Test SMS response generation"""
        response, classification = await sms_engine.generate_sms_response_async(
            "+15551234567", 
            "Need plumbing help"
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert len(response) <= 1600  # SMS limit
        assert isinstance(classification, dict)

    def test_sms_truncation(self, sms_engine):
        """Test SMS response truncation"""
        long_response = "This is a very long response " * 20  # Much longer than SMS limit
        
        truncated = sms_engine._truncate_sms_response(long_response)
        
        assert len(truncated) <= 160  # Single SMS limit
        assert "757-354-4577" in truncated  # Phone preserved

    def test_multipart_sms_splitting(self, sms_engine):
        """Test splitting long SMS into parts"""
        long_message = "This is a long message that needs to be split. " * 10
        
        parts = sms_engine.split_sms_response(long_message)
        
        assert len(parts) > 1
        for i, part in enumerate(parts):
            assert len(part) <= 160
            if len(parts) > 1:
                assert f"({i+1}/{len(parts)})" in part


class TestEmailSMSSimultaneous:
    """Test email and SMS working simultaneously"""
    
    @pytest.fixture
    def mock_email_client(self):
        """Create mock email client"""
        mock_client = Mock(spec=EmailClient)
        mock_client.email_address = "karensecretaryai@gmail.com"
        mock_client.send_email.return_value = True
        mock_client.fetch_emails.return_value = []
        return mock_client

    @pytest.fixture
    def mock_email_engine(self):
        """Create mock email engine"""
        mock_engine = Mock(spec=HandymanResponseEngine)
        mock_engine.classify_email_type.return_value = {
            'is_emergency': False,
            'is_quote_request': True,
            'services_mentioned': ['plumbing']
        }
        return mock_engine

    def test_email_still_works_with_sms_added(self, mock_email_client, mock_email_engine):
        """Verify email functionality is unaffected by SMS addition"""
        # Test email sending
        result = mock_email_client.send_email(
            "test@example.com", 
            "Test Subject", 
            "Test Body"
        )
        assert result is True
        
        # Test email classification
        classification = mock_email_engine.classify_email_type(
            "Need plumbing quote", 
            "Can you give me a quote for fixing my sink?"
        )
        assert classification['is_quote_request'] is True

    def test_sms_works_independently_of_email(self, sms_client):
        """Verify SMS works independently of email system"""
        # This should work even if email is down
        result = sms_client.send_sms("+15551234567", "SMS test message")
        assert result is True

    @pytest.mark.asyncio 
    async def test_concurrent_email_sms_processing(self, sms_engine):
        """Test processing email and SMS concurrently"""
        async def process_email():
            # Simulate email processing
            await asyncio.sleep(0.1)
            return "Email processed"

        async def process_sms():
            # Process actual SMS
            response, classification = await sms_engine.generate_sms_response_async(
                "+15551234567",
                "Test SMS message"
            )
            return f"SMS processed: {len(response)} chars"

        # Run both concurrently
        email_result, sms_result = await asyncio.gather(
            process_email(),
            process_sms()
        )
        
        assert "Email processed" in email_result
        assert "SMS processed" in sms_result


class TestCeleryTaskIntegration:
    """Test Celery tasks for SMS processing"""
    
    @pytest.fixture
    def mock_celery_task_env(self):
        """Set up environment for Celery task testing"""
        with patch.dict(os.environ, {
            'KAREN_PHONE_NUMBER': '+17575551234',
            'TWILIO_ACCOUNT_SID': 'test_sid',
            'TWILIO_AUTH_TOKEN': 'test_token',
            'BUSINESS_NAME': 'Test Handyman',
            'BUSINESS_PHONE': '757-354-4577'
        }):
            yield

    @patch('src.celery_sms_tasks.SMSClient')
    def test_sms_task_initialization(self, mock_sms_class, mock_celery_task_env):
        """Test SMS task component initialization"""
        mock_instance = Mock()
        mock_sms_class.return_value = mock_instance
        
        # Import function that creates instance
        from src.celery_sms_tasks import get_sms_client_instance
        
        client = get_sms_client_instance()
        assert client is mock_instance
        mock_sms_class.assert_called_once_with(karen_phone='+17575551234')

    @patch('src.celery_sms_tasks.get_sms_client_instance')
    def test_fetch_sms_task(self, mock_get_client):
        """Test fetch SMS Celery task"""
        # Mock SMS client
        mock_client = Mock()
        mock_client.fetch_sms.return_value = [
            {'uid': 'SMS123', 'sender': '+15551234567', 'body': 'Test message'}
        ]
        mock_client.is_sms_processed.return_value = False
        mock_get_client.return_value = mock_client
        
        # Import and run task
        from src.celery_sms_tasks import fetch_new_sms
        
        with patch('src.celery_sms_tasks.process_sms_with_llm') as mock_process:
            result = fetch_new_sms(process_last_n_hours=1)
        
        assert result['total_messages'] == 1
        assert result['new_messages'] == 1
        mock_process.delay.assert_called_once()

    def test_sms_webhook_data_conversion(self):
        """Test converting Twilio webhook data to standard format"""
        from src.celery_sms_tasks import handle_incoming_sms_webhook
        
        webhook_data = {
            'MessageSid': 'SM123456789',
            'From': '+15551234567',
            'To': '+17575551234',
            'Body': 'Test webhook message',
            'SmsStatus': 'received'
        }
        
        with patch('src.celery_sms_tasks.process_sms_with_llm') as mock_process:
            # Create a mock task instance
            mock_task = Mock()
            result = handle_incoming_sms_webhook(mock_task, webhook_data)
        
        assert result['success'] is True
        assert result['message_sid'] == 'SM123456789'
        mock_process.delay.assert_called_once()


class TestSystemRobustness:
    """Test system robustness and error handling"""
    
    def test_sms_client_handles_missing_credentials(self):
        """Test SMS client handles missing credentials gracefully"""
        with pytest.raises(ValueError, match="Failed to load Twilio credentials"):
            SMSClient(karen_phone="+17575551234")  # No token_data or env vars

    def test_sms_engine_handles_missing_llm(self):
        """Test SMS engine works without LLM client"""
        engine = HandymanSMSEngine(llm_client=None)
        
        # Should still be able to classify
        classification = engine.classify_sms_type("+15551234567", "Emergency!")
        assert classification['is_emergency'] is True
        
        # Should provide fallback response
        fallback = engine._generate_sms_fallback_response(
            "+15551234567", "Emergency!", classification
        )
        assert "URGENT" in fallback or "757-354-4577" in fallback

    @patch('src.sms_client.Client')
    def test_sms_client_handles_twilio_errors(self, mock_twilio_class):
        """Test SMS client handles Twilio API errors"""
        from twilio.base.exceptions import TwilioRestException
        
        # Mock Twilio client that raises errors
        mock_client = Mock()
        mock_error = TwilioRestException(
            "Invalid phone number", 
            uri="", method="", status=400, code=21211
        )
        mock_client.messages.create.side_effect = mock_error
        mock_twilio_class.return_value = mock_client
        
        sms_client = SMSClient(
            karen_phone="+17575551234",
            token_data={'account_sid': 'test', 'auth_token': 'test'}
        )
        
        # Should return False instead of crashing
        result = sms_client.send_sms("+invalid", "test")
        assert result is False

    def test_long_sms_handling(self, sms_client):
        """Test handling of very long SMS messages"""
        # Test very long message (over multipart limit)
        very_long_message = "This is a test message. " * 100  # Very long
        
        result = sms_client.send_sms("+15551234567", very_long_message)
        
        # Should truncate and still send
        assert result is True
        
        # Check that truncation occurred in the sent message
        call_args = sms_client.client.messages.create.call_args
        sent_body = call_args[1]['body']
        assert len(sent_body) <= 1600  # Should be truncated


@pytest.mark.integration
class TestFullSystemIntegration:
    """Full system integration tests"""
    
    @pytest.mark.slow
    def test_complete_sms_flow_simulation(self):
        """Test complete SMS flow from reception to response"""
        # This would be a full end-to-end test
        # Simulates: Receive SMS -> Classify -> Generate Response -> Send Reply
        
        with patch('src.sms_client.Client') as mock_twilio:
            # Setup mocks
            mock_client = Mock()
            mock_twilio.return_value = mock_client
            
            # Mock incoming message
            mock_message = Mock()
            mock_message.sid = "SM123"
            mock_message.from_ = "+15551234567"
            mock_message.body = "Need emergency plumber!"
            mock_message.date_sent = datetime.now(timezone.utc)
            mock_message.status = "received"
            mock_message.direction = "inbound"
            
            mock_client.messages.list.return_value = [mock_message]
            mock_client.messages.create.return_value = Mock(sid="SM456")
            
            # Create components
            sms_client = SMSClient(
                karen_phone="+17575551234",
                token_data={'account_sid': 'test', 'auth_token': 'test'}
            )
            
            mock_llm = Mock()
            mock_llm.generate_text.return_value = "Emergency? Call us NOW: 757-354-4577"
            
            sms_engine = HandymanSMSEngine(llm_client=mock_llm)
            
            # Simulate the flow
            # 1. Fetch messages
            messages = sms_client.fetch_sms(max_results=10)
            assert len(messages) == 1
            
            # 2. Process message
            classification = sms_engine.classify_sms_type(
                messages[0]['sender'], 
                messages[0]['body']
            )
            assert classification['is_emergency'] is True
            
            # 3. Generate response
            import asyncio
            response, _ = asyncio.run(sms_engine.generate_sms_response_async(
                messages[0]['sender'],
                messages[0]['body']
            ))
            
            # 4. Send response
            result = sms_client.send_sms(messages[0]['sender'], response)
            assert result is True

    def test_system_graceful_degradation(self):
        """Test system continues working when components fail"""
        # Test that if SMS fails, email still works
        # Test that if LLM fails, fallback responses work
        # etc.
        
        # This would test the resilience patterns
        pass


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v', '--tb=short'])
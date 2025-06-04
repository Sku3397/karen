"""
Unit tests specifically for SMSClient
"""
import pytest
import os
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta

from src.sms_client import SMSClient


class TestSMSClientUnit:
    """Unit tests for SMSClient class"""

    @pytest.fixture
    def mock_twilio_client(self):
        """Create mock Twilio client"""
        mock_client = MagicMock()
        
        # Mock successful message creation
        mock_msg = MagicMock()
        mock_msg.sid = "SM123456789"
        mock_msg.status = "sent"
        mock_client.messages.create.return_value = mock_msg
        
        # Mock message listing
        mock_incoming = MagicMock()
        mock_incoming.sid = "SM987654321"
        mock_incoming.from_ = "+15551234567"
        mock_incoming.to = "+17575551234"
        mock_incoming.body = "Test incoming message"
        mock_incoming.date_sent = datetime.now(timezone.utc)
        mock_incoming.status = "received"
        mock_incoming.direction = "inbound"
        
        mock_client.messages.list.return_value = [mock_incoming]
        
        return mock_client

    @pytest.fixture
    def sms_client(self, mock_twilio_client):
        """Create SMS client with mocked dependencies"""
        with patch('src.sms_client.Client', return_value=mock_twilio_client):
            return SMSClient(
                karen_phone="+17575551234",
                token_data={
                    'account_sid': 'AC123test',
                    'auth_token': 'test_token_123'
                }
            )

    def test_initialization_with_token_data(self, sms_client):
        """Test initialization with provided token data"""
        assert sms_client.karen_phone == "+17575551234"
        assert sms_client.account_sid == "AC123test"
        assert sms_client.auth_token == "test_token_123"

    def test_initialization_from_environment(self):
        """Test initialization from environment variables"""
        with patch.dict(os.environ, {
            'TWILIO_ACCOUNT_SID': 'AC456env',
            'TWILIO_AUTH_TOKEN': 'env_token_456'
        }):
            with patch('src.sms_client.Client') as mock_client_class:
                client = SMSClient(karen_phone="+17575555678")
                assert client.account_sid == "AC456env"
                assert client.auth_token == "env_token_456"

    def test_initialization_missing_credentials(self):
        """Test that missing credentials raise ValueError"""
        with pytest.raises(ValueError, match="Failed to load Twilio credentials"):
            SMSClient(karen_phone="+17575551234")

    def test_send_sms_success(self, sms_client):
        """Test successful SMS sending"""
        result = sms_client.send_sms("+15551234567", "Hello, this is a test!")
        
        assert result is True
        sms_client.client.messages.create.assert_called_once_with(
            body="Hello, this is a test!",
            from_="+17575551234",
            to="+15551234567"
        )

    def test_send_sms_truncation(self, sms_client):
        """Test SMS truncation for long messages"""
        long_message = "A" * 2000  # Longer than SMS limit
        
        result = sms_client.send_sms("+15551234567", long_message)
        
        assert result is True
        call_args = sms_client.client.messages.create.call_args
        sent_body = call_args[1]['body']
        assert len(sent_body) <= 1600
        assert sent_body.endswith("...")

    def test_send_sms_twilio_error(self, sms_client):
        """Test handling of Twilio errors during send"""
        from twilio.base.exceptions import TwilioRestException
        
        error = TwilioRestException("Test error", uri="", method="", status=400, code=21211)
        sms_client.client.messages.create.side_effect = error
        
        result = sms_client.send_sms("+15551234567", "Test message")
        
        assert result is False

    def test_fetch_sms_basic(self, sms_client):
        """Test basic SMS fetching"""
        messages = sms_client.fetch_sms(max_results=10)
        
        assert isinstance(messages, list)
        assert len(messages) == 1
        
        msg = messages[0]
        assert msg['id'] == "SM987654321"
        assert msg['sender'] == "+15551234567"
        assert msg['body'] == "Test incoming message"
        assert 'date_str' in msg
        assert 'received_date_dt' in msg

    def test_fetch_sms_with_date_filter(self, sms_client):
        """Test SMS fetching with date filters"""
        # Test newer_than filter
        messages = sms_client.fetch_sms(newer_than="2h", max_results=5)
        
        # Should call Twilio with date filter
        call_args = sms_client.client.messages.list.call_args[1]
        assert 'date_sent_after' in call_args
        assert call_args['limit'] == 5

    def test_fetch_sms_last_n_days(self, sms_client):
        """Test SMS fetching with last_n_days filter"""
        messages = sms_client.fetch_sms(last_n_days=3, max_results=20)
        
        call_args = sms_client.client.messages.list.call_args[1]
        assert 'date_sent_after' in call_args
        assert call_args['limit'] == 20

    def test_fetch_sms_inbound_only(self, sms_client):
        """Test that only inbound messages are returned"""
        # Mock both inbound and outbound messages
        mock_inbound = MagicMock()
        mock_inbound.direction = "inbound"
        mock_inbound.sid = "SM_IN_123"
        mock_inbound.from_ = "+15551111111"
        mock_inbound.body = "Inbound message"
        
        mock_outbound = MagicMock()
        mock_outbound.direction = "outbound-api"
        mock_outbound.sid = "SM_OUT_456"
        mock_outbound.to = "+15552222222"
        mock_outbound.body = "Outbound message"
        
        sms_client.client.messages.list.return_value = [mock_inbound, mock_outbound]
        
        messages = sms_client.fetch_sms()
        
        # Should only return inbound message
        assert len(messages) == 1
        assert messages[0]['id'] == "SM_IN_123"

    def test_mark_sms_as_processed(self, sms_client):
        """Test marking SMS as processed"""
        with patch('os.path.exists', return_value=False):
            with patch('builtins.open', create=True) as mock_open:
                with patch('json.dump') as mock_json_dump:
                    result = sms_client.mark_sms_as_processed("SM123456")
                    
                    assert result is True
                    mock_json_dump.assert_called_once()

    def test_is_sms_processed(self, sms_client):
        """Test checking if SMS is processed"""
        processed_ids = ["SM123", "SM456"]
        
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', create=True):
                with patch('json.load', return_value=processed_ids):
                    assert sms_client.is_sms_processed("SM123") is True
                    assert sms_client.is_sms_processed("SM789") is False

    def test_send_self_test_sms(self, sms_client):
        """Test self-test SMS functionality"""
        result = sms_client.send_self_test_sms("Test Prefix")
        
        assert result is True
        
        call_args = sms_client.client.messages.create.call_args
        assert call_args[1]['to'] == "+17575551234"  # Sent to self
        assert call_args[1]['from_'] == "+17575551234"
        assert "Test Prefix" in call_args[1]['body']
        assert "Verifying SMS capability" in call_args[1]['body']

    def test_send_designated_test_sms(self, sms_client):
        """Test designated test SMS functionality"""
        result = sms_client.send_designated_test_sms("+15559876543", "Custom Test")
        
        assert result is True
        
        call_args = sms_client.client.messages.create.call_args
        assert call_args[1]['to'] == "+15559876543"
        assert call_args[1]['from_'] == "+17575551234"
        assert "Custom Test" in call_args[1]['body']
        assert "external recipient" in call_args[1]['body']

    def test_fetch_last_n_sent_sms(self, sms_client):
        """Test fetching last sent SMS messages"""
        # Mock sent message
        mock_sent = MagicMock()
        mock_sent.sid = "SM_SENT_123"
        mock_sent.to = "+15551234567"
        mock_sent.body = "Sent message body"
        mock_sent.date_sent = datetime.now(timezone.utc)
        mock_sent.status = "delivered"
        mock_sent.direction = "outbound-api"
        
        sms_client.client.messages.list.return_value = [mock_sent]
        
        sent_messages = sms_client.fetch_last_n_sent_sms(n=5)
        
        assert len(sent_messages) == 1
        assert sent_messages[0]['id'] == "SM_SENT_123"
        assert sent_messages[0]['recipient'] == "+15551234567"
        assert sent_messages[0]['body_text'] == "Sent message body"
        
        # Verify correct call to Twilio
        call_args = sms_client.client.messages.list.call_args[1]
        assert call_args['from_'] == "+17575551234"
        assert call_args['limit'] == 5

    def test_fetch_last_n_sent_sms_metadata_only(self, sms_client):
        """Test fetching sent SMS metadata only"""
        mock_sent = MagicMock()
        mock_sent.sid = "SM_SENT_456"
        mock_sent.to = "+15551234567"
        mock_sent.body = "Message body"
        mock_sent.date_sent = datetime.now(timezone.utc)
        
        sms_client.client.messages.list.return_value = [mock_sent]
        
        sent_messages = sms_client.fetch_last_n_sent_sms(n=1, metadata_only=True)
        
        assert len(sent_messages) == 1
        assert sent_messages[0]['body_text'] is None  # Should be None for metadata only

    def test_fetch_last_n_sent_sms_with_recipient_filter(self, sms_client):
        """Test fetching sent SMS with recipient filter"""
        sms_client.fetch_last_n_sent_sms(n=3, recipient_filter="+15555555555")
        
        call_args = sms_client.client.messages.list.call_args[1]
        assert call_args['to'] == "+15555555555"
        assert call_args['from_'] == "+17575551234"
        assert call_args['limit'] == 3


class TestSMSClientErrorHandling:
    """Test error handling in SMS client"""

    def test_client_initialization_error(self):
        """Test error during Twilio client initialization"""
        with patch('src.sms_client.Client', side_effect=Exception("Auth failed")):
            with pytest.raises(Exception, match="Auth failed"):
                SMSClient(
                    karen_phone="+17575551234",
                    token_data={'account_sid': 'test', 'auth_token': 'test'}
                )

    def test_send_sms_unexpected_error(self, mock_twilio_client):
        """Test handling of unexpected errors during send"""
        mock_twilio_client.messages.create.side_effect = Exception("Unexpected error")
        
        with patch('src.sms_client.Client', return_value=mock_twilio_client):
            client = SMSClient(
                karen_phone="+17575551234",
                token_data={'account_sid': 'test', 'auth_token': 'test'}
            )
            
            result = client.send_sms("+15551234567", "Test")
            assert result is False

    def test_fetch_sms_twilio_error(self, mock_twilio_client):
        """Test handling of Twilio errors during fetch"""
        from twilio.base.exceptions import TwilioRestException
        
        error = TwilioRestException("Fetch error", uri="", method="", status=500, code=20001)
        mock_twilio_client.messages.list.side_effect = error
        
        with patch('src.sms_client.Client', return_value=mock_twilio_client):
            client = SMSClient(
                karen_phone="+17575551234",
                token_data={'account_sid': 'test', 'auth_token': 'test'}
            )
            
            messages = client.fetch_sms()
            assert messages == []

    def test_fetch_sms_unexpected_error(self, mock_twilio_client):
        """Test handling of unexpected errors during fetch"""
        mock_twilio_client.messages.list.side_effect = Exception("Unexpected fetch error")
        
        with patch('src.sms_client.Client', return_value=mock_twilio_client):
            client = SMSClient(
                karen_phone="+17575551234",
                token_data={'account_sid': 'test', 'auth_token': 'test'}
            )
            
            messages = client.fetch_sms()
            assert messages == []

    def test_mark_processed_file_error(self, mock_twilio_client):
        """Test error handling when writing processed file fails"""
        with patch('src.sms_client.Client', return_value=mock_twilio_client):
            client = SMSClient(
                karen_phone="+17575551234",
                token_data={'account_sid': 'test', 'auth_token': 'test'}
            )
            
            with patch('builtins.open', side_effect=IOError("File write error")):
                result = client.mark_sms_as_processed("SM123")
                assert result is False

    def test_is_processed_file_error(self, mock_twilio_client):
        """Test error handling when reading processed file fails"""
        with patch('src.sms_client.Client', return_value=mock_twilio_client):
            client = SMSClient(
                karen_phone="+17575551234",
                token_data={'account_sid': 'test', 'auth_token': 'test'}
            )
            
            with patch('builtins.open', side_effect=IOError("File read error")):
                result = client.is_sms_processed("SM123")
                assert result is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
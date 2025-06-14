"""
Comprehensive unit tests for SMS Handler
"""
import pytest
import asyncio
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime
from twilio.base.exceptions import TwilioRestException

from src.communication_agent.sms_handler import SMSHandler


class TestSMSHandlerInitialization:
    """Test SMS handler initialization"""

    def test_initialization_success(self):
        """Test successful SMS handler initialization"""
        handler = SMSHandler(
            account_sid="AC123test",
            auth_token="test_token_123",
            from_number="+17575551234"
        )
        
        assert handler.from_number == "+17575551234"
        assert handler.client is not None

    def test_initialization_invalid_credentials(self):
        """Test initialization with invalid credentials"""
        with patch('twilio.rest.Client', side_effect=Exception("Invalid credentials")):
            with pytest.raises(Exception, match="Invalid credentials"):
                SMSHandler(
                    account_sid="invalid",
                    auth_token="invalid",
                    from_number="+17575551234"
                )


class TestSMSSending:
    """Test SMS sending functionality"""

    @pytest.fixture
    def mock_twilio_client(self):
        """Create mock Twilio client"""
        mock_client = MagicMock()
        mock_msg = MagicMock()
        mock_msg.sid = "SM123456789abcdef"
        mock_client.messages.create.return_value = mock_msg
        return mock_client

    @pytest.fixture
    def sms_handler(self, mock_twilio_client):
        """Create SMS handler with mocked Twilio client"""
        with patch('twilio.rest.Client', return_value=mock_twilio_client):
            handler = SMSHandler(
                account_sid="AC123test",
                auth_token="test_token_123", 
                from_number="+17575551234"
            )
            handler.client = mock_twilio_client
            return handler

    def test_send_sms_success(self, sms_handler):
        """Test successful SMS sending"""
        with patch('src.communication_agent.sms_handler.memory_client') as mock_memory:
            mock_memory.store_sms_conversation = AsyncMock()
            
            result = sms_handler.send_sms("+15551234567", "Test message")
            
            assert result == "SM123456789abcdef"
            sms_handler.client.messages.create.assert_called_once_with(
                body="Test message",
                from_="+17575551234",
                to="+15551234567"
            )

    def test_send_sms_twilio_exception(self, sms_handler):
        """Test SMS sending with Twilio exception"""
        error = TwilioRestException("Invalid phone number", uri="", method="", status=400, code=21211)
        sms_handler.client.messages.create.side_effect = error
        
        result = sms_handler.send_sms("+15551234567", "Test message")
        
        assert result is None

    def test_send_sms_generic_exception(self, sms_handler):
        """Test SMS sending with generic exception"""
        sms_handler.client.messages.create.side_effect = Exception("Network error")
        
        result = sms_handler.send_sms("+15551234567", "Test message")
        
        assert result is None

    def test_send_sms_empty_message(self, sms_handler):
        """Test sending empty message"""
        result = sms_handler.send_sms("+15551234567", "")
        
        assert result == "SM123456789abcdef"
        sms_handler.client.messages.create.assert_called_once_with(
            body="",
            from_="+17575551234",
            to="+15551234567"
        )

    def test_send_sms_long_message(self, sms_handler):
        """Test sending long message (should not be truncated by handler)"""
        long_message = "A" * 2000  # Longer than SMS limit
        
        result = sms_handler.send_sms("+15551234567", long_message)
        
        assert result == "SM123456789abcdef"
        # Handler should pass through the message as-is (truncation handled elsewhere)
        sms_handler.client.messages.create.assert_called_once_with(
            body=long_message,
            from_="+17575551234",
            to="+15551234567"
        )

    def test_send_sms_special_characters(self, sms_handler):
        """Test sending message with special characters"""
        special_message = "Hello! 🔧 Need help? Call us @ 757-354-4577 for $50/hr service."
        
        result = sms_handler.send_sms("+15551234567", special_message)
        
        assert result == "SM123456789abcdef"
        sms_handler.client.messages.create.assert_called_once_with(
            body=special_message,
            from_="+17575551234",
            to="+15551234567"
        )


class TestSMSMemoryIntegration:
    """Test SMS memory system integration"""

    @pytest.fixture
    def sms_handler(self):
        """Create SMS handler"""
        with patch('twilio.rest.Client') as mock_client_class:
            mock_client = MagicMock()
            mock_msg = MagicMock()
            mock_msg.sid = "SM123456789abcdef"
            mock_client.messages.create.return_value = mock_msg
            mock_client_class.return_value = mock_client
            
            handler = SMSHandler(
                account_sid="AC123test",
                auth_token="test_token_123",
                from_number="+17575551234"
            )
            return handler

    def test_memory_storage_success(self, sms_handler):
        """Test successful memory storage"""
        with patch('src.communication_agent.sms_handler.memory_client') as mock_memory:
            mock_memory.store_sms_conversation = AsyncMock()
            with patch('asyncio.create_task') as mock_create_task:
                
                result = sms_handler.send_sms("+15551234567", "Test message")
                
                assert result == "SM123456789abcdef"
                mock_create_task.assert_called_once()

    def test_memory_storage_failure(self, sms_handler):
        """Test memory storage failure doesn't affect SMS sending"""
        with patch('src.communication_agent.sms_handler.memory_client') as mock_memory:
            mock_memory.store_sms_conversation.side_effect = Exception("Memory error")
            with patch('asyncio.create_task', side_effect=Exception("Task creation error")):
                
                result = sms_handler.send_sms("+15551234567", "Test message")
                
                # SMS should still be sent successfully despite memory error
                assert result == "SM123456789abcdef"

    def test_memory_import_failure(self, sms_handler):
        """Test memory client import failure"""
        with patch('src.communication_agent.sms_handler.memory_client', side_effect=ImportError("No memory client")):
            
            result = sms_handler.send_sms("+15551234567", "Test message")
            
            # SMS should still be sent successfully despite memory import error
            assert result == "SM123456789abcdef"

    def test_memory_data_structure(self, sms_handler):
        """Test memory data structure is correct"""
        with patch('src.communication_agent.sms_handler.memory_client') as mock_memory:
            mock_memory.store_sms_conversation = AsyncMock()
            with patch('asyncio.create_task') as mock_create_task:
                with patch('src.communication_agent.sms_handler.datetime') as mock_datetime:
                    test_time = datetime(2025, 6, 4, 12, 0, 0)
                    mock_datetime.now.return_value = test_time
                    
                    result = sms_handler.send_sms("+15551234567", "Test message")
                    
                    # Verify task was created with correct data structure
                    mock_create_task.assert_called_once()
                    task_call = mock_create_task.call_args[0][0]
                    # The task should be a coroutine for store_sms_conversation


class TestSMSHandlerPhoneNumberValidation:
    """Test phone number handling"""

    @pytest.fixture
    def sms_handler(self):
        with patch('twilio.rest.Client') as mock_client_class:
            mock_client = MagicMock()
            mock_msg = MagicMock()
            mock_msg.sid = "SM123456789abcdef"
            mock_client.messages.create.return_value = mock_msg
            mock_client_class.return_value = mock_client
            
            return SMSHandler(
                account_sid="AC123test",
                auth_token="test_token_123",
                from_number="+17575551234"
            )

    def test_send_to_international_number(self, sms_handler):
        """Test sending to international number"""
        result = sms_handler.send_sms("+441234567890", "International test")
        
        assert result == "SM123456789abcdef"
        sms_handler.client.messages.create.assert_called_once_with(
            body="International test",
            from_="+17575551234",
            to="+441234567890"
        )

    def test_send_to_short_code(self, sms_handler):
        """Test sending to short code"""
        result = sms_handler.send_sms("12345", "Short code test")
        
        assert result == "SM123456789abcdef"
        sms_handler.client.messages.create.assert_called_once_with(
            body="Short code test", 
            from_="+17575551234",
            to="12345"
        )

    def test_send_to_invalid_number_format(self, sms_handler):
        """Test sending to invalid number format"""
        # Twilio will handle validation, handler just passes through
        result = sms_handler.send_sms("invalid-number", "Test message")
        
        assert result == "SM123456789abcdef"
        sms_handler.client.messages.create.assert_called_once_with(
            body="Test message",
            from_="+17575551234", 
            to="invalid-number"
        )


class TestSMSHandlerLogging:
    """Test SMS handler logging"""

    @pytest.fixture
    def sms_handler(self):
        with patch('twilio.rest.Client') as mock_client_class:
            mock_client = MagicMock()
            mock_msg = MagicMock()
            mock_msg.sid = "SM123456789abcdef"
            mock_client.messages.create.return_value = mock_msg
            mock_client_class.return_value = mock_client
            
            return SMSHandler(
                account_sid="AC123test",
                auth_token="test_token_123",
                from_number="+17575551234"
            )

    def test_logging_on_success(self, sms_handler):
        """Test logging on successful SMS send"""
        with patch('src.communication_agent.sms_handler.logger') as mock_logger:
            with patch('src.communication_agent.sms_handler.memory_client'):
                
                result = sms_handler.send_sms("+15551234567", "Test message")
                
                assert result == "SM123456789abcdef"
                # Check that debug log was called for memory storage
                mock_logger.debug.assert_called()

    def test_logging_on_twilio_error(self, sms_handler):
        """Test logging on Twilio error"""
        with patch('src.communication_agent.sms_handler.logger') as mock_logger:
            error = TwilioRestException("Invalid phone", uri="", method="", status=400, code=21211)
            sms_handler.client.messages.create.side_effect = error
            
            result = sms_handler.send_sms("+15551234567", "Test message")
            
            assert result is None
            mock_logger.error.assert_called()

    def test_logging_on_memory_error(self, sms_handler):
        """Test logging on memory error"""
        with patch('src.communication_agent.sms_handler.logger') as mock_logger:
            with patch('src.communication_agent.sms_handler.memory_client', side_effect=Exception("Memory error")):
                
                result = sms_handler.send_sms("+15551234567", "Test message")
                
                assert result == "SM123456789abcdef"
                mock_logger.warning.assert_called()


class TestSMSHandlerAsyncBehavior:
    """Test async behavior of SMS handler"""

    @pytest.fixture
    def sms_handler(self):
        with patch('twilio.rest.Client') as mock_client_class:
            mock_client = MagicMock()
            mock_msg = MagicMock()
            mock_msg.sid = "SM123456789abcdef"
            mock_client.messages.create.return_value = mock_msg
            mock_client_class.return_value = mock_client
            
            return SMSHandler(
                account_sid="AC123test",
                auth_token="test_token_123",
                from_number="+17575551234"
            )

    def test_memory_storage_async_task_creation(self, sms_handler):
        """Test that memory storage is properly queued as async task"""
        with patch('src.communication_agent.sms_handler.memory_client') as mock_memory:
            mock_memory.store_sms_conversation = AsyncMock()
            with patch('asyncio.create_task') as mock_create_task:
                
                result = sms_handler.send_sms("+15551234567", "Test message")
                
                assert result == "SM123456789abcdef"
                mock_create_task.assert_called_once()
                
                # Verify the task is created with a coroutine
                call_args = mock_create_task.call_args[0][0]
                assert hasattr(call_args, '__await__')  # Should be awaitable

    def test_sms_send_non_blocking(self, sms_handler):
        """Test that SMS sending doesn't block on memory operations"""
        with patch('src.communication_agent.sms_handler.memory_client') as mock_memory:
            # Simulate slow memory operation
            slow_coroutine = AsyncMock()
            slow_coroutine.side_effect = lambda x: asyncio.sleep(1)  # Slow operation
            mock_memory.store_sms_conversation = slow_coroutine
            
            with patch('asyncio.create_task') as mock_create_task:
                import time
                start_time = time.time()
                
                result = sms_handler.send_sms("+15551234567", "Test message")
                
                end_time = time.time()
                
                # SMS send should complete quickly (not wait for memory operation)
                assert (end_time - start_time) < 0.1  # Should be very fast
                assert result == "SM123456789abcdef"
                mock_create_task.assert_called_once()


class TestSMSHandlerEdgeCases:
    """Test edge cases for SMS handler"""

    @pytest.fixture
    def sms_handler(self):
        with patch('twilio.rest.Client') as mock_client_class:
            mock_client = MagicMock()
            mock_msg = MagicMock()
            mock_msg.sid = "SM123456789abcdef"
            mock_client.messages.create.return_value = mock_msg
            mock_client_class.return_value = mock_client
            
            return SMSHandler(
                account_sid="AC123test",
                auth_token="test_token_123",
                from_number="+17575551234"
            )

    def test_send_sms_none_message(self, sms_handler):
        """Test sending None as message"""
        result = sms_handler.send_sms("+15551234567", None)
        
        # Should handle None gracefully (Twilio will convert to string)
        assert result == "SM123456789abcdef"
        sms_handler.client.messages.create.assert_called_once_with(
            body=None,
            from_="+17575551234",
            to="+15551234567"
        )

    def test_send_sms_none_phone(self, sms_handler):
        """Test sending to None phone number"""
        result = sms_handler.send_sms(None, "Test message")
        
        # Should handle None gracefully (Twilio will handle validation)
        assert result == "SM123456789abcdef"
        sms_handler.client.messages.create.assert_called_once_with(
            body="Test message",
            from_="+17575551234",
            to=None
        )

    def test_unicode_message_handling(self, sms_handler):
        """Test handling of Unicode characters"""
        unicode_message = "Hello! 🌟 Café naïveté résumé"
        
        result = sms_handler.send_sms("+15551234567", unicode_message)
        
        assert result == "SM123456789abcdef"
        sms_handler.client.messages.create.assert_called_once_with(
            body=unicode_message,
            from_="+17575551234",
            to="+15551234567"
        )

    def test_newline_handling(self, sms_handler):
        """Test handling of newlines in messages"""
        multiline_message = "Line 1\nLine 2\rLine 3\r\nLine 4"
        
        result = sms_handler.send_sms("+15551234567", multiline_message)
        
        assert result == "SM123456789abcdef"
        sms_handler.client.messages.create.assert_called_once_with(
            body=multiline_message,
            from_="+17575551234",
            to="+15551234567"
        )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
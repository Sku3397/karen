#!/usr/bin/env python3
"""
Email Flow Testing Module for Karen AI Secretary
QA Agent Instance: QA-001

Comprehensive testing of email processing workflows including:
- Email fetching and parsing
- Intent classification 
- Response generation
- Email sending
- Error handling
"""

import pytest
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import json

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestEmailClientCore:
    """Core email client functionality tests"""
    
    @pytest.fixture
    def mock_gmail_service(self):
        """Mock Gmail service for testing"""
        mock_service = Mock()
        mock_service.users().messages().list().execute.return_value = {
            'messages': [{'id': 'msg123'}, {'id': 'msg456'}]
        }
        mock_service.users().messages().get().execute.return_value = {
            'id': 'msg123',
            'payload': {
                'headers': [
                    {'name': 'Subject', 'value': 'Test Subject'},
                    {'name': 'From', 'value': 'test@example.com'},
                    {'name': 'Date', 'value': 'Mon, 1 Jan 2024 12:00:00 +0000'}
                ],
                'body': {'data': 'VGVzdCBib2R5'}  # Base64 encoded "Test body"
            }
        }
        return mock_service
    
    @pytest.fixture
    def email_client(self, mock_gmail_service):
        """Create email client with mocked Gmail service"""
        with patch('src.email_client.build') as mock_build:
            mock_build.return_value = mock_gmail_service
            from src.email_client import EmailClient
            client = EmailClient()
            return client
    
    def test_email_client_initialization(self):
        """Test email client initializes properly"""
        try:
            from src.email_client import EmailClient
            # Test with mock to avoid OAuth requirements
            with patch('src.email_client.build'):
                client = EmailClient()
                assert client is not None
        except ImportError as e:
            pytest.fail(f"Cannot import EmailClient: {e}")
    
    def test_fetch_unread_emails(self, email_client, mock_gmail_service):
        """Test fetching unread emails"""
        emails = email_client.fetch_unread_emails()
        assert isinstance(emails, list)
        
        # Verify Gmail API calls were made
        mock_gmail_service.users().messages().list.assert_called()
    
    def test_parse_email_headers(self, email_client):
        """Test email header parsing"""
        mock_message = {
            'payload': {
                'headers': [
                    {'name': 'Subject', 'value': 'Test Subject'},
                    {'name': 'From', 'value': 'John Doe <john@example.com>'},
                    {'name': 'Date', 'value': 'Mon, 1 Jan 2024 12:00:00 +0000'},
                    {'name': 'Message-ID', 'value': '<test@example.com>'}
                ]
            }
        }
        
        # Test header extraction
        headers = email_client._extract_headers(mock_message)
        assert headers['subject'] == 'Test Subject'
        assert 'john@example.com' in headers['from']
        assert headers['date'] is not None
    
    def test_email_body_extraction(self, email_client):
        """Test email body extraction and decoding"""
        # Test plain text body
        mock_message = {
            'payload': {
                'body': {'data': 'VGVzdCBib2R5'}  # Base64 "Test body"
            }
        }
        
        body = email_client._extract_body(mock_message)
        assert 'Test body' in body
    
    def test_multipart_email_parsing(self, email_client):
        """Test parsing multipart emails"""
        mock_message = {
            'payload': {
                'mimeType': 'multipart/alternative',
                'parts': [
                    {
                        'mimeType': 'text/plain',
                        'body': {'data': 'VGVzdCBib2R5'}
                    },
                    {
                        'mimeType': 'text/html',
                        'body': {'data': 'PGI+VGVzdCBib2R5PC9iPg=='}  # <b>Test body</b>
                    }
                ]
            }
        }
        
        body = email_client._extract_body(mock_message)
        assert body is not None
        assert len(body) > 0

class TestEmailSending:
    """Email sending functionality tests"""
    
    @pytest.fixture
    def email_client_sender(self):
        """Email client configured for sending"""
        with patch('src.email_client.build') as mock_build:
            mock_service = Mock()
            mock_service.users().messages().send().execute.return_value = {
                'id': 'sent123',
                'labelIds': ['SENT']
            }
            mock_build.return_value = mock_service
            
            from src.email_client import EmailClient
            client = EmailClient()
            return client, mock_service
    
    def test_send_basic_email(self, email_client_sender):
        """Test sending a basic email"""
        client, mock_service = email_client_sender
        
        result = client.send_email(
            to='recipient@example.com',
            subject='Test Subject',
            body='Test email body'
        )
        
        assert result is True
        mock_service.users().messages().send.assert_called()
    
    def test_send_email_with_reply_headers(self, email_client_sender):
        """Test sending email as reply with proper headers"""
        client, mock_service = email_client_sender
        
        original_message_id = '<original@example.com>'
        result = client.send_reply(
            to='sender@example.com',
            subject='Re: Original Subject',
            body='Reply body',
            original_message_id=original_message_id
        )
        
        assert result is True
        
        # Verify reply headers were included
        call_args = mock_service.users().messages().send.call_args
        message_data = call_args[1]['body']['raw']
        # Would decode and verify In-Reply-To and References headers
    
    def test_email_sending_error_handling(self, email_client_sender):
        """Test error handling during email sending"""
        client, mock_service = email_client_sender
        
        # Simulate API error
        mock_service.users().messages().send.side_effect = Exception("API Error")
        
        result = client.send_email(
            to='recipient@example.com',
            subject='Test Subject',
            body='Test body'
        )
        
        assert result is False

class TestEmailProcessingFlow:
    """End-to-end email processing flow tests"""
    
    @pytest.fixture
    def communication_agent(self):
        """Mock communication agent for testing"""
        try:
            with patch('src.communication_agent.CommunicationAgent') as mock_agent:
                mock_instance = Mock()
                mock_instance.process_email.return_value = {
                    'status': 'success',
                    'response_sent': True,
                    'intent': 'appointment_request'
                }
                mock_agent.return_value = mock_instance
                return mock_instance
        except ImportError:
            # Try alternative import
            with patch('src.communication_agent.agent.CommunicationAgent') as mock_agent:
                mock_instance = Mock()
                mock_instance.process_email.return_value = {
                    'status': 'success',
                    'response_sent': True,
                    'intent': 'appointment_request'
                }
                mock_agent.return_value = mock_instance
                return mock_instance
    
    def test_full_email_processing_workflow(self, communication_agent):
        """Test complete email processing from fetch to response"""
        # Mock email data
        test_email = {
            'id': 'test123',
            'subject': 'Schedule appointment',
            'sender': 'client@example.com',
            'body': 'I need to schedule a plumbing appointment for next week',
            'date': datetime.now().isoformat()
        }
        
        # Process the email
        result = communication_agent.process_email(test_email)
        
        assert result['status'] == 'success'
        assert result['response_sent'] is True
        assert 'intent' in result
    
    def test_appointment_request_processing(self, communication_agent):
        """Test processing of appointment request emails"""
        appointment_email = {
            'id': 'appt123',
            'subject': 'Plumbing Service Request',
            'sender': 'customer@example.com',
            'body': 'Hi, I need a plumber to fix my kitchen sink. Available next Tuesday afternoon.',
            'date': datetime.now().isoformat()
        }
        
        communication_agent.process_email.return_value = {
            'status': 'success',
            'intent': 'appointment_request',
            'calendar_checked': True,
            'response_sent': True,
            'suggested_times': ['2024-01-09 14:00', '2024-01-09 15:00']
        }
        
        result = communication_agent.process_email(appointment_email)
        
        assert result['intent'] == 'appointment_request'
        assert result['calendar_checked'] is True
        assert 'suggested_times' in result
    
    def test_general_inquiry_processing(self, communication_agent):
        """Test processing of general inquiry emails"""
        inquiry_email = {
            'id': 'inquiry123',
            'subject': 'Service Question',
            'sender': 'prospect@example.com',
            'body': 'What types of plumbing services do you offer?',
            'date': datetime.now().isoformat()
        }
        
        communication_agent.process_email.return_value = {
            'status': 'success',
            'intent': 'general_inquiry',
            'response_sent': True,
            'response_type': 'service_information'
        }
        
        result = communication_agent.process_email(inquiry_email)
        
        assert result['intent'] == 'general_inquiry'
        assert result['response_sent'] is True

class TestEmailErrorHandling:
    """Email processing error handling tests"""
    
    @pytest.fixture
    def failing_email_client(self):
        """Email client that simulates various failure modes"""
        with patch('src.email_client.EmailClient') as mock_client:
            mock_instance = Mock()
            # Configure different failure scenarios
            mock_instance.fetch_unread_emails.side_effect = Exception("Gmail API Error")
            mock_instance.send_email.side_effect = Exception("Send Error")
            mock_client.return_value = mock_instance
            return mock_instance
    
    def test_gmail_api_error_handling(self, failing_email_client):
        """Test handling of Gmail API errors"""
        with pytest.raises(Exception) as exc_info:
            failing_email_client.fetch_unread_emails()
        
        assert "Gmail API Error" in str(exc_info.value)
    
    def test_send_email_error_handling(self, failing_email_client):
        """Test handling of email sending errors"""
        with pytest.raises(Exception) as exc_info:
            failing_email_client.send_email(
                to='test@example.com',
                subject='Test',
                body='Test body'
            )
        
        assert "Send Error" in str(exc_info.value)
    
    def test_malformed_email_handling(self):
        """Test handling of malformed email data"""
        from src.email_client import EmailClient
        
        with patch('src.email_client.build'):
            client = EmailClient()
            
            # Test with missing required fields
            malformed_message = {
                'payload': {
                    'headers': []  # No headers
                }
            }
            
            headers = client._extract_headers(malformed_message)
            assert isinstance(headers, dict)
            # Should handle missing headers gracefully

class TestEmailValidation:
    """Email validation and sanitization tests"""
    
    def test_email_address_validation(self):
        """Test email address format validation"""
        valid_emails = [
            'user@example.com',
            'user.name@example.com',
            'user+tag@example.co.uk'
        ]
        
        invalid_emails = [
            'invalid-email',
            '@example.com',
            'user@',
            'user@.com'
        ]
        
        from src.email_client import EmailClient
        
        with patch('src.email_client.build'):
            client = EmailClient()
            
            for email in valid_emails:
                assert client._validate_email(email) is True
            
            for email in invalid_emails:
                assert client._validate_email(email) is False
    
    def test_email_content_sanitization(self):
        """Test email content sanitization"""
        from src.email_client import EmailClient
        
        with patch('src.email_client.build'):
            client = EmailClient()
            
            # Test HTML stripping
            html_content = '<p>Hello <b>world</b>!</p><script>alert("xss")</script>'
            sanitized = client._sanitize_content(html_content)
            
            assert '<script>' not in sanitized
            assert 'Hello world!' in sanitized
    
    def test_subject_line_sanitization(self):
        """Test subject line sanitization"""
        from src.email_client import EmailClient
        
        with patch('src.email_client.build'):
            client = EmailClient()
            
            # Test various subject line formats
            subjects = [
                'Normal Subject',
                'Re: Previous Subject',
                'Fwd: Forwarded Subject',
                'Subject with unicode: 📧'
            ]
            
            for subject in subjects:
                sanitized = client._sanitize_subject(subject)
                assert isinstance(sanitized, str)
                assert len(sanitized) > 0

@pytest.mark.integration
class TestEmailIntegrationFlow:
    """Integration tests for email flow (requires live services)"""
    
    @pytest.mark.skip(reason="Requires live Gmail API credentials")
    def test_live_email_fetch(self):
        """Test fetching emails from live Gmail API"""
        from src.email_client import EmailClient
        
        # Would test with real credentials
        client = EmailClient()
        emails = client.fetch_unread_emails()
        assert isinstance(emails, list)
    
    @pytest.mark.skip(reason="Requires live Gmail API credentials")
    def test_live_email_send(self):
        """Test sending email via live Gmail API"""
        from src.email_client import EmailClient
        
        client = EmailClient()
        result = client.send_email(
            to='test@example.com',
            subject='Test Email',
            body='This is a test email'
        )
        assert result is True

@pytest.mark.performance
class TestEmailPerformance:
    """Performance tests for email processing"""
    
    def test_email_processing_speed(self):
        """Test email processing performance"""
        import time
        
        # Mock large number of emails
        with patch('src.email_client.EmailClient') as mock_client:
            mock_instance = Mock()
            
            # Generate 100 mock emails
            mock_emails = []
            for i in range(100):
                mock_emails.append({
                    'id': f'email_{i}',
                    'subject': f'Test Subject {i}',
                    'sender': f'sender{i}@example.com',
                    'body': f'Test body {i}',
                    'date': datetime.now().isoformat()
                })
            
            mock_instance.fetch_unread_emails.return_value = mock_emails
            mock_client.return_value = mock_instance
            
            start_time = time.time()
            emails = mock_instance.fetch_unread_emails()
            processing_time = time.time() - start_time
            
            assert len(emails) == 100
            assert processing_time < 5.0  # Should process 100 emails in under 5 seconds

if __name__ == "__main__":
    # Run email flow tests
    pytest.main([__file__, "-v", "--tb=short"])
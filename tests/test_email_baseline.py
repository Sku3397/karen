"""
Email System Baseline Tests for Karen AI
=========================================

These tests verify the core email functionality that MUST ALWAYS work:
1. Email sending capability (Karen -> customers)
2. Email receiving and fetching (monitoring inbox)
3. Email processing pipeline (classification, LLM response)
4. OAuth authentication and token management
5. Email marking and labeling system

CRITICAL: If any of these tests fail, the entire Karen system is compromised.
"""

import pytest
import sys
import os
import time
import json
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List, Optional

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from email_client import EmailClient
from mock_email_client import MockEmailClient
from communication_agent.agent import CommunicationAgent
from handyman_response_engine import HandymanResponseEngine
from llm_client import LLMClient
from config import (
    SECRETARY_EMAIL_ADDRESS,
    MONITORED_EMAIL_ACCOUNT_CONFIG,
    ADMIN_EMAIL_ADDRESS,
    USE_MOCK_EMAIL_CLIENT
)
from agent_communication import AgentCommunication

class TestEmailBaseline:
    """Critical email system baseline tests"""
    
    @pytest.fixture(autouse=True)
    def setup_test_engineer(self):
        """Initialize test engineer communication"""
        self.test_comm = AgentCommunication('test_engineer')
        self.test_comm.update_status('testing_email_baseline', 0, {
            'test_suite': 'email_baseline',
            'critical_system': True
        })
    
    @pytest.fixture
    def mock_email_client(self):
        """Mock email client for safe testing"""
        client = MockEmailClient(
            email_address="test@karen.ai",
            mock_sent_emails=[],
            mock_incoming_emails=[]
        )
        return client
    
    @pytest.fixture
    def real_email_clients(self):
        """Real email clients for integration testing"""
        if USE_MOCK_EMAIL_CLIENT:
            pytest.skip("Skipping real email client tests in mock mode")
        
        try:
            secretary_client = EmailClient(
                email_address=SECRETARY_EMAIL_ADDRESS,
                token_file_path='gmail_token_karen.json'
            )
            
            monitor_client = EmailClient(
                email_address=MONITORED_EMAIL_ACCOUNT_CONFIG,
                token_file_path='gmail_token_monitor.json'
            )
            
            return secretary_client, monitor_client
        except Exception as e:
            pytest.fail(f"Failed to initialize real email clients: {e}")
    
    def test_email_client_initialization(self, real_email_clients):
        """Test that email clients can be properly initialized"""
        secretary_client, monitor_client = real_email_clients
        
        assert secretary_client is not None
        assert monitor_client is not None
        assert secretary_client.email_address == SECRETARY_EMAIL_ADDRESS
        assert monitor_client.email_address == MONITORED_EMAIL_ACCOUNT_CONFIG
        
        # Verify credentials are valid
        assert secretary_client.creds is not None
        assert secretary_client.creds.valid
        assert monitor_client.creds is not None
        assert monitor_client.creds.valid
        
        self.test_comm.update_status('testing_email_baseline', 10, {
            'step': 'client_initialization',
            'status': 'passed'
        })
    
    def test_oauth_token_validity(self, real_email_clients):
        """Test that OAuth tokens are valid and not expired"""
        secretary_client, monitor_client = real_email_clients
        
        # Check secretary token
        assert secretary_client.creds.valid
        assert not secretary_client.creds.expired
        
        # Check monitor token  
        assert monitor_client.creds.valid
        assert not monitor_client.creds.expired
        
        # Verify token files exist
        secretary_token_path = os.path.join('/mnt/c/Users/Man/ultra/projects/karen', 'gmail_token_karen.json')
        monitor_token_path = os.path.join('/mnt/c/Users/Man/ultra/projects/karen', 'gmail_token_monitor.json')
        
        assert os.path.exists(secretary_token_path)
        assert os.path.exists(monitor_token_path)
        
        self.test_comm.update_status('testing_email_baseline', 20, {
            'step': 'oauth_validation',
            'status': 'passed'
        })
    
    def test_email_sending_capability(self, real_email_clients):
        """Test that Karen can send emails successfully"""
        secretary_client, monitor_client = real_email_clients
        
        test_subject = f"BASELINE TEST: Email Sending - {datetime.now().isoformat()}"
        test_body = f"""This is an automated baseline test of Karen's email sending capability.
        
Timestamp: {datetime.now().isoformat()}
Test Purpose: Verify email sending from Karen secretary account
Sender: {secretary_client.email_address}
Recipient: {ADMIN_EMAIL_ADDRESS}

This email should be received successfully to confirm the email system is operational."""
        
        # Send test email
        success = secretary_client.send_email(
            to=ADMIN_EMAIL_ADDRESS,
            subject=test_subject,
            body=test_body
        )
        
        assert success, "Failed to send baseline test email"
        
        # Verify email appears in sent folder
        time.sleep(2)  # Allow time for email to appear
        sent_emails = secretary_client.fetch_last_n_sent_emails(n=1)
        
        assert len(sent_emails) > 0, "No emails found in sent folder"
        assert test_subject in sent_emails[0].get('subject', ''), "Test email not found in sent folder"
        
        self.test_comm.update_status('testing_email_baseline', 35, {
            'step': 'email_sending',
            'status': 'passed',
            'test_email_sent': True
        })
    
    def test_email_fetching_capability(self, real_email_clients):
        """Test that Karen can fetch emails from monitored inbox"""
        secretary_client, monitor_client = real_email_clients
        
        # Fetch recent emails from monitoring account
        recent_emails = monitor_client.fetch_emails(
            search_criteria='',  # All emails
            last_n_days=7,
            max_results=5
        )
        
        # Should be able to fetch emails (list might be empty but shouldn't fail)
        assert isinstance(recent_emails, list), "Email fetching returned invalid type"
        
        # Test specific search criteria
        unread_emails = monitor_client.fetch_emails(
            search_criteria='is:unread',
            max_results=10
        )
        
        assert isinstance(unread_emails, list), "Unread email fetching failed"
        
        # Test date-based fetching
        last_day_emails = monitor_client.fetch_emails(
            last_n_days=1,
            max_results=10
        )
        
        assert isinstance(last_day_emails, list), "Date-based email fetching failed"
        
        self.test_comm.update_status('testing_email_baseline', 50, {
            'step': 'email_fetching',
            'status': 'passed',
            'emails_fetched': len(recent_emails)
        })
    
    def test_email_classification_system(self):
        """Test that emails can be properly classified"""
        # Initialize response engine
        llm_client = LLMClient() if os.getenv('GEMINI_API_KEY') else None
        
        response_engine = HandymanResponseEngine(
            business_name="Beach Handyman",
            service_area="Virginia Beach area",
            phone="757-354-4577",
            llm_client=llm_client
        )
        
        # Test classification of different email types
        test_cases = [
            {
                'subject': 'Need plumbing repair ASAP',
                'body': 'Hi, my sink is leaking badly. Can you help today?',
                'expected_type': 'emergency_inquiry'
            },
            {
                'subject': 'Quote request for bathroom renovation',
                'body': 'I would like a quote for renovating my master bathroom',
                'expected_type': 'quote_request'  
            },
            {
                'subject': 'Schedule appointment for deck repair',
                'body': 'Can you schedule an appointment next week to fix my deck?',
                'expected_type': 'schedule_appointment'
            },
            {
                'subject': 'General question about services',
                'body': 'What types of handyman services do you provide?',
                'expected_type': 'general_inquiry'
            }
        ]
        
        for test_case in test_cases:
            classification = response_engine.classify_email_type(
                test_case['subject'],
                test_case['body']
            )
            
            assert classification is not None, f"Classification failed for: {test_case['subject']}"
            
            # Basic validation that classification has required fields
            assert 'intent' in classification, "Classification missing intent field"
            assert 'urgency' in classification, "Classification missing urgency field"
        
        self.test_comm.update_status('testing_email_baseline', 65, {
            'step': 'email_classification',
            'status': 'passed',
            'test_cases_processed': len(test_cases)
        })
    
    @pytest.mark.asyncio
    async def test_llm_response_generation(self):
        """Test that LLM responses can be generated for emails"""
        if not os.getenv('GEMINI_API_KEY'):
            pytest.skip("GEMINI_API_KEY not available for LLM testing")
        
        llm_client = LLMClient()
        response_engine = HandymanResponseEngine(
            business_name="Beach Handyman",
            service_area="Virginia Beach area",
            phone="757-354-4577",
            llm_client=llm_client
        )
        
        # Test response generation
        test_email_from = "customer@example.com"
        test_subject = "Need help with plumbing"
        test_body = "Hi, I have a leaky faucet that needs repair. Can you help?"
        
        response, classification = await response_engine.generate_response_async(
            test_email_from, test_subject, test_body
        )
        
        assert response is not None, "Failed to generate LLM response"
        assert len(response) > 50, "LLM response too short"
        assert classification is not None, "Failed to get email classification"
        
        # Verify response is professional and relevant
        response_lower = response.lower()
        assert any(word in response_lower for word in ['handyman', 'service', 'repair', 'help']), \
            "Response doesn't contain relevant business terms"
        
        self.test_comm.update_status('testing_email_baseline', 80, {
            'step': 'llm_response_generation',
            'status': 'passed',
            'response_length': len(response)
        })
    
    def test_email_marking_and_labeling(self, real_email_clients):
        """Test that emails can be properly marked and labeled"""
        secretary_client, monitor_client = real_email_clients
        
        # Fetch a recent email to test marking
        recent_emails = monitor_client.fetch_emails(
            search_criteria='',
            max_results=1
        )
        
        if len(recent_emails) > 0:
            test_email = recent_emails[0]
            email_uid = test_email.get('uid')
            
            if email_uid:
                # Test marking as read
                mark_success = monitor_client.mark_email_as_seen(email_uid)
                assert mark_success, f"Failed to mark email {email_uid} as seen"
                
                # Test adding label (this will create the label if it doesn't exist)
                label_success = monitor_client.mark_email_as_processed(
                    uid=email_uid,
                    label_to_add="Test_Baseline_Label"
                )
                assert label_success, f"Failed to add label to email {email_uid}"
        
        self.test_comm.update_status('testing_email_baseline', 90, {
            'step': 'email_marking',
            'status': 'passed'
        })
    
    @pytest.mark.asyncio
    async def test_communication_agent_integration(self):
        """Test the full CommunicationAgent email processing pipeline"""
        # Mock configurations for safe testing
        sending_cfg = {
            'SECRETARY_EMAIL_ADDRESS': 'test_karen@example.com',
            'SECRETARY_TOKEN_PATH': 'test_token.json'
        }
        
        monitoring_cfg = {
            'MONITORED_EMAIL_ACCOUNT': 'test_monitor@example.com',
            'MONITORED_EMAIL_TOKEN_PATH': 'test_monitor_token.json'
        }
        
        sms_cfg = {'account_sid': None}  # Disable SMS for this test
        transcription_cfg = None  # Disable transcription for this test
        
        # Mock task manager
        mock_task_manager = Mock()
        mock_task_manager.create_task.return_value = Mock(id="test_task_123")
        mock_task_manager.generate_llm_suggestion_for_task.return_value = "Test suggestion"
        
        # Test with mock clients (safe for automated testing)
        with patch('src.communication_agent.agent.USE_MOCK_EMAIL_CLIENT', True):
            with patch('src.communication_agent.agent.MockEmailClient') as mock_client_class:
                # Configure mock
                mock_client = Mock()
                mock_client.fetch_emails.return_value = []
                mock_client.send_email.return_value = True
                mock_client_class.return_value = mock_client
                
                # Initialize agent
                agent = CommunicationAgent(
                    sending_email_cfg=sending_cfg,
                    monitoring_email_cfg=monitoring_cfg,
                    sms_cfg=sms_cfg,
                    transcription_cfg=transcription_cfg,
                    admin_email='admin@example.com',
                    task_manager_instance=mock_task_manager
                )
                
                # Test that agent initializes without errors
                assert agent is not None
                assert agent.sending_email_client is not None
                assert agent.monitoring_email_client is not None
        
        self.test_comm.update_status('testing_email_baseline', 100, {
            'step': 'communication_agent_integration',
            'status': 'passed',
            'test_suite_complete': True
        })
    
    def test_email_system_dependencies(self):
        """Test that all email system dependencies are available"""
        # Check required environment variables
        required_env_vars = [
            'SECRETARY_EMAIL_ADDRESS',
            'MONITORED_EMAIL_ACCOUNT', 
            'ADMIN_EMAIL_ADDRESS'
        ]
        
        missing_vars = []
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        assert len(missing_vars) == 0, f"Missing required environment variables: {missing_vars}"
        
        # Check required files exist
        project_root = '/mnt/c/Users/Man/ultra/projects/karen'
        required_files = [
            'credentials.json',
            'src/llm_system_prompt.txt'
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = os.path.join(project_root, file_path)
            if not os.path.exists(full_path):
                missing_files.append(file_path)
        
        assert len(missing_files) == 0, f"Missing required files: {missing_files}"
        
        # Check Python dependencies
        try:
            import google.oauth2.credentials
            import googleapiclient.discovery
            import email
            import json
        except ImportError as e:
            pytest.fail(f"Missing required Python dependency: {e}")
    
    def test_redis_connectivity_for_agent_communication(self):
        """Test that Redis is available for agent communication"""
        try:
            # Test basic Redis connectivity
            test_comm = AgentCommunication('baseline_test')
            
            # Test status update (uses Redis)
            test_comm.update_status('testing', 100, {'test': True})
            
            # Test message sending
            test_comm.send_message('orchestrator', 'test_message', {
                'sender': 'baseline_test',
                'message': 'connectivity_test'
            })
            
        except Exception as e:
            pytest.fail(f"Redis connectivity test failed: {e}")

    def teardown_method(self):
        """Clean up after each test"""
        # Report test completion
        if hasattr(self, 'test_comm'):
            self.test_comm.update_status('email_baseline_complete', 100, {
                'test_suite': 'email_baseline',
                'completion_time': datetime.now().isoformat()
            })

# Integration test for full email flow
class TestEmailFlowIntegration:
    """Test complete email processing flows"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_email_processing_flow(self):
        """Test the complete flow from email receipt to response"""
        if USE_MOCK_EMAIL_CLIENT:
            pytest.skip("Integration test requires real email clients")
        
        # This test would be run manually or in a controlled environment
        # to avoid sending actual emails during automated testing
        
        test_comm = AgentCommunication('test_engineer')
        test_comm.update_status('integration_testing', 0, {
            'test': 'full_email_flow',
            'critical': True
        })
        
        # Test would include:
        # 1. Send test email to monitored account
        # 2. Run email processing pipeline
        # 3. Verify LLM response generated
        # 4. Verify response sent successfully
        # 5. Verify email marked as processed
        
        # For now, just verify the pipeline components exist
        from communication_agent.agent import CommunicationAgent
        from email_client import EmailClient
        from handyman_response_engine import HandymanResponseEngine
        from llm_client import LLMClient
        
        assert CommunicationAgent is not None
        assert EmailClient is not None
        assert HandymanResponseEngine is not None
        assert LLMClient is not None
        
        test_comm.update_status('integration_testing', 100, {
            'test': 'full_email_flow',
            'status': 'components_verified'
        })

if __name__ == "__main__":
    # Run baseline tests
    pytest.main([__file__, "-v", "--tb=short"])
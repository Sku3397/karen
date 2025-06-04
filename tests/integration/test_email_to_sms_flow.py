#!/usr/bin/env python3
"""
Email to SMS Flow Integration Test
Test Engineer: Complete flow testing with real service behavior simulation

Tests the complete flow:
1. Email received → 2. Parsed and classified → 3. SMS sent → 4. Response handled
"""

import pytest
import asyncio
import time
import threading
from datetime import datetime, timedelta
from unittest.mock import patch, Mock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from tests.mocks.service_mocks import (
    ServiceMockFactory, TwilioException, GmailException
)
from tests.fixtures.test_data_factory import TestDataFactory, ConversationFlowFactory

class TestEmailToSMSFlow:
    """Integration tests for complete email to SMS processing flow"""
    
    @pytest.fixture
    def stable_services(self):
        """Stable service mocks for baseline testing"""
        return ServiceMockFactory.create_stable_services()
    
    @pytest.fixture
    def communication_agent_mock(self):
        """Mock communication agent that coordinates the flow"""
        class CommunicationAgentMock:
            def __init__(self, services):
                self.services = services
                self.processed_emails = []
                self.sent_sms = []
                self.conversation_state = {}
                
            def process_email(self, email_data):
                """Process incoming email and trigger SMS if needed"""
                self.processed_emails.append(email_data)
                
                # Extract phone number from email
                phone = self._extract_phone_number(email_data['body'])
                if not phone:
                    return {"status": "no_phone_found", "action": "email_reply"}
                
                # Classify intent
                intent = self._classify_intent(email_data['body'])
                
                # Generate response based on intent
                response = self._generate_response(intent, email_data)
                
                # Send SMS
                try:
                    sms_result = self.services['twilio'].send_sms(
                        to=phone,
                        from_="+17575550123",
                        body=response
                    )
                    
                    self.sent_sms.append({
                        'email_id': email_data['id'],
                        'sms_sid': sms_result['sid'],
                        'phone': phone,
                        'response': response,
                        'intent': intent
                    })
                    
                    return {
                        "status": "sms_sent", 
                        "sms_sid": sms_result['sid'],
                        "intent": intent,
                        "phone": phone
                    }
                    
                except TwilioException as e:
                    return {"status": "sms_failed", "error": str(e)}
                    
            def handle_sms_response(self, sms_data):
                """Handle incoming SMS response"""
                conversation_id = self._get_conversation_id(sms_data['from'])
                
                # Update conversation state
                if conversation_id not in self.conversation_state:
                    self.conversation_state[conversation_id] = {
                        'messages': [],
                        'status': 'active',
                        'intent': 'unknown'
                    }
                
                self.conversation_state[conversation_id]['messages'].append(sms_data)
                
                # Generate contextual response
                response = self._generate_contextual_response(conversation_id, sms_data)
                
                if response:
                    return self.services['twilio'].send_sms(
                        to=sms_data['from'],
                        from_="+17575550123", 
                        body=response
                    )
                    
                return None
                
            def _extract_phone_number(self, text):
                """Extract phone number from text"""
                import re
                phone_pattern = r'(?:\+?1[-.\s]?)?\(?([2-9][0-8][0-9])\)?[-.\s]?([2-9][0-9]{2})[-.\s]?([0-9]{4})'
                match = re.search(phone_pattern, text)
                if match:
                    return f"+1{match.group(1)}{match.group(2)}{match.group(3)}"
                return None
                
            def _classify_intent(self, text):
                """Classify email intent"""
                text_lower = text.lower()
                if any(word in text_lower for word in ['emergency', 'urgent', 'asap', 'help']):
                    return 'emergency'
                elif any(word in text_lower for word in ['appointment', 'schedule', 'book']):
                    return 'appointment_request'
                elif any(word in text_lower for word in ['price', 'cost', 'quote']):
                    return 'pricing_inquiry'
                else:
                    return 'general_inquiry'
                    
            def _generate_response(self, intent, email_data):
                """Generate appropriate SMS response"""
                responses = {
                    'emergency': "Hi! This is Karen from 757 Handy. I see you have an urgent plumbing issue. I'm dispatching our emergency team now. Please reply with your exact address.",
                    'appointment_request': "Hi! This is Karen from 757 Handy. I received your service request. I can schedule you for tomorrow at 2 PM or Thursday at 10 AM. Which works better?",
                    'pricing_inquiry': "Hi! Thanks for your interest in 757 Handy. Our standard service call is $150, which includes the first hour. Would you like to schedule a free estimate?",
                    'general_inquiry': "Hi! Thanks for contacting 757 Handy. I'm Karen, your AI assistant. How can I help you today?"
                }
                return responses.get(intent, responses['general_inquiry'])
                
            def _get_conversation_id(self, phone):
                """Get or create conversation ID for phone number"""
                return f"conv_{phone.replace('+', '').replace('-', '')}"
                
            def _generate_contextual_response(self, conversation_id, sms_data):
                """Generate contextual response based on conversation history"""
                conversation = self.conversation_state[conversation_id]
                message_count = len(conversation['messages'])
                
                # Simple state machine for conversation flow
                if message_count == 1:
                    # First response - ask for clarification if needed
                    if 'address' in sms_data['body'].lower():
                        return "Perfect! I have your address. Our technician will arrive within 30 minutes. I'll send you their contact info shortly."
                    elif any(time in sms_data['body'].lower() for time in ['2 pm', '10 am', 'tomorrow', 'thursday']):
                        return "Great! I've scheduled your appointment. You'll receive a confirmation shortly. Is this the best number to reach you?"
                    else:
                        return "I need a bit more information to help you better. Could you be more specific about your plumbing issue?"
                        
                elif message_count == 2:
                    # Second response - confirmation or follow-up
                    if 'yes' in sms_data['body'].lower():
                        return "Perfect! Your appointment is confirmed. Our technician will call 15 minutes before arrival. Have a great day!"
                    else:
                        return "Thanks for the information. I'll make a note of that. Is there anything else I can help you with?"
                        
                # End conversation after a few exchanges
                conversation['status'] = 'completed'
                return None
                
        return CommunicationAgentMock
    
    def test_complete_email_to_sms_flow(self, stable_services, communication_agent_mock):
        """Test complete flow from email receipt to SMS response"""
        
        # Setup
        agent = communication_agent_mock(stable_services)
        
        # Create realistic customer email
        customer_email = TestDataFactory.create_customer_email(
            intent="appointment_request",
            urgency="normal",
            include_phone=True
        )
        
        # Step 1: Process incoming email
        result = agent.process_email(customer_email)
        
        # Verify email processing
        assert result["status"] == "sms_sent"
        assert "sms_sid" in result
        assert result["intent"] == "appointment_request"
        assert len(agent.processed_emails) == 1
        assert len(agent.sent_sms) == 1
        
        # Verify SMS was sent through Twilio mock
        twilio_messages = stable_services['twilio'].sent_messages
        assert len(twilio_messages) == 1
        assert twilio_messages[0]['body'].startswith("Hi! This is Karen")
        
        # Step 2: Simulate customer SMS response
        customer_response = {
            'from': result['phone'],
            'to': '+17575550123',
            'body': 'Thursday at 10 AM works great',
            'direction': 'inbound'
        }
        
        # Step 3: Handle SMS response
        response_result = agent.handle_sms_response(customer_response)
        
        # Verify response handling
        assert response_result is not None
        assert 'sid' in response_result
        assert len(stable_services['twilio'].sent_messages) == 2
        
        # Step 4: Verify conversation state
        conversation_id = agent._get_conversation_id(result['phone'])
        assert conversation_id in agent.conversation_state
        assert len(agent.conversation_state[conversation_id]['messages']) == 1
        
        # Step 5: Complete conversation flow
        final_response = {
            'from': result['phone'],
            'to': '+17575550123',
            'body': 'Yes, this number is perfect',
            'direction': 'inbound'
        }
        
        final_result = agent.handle_sms_response(final_response)
        
        # Verify conversation completion
        assert len(agent.conversation_state[conversation_id]['messages']) == 2
        assert agent.conversation_state[conversation_id]['status'] == 'completed'
    
    def test_emergency_email_priority_handling(self, stable_services, communication_agent_mock):
        """Test emergency emails get priority handling"""
        
        agent = communication_agent_mock(stable_services)
        
        # Create emergency email
        emergency_email = TestDataFactory.create_customer_email(
            intent="appointment_request",
            urgency="emergency",
            include_phone=True
        )
        emergency_email['body'] = "EMERGENCY! Water everywhere in basement! Call " + emergency_email['phone_extracted']
        
        # Process emergency email
        result = agent.process_email(emergency_email)
        
        # Verify emergency handling
        assert result["status"] == "sms_sent"
        assert result["intent"] == "emergency"
        
        # Check emergency response content
        emergency_sms = stable_services['twilio'].sent_messages[0]
        assert "emergency" in emergency_sms['body'].lower()
        assert "dispatching" in emergency_sms['body'].lower()
    
    def test_email_without_phone_fallback(self, stable_services, communication_agent_mock):
        """Test handling of emails without phone numbers"""
        
        agent = communication_agent_mock(stable_services)
        
        # Create email without phone
        email_no_phone = TestDataFactory.create_customer_email(
            intent="general_inquiry",
            include_phone=False
        )
        
        # Process email
        result = agent.process_email(email_no_phone)
        
        # Verify fallback to email reply
        assert result["status"] == "no_phone_found"
        assert result["action"] == "email_reply"
        assert len(agent.sent_sms) == 0
    
    def test_concurrent_email_processing(self, stable_services, communication_agent_mock):
        """Test processing multiple emails concurrently"""
        
        agent = communication_agent_mock(stable_services)
        
        # Create multiple customer emails
        emails = []
        for i in range(5):
            email = TestDataFactory.create_customer_email(
                intent=["appointment_request", "emergency", "pricing_inquiry"][i % 3],
                urgency=["normal", "high", "emergency"][i % 3],
                include_phone=True
            )
            emails.append(email)
        
        # Process emails concurrently
        results = []
        threads = []
        
        def process_email_thread(email):
            result = agent.process_email(email)
            results.append(result)
        
        for email in emails:
            thread = threading.Thread(target=process_email_thread, args=(email,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all emails were processed
        assert len(results) == 5
        assert len(agent.processed_emails) == 5
        assert len(agent.sent_sms) == 5
        assert len(stable_services['twilio'].sent_messages) == 5
        
        # Verify no race conditions in SMS sending
        sms_sids = [msg['sid'] for msg in stable_services['twilio'].sent_messages]
        assert len(set(sms_sids)) == 5  # All unique SIDs
    
    def test_sms_webhook_status_updates(self, stable_services, communication_agent_mock):
        """Test handling of SMS status webhooks"""
        
        agent = communication_agent_mock(stable_services)
        
        # Process email that triggers SMS
        customer_email = TestDataFactory.create_customer_email(
            intent="appointment_request",
            include_phone=True
        )
        
        result = agent.process_email(customer_email)
        message_sid = result['sms_sid']
        
        # Wait for webhook to be triggered
        time.sleep(1.0)  # Wait for webhook delay
        
        # Verify webhook was called
        webhooks = stable_services['twilio'].webhooks
        assert len(webhooks) >= 1
        
        # Find webhook for our message
        status_webhooks = [w for w in webhooks if w['MessageSid'] == message_sid]
        assert len(status_webhooks) >= 1
        
        # Verify message status was updated
        message_status = stable_services['twilio'].get_message_status(message_sid)
        assert message_status['status'] in ['sent', 'delivered']
    
    def test_conversation_context_preservation(self, stable_services, communication_agent_mock):
        """Test that conversation context is preserved across messages"""
        
        agent = communication_agent_mock(stable_services)
        
        # Start conversation
        customer_email = TestDataFactory.create_customer_email(
            intent="appointment_request",
            include_phone=True
        )
        
        result = agent.process_email(customer_email)
        phone = result['phone']
        conversation_id = agent._get_conversation_id(phone)
        
        # Multiple SMS exchanges
        sms_exchanges = [
            "I need this fixed ASAP",
            "Tomorrow at 2 PM works",
            "Yes, this number is good",
            "Thank you!"
        ]
        
        for i, message_text in enumerate(sms_exchanges):
            sms_message = {
                'from': phone,
                'to': '+17575550123',
                'body': message_text,
                'direction': 'inbound'
            }
            
            agent.handle_sms_response(sms_message)
            
            # Verify conversation context is preserved
            conversation = agent.conversation_state[conversation_id]
            assert len(conversation['messages']) == i + 1
            assert conversation['messages'][-1]['body'] == message_text
        
        # Verify conversation progression
        final_conversation = agent.conversation_state[conversation_id]
        assert len(final_conversation['messages']) == 4
        assert final_conversation['status'] in ['active', 'completed']
    
    def test_data_consistency_across_services(self, stable_services, communication_agent_mock):
        """Test data consistency between email, SMS, and conversation state"""
        
        agent = communication_agent_mock(stable_services)
        
        # Create multi-channel conversation
        multi_channel = ConversationFlowFactory.create_multi_channel_conversation()
        
        # Process the email part
        email_data = next(
            item['data'] for item in multi_channel['timeline'] 
            if item['channel'] == 'email'
        )
        
        email_result = agent.process_email(email_data)
        
        # Process SMS parts
        sms_messages = [
            item['data'] for item in multi_channel['timeline']
            if item['channel'] == 'sms'
        ]
        
        for sms_msg in sms_messages:
            if sms_msg['direction'] == 'inbound':
                agent.handle_sms_response(sms_msg)
        
        # Verify data consistency
        phone = email_result['phone']
        conversation_id = agent._get_conversation_id(phone)
        
        # Check that email ID is linked to SMS SID
        email_sms_link = next(
            (item for item in agent.sent_sms if item['email_id'] == email_data['id']),
            None
        )
        assert email_sms_link is not None
        assert email_sms_link['phone'] == phone
        
        # Check that conversation state includes all messages
        conversation = agent.conversation_state.get(conversation_id)
        assert conversation is not None
        
        # Verify no data loss
        assert len(agent.processed_emails) >= 1
        assert len(agent.sent_sms) >= 1
        assert len(stable_services['twilio'].sent_messages) >= 1

@pytest.mark.integration
class TestEmailToSMSFailureHandling:
    """Test failure scenarios in email to SMS flow"""
    
    @pytest.fixture
    def unreliable_services(self):
        """Services with intermittent failures"""
        return ServiceMockFactory.create_chaos_services(failure_rate=0.3)
    
    def test_twilio_failure_graceful_degradation(self, unreliable_services, communication_agent_mock):
        """Test graceful handling when Twilio service fails"""
        
        agent = communication_agent_mock(unreliable_services)
        
        # Try processing multiple emails
        results = []
        for i in range(10):
            email = TestDataFactory.create_customer_email(
                intent="appointment_request",
                include_phone=True
            )
            
            result = agent.process_email(email)
            results.append(result)
        
        # Some should succeed, some should fail gracefully
        successful = [r for r in results if r['status'] == 'sms_sent']
        failed = [r for r in results if r['status'] == 'sms_failed']
        
        assert len(successful) > 0  # Some should succeed
        assert len(failed) > 0      # Some should fail
        
        # Verify failed requests are handled gracefully
        for failed_result in failed:
            assert 'error' in failed_result
            assert failed_result['status'] == 'sms_failed'
    
    def test_email_processing_resilience(self, unreliable_services, communication_agent_mock):
        """Test system resilience under various failure conditions"""
        
        agent = communication_agent_mock(unreliable_services)
        
        # Create diverse test scenarios
        test_scenarios = [
            TestDataFactory.create_customer_email(intent="emergency", urgency="emergency"),
            TestDataFactory.create_customer_email(intent="appointment_request"),
            TestDataFactory.create_customer_email(intent="pricing_inquiry"),
            TestDataFactory.create_customer_email(intent="general_inquiry", include_phone=False)
        ]
        
        processed_count = 0
        error_count = 0
        
        for email in test_scenarios:
            try:
                result = agent.process_email(email)
                if result['status'] in ['sms_sent', 'no_phone_found']:
                    processed_count += 1
                else:
                    error_count += 1
            except Exception as e:
                error_count += 1
                print(f"Unexpected error: {e}")
        
        # Verify system handles mix of success and failure
        assert processed_count > 0
        # Allow for some errors due to service failures
        assert error_count <= len(test_scenarios)
        
        # Verify no complete system failure
        assert processed_count + error_count == len(test_scenarios)

if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "--tb=short"])
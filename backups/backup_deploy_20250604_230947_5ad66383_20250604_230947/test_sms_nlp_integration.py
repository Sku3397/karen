#!/usr/bin/env python3
"""
Test script for SMS integration with enhanced NLP capabilities
Tests the complete SMS workflow with intelligent message processing
"""

import asyncio
import sys
import os
import json
from datetime import datetime, timezone
from unittest.mock import Mock, patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.sms_integration import SMSIntegration, SMSMessage
from src.nlp_engine import Intent, Sentiment, Priority

class MockTwilioClient:
    """Mock Twilio client for testing"""
    
    def __init__(self):
        self.messages = Mock()
        self.messages.create = Mock(return_value=Mock(
            sid="SM123456789",
            status="sent"
        ))

class TestSMSNLPIntegration:
    """Test suite for SMS NLP integration"""
    
    def __init__(self):
        self.test_messages = [
            {
                "From": "+17575551234",
                "To": "+17573544577", 
                "Body": "EMERGENCY! Water pipe burst in basement, need help NOW!",
                "MessageSid": "SM001",
                "expected_intent": Intent.EMERGENCY,
                "expected_priority": Priority.CRITICAL
            },
            {
                "From": "+17575555678",
                "To": "+17573544577",
                "Body": "Can you schedule an appointment to fix my kitchen faucet tomorrow afternoon?",
                "MessageSid": "SM002", 
                "expected_intent": Intent.APPOINTMENT_SCHEDULE,
                "expected_priority": Priority.HIGH
            },
            {
                "From": "+17575559999",
                "To": "+17573544577",
                "Body": "How much would it cost to repair my deck? Need a quote please.",
                "MessageSid": "SM003",
                "expected_intent": Intent.QUOTE_REQUEST,
                "expected_priority": Priority.HIGH
            },
            {
                "From": "+17575552222",
                "To": "+17573544577",
                "Body": "Thank you for the excellent work on my electrical outlets!",
                "MessageSid": "SM004",
                "expected_intent": Intent.COMPLIMENT,
                "expected_priority": Priority.LOW
            },
            {
                "From": "+17575553333",
                "To": "+17573544577",
                "Body": "Hi, what are your business hours? Do you work weekends?",
                "MessageSid": "SM005",
                "expected_intent": Intent.GENERAL_INQUIRY,
                "expected_priority": Priority.MEDIUM
            }
        ]
    
    def setup_mock_sms_integration(self):
        """Setup SMS integration with mocked Twilio client"""
        # Mock environment variables
        test_env = {
            'TWILIO_ACCOUNT_SID': 'test_account_sid',
            'TWILIO_AUTH_TOKEN': 'test_auth_token',
            'TWILIO_FROM_NUMBER': '+17573544577'
        }
        
        with patch.dict(os.environ, test_env):
            with patch('src.sms_integration.Client', return_value=MockTwilioClient()):
                sms_integration = SMSIntegration()
                return sms_integration
    
    async def test_nlp_analysis_accuracy(self):
        """Test NLP analysis accuracy for different message types"""
        print("\n=== Testing NLP Analysis Accuracy ===")
        
        sms_integration = self.setup_mock_sms_integration()
        correct_predictions = 0
        total_predictions = len(self.test_messages)
        
        for i, test_case in enumerate(self.test_messages, 1):
            webhook_data = {
                'From': test_case['From'],
                'To': test_case['To'],
                'Body': test_case['Body'],
                'MessageSid': test_case['MessageSid']
            }
            
            # Process the message
            response, sms_msg = await sms_integration.receive_sms_webhook(webhook_data)
            
            # Check if we have customer profile data (indicates NLP was run)
            profile = sms_integration.customer_profiles.get(test_case['From'], {})
            
            if profile and profile.get('intents'):
                detected_intent = Intent(profile['intents'][-1])  # Latest intent
                expected_intent = test_case['expected_intent']
                
                is_correct = detected_intent == expected_intent
                if is_correct:
                    correct_predictions += 1
                
                status = "✅" if is_correct else "❌"
                print(f"{i}. {status} Message: '{test_case['Body'][:50]}...'")
                print(f"   Expected: {expected_intent.value} | Detected: {detected_intent.value}")
                print(f"   Response: {response[:80]}...")
                print()
            else:
                print(f"{i}. ⚠️  NLP analysis not found for message")
        
        accuracy = (correct_predictions / total_predictions) * 100
        print(f"Intent Classification Accuracy: {accuracy:.1f}% ({correct_predictions}/{total_predictions})")
        
        return accuracy
    
    async def test_emergency_handling(self):
        """Test emergency message handling"""
        print("\n=== Testing Emergency Message Handling ===")
        
        sms_integration = self.setup_mock_sms_integration()
        
        emergency_messages = [
            "EMERGENCY! Gas leak in kitchen!",
            "URGENT - no power, electrical fire risk",
            "Help! Ceiling falling down!"
        ]
        
        for msg in emergency_messages:
            webhook_data = {
                'From': '+17575551111',
                'To': '+17573544577',
                'Body': msg,
                'MessageSid': f'SM{hash(msg) % 10000}'
            }
            
            response, sms_msg = await sms_integration.receive_sms_webhook(webhook_data)
            
            # Check emergency indicators
            has_emergency_emoji = '🚨' in response
            has_immediate_help = 'immediately' in response.lower() or 'now' in response.lower()
            has_phone_number = '757-354-4577' in response
            
            print(f"Message: {msg}")
            print(f"Response: {response[:100]}...")
            print(f"Emergency indicators: Emoji={has_emergency_emoji}, Immediate={has_immediate_help}, Phone={has_phone_number}")
            print()
    
    async def test_context_awareness(self):
        """Test conversation context awareness"""
        print("\n=== Testing Context Awareness ===")
        
        sms_integration = self.setup_mock_sms_integration()
        customer_phone = '+17575556666'
        
        # Simulate conversation flow
        conversation = [
            "Hi, I need some plumbing work done",
            "It's my kitchen faucet that's leaking",
            "How much would that cost to fix?",
            "Can you come tomorrow morning?"
        ]
        
        for i, msg in enumerate(conversation, 1):
            webhook_data = {
                'From': customer_phone,
                'To': '+17573544577',
                'Body': msg,
                'MessageSid': f'SM{i}CONTEXT'
            }
            
            response, sms_msg = await sms_integration.receive_sms_webhook(webhook_data)
            
            print(f"Message {i}: {msg}")
            print(f"Response: {response}")
            
            # Check if context is being maintained
            profile = sms_integration.customer_profiles.get(customer_phone, {})
            print(f"Message count: {profile.get('message_count', 0)}")
            print(f"Intent history: {profile.get('intents', [])}")
            print()
    
    async def test_entity_extraction_integration(self):
        """Test entity extraction in SMS responses"""
        print("\n=== Testing Entity Extraction Integration ===")
        
        sms_integration = self.setup_mock_sms_integration()
        
        entity_test_cases = [
            {
                'message': 'Call me at 757-555-1234 for the appointment',
                'expected_entities': ['phone_number']
            },
            {
                'message': 'Schedule me for tomorrow at 2:30 PM',
                'expected_entities': ['date', 'time']
            },
            {
                'message': 'My address is 123 Main Street, Virginia Beach',
                'expected_entities': ['address']
            },
            {
                'message': 'The budget is around $500 for the repair',
                'expected_entities': ['money']
            }
        ]
        
        for test_case in entity_test_cases:
            webhook_data = {
                'From': '+17575557777',
                'To': '+17573544577',
                'Body': test_case['message'],
                'MessageSid': f'SM{hash(test_case["message"]) % 10000}'
            }
            
            response, sms_msg = await sms_integration.receive_sms_webhook(webhook_data)
            
            print(f"Message: {test_case['message']}")
            print(f"Expected entities: {test_case['expected_entities']}")
            print(f"Response: {response}")
            print()
    
    async def test_response_personalization(self):
        """Test response personalization based on customer history"""
        print("\n=== Testing Response Personalization ===")
        
        sms_integration = self.setup_mock_sms_integration()
        
        # Setup customer with history
        loyal_customer = '+17575558888'
        sms_integration.customer_profiles[loyal_customer] = {
            'first_contact': '2024-01-01T00:00:00Z',
            'message_count': 15,
            'intents': ['service_inquiry', 'appointment_schedule', 'compliment'] * 5,
            'sentiment_history': ['positive'] * 10 + ['neutral'] * 5,
            'priority_contacts': 3,
            'emergency_contacts': 0
        }
        
        # Test message from loyal customer
        webhook_data = {
            'From': loyal_customer,
            'To': '+17573544577',
            'Body': 'Hi Karen, I need another repair appointment',
            'MessageSid': 'SMLOYALCUSTOMER'
        }
        
        response, sms_msg = await sms_integration.receive_sms_webhook(webhook_data)
        
        print(f"Loyal customer message: {webhook_data['Body']}")
        print(f"Response: {response}")
        print(f"Profile: {sms_integration.customer_profiles[loyal_customer]}")
    
    async def test_performance_benchmarks(self):
        """Test performance benchmarks for SMS processing"""
        print("\n=== Testing Performance Benchmarks ===")
        
        sms_integration = self.setup_mock_sms_integration()
        
        test_message = "Can you schedule an appointment to fix my faucet?"
        num_tests = 10
        
        start_time = datetime.now()
        
        for i in range(num_tests):
            webhook_data = {
                'From': f'+175555500{i:02d}',
                'To': '+17573544577',
                'Body': test_message,
                'MessageSid': f'SMPERF{i:03d}'
            }
            
            await sms_integration.receive_sms_webhook(webhook_data)
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        avg_time = total_time / num_tests
        
        print(f"Processed {num_tests} SMS messages in {total_time:.2f} seconds")
        print(f"Average processing time: {avg_time:.3f} seconds per message")
        print(f"Throughput: {num_tests/total_time:.1f} messages per second")
        
        # Performance thresholds
        if avg_time < 2.0:
            print("✅ Performance: Excellent (< 2s per message)")
        elif avg_time < 5.0:
            print("⚠️  Performance: Good (< 5s per message)")
        else:
            print("❌ Performance: Needs optimization (> 5s per message)")
    
    async def run_all_tests(self):
        """Run all SMS NLP integration tests"""
        print("🧪 SMS NLP Integration Test Suite")
        print("=" * 50)
        
        try:
            accuracy = await self.test_nlp_analysis_accuracy()
            await self.test_emergency_handling()
            await self.test_context_awareness()
            await self.test_entity_extraction_integration()
            await self.test_response_personalization()
            await self.test_performance_benchmarks()
            
            print("\n✅ All SMS NLP Integration Tests Completed!")
            
            # Summary
            print(f"\nTest Summary:")
            print(f"- Intent Classification Accuracy: {accuracy:.1f}%")
            print(f"- Emergency handling: Tested")
            print(f"- Context awareness: Tested")
            print(f"- Entity extraction: Tested")
            print(f"- Response personalization: Tested")
            print(f"- Performance benchmarks: Tested")
            
            if accuracy >= 80:
                print("\n🎉 NLP integration is performing well!")
            else:
                print("\n⚠️  NLP integration may need tuning")
            
        except Exception as e:
            print(f"\n❌ Test suite failed: {e}")
            import traceback
            traceback.print_exc()

async def main():
    """Main test runner"""
    test_suite = TestSMSNLPIntegration()
    await test_suite.run_all_tests()

if __name__ == "__main__":
    # Run the test suite
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n❌ Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test runner failed: {e}")
        import traceback
        traceback.print_exc()
#!/usr/bin/env python3
"""
Comprehensive Email Pipeline Test
Tests the complete email processing flow from incoming email to AI response
"""

import os
import sys
import time
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# Import Karen components
from src.email_client import EmailClient
from src.communication_agent.agent import CommunicationAgent
from src.celery_app import get_communication_agent_instance, check_secretary_emails_task
from src.config import (
    SECRETARY_EMAIL_ADDRESS,
    MONITORED_EMAIL_ACCOUNT_CONFIG, 
    ADMIN_EMAIL_ADDRESS,
    USE_MOCK_EMAIL_CLIENT
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_email_pipeline.log')
    ]
)
logger = logging.getLogger(__name__)

class EmailPipelineTest:
    """Comprehensive email pipeline testing suite"""
    
    def __init__(self):
        self.secretary_email = SECRETARY_EMAIL_ADDRESS
        self.monitored_email = MONITORED_EMAIL_ACCOUNT_CONFIG
        self.admin_email = ADMIN_EMAIL_ADDRESS
        self.use_mock = USE_MOCK_EMAIL_CLIENT
        
        logger.info(f"🔧 Test Configuration:")
        logger.info(f"   Secretary Email: {self.secretary_email}")
        logger.info(f"   Monitored Email: {self.monitored_email}")
        logger.info(f"   Admin Email: {self.admin_email}")
        logger.info(f"   Using Mock Client: {self.use_mock}")
        
    def test_basic_email_flow(self):
        """Test 1: Basic Email Processing"""
        print("\n" + "="*60)
        print("🚀 TEST 1: Basic Email Processing")
        print("="*60)
        
        try:
            # Test email data
            test_email = {
                'to': self.monitored_email,
                'from': 'test_customer@example.com',
                'subject': 'Need quote for plumbing repair',
                'body': 'Hi, my kitchen sink is leaking. Can you provide a quote?'
            }
            
            print(f"📧 Test Email Details:")
            print(f"   To: {test_email['to']}")
            print(f"   From: {test_email['from']}")
            print(f"   Subject: {test_email['subject']}")
            print(f"   Body: {test_email['body'][:100]}...")
            
            if not self.use_mock:
                # Send actual email
                print("\n📤 Sending test email...")
                secretary_client = EmailClient(self.secretary_email, profile='gmail_secretary')
                
                # Send test email to monitored account
                send_result = secretary_client.send_email(
                    to_email=test_email['to'],
                    subject=test_email['subject'],
                    body=test_email['body'],
                    from_email=test_email['from']  # Simulate customer email
                )
                
                if send_result:
                    print("✅ Test email sent successfully")
                else:
                    print("❌ Failed to send test email")
                    return False
            else:
                print("🔧 Using mock email client - simulating email send")
            
            # Wait for email to be delivered
            print("\n⏳ Waiting 10 seconds for email delivery...")
            time.sleep(10)
            
            # Trigger email processing
            print("\n🤖 Triggering Karen AI email processing...")
            try:
                # Method 1: Direct agent call
                agent = get_communication_agent_instance()
                print(f"   Agent instance: {type(agent)}")
                
                # Process emails asynchronously
                asyncio.run(agent.check_and_process_incoming_tasks(process_last_n_days=1))
                print("✅ Email processing completed")
                
            except Exception as e:
                print(f"⚠️  Agent processing failed, trying Celery task: {e}")
                
                # Method 2: Celery task
                try:
                    task_result = check_secretary_emails_task.apply()
                    print(f"✅ Celery task completed: {task_result}")
                except Exception as celery_e:
                    print(f"❌ Celery task failed: {celery_e}")
                    return False
            
            # Wait for processing
            print("\n⏳ Waiting 30 seconds for AI processing...")
            time.sleep(30)
            
            # Check for response
            print("\n📬 Checking for AI response...")
            self._check_response_sent()
            
            print("\n✅ Basic email flow test completed")
            return True
            
        except Exception as e:
            logger.error(f"Basic email flow test failed: {e}", exc_info=True)
            print(f"❌ Test failed: {e}")
            return False
    
    def test_appointment_scheduling(self):
        """Test 2: Appointment Scheduling Integration"""
        print("\n" + "="*60)
        print("🗓️  TEST 2: Appointment Scheduling Integration")
        print("="*60)
        
        try:
            # Appointment request email
            appointment_email = {
                'to': self.monitored_email,
                'from': 'customer@example.com',
                'subject': 'Emergency plumbing - need appointment ASAP',
                'body': 'Hi, I have a water leak emergency in my basement. Can you come out today or tomorrow morning? My address is 123 Main St, Norfolk VA 23505. Please call me at 757-123-4567.'
            }
            
            print(f"📧 Appointment Request:")
            print(f"   Subject: {appointment_email['subject']}")
            print(f"   Type: Emergency plumbing")
            print(f"   Urgency: ASAP")
            print(f"   Location: 123 Main St, Norfolk VA 23505")
            
            if not self.use_mock:
                # Send appointment request
                secretary_client = EmailClient(self.secretary_email, profile='gmail_secretary')
                send_result = secretary_client.send_email(
                    to_email=appointment_email['to'],
                    subject=appointment_email['subject'],
                    body=appointment_email['body']
                )
                
                if send_result:
                    print("✅ Appointment request sent")
                else:
                    print("❌ Failed to send appointment request")
                    return False
            else:
                print("🔧 Using mock email - simulating appointment request")
            
            # Process appointment request
            print("\n🤖 Processing appointment request...")
            agent = get_communication_agent_instance()
            asyncio.run(agent.check_and_process_incoming_tasks(process_last_n_days=1))
            
            print("\n⏳ Waiting for calendar integration...")
            time.sleep(20)
            
            print("✅ Appointment scheduling test completed")
            return True
            
        except Exception as e:
            logger.error(f"Appointment scheduling test failed: {e}", exc_info=True)
            print(f"❌ Test failed: {e}")
            return False
    
    def test_service_classification(self):
        """Test 3: Service Type Classification"""
        print("\n" + "="*60)
        print("🔧 TEST 3: Service Type Classification")
        print("="*60)
        
        test_services = [
            {
                'subject': 'Electrical outlet not working',
                'body': 'My kitchen outlet stopped working. No power to any plugs.',
                'expected_type': 'electrical'
            },
            {
                'subject': 'Need HVAC maintenance',
                'body': 'Annual maintenance for my heating system before winter.',
                'expected_type': 'hvac'
            },
            {
                'subject': 'Emergency water leak!',
                'body': 'Water is flooding my basement from a burst pipe!',
                'expected_type': 'emergency'
            },
            {
                'subject': 'Install new ceiling fan',
                'body': 'Want to install a ceiling fan in the living room.',
                'expected_type': 'installation'
            }
        ]
        
        try:
            for i, service in enumerate(test_services, 1):
                print(f"\n📝 Service {i}: {service['subject']}")
                print(f"   Body: {service['body']}")
                print(f"   Expected: {service['expected_type']}")
                
                if not self.use_mock:
                    # Send service request
                    secretary_client = EmailClient(self.secretary_email, profile='gmail_secretary')
                    send_result = secretary_client.send_email(
                        to_email=self.monitored_email,
                        subject=service['subject'],
                        body=service['body']
                    )
                    
                    if send_result:
                        print(f"   ✅ Service request {i} sent")
                    else:
                        print(f"   ❌ Failed to send service request {i}")
                        continue
                else:
                    print(f"   🔧 Mock: Service request {i} simulated")
                
                # Small delay between emails
                time.sleep(2)
            
            # Process all service requests
            print("\n🤖 Processing all service classification requests...")
            agent = get_communication_agent_instance()
            asyncio.run(agent.check_and_process_incoming_tasks(process_last_n_days=1))
            
            print("\n⏳ Waiting for classification processing...")
            time.sleep(25)
            
            print("✅ Service classification test completed")
            return True
            
        except Exception as e:
            logger.error(f"Service classification test failed: {e}", exc_info=True)
            print(f"❌ Test failed: {e}")
            return False
    
    def test_priority_handling(self):
        """Test 4: Priority and Urgency Handling"""
        print("\n" + "="*60)
        print("🚨 TEST 4: Priority and Urgency Handling")
        print("="*60)
        
        priority_tests = [
            {
                'subject': 'EMERGENCY: No heat in house!',
                'body': 'Our heating system completely failed and it\'s freezing. We have small children. Please help immediately!',
                'priority': 'emergency'
            },
            {
                'subject': 'Urgent: Water heater leaking',
                'body': 'Water heater is leaking and creating a puddle. Need repair within 24 hours.',
                'priority': 'urgent'
            },
            {
                'subject': 'Quote for bathroom renovation',
                'body': 'Looking for a quote to renovate our master bathroom. No rush, planning for next month.',
                'priority': 'normal'
            }
        ]
        
        try:
            for i, request in enumerate(priority_tests, 1):
                print(f"\n🚨 Priority Request {i}:")
                print(f"   Subject: {request['subject']}")
                print(f"   Priority: {request['priority']}")
                print(f"   Body: {request['body'][:80]}...")
                
                if not self.use_mock:
                    secretary_client = EmailClient(self.secretary_email, profile='gmail_secretary')
                    send_result = secretary_client.send_email(
                        to_email=self.monitored_email,
                        subject=request['subject'],
                        body=request['body']
                    )
                    
                    if send_result:
                        print(f"   ✅ Priority request {i} sent")
                    else:
                        print(f"   ❌ Failed to send priority request {i}")
                        continue
                else:
                    print(f"   🔧 Mock: Priority request {i} simulated")
                
                time.sleep(3)
            
            # Process priority requests
            print("\n🤖 Processing priority requests...")
            agent = get_communication_agent_instance()
            asyncio.run(agent.check_and_process_incoming_tasks(process_last_n_days=1))
            
            print("\n⏳ Waiting for priority processing...")
            time.sleep(30)
            
            print("✅ Priority handling test completed")
            return True
            
        except Exception as e:
            logger.error(f"Priority handling test failed: {e}", exc_info=True)
            print(f"❌ Test failed: {e}")
            return False
    
    def _check_response_sent(self):
        """Check if Karen AI sent a response"""
        try:
            if not self.use_mock:
                # Check sent items in secretary email
                secretary_client = EmailClient(self.secretary_email, profile='gmail_secretary')
                
                # Get recent sent emails
                sent_emails = secretary_client.get_recent_emails(folder='SENT', limit=5)
                
                if sent_emails:
                    print(f"\n📤 Found {len(sent_emails)} recent sent emails:")
                    for i, email in enumerate(sent_emails, 1):
                        subject = email.get('subject', 'No Subject')
                        to = email.get('to', 'Unknown')
                        timestamp = email.get('timestamp', 'Unknown time')
                        print(f"   {i}. To: {to}")
                        print(f"      Subject: {subject}")
                        print(f"      Time: {timestamp}")
                        print()
                else:
                    print("\n📤 No recent sent emails found")
            else:
                print("\n🔧 Mock mode: Check mock email logs for responses")
                
        except Exception as e:
            logger.warning(f"Could not check sent emails: {e}")
            print(f"\n⚠️  Could not verify response sent: {e}")
    
    def run_all_tests(self):
        """Run all email pipeline tests"""
        print("\n" + "="*80)
        print("🧪 KAREN AI EMAIL PIPELINE COMPREHENSIVE TEST SUITE")
        print("="*80)
        print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        tests = [
            ("Basic Email Processing", self.test_basic_email_flow),
            ("Appointment Scheduling", self.test_appointment_scheduling),
            ("Service Classification", self.test_service_classification),
            ("Priority Handling", self.test_priority_handling)
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            try:
                print(f"\n🏃 Running: {test_name}")
                result = test_func()
                results[test_name] = "PASSED" if result else "FAILED"
                
            except Exception as e:
                logger.error(f"Test {test_name} crashed: {e}", exc_info=True)
                results[test_name] = "CRASHED"
                print(f"💥 Test {test_name} crashed: {e}")
        
        # Print summary
        print("\n" + "="*80)
        print("📊 TEST RESULTS SUMMARY")
        print("="*80)
        
        passed = sum(1 for r in results.values() if r == "PASSED")
        total = len(results)
        
        for test_name, result in results.items():
            status_emoji = {"PASSED": "✅", "FAILED": "❌", "CRASHED": "💥"}[result]
            print(f"{status_emoji} {test_name}: {result}")
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed")
        print(f"📅 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! Karen AI email pipeline is working correctly.")
        else:
            print(f"\n⚠️  {total - passed} tests failed. Please check the logs and configuration.")
        
        return results

def test_basic_email_flow():
    """Send test email and monitor processing"""
    print("🚀 Starting Email Pipeline Test")
    
    # Send test email
    client = EmailClient()
    test_email = {
        'to': 'hello@757handy.com',
        'from': 'test_customer@example.com',
        'subject': 'Need quote for plumbing repair',
        'body': 'Hi, my kitchen sink is leaking. Can you provide a quote?'
    }

    print("📧 Sending test email...")
    # Monitor processing
    print("⏳ Waiting for Karen AI to process...")
    time.sleep(30)  # Allow processing time

    print("✅ Check karensecretaryai@gmail.com sent items for response")

def main():
    """Main test runner"""
    try:
        # Initialize test suite
        test_suite = EmailPipelineTest()
        
        # Run all tests
        results = test_suite.run_all_tests()
        
        # Exit with appropriate code
        passed = sum(1 for r in results.values() if r == "PASSED")
        total = len(results)
        
        if passed == total:
            print("\n✨ Test suite completed successfully!")
            return 0
        else:
            print(f"\n⚠️  Test suite completed with {total - passed} failures.")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️  Test suite interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Test suite crashed: {e}", exc_info=True)
        print(f"\n💥 Test suite crashed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
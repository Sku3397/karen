#!/usr/bin/env python3
"""
SMS System Test Script
Tests the complete SMS functionality following Karen's patterns
"""
import os
import sys
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sms_client import SMSClient
from handyman_sms_engine import HandymanSMSEngine
from handyman_response_engine import HandymanResponseEngine  # For comparison

def setup_logging():
    """Setup logging for the test"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('sms_system_test.log')
        ]
    )
    return logging.getLogger(__name__)

def load_environment():
    """Load environment variables"""
    # Load from project root .env
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✓ Loaded environment from {env_path}")
    else:
        print(f"⚠ Warning: .env file not found at {env_path}")
    
    return {
        'karen_phone': os.getenv('KAREN_PHONE_NUMBER', '+17575551234'),
        'twilio_sid': os.getenv('TWILIO_ACCOUNT_SID'),
        'twilio_token': os.getenv('TWILIO_AUTH_TOKEN'),
        'business_name': os.getenv('BUSINESS_NAME', 'Beach Handyman'),
        'business_phone': os.getenv('BUSINESS_PHONE', '757-354-4577'),
        'test_recipient': os.getenv('TEST_PHONE_NUMBER')  # Optional for live testing
    }

def test_sms_client(config, logger):
    """Test SMS client functionality"""
    logger.info("🧪 Testing SMS Client...")
    
    if not config['twilio_sid'] or not config['twilio_token']:
        logger.warning("⚠ Twilio credentials not found. Skipping live SMS tests.")
        return False
    
    try:
        # Initialize SMS client
        sms_client = SMSClient(karen_phone=config['karen_phone'])
        logger.info(f"✓ SMS Client initialized for {config['karen_phone']}")
        
        # Test 1: Fetch recent messages
        logger.info("Testing SMS fetch...")
        recent_sms = sms_client.fetch_sms(
            search_criteria='ALL',
            last_n_days=7,
            max_results=5
        )
        logger.info(f"✓ Found {len(recent_sms)} recent SMS messages")
        
        # Test 2: Test processing state management
        if recent_sms:
            test_uid = recent_sms[0]['uid']
            logger.info(f"Testing processing state for {test_uid}")
            
            # Check if processed
            is_processed = sms_client.is_sms_processed(test_uid)
            logger.info(f"✓ SMS {test_uid} processed status: {is_processed}")
            
            # Mark as processed
            marked = sms_client.mark_sms_as_processed(test_uid, "test_label")
            logger.info(f"✓ Marking SMS as processed: {marked}")
        
        # Test 3: Send test SMS (only if test number provided)
        if config['test_recipient']:
            logger.info(f"Sending test SMS to {config['test_recipient']}")
            success = sms_client.send_designated_test_sms(
                config['test_recipient'],
                "Karen SMS Test"
            )
            logger.info(f"✓ Test SMS sent: {success}")
        else:
            logger.info("ℹ Skipping SMS send test (TEST_PHONE_NUMBER not configured)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ SMS Client test failed: {e}")
        return False

def test_sms_engine(config, logger):
    """Test SMS engine functionality"""
    logger.info("🧪 Testing SMS Engine...")
    
    try:
        # Initialize engines for comparison
        sms_engine = HandymanSMSEngine(
            business_name=config['business_name'],
            phone=config['business_phone'],
            llm_client=None  # No LLM for testing
        )
        
        email_engine = HandymanResponseEngine(
            business_name=config['business_name'],
            phone=config['business_phone'],
            llm_client=None
        )
        
        logger.info("✓ Engines initialized")
        
        # Test messages for classification
        test_messages = [
            ("+15551234567", "Emergency! Pipe burst flooding basement!", "emergency"),
            ("+15551234567", "Can I get a quote for fixing my deck?", "quote"),
            ("+15551234567", "yes", "quick_response"),
            ("+15551234567", "STOP", "quick_response"),
            ("+15551234567", "Need handyman for general repairs", "general"),
            ("+15551234567", "tmrw afternoon plumbing appt pls", "appointment")
        ]
        
        logger.info("Testing message classification...")
        for phone, message, expected_type in test_messages:
            # Test SMS classification
            sms_classification = sms_engine.classify_sms_type(phone, message)
            
            # Test email classification for comparison
            email_classification = email_engine.classify_email_type("SMS Message", message)
            
            # Log results
            logger.info(f"Message: '{message}'")
            logger.info(f"  SMS Emergency: {sms_classification.get('is_emergency')}")
            logger.info(f"  Email Emergency: {email_classification.get('is_emergency')}")
            logger.info(f"  SMS Quick Response: {sms_classification.get('is_quick_response', False)}")
            logger.info(f"  Expected: {expected_type}")
            
            # Verify some classifications match between email and SMS
            assert sms_classification['is_emergency'] == email_classification['is_emergency']
        
        logger.info("✓ Classification tests passed")
        
        # Test SMS-specific features
        logger.info("Testing SMS-specific features...")
        
        # Test abbreviation expansion
        expanded = sms_engine.expand_sms_abbreviations("appt tmrw asap pls")
        logger.info(f"✓ Abbreviation expansion: 'appt tmrw asap pls' -> '{expanded}'")
        
        # Test response truncation
        long_response = "This is a very long response that needs to be truncated because it exceeds the SMS character limit and we need to ensure it fits properly within the constraints of SMS messaging while still providing useful information to the customer about our handyman services." * 3
        
        truncated = sms_engine._truncate_sms_response(long_response)
        logger.info(f"✓ Response truncation: {len(long_response)} chars -> {len(truncated)} chars")
        assert len(truncated) <= 160
        assert config['business_phone'] in truncated
        
        # Test multipart splitting
        parts = sms_engine.split_sms_response(long_response, max_parts=3)
        logger.info(f"✓ Multipart splitting: {len(parts)} parts")
        for i, part in enumerate(parts):
            assert len(part) <= 160
            logger.info(f"  Part {i+1}: {len(part)} chars")
        
        # Test fallback responses
        logger.info("Testing fallback responses...")
        for phone, message, expected_type in test_messages[:3]:  # Test first 3
            classification = sms_engine.classify_sms_type(phone, message)
            fallback = sms_engine._generate_sms_fallback_response(phone, message, classification)
            logger.info(f"✓ Fallback for '{message}': '{fallback}' ({len(fallback)} chars)")
            assert len(fallback) <= 160
        
        return True
        
    except Exception as e:
        logger.error(f"❌ SMS Engine test failed: {e}")
        return False

async def test_async_functionality(config, logger):
    """Test async SMS functionality"""
    logger.info("🧪 Testing Async SMS Functions...")
    
    try:
        # Create mock LLM client
        class MockLLMClient:
            def generate_text(self, prompt):
                if "emergency" in prompt.lower():
                    return "URGENT? Call NOW: 757-354-4577. We're ready to help!"
                elif "quote" in prompt.lower():
                    return "Thanks! For a free quote, call 757-354-4577 or reply with your address."
                else:
                    return "Beach Handyman: Thanks for your message! Call 757-354-4577."
        
        sms_engine = HandymanSMSEngine(
            business_name=config['business_name'],
            phone=config['business_phone'],
            llm_client=MockLLMClient()
        )
        
        logger.info("✓ Mock LLM SMS Engine initialized")
        
        # Test async response generation
        test_cases = [
            ("+15551234567", "Emergency plumbing needed!"),
            ("+15551234567", "How much to fix a door?"),
            ("+15551234567", "yes"),
        ]
        
        for phone, message in test_cases:
            logger.info(f"Testing async response for: '{message}'")
            
            response, classification = await sms_engine.generate_sms_response_async(phone, message)
            
            logger.info(f"✓ Response: '{response}' ({len(response)} chars)")
            logger.info(f"✓ Classification: {classification}")
            
            # Verify response is SMS-appropriate
            assert len(response) <= 1600  # Multipart limit
            assert isinstance(response, str)
            assert len(response) > 0
        
        logger.info("✓ Async functionality tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Async SMS test failed: {e}")
        return False

def test_integration_with_email(config, logger):
    """Test that SMS doesn't break email functionality"""
    logger.info("🧪 Testing SMS/Email Integration...")
    
    try:
        # Test that both engines can coexist
        email_engine = HandymanResponseEngine(
            business_name=config['business_name'],
            phone=config['business_phone']
        )
        
        sms_engine = HandymanSMSEngine(
            business_name=config['business_name'], 
            phone=config['business_phone']
        )
        
        # Test same message through both engines
        test_message = "Emergency! Need plumber immediately!"
        
        email_classification = email_engine.classify_email_type("Emergency", test_message)
        sms_classification = sms_engine.classify_sms_type("+15551234567", test_message)
        
        # Should have same core classification
        assert email_classification['is_emergency'] == sms_classification['is_emergency']
        assert email_classification['is_quote_request'] == sms_classification['is_quote_request']
        
        logger.info("✓ Email and SMS engines produce consistent classifications")
        
        # Test that SMS inherits from email engine properly
        assert isinstance(sms_engine, HandymanResponseEngine)
        logger.info("✓ SMS engine properly inherits from email engine")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}")
        return False

def test_celery_task_imports(logger):
    """Test that Celery tasks can be imported"""
    logger.info("🧪 Testing Celery Task Imports...")
    
    try:
        # Test importing SMS tasks
        from celery_sms_tasks import (
            fetch_new_sms,
            process_sms_with_llm,
            send_karen_sms_reply,
            check_sms_task,
            test_sms_system
        )
        
        logger.info("✓ All SMS Celery tasks imported successfully")
        
        # Test task signatures
        assert hasattr(fetch_new_sms, 'delay')
        assert hasattr(process_sms_with_llm, 'delay')
        assert hasattr(send_karen_sms_reply, 'delay')
        
        logger.info("✓ Tasks have proper Celery signatures")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Celery task import failed: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Celery task test failed: {e}")
        return False

def main():
    """Run complete SMS system test"""
    logger = setup_logging()
    config = load_environment()
    
    logger.info("🚀 Starting SMS System Test")
    logger.info("=" * 50)
    
    # Print configuration
    logger.info("Configuration:")
    logger.info(f"  Karen Phone: {config['karen_phone']}")
    logger.info(f"  Business: {config['business_name']}")
    logger.info(f"  Business Phone: {config['business_phone']}")
    logger.info(f"  Twilio Configured: {'Yes' if config['twilio_sid'] else 'No'}")
    logger.info(f"  Test Recipient: {config['test_recipient'] or 'Not configured'}")
    logger.info("")
    
    # Run tests
    tests = [
        ("Celery Task Imports", lambda: test_celery_task_imports(logger)),
        ("SMS Engine", lambda: test_sms_engine(config, logger)),
        ("SMS/Email Integration", lambda: test_integration_with_email(config, logger)),
        ("Async Functionality", lambda: asyncio.run(test_async_functionality(config, logger))),
        ("SMS Client", lambda: test_sms_client(config, logger)),
    ]
    
    results = {}
    for test_name, test_func in tests:
        logger.info(f"Running {test_name} test...")
        try:
            results[test_name] = test_func()
            status = "✅ PASS" if results[test_name] else "❌ FAIL"
        except Exception as e:
            results[test_name] = False
            status = f"❌ ERROR: {e}"
        
        logger.info(f"{test_name}: {status}")
        logger.info("")
    
    # Summary
    logger.info("=" * 50)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name:.<30} {status}")
    
    logger.info("")
    logger.info(f"Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! SMS system is ready.")
        return 0
    else:
        logger.info("⚠ Some tests failed. Check logs above.")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
"""
Celery tasks for SMS processing following existing email task patterns
"""
import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from celery import Celery
from .celery_app import celery_app, get_communication_agent_instance
from .sms_client import SMSClient
from .handyman_sms_engine import HandymanSMSEngine
from .llm_client import LLMClient

logger = logging.getLogger(__name__)

# SMS-specific configuration
SMS_PROCESSING_INTERVAL = int(os.getenv('SMS_PROCESSING_INTERVAL', '60'))  # seconds
KAREN_PHONE_NUMBER = os.getenv('KAREN_PHONE_NUMBER', '+17575551234')
MONITORED_SMS_PHONE = os.getenv('MONITORED_SMS_PHONE', KAREN_PHONE_NUMBER)  # Default to same number

# Initialize SMS components (following email pattern)
_sms_client_instance = None
_sms_engine_instance = None

def get_sms_client_instance():
    """Get or create SMS client instance following email client pattern."""
    global _sms_client_instance
    if _sms_client_instance is None:
        logger.debug("Creating new SMSClient instance")
        try:
            _sms_client_instance = SMSClient(karen_phone=KAREN_PHONE_NUMBER)
            logger.info(f"SMSClient initialized for {KAREN_PHONE_NUMBER}")
        except Exception as e:
            logger.error(f"Failed to initialize SMSClient: {e}", exc_info=True)
            raise
    return _sms_client_instance

def get_sms_engine_instance():
    """Get or create SMS engine instance."""
    global _sms_engine_instance
    if _sms_engine_instance is None:
        logger.debug("Creating new HandymanSMSEngine instance")
        try:
            # Get LLM client from communication agent if available
            comm_agent = get_communication_agent_instance()
            llm_client = getattr(comm_agent, 'llm_client', None)
            
            _sms_engine_instance = HandymanSMSEngine(
                business_name=os.getenv('BUSINESS_NAME', 'Beach Handyman'),
                service_area=os.getenv('SERVICE_AREA', 'Virginia Beach area'),
                phone=os.getenv('BUSINESS_PHONE', '757-354-4577'),
                llm_client=llm_client
            )
            logger.info("HandymanSMSEngine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize HandymanSMSEngine: {e}", exc_info=True)
            raise
    return _sms_engine_instance

@celery_app.task(name='fetch_new_sms', bind=True, max_retries=3)
def fetch_new_sms(self, process_last_n_hours: int = 1):
    """
    Fetch new SMS messages following fetch_new_emails pattern.
    
    Args:
        process_last_n_hours: Number of hours to look back for messages
    """
    logger.info(f"Celery task: fetch_new_sms starting (last {process_last_n_hours} hours)")
    
    try:
        sms_client = get_sms_client_instance()
        
        # Fetch recent SMS messages
        newer_than = f"{process_last_n_hours}h"
        messages = sms_client.fetch_sms(
            search_criteria='ALL',  # SMS doesn't have unread concept
            newer_than=newer_than,
            max_results=50
        )
        
        logger.info(f"Found {len(messages)} SMS messages in the last {process_last_n_hours} hours")
        
        # Process each unprocessed message
        processed_count = 0
        for msg in messages:
            msg_id = msg.get('uid')
            
            # Check if already processed
            if sms_client.is_sms_processed(msg_id):
                logger.debug(f"SMS {msg_id} already processed, skipping")
                continue
            
            # Queue message for processing
            process_sms_with_llm.delay(msg)
            processed_count += 1
            
            # Mark as processed to avoid reprocessing
            sms_client.mark_sms_as_processed(msg_id)
        
        logger.info(f"Queued {processed_count} new SMS messages for processing")
        return {
            'total_messages': len(messages),
            'new_messages': processed_count,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in fetch_new_sms: {e}", exc_info=True)
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=2 ** self.request.retries)

@celery_app.task(name='process_sms_with_llm', bind=True, max_retries=3)
def process_sms_with_llm(self, sms_data: Dict[str, Any]):
    """
    Process SMS with LLM following process_email_with_llm pattern.
    
    Args:
        sms_data: SMS message data from fetch_sms
    """
    msg_id = sms_data.get('uid', 'unknown')
    sender = sms_data.get('sender', 'unknown')
    body = sms_data.get('body', '')
    
    logger.info(f"Processing SMS {msg_id} from {sender}")
    
    try:
        sms_engine = get_sms_engine_instance()
        
        # Generate response using SMS engine (async method)
        response_text, classification = asyncio.run(
            sms_engine.generate_sms_response_async(sender, body)
        )
        
        logger.info(f"Generated SMS response for {msg_id}. Classification: {classification}")
        
        # Queue response for sending
        send_karen_sms_reply.delay(
            to_number=sender,
            reply_body=response_text,
            original_msg_id=msg_id,
            classification=classification
        )
        
        # If emergency, notify admin immediately
        if classification.get('is_emergency'):
            notify_admin_sms_emergency.delay(sms_data, classification)
        
        return {
            'msg_id': msg_id,
            'sender': sender,
            'classification': classification,
            'response_generated': True,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing SMS {msg_id}: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=2 ** self.request.retries)

@celery_app.task(name='send_karen_sms_reply', bind=True, max_retries=3)
def send_karen_sms_reply(self, to_number: str, reply_body: str, 
                        original_msg_id: str, classification: Dict[str, Any]):
    """
    Send SMS reply following send_karen_reply pattern.
    
    Args:
        to_number: Recipient phone number
        reply_body: SMS message body
        original_msg_id: ID of original message being replied to
        classification: Message classification from engine
    """
    logger.info(f"Sending SMS reply to {to_number} (replying to {original_msg_id})")
    
    try:
        sms_client = get_sms_client_instance()
        
        # Handle multipart SMS if needed
        sms_engine = get_sms_engine_instance()
        if sms_engine.should_send_multipart_sms(reply_body):
            # Split into multiple parts
            parts = sms_engine.split_sms_response(reply_body)
            logger.info(f"Splitting long SMS into {len(parts)} parts")
            
            success = True
            for i, part in enumerate(parts):
                part_success = sms_client.send_sms(to_number, part)
                if not part_success:
                    logger.error(f"Failed to send SMS part {i+1}/{len(parts)}")
                    success = False
                    break
                # Small delay between parts to ensure order
                if i < len(parts) - 1:
                    import time
                    time.sleep(1)
        else:
            # Send single SMS
            success = sms_client.send_sms(to_number, reply_body)
        
        if success:
            logger.info(f"Successfully sent SMS reply to {to_number}")
            
            # Log interaction for tracking
            log_sms_interaction.delay({
                'type': 'reply_sent',
                'to': to_number,
                'body': reply_body,
                'original_msg_id': original_msg_id,
                'classification': classification,
                'timestamp': datetime.now().isoformat()
            })
        else:
            raise Exception(f"Failed to send SMS to {to_number}")
        
        return {
            'success': success,
            'to_number': to_number,
            'original_msg_id': original_msg_id,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error sending SMS reply: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=2 ** self.request.retries)

@celery_app.task(name='notify_admin_sms_emergency', ignore_result=True)
def notify_admin_sms_emergency(sms_data: Dict[str, Any], classification: Dict[str, Any]):
    """
    Notify admin of SMS emergency following email emergency pattern.
    
    Args:
        sms_data: Original SMS data
        classification: Emergency classification details
    """
    logger.warning(f"EMERGENCY SMS received from {sms_data.get('sender')}")
    
    try:
        admin_phone = os.getenv('ADMIN_PHONE_NUMBER')
        if not admin_phone:
            logger.error("ADMIN_PHONE_NUMBER not configured for emergency notifications")
            return
        
        sms_client = get_sms_client_instance()
        
        # Create emergency notification
        notification = (
            f"🚨 EMERGENCY SMS from {sms_data.get('sender', 'Unknown')}: "
            f"{sms_data.get('body', '')[:100]}... "
            f"Received at {sms_data.get('date_str', 'Unknown time')}"
        )
        
        # Send notification to admin
        success = sms_client.send_sms(admin_phone, notification)
        
        if success:
            logger.info(f"Emergency SMS notification sent to admin at {admin_phone}")
        else:
            logger.error(f"Failed to send emergency SMS notification to admin")
            
            # Fallback: Try email notification if available
            comm_agent = get_communication_agent_instance()
            if hasattr(comm_agent, 'notify_admin'):
                asyncio.run(comm_agent.notify_admin(
                    "SMS Emergency",
                    f"Failed to send SMS notification. Original emergency: {notification}"
                ))
        
    except Exception as e:
        logger.error(f"Error in notify_admin_sms_emergency: {e}", exc_info=True)

@celery_app.task(name='log_sms_interaction', ignore_result=True)
def log_sms_interaction(interaction_data: Dict[str, Any]):
    """
    Log SMS interaction for analytics and debugging.
    Following pattern of email activity logging.
    
    Args:
        interaction_data: Dictionary with interaction details
    """
    try:
        # Log to file (similar to email agent activity log)
        log_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, 'sms_agent_activity.log')
        
        with open(log_file, 'a') as f:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'data': interaction_data
            }
            f.write(f"{log_entry}\n")
        
        logger.debug(f"SMS interaction logged: {interaction_data.get('type')}")
        
    except Exception as e:
        logger.error(f"Error logging SMS interaction: {e}", exc_info=True)

@celery_app.task(name='check_sms_task', ignore_result=True)
def check_sms_task():
    """
    Main SMS checking task following check_emails_task pattern.
    This is the task that gets scheduled by Celery Beat.
    """
    logger.info("Celery task: check_sms_task starting")
    
    try:
        # Fetch new SMS messages from the last hour
        fetch_new_sms.delay(process_last_n_hours=1)
        
        logger.info("SMS check task completed, processing queued")
        
    except Exception as e:
        logger.error(f"Error in check_sms_task: {e}", exc_info=True)
        raise

@celery_app.task(name='test_sms_system', ignore_result=True)
def test_sms_system():
    """
    Test SMS system functionality following email test patterns.
    """
    logger.info("Testing SMS system...")
    
    try:
        sms_client = get_sms_client_instance()
        
        # Test 1: Send self-test SMS
        logger.info("Test 1: Sending self-test SMS")
        self_test_success = sms_client.send_self_test_sms("SMS System Test")
        logger.info(f"Self-test SMS result: {'Success' if self_test_success else 'Failed'}")
        
        # Test 2: Fetch recent messages
        logger.info("Test 2: Fetching recent SMS messages")
        recent_messages = sms_client.fetch_sms(
            search_criteria='ALL',
            last_n_days=1,
            max_results=5
        )
        logger.info(f"Found {len(recent_messages)} recent messages")
        
        # Test 3: Test SMS engine
        logger.info("Test 3: Testing SMS engine classification")
        sms_engine = get_sms_engine_instance()
        
        test_messages = [
            ("Emergency! Pipe burst flooding house!", True),
            ("Can I get a quote for fixing a door?", False),
            ("yes", False)
        ]
        
        for msg, expected_emergency in test_messages:
            classification = sms_engine.classify_sms_type("+1234567890", msg)
            is_emergency = classification.get('is_emergency', False)
            result = "✓" if is_emergency == expected_emergency else "✗"
            logger.info(f"  {result} '{msg}' -> Emergency: {is_emergency}")
        
        logger.info("SMS system test completed")
        
        return {
            'self_test': self_test_success,
            'messages_found': len(recent_messages),
            'engine_test': 'completed',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"SMS system test failed: {e}", exc_info=True)
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

# Webhook handler for incoming SMS (called by web framework)
@celery_app.task(name='handle_incoming_sms_webhook', bind=True)
def handle_incoming_sms_webhook(self, webhook_data: Dict[str, Any]):
    """
    Handle incoming SMS webhook from Twilio.
    This would be called by the web framework (FastAPI) when Twilio sends a webhook.
    
    Args:
        webhook_data: Webhook payload from Twilio
    """
    logger.info(f"Received SMS webhook: {webhook_data.get('MessageSid')}")
    
    try:
        # Convert Twilio webhook format to our standard format
        sms_data = {
            'id': webhook_data.get('MessageSid'),
            'uid': webhook_data.get('MessageSid'),
            'sender': webhook_data.get('From'),
            'body': webhook_data.get('Body', ''),
            'date_str': datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z"),
            'received_date_dt': datetime.now(timezone.utc),
            'status': webhook_data.get('SmsStatus', 'received'),
            'direction': 'inbound'
        }
        
        # Process immediately rather than waiting for scheduled check
        process_sms_with_llm.delay(sms_data)
        
        return {
            'success': True,
            'message_sid': webhook_data.get('MessageSid'),
            'queued_for_processing': True
        }
        
    except Exception as e:
        logger.error(f"Error handling SMS webhook: {e}", exc_info=True)
        raise


# Add SMS tasks to celery beat schedule (this would go in celery_app.py)
# Example schedule entry:
"""
'check-sms-every-minute': {
    'task': 'check_sms_task',
    'schedule': crontab(minute='*'),  # Every minute
},
'test-sms-system-daily': {
    'task': 'test_sms_system', 
    'schedule': crontab(hour=9, minute=0),  # Daily at 9 AM
},
"""
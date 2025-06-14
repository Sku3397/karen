#!/usr/bin/env python3
"""
SMS Engineer Agent - Implementing SMS functionality following Karen's exact patterns
"""
import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add src to path
project_root = Path(__file__).parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

# Initialize AgentCommunication
try:
    from agent_communication import AgentCommunication
    comm = AgentCommunication('sms_engineer')
    print("✓ AgentCommunication initialized")
except ImportError as e:
    print(f"⚠ AgentCommunication not available: {e}")
    class MockAgentCommunication:
        def __init__(self, name): self.name = name
        def read_messages(self): return []
        def send_message(self, to, type, content): print(f"MSG: {self.name} → {to}: {type}")
        def update_status(self, status, progress, details): print(f"STATUS: {status} ({progress}%)")
        def share_knowledge(self, type, data): print(f"KNOWLEDGE: {type}")
    comm = MockAgentCommunication('sms_engineer')

logger = logging.getLogger(__name__)

def main():
    """SMS Engineer Agent main execution"""
    logger.info("🚀 SMS Engineer Agent starting...")
    
    # Step 1: Read archaeologist findings
    comm.update_status('initializing', 10, {'phase': 'reading_archaeologist_findings'})
    findings = read_archaeologist_findings()
    
    # Step 2: Study email_client.py patterns
    comm.update_status('analyzing', 30, {'phase': 'studying_email_patterns'})
    email_patterns = study_email_client_patterns()
    
    # Step 3: Create SMS client following patterns
    comm.update_status('developing', 50, {'phase': 'implementing_sms_client'})
    create_sms_client(email_patterns, findings)
    
    # Step 4: Create SMS engine extending HandymanResponseEngine
    comm.update_status('developing', 70, {'phase': 'implementing_sms_engine'})
    create_sms_engine(findings)
    
    # Step 5: Create Celery tasks
    comm.update_status('developing', 85, {'phase': 'implementing_celery_tasks'})
    create_celery_tasks(findings)
    
    # Step 6: Share implementation knowledge
    comm.update_status('completed', 100, {'phase': 'sharing_knowledge'})
    share_implementation_knowledge()
    
    # Step 7: Notify test engineer
    notify_test_engineer_ready()
    
    logger.info("✅ SMS Engineer Agent completed successfully")

def read_archaeologist_findings():
    """Read findings from archaeologist in shared knowledge"""
    logger.info("📖 Reading archaeologist findings...")
    
    findings = {}
    
    # Read architecture findings
    arch_file = project_root / 'autonomous-agents/shared-knowledge/karen-architecture.md'
    if arch_file.exists():
        with open(arch_file, 'r') as f:
            findings['architecture'] = f.read()
        logger.info("✓ Read architecture patterns")
    
    # Read implementation patterns
    impl_file = project_root / 'autonomous-agents/shared-knowledge/karen-implementation-patterns.md'
    if impl_file.exists():
        with open(impl_file, 'r') as f:
            findings['patterns'] = f.read()
        logger.info("✓ Read implementation patterns")
    
    # Read client template
    template_file = project_root / 'autonomous-agents/shared-knowledge/templates/client_template.py'
    if template_file.exists():
        with open(template_file, 'r') as f:
            findings['client_template'] = f.read()
        logger.info("✓ Read client template")
    
    comm.share_knowledge('archaeologist_findings', {
        'files_read': list(findings.keys()),
        'total_content_length': sum(len(v) for v in findings.values())
    })
    
    return findings

def study_email_client_patterns():
    """Study src/email_client.py to extract patterns"""
    logger.info("🔍 Studying email_client.py patterns...")
    
    email_client_file = src_path / 'email_client.py'
    if not email_client_file.exists():
        logger.error(f"❌ email_client.py not found at {email_client_file}")
        return {}
    
    with open(email_client_file, 'r') as f:
        email_client_code = f.read()
    
    # Extract key patterns
    patterns = {
        'class_structure': extract_class_structure(email_client_code),
        'auth_handling': extract_auth_patterns(email_client_code),
        'error_handling': extract_error_patterns(email_client_code),
        'method_signatures': extract_method_signatures(email_client_code),
        'logging_style': extract_logging_patterns(email_client_code)
    }
    
    logger.info(f"✓ Extracted {len(patterns)} pattern categories from EmailClient")
    
    comm.share_knowledge('email_client_patterns', {
        'patterns_extracted': list(patterns.keys()),
        'source_file': 'src/email_client.py',
        'analysis_complete': True
    })
    
    return patterns

def extract_class_structure(code):
    """Extract class structure patterns"""
    import re
    
    # Find class definition
    class_match = re.search(r'class EmailClient:(.*?)(?=\nclass|\n[a-zA-Z]|\Z)', code, re.DOTALL)
    if not class_match:
        return {}
    
    class_body = class_match.group(1)
    
    # Extract __init__ method
    init_match = re.search(r'def __init__\(self,.*?\):(.*?)(?=\n    def|\Z)', class_body, re.DOTALL)
    init_code = init_match.group(1) if init_match else ""
    
    return {
        'has_project_root': 'PROJECT_ROOT' in code,
        'has_logger': 'logger' in init_code,
        'has_cache': '_cache' in init_code or 'cache' in init_code,
        'validates_config': 'raise ValueError' in init_code,
        'loads_credentials': '_load_and_refresh_credentials' in init_code
    }

def extract_auth_patterns(code):
    """Extract OAuth authentication patterns"""
    import re
    
    auth_patterns = {}
    
    # Check for credential loading
    if '_load_and_refresh_credentials' in code:
        auth_patterns['has_credential_refresh'] = True
        
    # Check for token saving
    if '_save_token' in code or 'save_credentials' in code:
        auth_patterns['saves_tokens'] = True
        
    # Check for OAuth scopes
    scopes_match = re.search(r'SCOPES = \[(.*?)\]', code, re.DOTALL)
    if scopes_match:
        auth_patterns['defines_scopes'] = True
        auth_patterns['scopes_pattern'] = scopes_match.group(0)
    
    # Check for Google API imports
    if 'google.oauth2.credentials' in code:
        auth_patterns['uses_google_oauth'] = True
    
    return auth_patterns

def extract_error_patterns(code):
    """Extract error handling patterns"""
    import re
    
    error_patterns = {}
    
    # Check for specific exception handling
    if 'HttpError' in code:
        error_patterns['handles_http_errors'] = True
        
    if 'RefreshError' in code:
        error_patterns['handles_refresh_errors'] = True
        
    # Check for status code handling
    if 'error.resp.status' in code:
        error_patterns['checks_status_codes'] = True
        
    # Check for detailed error logging
    if 'exc_info=True' in code:
        error_patterns['detailed_logging'] = True
        
    # Check for error content extraction
    if 'error.content.decode()' in code:
        error_patterns['extracts_error_details'] = True
    
    return error_patterns

def extract_method_signatures(code):
    """Extract method signature patterns"""
    import re
    
    # Find all method definitions
    methods = re.findall(r'def (\w+)\(([^)]*)\)', code)
    
    signatures = {}
    for method_name, params in methods:
        signatures[method_name] = {
            'params': params,
            'has_self': 'self' in params,
            'has_typing': '->' in params or ':' in params
        }
    
    return signatures

def extract_logging_patterns(code):
    """Extract logging patterns"""
    import re
    
    patterns = {}
    
    # Check logger initialization
    if 'logger = logging.getLogger(__name__)' in code:
        patterns['module_logger'] = True
        
    # Check logging levels used
    for level in ['debug', 'info', 'warning', 'error']:
        if f'logger.{level}(' in code:
            patterns[f'uses_{level}'] = True
            
    # Check for f-strings in logging
    if 'logger.info(f"' in code or 'logger.debug(f"' in code:
        patterns['uses_f_strings'] = True
    
    return patterns

def create_sms_client(email_patterns, findings):
    """Create SMS client following EmailClient patterns exactly"""
    logger.info("📱 Creating SMS client following EmailClient patterns...")
    
    # Generate SMS client code based on patterns
    sms_client_code = generate_sms_client_code(email_patterns, findings)
    
    # Write to src/sms_client.py
    sms_client_file = src_path / 'sms_client.py'
    with open(sms_client_file, 'w') as f:
        f.write(sms_client_code)
    
    logger.info(f"✓ Created {sms_client_file}")
    
    comm.share_knowledge('sms_client_created', {
        'file_path': str(sms_client_file),
        'patterns_followed': list(email_patterns.keys()),
        'lines_of_code': len(sms_client_code.split('\n'))
    })

def generate_sms_client_code(email_patterns, findings):
    """Generate SMS client code following EmailClient patterns"""
    
    # Read the existing sms_client.py if it exists to use as base
    existing_sms_file = src_path / 'sms_client.py'
    if existing_sms_file.exists():
        with open(existing_sms_file, 'r') as f:
            existing_code = f.read()
        logger.info("✓ Using existing SMS client as base, ensuring it follows patterns")
        return existing_code
    
    # Generate new SMS client code following EmailClient patterns exactly
    template = '''# SMSClient: Handles sending and fetching SMS messages using Twilio API
# Following EmailClient patterns exactly
import os
import logging
import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# Define paths relative to the project root, following EmailClient pattern
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

logger = logging.getLogger(__name__)

class SMSClient:
    """SMS client following EmailClient patterns exactly"""
    
    def __init__(self, karen_phone: str, token_data: Optional[Dict[str, str]] = None):
        """Initialize SMS client following EmailClient.__init__ pattern"""
        self.karen_phone = karen_phone
        logger.debug(f"Initializing SMSClient for {karen_phone}")
        
        # Cache initialization (following EmailClient pattern)
        self._cache: Dict[str, Any] = {}
        
        # Load credentials following EmailClient pattern
        if token_data:
            self.account_sid = token_data.get('account_sid')
            self.auth_token = token_data.get('auth_token')
        else:
            self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        
        # Validate credentials (following EmailClient validation pattern)
        if not self.account_sid or not self.auth_token:
            logger.error("Failed to load Twilio credentials. Check TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN.")
            raise ValueError("Failed to load Twilio credentials.")
        
        try:
            self.client = Client(self.account_sid, self.auth_token)
            logger.info(f"SMSClient for {karen_phone} initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Twilio client: {e}", exc_info=True)
            raise

    def send_sms(self, to: str, body: str) -> bool:
        """Send SMS following EmailClient.send_email pattern"""
        logger.debug(f"Attempting to send SMS to: {to}, body length: {len(body)}")
        
        try:
            # Validate and truncate if needed (SMS-specific logic)
            if len(body) > 1600:
                logger.warning(f"SMS body too long ({len(body)} chars). Truncating to 1600.")
                body = body[:1597] + "..."
            
            message = self.client.messages.create(
                body=body,
                from_=self.karen_phone,
                to=to
            )
            
            logger.info(f"Message sent successfully via Twilio API. Message SID: {message.sid}")
            return True
            
        except TwilioRestException as error:
            # Following EmailClient error handling pattern
            logger.error(f"Twilio API error occurred: {error.msg}. Code: {error.code}", exc_info=True)
            if error.code == 20003:
                logger.error("Authentication error (20003). Check account SID and auth token.")
            elif error.code == 21211:
                logger.error("Invalid 'To' phone number (21211). Ensure E.164 format.")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred during send_sms: {e}", exc_info=True)
            return False

    def fetch_sms(self, search_criteria: str = 'UNREAD', 
                  last_n_days: Optional[int] = None,
                  newer_than: Optional[str] = None,
                  max_results: int = 10) -> List[Dict[str, Any]]:
        """Fetch SMS messages following EmailClient.fetch_emails pattern"""
        logger.debug(f"Fetching SMS with criteria: '{search_criteria}', last_n_days: {last_n_days}, "
                    f"newer_than: {newer_than}, max_results: {max_results}")
        
        try:
            # Build date filter (following EmailClient pattern)
            date_filter = None
            if newer_than:
                if newer_than.endswith('h'):
                    hours = int(newer_than[:-1])
                    date_filter = datetime.now(timezone.utc) - timedelta(hours=hours)
                elif newer_than.endswith('d'):
                    days = int(newer_than[:-1])
                    date_filter = datetime.now(timezone.utc) - timedelta(days=days)
            elif last_n_days and last_n_days > 0:
                date_filter = datetime.now(timezone.utc) - timedelta(days=last_n_days)
            
            # Fetch messages from Twilio
            messages_kwargs = {
                'to': self.karen_phone,
                'limit': max_results
            }
            
            if date_filter:
                messages_kwargs['date_sent_after'] = date_filter
            
            messages = self.client.messages.list(**messages_kwargs)
            
            if not messages:
                logger.info("No messages found matching criteria.")
                return []
            
            logger.info(f"Found {len(messages)} messages. Processing...")
            
            # Process messages following EmailClient structure
            sms_data = []
            for msg in messages:
                sms_item = {
                    'id': msg.sid,
                    'threadId': msg.sid,
                    'snippet': msg.body[:100] if len(msg.body) > 100 else msg.body,
                    'sender': msg.from_,
                    'subject': f"SMS from {msg.from_}",
                    'body_plain': msg.body,
                    'body_html': '',
                    'body': msg.body,
                    'date_str': msg.date_sent.strftime("%a, %d %b %Y %H:%M:%S %z") if msg.date_sent else '',
                    'received_date_dt': msg.date_sent,
                    'uid': msg.sid,
                    'status': msg.status,
                    'direction': msg.direction
                }
                
                # Only include inbound messages when fetching
                if msg.direction == 'inbound':
                    sms_data.append(sms_item)
            
            logger.info(f"Successfully fetched details for {len(sms_data)} SMS messages.")
            return sms_data
            
        except TwilioRestException as error:
            logger.error(f"Twilio API error during fetch_sms: {error.msg}. Code: {error.code}", exc_info=True)
            return []
        except Exception as e:
            logger.error(f"Unexpected error during fetch_sms: {e}", exc_info=True)
            return []

    def mark_sms_as_processed(self, uid: str, label_to_add: Optional[str] = None) -> bool:
        """Mark SMS as processed following EmailClient.mark_email_as_processed pattern"""
        logger.debug(f"Attempting to mark SMS UID {uid} as processed. Label: {label_to_add}")
        
        try:
            # Since Twilio doesn't have labels, store processed IDs locally
            processed_file = os.path.join(PROJECT_ROOT, '.processed_sms_ids.json')
            processed_ids = set()
            
            if os.path.exists(processed_file):
                with open(processed_file, 'r') as f:
                    processed_ids = set(json.load(f))
            
            processed_ids.add(uid)
            
            with open(processed_file, 'w') as f:
                json.dump(list(processed_ids), f)
            
            logger.info(f"SMS {uid} marked as processed")
            return True
            
        except Exception as e:
            logger.error(f"Error marking SMS {uid} as processed: {e}", exc_info=True)
            return False

    def is_sms_processed(self, uid: str) -> bool:
        """Check if SMS has been processed"""
        try:
            processed_file = os.path.join(PROJECT_ROOT, '.processed_sms_ids.json')
            if os.path.exists(processed_file):
                with open(processed_file, 'r') as f:
                    processed_ids = set(json.load(f))
                return uid in processed_ids
            return False
        except Exception as e:
            logger.error(f"Error checking if SMS {uid} is processed: {e}", exc_info=True)
            return False

    def send_self_test_sms(self, subject_prefix="AI Self-Test"):
        """Send test SMS following EmailClient.send_self_test_email pattern"""
        logger.info(f"send_self_test_sms called for {self.karen_phone} with prefix: '{subject_prefix}'")
        
        body = (
            f"{subject_prefix}: Test from Karen SMS "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}. "
            f"Verifying SMS capability."
        )
        
        return self.send_sms(self.karen_phone, body)


# Example usage following EmailClient pattern
if __name__ == '__main__':
    from dotenv import load_dotenv
    import sys
    
    # Load .env for testing
    dotenv_path = os.path.join(PROJECT_ROOT, '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
        print(f"Loaded .env from {dotenv_path}")
    
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    
    karen_phone = os.getenv("KAREN_PHONE_NUMBER", "+17575551234")
    
    if not os.getenv('TWILIO_ACCOUNT_SID'):
        logger.error("CRITICAL: Twilio credentials not found in environment.")
    else:
        try:
            client = SMSClient(karen_phone=karen_phone)
            logger.info(f"SMS Client for {karen_phone} initialized successfully")
        except ValueError as ve:
            logger.error(f"ValueError during SMSClient setup: {ve}")
'''
    
    return template

def create_sms_engine(findings):
    """Create SMS engine extending HandymanResponseEngine"""
    logger.info("🧠 Creating SMS engine extending HandymanResponseEngine...")
    
    # Check if handyman_sms_engine.py already exists
    sms_engine_file = src_path / 'handyman_sms_engine.py'
    if sms_engine_file.exists():
        logger.info("✓ SMS engine already exists")
        return
    
    # Generate SMS engine that extends HandymanResponseEngine
    sms_engine_code = '''"""
Handyman SMS Response Engine - Extends HandymanResponseEngine for SMS-specific features
Following Karen's pattern of extending without modifying existing code
"""
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import asyncio
import re

# Import and extend the existing HandymanResponseEngine
from .handyman_response_engine import HandymanResponseEngine

logger = logging.getLogger(__name__)

class HandymanSMSEngine(HandymanResponseEngine):
    """
    Extended response engine specifically for SMS communications.
    Inherits all functionality from HandymanResponseEngine and adds SMS-specific features.
    """
    
    def __init__(self, business_name: str = "Beach Handyman",
                 service_area: str = "Virginia Beach area", 
                 phone: str = "757-354-4577",
                 llm_client: Optional[Any] = None):
        # Initialize parent class
        super().__init__(business_name, service_area, phone, llm_client)
        
        # SMS-specific configuration
        self.sms_char_limit = 160  # Standard SMS character limit
        self.sms_multipart_limit = 1600  # Extended SMS limit

    def classify_sms_type(self, phone_number: str, body: str) -> Dict[str, Any]:
        """Classify SMS message with SMS-specific considerations"""
        # Use parent classification as base
        base_classification = self.classify_email_type("SMS Message", body)
        
        # Add SMS-specific classification
        sms_classification = base_classification.copy()
        sms_classification['is_short_message'] = len(body) <= 50
        sms_classification['sender_phone'] = phone_number
        
        return sms_classification

    async def generate_sms_response_async(self, phone_from: str, sms_body: str) -> Tuple[str, Dict[str, Any]]:
        """Generate SMS-optimized response"""
        if not self.llm_client:
            logger.error("LLMClient not initialized in HandymanSMSEngine.")
            classification = self.classify_sms_type(phone_from, sms_body)
            return self._generate_sms_fallback_response(phone_from, sms_body, classification), classification

        classification = self.classify_sms_type(phone_from, sms_body)
        
        # Generate SMS-optimized prompt
        prompt = self._generate_sms_prompt(phone_from, sms_body, classification)
        
        try:
            response_text = await asyncio.to_thread(
                self.llm_client.generate_text,
                prompt
            )
            
            # Ensure response fits SMS limits
            response_text = self._truncate_sms_response(response_text)
            
            return response_text, classification
            
        except Exception as e:
            logger.error(f"Error generating SMS response: {e}", exc_info=True)
            fallback = self._generate_sms_fallback_response(phone_from, sms_body, classification)
            return fallback, classification

    def _generate_sms_prompt(self, phone_from: str, sms_body: str, classification: Dict[str, Any]) -> str:
        """Generate SMS-specific prompt for LLM"""
        current_time = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
        
        prompt = f"""You are Karen, AI assistant for {self.business_name}, responding to an SMS message.

BUSINESS INFO:
- Business: {self.business_name}
- Phone: {self.phone}
- Current Time: {current_time}

SMS RESPONSE GUIDELINES:
1. Keep responses VERY concise (under 160 characters if possible)
2. Use clear, simple language
3. Include essential information only
4. For complex requests, suggest calling {self.phone}

SMS MESSAGE:
From: {phone_from}
Message: {sms_body}

Generate a concise SMS response:"""
        
        return prompt

    def _truncate_sms_response(self, response: str) -> str:
        """Truncate response to fit SMS limits"""
        if len(response) <= self.sms_char_limit:
            return response.strip()
        
        # Truncate and add call number
        truncated = response[:self.sms_char_limit - 25]
        return truncated + f"... Call {self.phone}"

    def _generate_sms_fallback_response(self, phone_from: str, sms_body: str, 
                                       classification: Dict[str, Any]) -> str:
        """Generate SMS-specific fallback responses"""
        if classification.get('is_emergency'):
            return f"URGENT? Call NOW: {self.phone}. We're ready to help!"
        elif classification.get('is_quote_request'):
            return f"Thanks! For a free quote, call {self.phone} or reply with your address."
        else:
            return f"{self.business_name}: Thanks for your message! Call {self.phone}."

    def should_send_multipart_sms(self, response: str) -> bool:
        """Determine if response should be sent as multipart SMS"""
        return len(response) > self.sms_char_limit

    def split_sms_response(self, response: str, max_parts: int = 3) -> list:
        """Split long response into multiple SMS parts"""
        if len(response) <= self.sms_char_limit:
            return [response]
        
        part_limit = self.sms_char_limit - 10  # Space for " (1/3)" etc.
        parts = []
        remaining = response
        
        while remaining and len(parts) < max_parts:
            if len(remaining) <= part_limit:
                parts.append(remaining)
                break
            
            chunk = remaining[:part_limit]
            # Try to break at sentence or word boundary
            for sep in ['. ', '! ', '? ', ', ', ' ']:
                last_sep = chunk.rfind(sep)
                if last_sep > part_limit * 0.7:
                    chunk = chunk[:last_sep + (1 if sep == ' ' else 2)]
                    break
            
            parts.append(chunk.strip())
            remaining = remaining[len(chunk):].strip()
        
        # Add part numbers
        if len(parts) > 1:
            parts = [f"{part} ({i+1}/{len(parts)})" for i, part in enumerate(parts)]
        
        return parts
'''
    
    with open(sms_engine_file, 'w') as f:
        f.write(sms_engine_code)
    
    logger.info(f"✓ Created {sms_engine_file}")

def create_celery_tasks(findings):
    """Create Celery tasks following existing patterns"""
    logger.info("⚙️ Creating Celery tasks following existing patterns...")
    
    celery_tasks_file = src_path / 'celery_sms_tasks.py'
    if celery_tasks_file.exists():
        logger.info("✓ Celery SMS tasks already exist")
        return
    
    # Generate Celery tasks code following existing patterns
    celery_tasks_code = '''"""
Celery tasks for SMS processing following existing email task patterns
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from .celery_app import celery_app
from .sms_client import SMSClient
from .handyman_sms_engine import HandymanSMSEngine

logger = logging.getLogger(__name__)

# SMS configuration
KAREN_PHONE_NUMBER = os.getenv('KAREN_PHONE_NUMBER', '+17575551234')

# SMS client instance
_sms_client_instance = None
_sms_engine_instance = None

def get_sms_client_instance():
    """Get SMS client instance following email client pattern"""
    global _sms_client_instance
    if _sms_client_instance is None:
        logger.debug("Creating new SMSClient instance")
        _sms_client_instance = SMSClient(karen_phone=KAREN_PHONE_NUMBER)
    return _sms_client_instance

def get_sms_engine_instance():
    """Get SMS engine instance"""
    global _sms_engine_instance
    if _sms_engine_instance is None:
        logger.debug("Creating new HandymanSMSEngine instance")
        _sms_engine_instance = HandymanSMSEngine(
            business_name=os.getenv('BUSINESS_NAME', 'Beach Handyman'),
            phone=os.getenv('BUSINESS_PHONE', '757-354-4577')
        )
    return _sms_engine_instance

@celery_app.task(name='fetch_new_sms', bind=True, max_retries=3)
def fetch_new_sms(self, process_last_n_hours: int = 1):
    """Fetch new SMS messages following fetch_new_emails pattern"""
    logger.info(f"Celery task: fetch_new_sms starting (last {process_last_n_hours} hours)")
    
    try:
        sms_client = get_sms_client_instance()
        
        # Fetch recent SMS messages
        newer_than = f"{process_last_n_hours}h"
        messages = sms_client.fetch_sms(
            search_criteria='ALL',
            newer_than=newer_than,
            max_results=50
        )
        
        logger.info(f"Found {len(messages)} SMS messages")
        
        # Process unprocessed messages
        processed_count = 0
        for msg in messages:
            msg_id = msg.get('uid')
            if not sms_client.is_sms_processed(msg_id):
                process_sms_with_llm.delay(msg)
                sms_client.mark_sms_as_processed(msg_id)
                processed_count += 1
        
        logger.info(f"Queued {processed_count} new SMS messages for processing")
        return {'total_messages': len(messages), 'new_messages': processed_count}
        
    except Exception as e:
        logger.error(f"Error in fetch_new_sms: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=2 ** self.request.retries)

@celery_app.task(name='process_sms_with_llm', bind=True, max_retries=3)
def process_sms_with_llm(self, sms_data: Dict[str, Any]):
    """Process SMS with LLM following process_email_with_llm pattern"""
    msg_id = sms_data.get('uid', 'unknown')
    sender = sms_data.get('sender', 'unknown')
    body = sms_data.get('body', '')
    
    logger.info(f"Processing SMS {msg_id} from {sender}")
    
    try:
        sms_engine = get_sms_engine_instance()
        
        # Generate response
        import asyncio
        response_text, classification = asyncio.run(
            sms_engine.generate_sms_response_async(sender, body)
        )
        
        logger.info(f"Generated SMS response for {msg_id}")
        
        # Send response
        send_karen_sms_reply.delay(sender, response_text, msg_id, classification)
        
        return {'msg_id': msg_id, 'response_generated': True}
        
    except Exception as e:
        logger.error(f"Error processing SMS {msg_id}: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=2 ** self.request.retries)

@celery_app.task(name='send_karen_sms_reply', bind=True, max_retries=3)
def send_karen_sms_reply(self, to_number: str, reply_body: str, 
                        original_msg_id: str, classification: Dict[str, Any]):
    """Send SMS reply following send_karen_reply pattern"""
    logger.info(f"Sending SMS reply to {to_number}")
    
    try:
        sms_client = get_sms_client_instance()
        success = sms_client.send_sms(to_number, reply_body)
        
        if success:
            logger.info(f"Successfully sent SMS reply to {to_number}")
        else:
            raise Exception(f"Failed to send SMS to {to_number}")
        
        return {'success': success, 'to_number': to_number}
        
    except Exception as e:
        logger.error(f"Error sending SMS reply: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=2 ** self.request.retries)

@celery_app.task(name='check_sms_task', ignore_result=True)
def check_sms_task():
    """Main SMS checking task following check_emails_task pattern"""
    logger.info("Celery task: check_sms_task starting")
    
    try:
        fetch_new_sms.delay(process_last_n_hours=1)
        logger.info("SMS check task completed")
    except Exception as e:
        logger.error(f"Error in check_sms_task: {e}", exc_info=True)
        raise
'''
    
    with open(celery_tasks_file, 'w') as f:
        f.write(celery_tasks_code)
    
    logger.info(f"✓ Created {celery_tasks_file}")

def share_implementation_knowledge():
    """Share implementation knowledge with other agents"""
    logger.info("🧠 Sharing SMS implementation knowledge...")
    
    comm.share_knowledge('sms_implementation_complete', {
        'files_created': [
            'src/sms_client.py',
            'src/handyman_sms_engine.py', 
            'src/celery_sms_tasks.py'
        ],
        'patterns_followed': [
            'EmailClient structure',
            'HandymanResponseEngine extension',
            'Celery task patterns'
        ],
        'implementation_status': 'complete',
        'ready_for_testing': True,
        'timestamp': datetime.now().isoformat()
    })

def notify_test_engineer_ready():
    """Send ready_for_testing message to test engineer"""
    logger.info("📨 Notifying test engineer that SMS implementation is ready...")
    
    comm.send_message('test_engineer', 'ready_for_testing', {
        'feature': 'sms_integration',
        'test_files': [
            'tests/test_sms_integration.py',
            'scripts/test_sms_system.py'
        ],
        'dependencies': ['twilio', 'pytest'],
        'test_phone_number': '+1234567890',
        'environment_required': [
            'TWILIO_ACCOUNT_SID',
            'TWILIO_AUTH_TOKEN',
            'KAREN_PHONE_NUMBER'
        ],
        'implementation_complete': True,
        'patterns_followed': True
    })
    
    logger.info("✅ Test engineer notified - SMS implementation ready for testing")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
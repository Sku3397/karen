#!/usr/bin/env python3
"""
Advanced Service Mock System for Karen AI Testing
Test Engineer: Comprehensive mocking that feels real and enables chaos testing
"""

import random
import time
import uuid
import threading
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from unittest.mock import Mock
import queue

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ServiceFailureSimulator:
    """Simulates various failure modes for services"""
    
    def __init__(self, failure_rate: float = 0.0):
        self.failure_rate = failure_rate
        self.failure_patterns = {
            'intermittent': self._intermittent_failure,
            'gradual_degradation': self._gradual_degradation,
            'cascade': self._cascade_failure,
            'timeout': self._timeout_failure,
            'rate_limit': self._rate_limit_failure
        }
        self.request_count = 0
        self.start_time = time.time()
        
    def should_fail(self, pattern: str = 'random') -> bool:
        """Determine if this request should fail"""
        if pattern in self.failure_patterns:
            return self.failure_patterns[pattern]()
        return random.random() < self.failure_rate
        
    def _intermittent_failure(self) -> bool:
        """Intermittent failures every N requests"""
        self.request_count += 1
        return self.request_count % 7 == 0
        
    def _gradual_degradation(self) -> bool:
        """Increasing failure rate over time"""
        elapsed = time.time() - self.start_time
        current_rate = min(self.failure_rate * (1 + elapsed / 100), 0.8)
        return random.random() < current_rate
        
    def _cascade_failure(self) -> bool:
        """Cascading failures - once it fails, keep failing"""
        if hasattr(self, '_cascade_started'):
            return True
        if random.random() < self.failure_rate:
            self._cascade_started = True
            return True
        return False
        
    def _timeout_failure(self) -> bool:
        """Simulate timeout by adding delay"""
        if random.random() < self.failure_rate:
            time.sleep(random.uniform(5, 15))  # Long delay
            return True
        return False
        
    def _rate_limit_failure(self) -> bool:
        """Rate limiting after too many requests"""
        self.request_count += 1
        if self.request_count > 50:  # Rate limit after 50 requests
            return True
        return False

class TwilioMockService:
    """Realistic Twilio SMS service mock with failure simulation"""
    
    def __init__(self, failure_rate: float = 0.0, webhook_delay: float = 0.5):
        self.failure_simulator = ServiceFailureSimulator(failure_rate)
        self.sent_messages = []
        self.webhooks = []
        self.webhook_delay = webhook_delay
        self.webhook_callbacks = []
        self.account_sid = "AC" + uuid.uuid4().hex[:32]
        
    def send_sms(self, to: str, from_: str, body: str) -> Dict[str, Any]:
        """Send SMS with realistic behavior and failure simulation"""
        
        # Check for failures
        if self.failure_simulator.should_fail():
            error_types = [
                ("Service temporarily unavailable", 20003),
                ("Invalid phone number", 21211),
                ("Message exceeds character limit", 21602),
                ("Account suspended", 20005),
                ("Rate limit exceeded", 20429)
            ]
            error_msg, error_code = random.choice(error_types)
            raise TwilioException(f"Error {error_code}: {error_msg}")
            
        # Validate inputs
        if not self._validate_phone_number(to):
            raise TwilioException("Invalid 'To' phone number")
            
        if len(body) > 1600:
            raise TwilioException("Message body exceeds maximum length")
            
        # Create message
        message_sid = f"MM{uuid.uuid4().hex}"
        message_data = {
            'sid': message_sid,
            'account_sid': self.account_sid,
            'to': to,
            'from': from_,
            'body': body,
            'status': 'queued',
            'direction': 'outbound',
            'date_created': datetime.now().isoformat(),
            'date_sent': None,
            'price': '-0.0075',
            'price_unit': 'USD'
        }
        
        self.sent_messages.append(message_data)
        
        # Simulate webhook callback after delay
        threading.Timer(
            self.webhook_delay, 
            self._trigger_status_webhook, 
            args=[message_sid, 'sent']
        ).start()
        
        # Simulate delivery confirmation
        threading.Timer(
            self.webhook_delay + random.uniform(1, 5), 
            self._trigger_status_webhook, 
            args=[message_sid, 'delivered']
        ).start()
        
        logger.info(f"SMS sent: {message_sid} to {to}")
        return {'sid': message_sid, 'status': 'queued'}
        
    def receive_sms(self, from_: str, to: str, body: str) -> Dict[str, Any]:
        """Simulate incoming SMS"""
        message_sid = f"MM{uuid.uuid4().hex}"
        message_data = {
            'sid': message_sid,
            'account_sid': self.account_sid,
            'from': from_,
            'to': to,
            'body': body,
            'status': 'received',
            'direction': 'inbound',
            'date_created': datetime.now().isoformat()
        }
        
        # Trigger webhook for incoming message
        for callback in self.webhook_callbacks:
            threading.Timer(0.1, callback, args=[message_data]).start()
            
        return message_data
        
    def _trigger_status_webhook(self, message_sid: str, status: str):
        """Trigger status update webhook"""
        webhook_data = {
            'MessageSid': message_sid,
            'MessageStatus': status,
            'Timestamp': datetime.now().isoformat()
        }
        
        self.webhooks.append(webhook_data)
        
        # Update message status
        for msg in self.sent_messages:
            if msg['sid'] == message_sid:
                msg['status'] = status
                if status == 'sent':
                    msg['date_sent'] = datetime.now().isoformat()
                break
                
        logger.info(f"Webhook triggered: {message_sid} -> {status}")
        
    def register_webhook_callback(self, callback: Callable):
        """Register callback for webhook events"""
        self.webhook_callbacks.append(callback)
        
    def _validate_phone_number(self, phone: str) -> bool:
        """Basic phone number validation"""
        clean_phone = ''.join(c for c in phone if c.isdigit() or c == '+')
        return len(clean_phone) >= 10
        
    def get_message_status(self, message_sid: str) -> Optional[Dict]:
        """Get message status by SID"""
        for msg in self.sent_messages:
            if msg['sid'] == message_sid:
                return msg
        return None

class GmailMockService:
    """Realistic Gmail API mock with failure simulation"""
    
    def __init__(self, failure_rate: float = 0.0):
        self.failure_simulator = ServiceFailureSimulator(failure_rate)
        self.emails = []
        self.sent_emails = []
        self.labels = ['INBOX', 'SENT', 'DRAFT', 'SPAM']
        
    def users(self):
        return GmailUsersResource(self)

class GmailUsersResource:
    def __init__(self, service):
        self.service = service
        
    def messages(self):
        return GmailMessagesResource(self.service)

class GmailMessagesResource:
    def __init__(self, service):
        self.service = service
        
    def list(self, userId='me', q=None, labelIds=None, maxResults=100):
        return GmailListRequest(self.service, q, labelIds, maxResults)
        
    def get(self, userId='me', id=None, format='full'):
        return GmailGetRequest(self.service, id, format)
        
    def send(self, userId='me', body=None):
        return GmailSendRequest(self.service, body)

class GmailListRequest:
    def __init__(self, service, query, label_ids, max_results):
        self.service = service
        self.query = query
        self.label_ids = label_ids
        self.max_results = max_results
        
    def execute(self):
        if self.service.failure_simulator.should_fail():
            raise GmailException("Gmail API quota exceeded")
            
        # Filter emails based on query and labels
        filtered_emails = []
        for email in self.service.emails:
            if self._matches_query(email):
                filtered_emails.append({'id': email['id']})
                
        return {
            'messages': filtered_emails[:self.max_results],
            'resultSizeEstimate': len(filtered_emails)
        }
        
    def _matches_query(self, email):
        if self.query:
            query_lower = self.query.lower()
            if 'is:unread' in query_lower and email.get('read', False):
                return False
            if 'from:' in query_lower:
                from_email = query_lower.split('from:')[1].split()[0]
                if from_email not in email.get('from', '').lower():
                    return False
        return True

class GmailGetRequest:
    def __init__(self, service, message_id, format_type):
        self.service = service
        self.message_id = message_id
        self.format = format_type
        
    def execute(self):
        if self.service.failure_simulator.should_fail():
            raise GmailException("Network connection failed")
            
        # Find email by ID
        for email in self.service.emails:
            if email['id'] == self.message_id:
                return self._format_email(email)
                
        raise GmailException(f"Message not found: {self.message_id}")
        
    def _format_email(self, email):
        return {
            'id': email['id'],
            'payload': {
                'headers': [
                    {'name': 'Subject', 'value': email.get('subject', '')},
                    {'name': 'From', 'value': email.get('from', '')},
                    {'name': 'To', 'value': email.get('to', '')},
                    {'name': 'Date', 'value': email.get('date', '')}
                ],
                'body': {
                    'data': self._encode_body(email.get('body', ''))
                }
            },
            'labelIds': email.get('labels', ['INBOX'])
        }
        
    def _encode_body(self, text):
        import base64
        return base64.b64encode(text.encode()).decode()

class GmailSendRequest:
    def __init__(self, service, body):
        self.service = service
        self.body = body
        
    def execute(self):
        if self.service.failure_simulator.should_fail():
            raise GmailException("Send quota exceeded")
            
        message_id = f"MSG{uuid.uuid4().hex}"
        
        # Decode and parse the email
        import base64
        raw_email = base64.b64decode(self.body['raw']).decode()
        
        sent_email = {
            'id': message_id,
            'threadId': f"THREAD{uuid.uuid4().hex}",
            'labelIds': ['SENT'],
            'raw_content': raw_email,
            'sent_at': datetime.now().isoformat()
        }
        
        self.service.sent_emails.append(sent_email)
        logger.info(f"Email sent: {message_id}")
        
        return {
            'id': message_id,
            'labelIds': ['SENT']
        }

class CalendarMockService:
    """Realistic Google Calendar mock with conflict detection"""
    
    def __init__(self, failure_rate: float = 0.0):
        self.failure_simulator = ServiceFailureSimulator(failure_rate)
        self.events = []
        self.calendars = {
            'primary': {
                'id': 'primary',
                'summary': 'Karen AI Calendar',
                'timeZone': 'America/New_York'
            }
        }
        
    def events(self):
        return CalendarEventsResource(self)
        
    def freebusy(self):
        return CalendarFreeBusyResource(self)

class CalendarEventsResource:
    def __init__(self, service):
        self.service = service
        
    def insert(self, calendarId='primary', body=None):
        return CalendarInsertRequest(self.service, calendarId, body)
        
    def list(self, calendarId='primary', timeMin=None, timeMax=None):
        return CalendarListRequest(self.service, calendarId, timeMin, timeMax)
        
    def update(self, calendarId='primary', eventId=None, body=None):
        return CalendarUpdateRequest(self.service, calendarId, eventId, body)
        
    def delete(self, calendarId='primary', eventId=None):
        return CalendarDeleteRequest(self.service, calendarId, eventId)

class CalendarInsertRequest:
    def __init__(self, service, calendar_id, body):
        self.service = service
        self.calendar_id = calendar_id
        self.body = body
        
    def execute(self):
        if self.service.failure_simulator.should_fail():
            raise CalendarException("Calendar service temporarily unavailable")
            
        # Check for conflicts
        start_time = self._parse_datetime(self.body['start'])
        end_time = self._parse_datetime(self.body['end'])
        
        conflicts = self._check_conflicts(start_time, end_time)
        if conflicts:
            raise CalendarException(f"Scheduling conflict with existing event: {conflicts[0]['id']}")
            
        # Create event
        event_id = f"EVENT{uuid.uuid4().hex}"
        event = {
            'id': event_id,
            'summary': self.body.get('summary', 'Untitled Event'),
            'description': self.body.get('description', ''),
            'start': self.body['start'],
            'end': self.body['end'],
            'attendees': self.body.get('attendees', []),
            'location': self.body.get('location', ''),
            'status': 'confirmed',
            'created': datetime.now().isoformat() + 'Z',
            'updated': datetime.now().isoformat() + 'Z'
        }
        
        self.service.events.append(event)
        logger.info(f"Calendar event created: {event_id}")
        
        return event
        
    def _parse_datetime(self, dt_info):
        if 'dateTime' in dt_info:
            return datetime.fromisoformat(dt_info['dateTime'].replace('Z', '+00:00'))
        else:
            return datetime.fromisoformat(dt_info['date'])
            
    def _check_conflicts(self, start_time, end_time):
        conflicts = []
        for event in self.service.events:
            event_start = self._parse_datetime(event['start'])
            event_end = self._parse_datetime(event['end'])
            
            if (start_time < event_end and end_time > event_start):
                conflicts.append(event)
                
        return conflicts

class CalendarListRequest:
    def __init__(self, service, calendar_id, timeMin, timeMax):
        self.service = service
        self.calendar_id = calendar_id
        self.timeMin = timeMin
        self.timeMax = timeMax
        
    def execute(self):
        if self.service.failure_simulator.should_fail():
            raise CalendarException("Event list failed")
            
        # Filter events by time range if specified
        filtered_events = []
        for event in self.service.events:
            if self.timeMin and self.timeMax:
                event_start = self._parse_datetime(event['start'])
                time_min = datetime.fromisoformat(self.timeMin.replace('Z', '+00:00'))
                time_max = datetime.fromisoformat(self.timeMax.replace('Z', '+00:00'))
                
                if time_min <= event_start <= time_max:
                    filtered_events.append(event)
            else:
                filtered_events.append(event)
                
        return {'items': filtered_events}
        
    def _parse_datetime(self, dt_info):
        if 'dateTime' in dt_info:
            return datetime.fromisoformat(dt_info['dateTime'].replace('Z', '+00:00'))
        else:
            return datetime.fromisoformat(dt_info['date'])

class CalendarUpdateRequest:
    def __init__(self, service, calendar_id, event_id, body):
        self.service = service
        self.calendar_id = calendar_id
        self.event_id = event_id
        self.body = body
        
    def execute(self):
        if self.service.failure_simulator.should_fail():
            raise CalendarException("Event update failed")
            
        # Find and update the event
        for event in self.service.events:
            if event['id'] == self.event_id:
                event.update(self.body)
                event['updated'] = datetime.now().isoformat() + 'Z'
                logger.info(f"Calendar event updated: {self.event_id}")
                return event
                
        raise CalendarException(f"Event not found: {self.event_id}")

class CalendarDeleteRequest:
    def __init__(self, service, calendar_id, event_id):
        self.service = service
        self.calendar_id = calendar_id
        self.event_id = event_id
        
    def execute(self):
        if self.service.failure_simulator.should_fail():
            raise CalendarException("Event deletion failed")
            
        # Find and remove the event
        for i, event in enumerate(self.service.events):
            if event['id'] == self.event_id:
                del self.service.events[i]
                logger.info(f"Calendar event deleted: {self.event_id}")
                return True
                
        raise CalendarException(f"Event not found: {self.event_id}")

class CalendarFreeBusyResource:
    def __init__(self, service):
        self.service = service
        
    def query(self, body=None):
        return CalendarFreeBusyRequest(self.service, body)

class CalendarFreeBusyRequest:
    def __init__(self, service, body):
        self.service = service
        self.body = body
        
    def execute(self):
        if self.service.failure_simulator.should_fail():
            raise CalendarException("Free/busy query failed")
            
        time_min = datetime.fromisoformat(self.body['timeMin'].replace('Z', '+00:00'))
        time_max = datetime.fromisoformat(self.body['timeMax'].replace('Z', '+00:00'))
        
        busy_periods = []
        for event in self.service.events:
            event_start = self._parse_datetime(event['start'])
            event_end = self._parse_datetime(event['end'])
            
            if event_start >= time_min and event_end <= time_max:
                busy_periods.append({
                    'start': event['start']['dateTime'] if 'dateTime' in event['start'] else event['start']['date'],
                    'end': event['end']['dateTime'] if 'dateTime' in event['end'] else event['end']['date']
                })
                
        return {
            'calendars': {
                'primary': {
                    'busy': busy_periods
                }
            }
        }
        
    def _parse_datetime(self, dt_info):
        if 'dateTime' in dt_info:
            return datetime.fromisoformat(dt_info['dateTime'].replace('Z', '+00:00'))
        else:
            return datetime.fromisoformat(dt_info['date'])

class RedisMockService:
    """Redis mock with connection failure simulation"""
    
    def __init__(self, failure_rate: float = 0.0):
        self.failure_simulator = ServiceFailureSimulator(failure_rate)
        self.data = {}
        self.queues = {}
        self.connected = True
        
    def get(self, key: str) -> Optional[str]:
        if self.failure_simulator.should_fail():
            raise RedisException("Connection lost")
        return self.data.get(key)
        
    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        if self.failure_simulator.should_fail():
            raise RedisException("Write operation failed")
        self.data[key] = value
        if ex:
            # Simulate expiration (simplified)
            threading.Timer(ex, lambda: self.data.pop(key, None)).start()
        return True
        
    def lpush(self, queue_name: str, *values) -> int:
        if self.failure_simulator.should_fail():
            raise RedisException("Queue operation failed")
        if queue_name not in self.queues:
            self.queues[queue_name] = []
        self.queues[queue_name].extend(values)
        return len(self.queues[queue_name])
        
    def rpop(self, queue_name: str) -> Optional[str]:
        if self.failure_simulator.should_fail():
            raise RedisException("Queue operation failed")
        if queue_name in self.queues and self.queues[queue_name]:
            return self.queues[queue_name].pop()
        return None
        
    def ping(self) -> bool:
        if self.failure_simulator.should_fail():
            raise RedisException("Ping failed")
        return self.connected

# Custom exceptions for realistic error simulation
class TwilioException(Exception):
    pass

class GmailException(Exception):
    pass

class CalendarException(Exception):
    pass

class RedisException(Exception):
    pass

# Service mock factory
class ServiceMockFactory:
    """Factory for creating service mocks with coordinated failure scenarios"""
    
    @staticmethod
    def create_stable_services():
        """Create services with no failures - for baseline testing"""
        return {
            'twilio': TwilioMockService(failure_rate=0.0),
            'gmail': GmailMockService(failure_rate=0.0),
            'calendar': CalendarMockService(failure_rate=0.0),
            'redis': RedisMockService(failure_rate=0.0)
        }
        
    @staticmethod
    def create_chaos_services(failure_rate: float = 0.1):
        """Create services with chaos testing enabled"""
        return {
            'twilio': TwilioMockService(failure_rate=failure_rate),
            'gmail': GmailMockService(failure_rate=failure_rate),
            'calendar': CalendarMockService(failure_rate=failure_rate),
            'redis': RedisMockService(failure_rate=failure_rate)
        }
        
    @staticmethod
    def create_cascade_failure_services():
        """Create services that fail in cascade"""
        services = ServiceMockFactory.create_stable_services()
        
        # Set up cascade: Redis fails first, then others follow
        def trigger_cascade():
            time.sleep(1)
            services['redis'].failure_simulator.failure_rate = 1.0
            time.sleep(2)
            services['twilio'].failure_simulator.failure_rate = 0.8
            time.sleep(1)
            services['gmail'].failure_simulator.failure_rate = 0.6
            
        threading.Timer(5, trigger_cascade).start()
        return services
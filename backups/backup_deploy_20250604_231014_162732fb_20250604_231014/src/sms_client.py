# SMSClient: Handles sending and fetching SMS messages using Twilio API
import os
import logging
import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import base64
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# Define paths relative to the project root, assuming this file is in src/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

logger = logging.getLogger(__name__)

class SMSClient:
    def __init__(self, karen_phone: str, token_data: Optional[Dict[str, str]] = None):
        """
        Initialize SMS client following EmailClient pattern.
        
        Args:
            karen_phone: Karen's phone number (e.g., +17575551234)
            token_data: Optional dict with account_sid, auth_token (for testing)
        """
        self.karen_phone = karen_phone
        logger.debug(f"Initializing SMSClient for {karen_phone}")
        
        # Load credentials following EmailClient pattern
        if token_data:
            # For testing - credentials passed directly
            self.account_sid = token_data.get('account_sid')
            self.auth_token = token_data.get('auth_token')
        else:
            # Load from environment variables
            self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        
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
        """
        Send SMS message following EmailClient.send_email pattern.
        
        Args:
            to: Recipient phone number in E.164 format (e.g., +1234567890)
            body: SMS message content
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        logger.debug(f"Attempting to send SMS to: {to}, body length: {len(body)}")
        
        try:
            # Truncate body if too long (SMS limit is 1600 chars)
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
            logger.error(f"Twilio API error occurred: {error.msg}. Code: {error.code}", exc_info=True)
            if error.code == 20003:
                logger.error("Authentication error (20003). Check account SID and auth token.")
            elif error.code == 21211:
                logger.error("Invalid 'To' phone number (21211). Ensure E.164 format.")
            elif error.code == 21212:
                logger.error("Invalid 'From' phone number (21212). Check karen_phone.")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred during send_sms: {e}", exc_info=True)
            return False

    def fetch_sms(self, search_criteria: str = 'UNREAD', 
                  last_n_days: Optional[int] = None,
                  newer_than: Optional[str] = None,
                  max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch SMS messages following EmailClient.fetch_emails pattern.
        
        Args:
            search_criteria: 'UNREAD' or 'ALL' (Twilio doesn't have unread concept, so this is simulated)
            last_n_days: Fetch messages from last N days
            newer_than: Fetch messages newer than (e.g., "1h", "2d")
            max_results: Maximum number of messages to return
            
        Returns:
            List of message dictionaries following EmailClient structure
        """
        logger.debug(f"Fetching SMS with criteria: '{search_criteria}', last_n_days: {last_n_days}, "
                    f"newer_than: {newer_than}, max_results: {max_results}")
        
        try:
            # Build date filter
            date_filter = None
            if newer_than:
                # Parse newer_than format (1h, 2d, etc.)
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
                'to': self.karen_phone,  # Messages TO Karen (incoming)
                'limit': max_results
            }
            
            if date_filter:
                messages_kwargs['date_sent_after'] = date_filter
            
            messages = self.client.messages.list(**messages_kwargs)
            
            if not messages:
                logger.info("No messages found matching criteria.")
                return []
            
            logger.info(f"Found {len(messages)} messages. Processing...")
            
            sms_data = []
            for msg in messages:
                # Map Twilio message to EmailClient structure for compatibility
                sms_item = {
                    'id': msg.sid,  # Use Twilio SID as ID
                    'threadId': msg.sid,  # SMS doesn't have threads, use SID
                    'snippet': msg.body[:100] if len(msg.body) > 100 else msg.body,
                    'sender': msg.from_,  # Phone number of sender
                    'subject': f"SMS from {msg.from_}",  # Generate subject for compatibility
                    'body_plain': msg.body,
                    'body_html': '',  # SMS doesn't have HTML
                    'body': msg.body,
                    'date_str': msg.date_sent.strftime("%a, %d %b %Y %H:%M:%S %z") if msg.date_sent else '',
                    'received_date_dt': msg.date_sent,
                    'uid': msg.sid,  # Use SID as UID for compatibility
                    'status': msg.status,  # Twilio status (received, sent, etc.)
                    'direction': msg.direction  # inbound/outbound-api/outbound-call/outbound-reply
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
        """
        Mark SMS as processed. Since Twilio doesn't have labels/read status,
        we'll store this in a local file or just log it.
        
        Following EmailClient.mark_email_as_processed pattern.
        """
        logger.debug(f"Attempting to mark SMS UID {uid} as processed. Label: {label_to_add}")
        
        try:
            # Twilio doesn't support marking messages as read/processed
            # We could maintain a local state file or database
            # For now, just log it
            logger.info(f"SMS {uid} marked as processed (logged only - Twilio doesn't support message states)")
            
            # Optional: Store processed SMS IDs in a local file
            processed_file = os.path.join(PROJECT_ROOT, '.processed_sms_ids.json')
            processed_ids = set()
            
            if os.path.exists(processed_file):
                with open(processed_file, 'r') as f:
                    processed_ids = set(json.load(f))
            
            processed_ids.add(uid)
            
            with open(processed_file, 'w') as f:
                json.dump(list(processed_ids), f)
            
            return True
            
        except Exception as e:
            logger.error(f"Error marking SMS {uid} as processed: {e}", exc_info=True)
            return False

    def mark_sms_as_seen(self, uid: str) -> bool:
        """Mark SMS as seen - alias for mark_sms_as_processed."""
        logger.debug(f"mark_sms_as_seen called for {uid}, aliasing to mark_sms_as_processed.")
        return self.mark_sms_as_processed(uid)

    def mark_sms_as_read(self, message_id: str) -> bool:
        """Mark SMS as read - alias for mark_sms_as_seen."""
        logger.debug(f"mark_sms_as_read called for {message_id}, aliasing to mark_sms_as_seen.")
        return self.mark_sms_as_seen(uid=message_id)

    def send_self_test_sms(self, subject_prefix="AI Self-Test"):
        """Send a test SMS from Karen's number to itself (following email pattern)."""
        logger.info(f"send_self_test_sms called for {self.karen_phone} with prefix: '{subject_prefix}'")
        
        recipient = self.karen_phone  # Send to self
        body = (
            f"{subject_prefix}: Test from Karen SMS "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}. "
            f"Verifying SMS capability."
        )
        
        logger.info(f"Attempting to send self-test SMS to {recipient} (self)")
        try:
            success = self.send_sms(to=recipient, body=body)
            
            if success:
                logger.info(f"Self-test SMS successfully dispatched to {recipient} (self).")
                return True
            else:
                logger.error(f"Failed to send self-test SMS to {recipient} (self): send_sms returned False")
                return False
        except Exception as e:
            logger.error(f"Failed to send self-test SMS to {recipient} (self): {e}", exc_info=True)
            return False

    def send_designated_test_sms(self, recipient_number: str, subject_prefix="AI Test"):
        """Send a test SMS to a designated recipient (following email pattern)."""
        logger.info(f"send_designated_test_sms called to send to {recipient_number} with prefix: '{subject_prefix}'")
        
        body = (
            f"{subject_prefix}: Test from Karen ({self.karen_phone}) "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}. "
            f"Verifying SMS to external recipient."
        )
        
        logger.info(f"Attempting to send designated test SMS from {self.karen_phone} to {recipient_number}")
        try:
            success = self.send_sms(to=recipient_number, body=body)
            
            if success:
                logger.info(f"Designated test SMS successfully dispatched to {recipient_number}.")
                return True
            else:
                logger.error(f"Failed to send designated test SMS to {recipient_number}: send_sms returned False")
                return False
        except Exception as e:
            logger.error(f"Failed to send designated test SMS to {recipient_number}: {e}", exc_info=True)
            return False

    def fetch_last_n_sent_sms(self, n: int = 1, recipient_filter: Optional[str] = None, 
                              metadata_only: bool = False) -> List[Dict[str, Any]]:
        """
        Fetch the last N SMS messages sent by Karen.
        
        Following EmailClient.fetch_last_n_sent_emails pattern.
        """
        fetch_type = "metadata" if metadata_only else "full content"
        logger.info(f"Fetching {fetch_type} for the last {n} sent SMS for {self.karen_phone}"
                   f"{f' to {recipient_filter}' if recipient_filter else ''}...")
        
        try:
            # Fetch messages FROM Karen (outgoing)
            messages_kwargs = {
                'from_': self.karen_phone,
                'limit': n
            }
            
            if recipient_filter:
                messages_kwargs['to'] = recipient_filter
            
            messages = self.client.messages.list(**messages_kwargs)
            
            if not messages:
                logger.info(f"No sent SMS found for {self.karen_phone}"
                          f"{f' to {recipient_filter}' if recipient_filter else ''}.")
                return []
            
            logger.info(f"Found {len(messages)} sent message(s). Processing...")
            
            sms_details = []
            for msg in messages[:n]:
                sms_data = {
                    'id': msg.sid,
                    'threadId': msg.sid,
                    'snippet': msg.body[:100] if len(msg.body) > 100 else msg.body,
                    'subject': f"SMS to {msg.to}",
                    'sender': self.karen_phone,
                    'recipient': msg.to,
                    'date_utc_timestamp': msg.date_sent.timestamp() if msg.date_sent else None,
                    'date_iso': msg.date_sent.isoformat() + "Z" if msg.date_sent else None,
                    'body_text': msg.body if not metadata_only else None,
                    'body_html': None,  # SMS doesn't have HTML
                    'status': msg.status,
                    'direction': msg.direction
                }
                
                sms_details.append(sms_data)
                logger.debug(f"Successfully processed sent SMS ID {msg.sid} (metadata_only={metadata_only}).")
            
            logger.info(f"Successfully fetched details for {len(sms_details)} sent SMS message(s).")
            return sms_details
            
        except TwilioRestException as error:
            logger.error(f"Twilio error fetching sent SMS list: {error.msg}", exc_info=True)
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching last {n} sent SMS: {e}", exc_info=True)
            return []

    def is_sms_processed(self, uid: str) -> bool:
        """Check if SMS has been processed (using local state file)."""
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


# Example usage (for testing, if run directly)
if __name__ == '__main__':
    from dotenv import load_dotenv
    import sys
    
    # Load .env for testing
    dotenv_path = os.path.join(PROJECT_ROOT, '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path=dotenv_path)
        print(f"Loaded .env from {dotenv_path} for SMSClient testing.")
    else:
        print(f"Warning: .env file not found at {dotenv_path} for SMSClient testing.")
    
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    
    # Test with Karen's SMS credentials
    karen_phone = os.getenv("KAREN_PHONE_NUMBER", "+17575551234")  # Default if not in .env
    
    if not os.getenv('TWILIO_ACCOUNT_SID') or not os.getenv('TWILIO_AUTH_TOKEN'):
        logger.error("CRITICAL: Twilio credentials not found in environment. Cannot run test.")
    else:
        try:
            logger.info(f"--- TESTING SMS Client for {karen_phone} ---")
            client = SMSClient(karen_phone=karen_phone)
            
            # Test fetching last N sent SMS
            last_sent = client.fetch_last_n_sent_sms(n=3)
            if last_sent:
                print(f"\n--- Last {len(last_sent)} SMS Sent by {karen_phone} ---")
                for i, sms_detail in enumerate(last_sent):
                    print(f"SMS {i+1}:")
                    print(f"  ID: {sms_detail.get('id')}")
                    print(f"  To: {sms_detail.get('recipient')}")
                    print(f"  Date: {sms_detail.get('date_iso')}")
                    print(f"  Body: {sms_detail.get('snippet')}")
                    print("---")
            else:
                print(f"No sent SMS found for {karen_phone} or error fetching them.")
            
            # Test fetching incoming SMS
            print(f"\nFetching recent incoming SMS for {karen_phone}...")
            incoming_sms = client.fetch_sms(search_criteria='ALL', last_n_days=7, max_results=5)
            if incoming_sms:
                print(f"Found {len(incoming_sms)} incoming SMS:")
                for sms in incoming_sms:
                    print(f"  From: {sms.get('sender')}, Body: {sms.get('snippet')}, ID: {sms.get('uid')}")
            else:
                print(f"No incoming SMS found for {karen_phone}.")
                
        except ValueError as ve:
            logger.error(f"ValueError during SMSClient test setup: {ve}")
        except Exception as e:
            logger.error(f"An error occurred during SMSClient test: {e}", exc_info=True)

# src/calendar_client.py - Secure calendar client with OAuth token management
import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleAuthRequest
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import google.auth.exceptions

# Import secure OAuth token manager
from .oauth_token_manager import get_calendar_credentials, get_token_manager

logger = logging.getLogger(__name__)

class CalendarClient:
    def __init__(self, email_address: str, token_path: str = None, credentials_path: str = None):
        """
        Initialize CalendarClient with secure OAuth token management
        
        Args:
            email_address: Email address for calendar access
            token_path: Legacy parameter, ignored (for backward compatibility)
            credentials_path: Legacy parameter, ignored (for backward compatibility)
        """
        self.email_address = email_address
        
        # Legacy compatibility warnings
        if token_path:
            logger.warning(f"token_path parameter is deprecated. Using secure token manager instead.")
        if credentials_path:
            logger.warning(f"credentials_path parameter is deprecated. Using secure token manager instead.")
        
        logger.info(f"Initializing secure CalendarClient for {email_address}")
        
        # Use secure token manager for credentials
        self.creds = self._get_secure_credentials()
        
        if not self.creds:
            msg = f"Failed to obtain secure OAuth credentials for calendar access: {email_address}"
            logger.error(msg)
            raise ValueError(msg)
        
        try:
            self.service = build('calendar', 'v3', credentials=self.creds)
            logger.info(f"Secure Google Calendar service built successfully for {email_address}")
        except Exception as e:
            logger.error(f"Failed to build Google Calendar service for {email_address}: {e}", exc_info=True)
            raise

    def _get_secure_credentials(self) -> Optional[Credentials]:
        """Get secure OAuth credentials using the token manager"""
        try:
            logger.debug(f"Requesting secure calendar credentials for {self.email_address}")
            
            # Use the secure token manager to get credentials
            creds = get_calendar_credentials(self.email_address)
            
            if creds and creds.valid:
                logger.info(f"Secure calendar credentials obtained for {self.email_address}")
                return creds
            else:
                logger.error(f"Failed to obtain valid secure calendar credentials for {self.email_address}")
                return None
                
        except Exception as e:
            logger.error(f"Error obtaining secure calendar credentials for {self.email_address}: {e}", exc_info=True)
            return None
    
    def refresh_credentials(self) -> bool:
        """Refresh credentials using the secure token manager"""
        try:
            logger.info(f"Refreshing calendar credentials for {self.email_address}")
            
            # Get fresh credentials from token manager
            new_creds = get_calendar_credentials(self.email_address)
            
            if new_creds and new_creds.valid:
                self.creds = new_creds
                # Rebuild service with new credentials
                self.service = build('calendar', 'v3', credentials=self.creds)
                logger.info(f"Calendar credentials refreshed successfully for {self.email_address}")
                return True
            else:
                logger.error(f"Failed to refresh calendar credentials for {self.email_address}")
                return False
                
        except Exception as e:
            logger.error(f"Error refreshing calendar credentials for {self.email_address}: {e}", exc_info=True)
            return False
    
    def _ensure_valid_credentials(self) -> bool:
        """Ensure credentials are valid, refresh if necessary"""
        if not self.creds or not self.creds.valid:
            logger.warning(f"Invalid calendar credentials detected for {self.email_address}, attempting refresh")
            return self.refresh_credentials()
        return True


    # --- Calendar specific methods will go here ---
    def get_availability(self, start_time_iso: str, end_time_iso: str, calendar_id: str = 'primary') -> Optional[List[Dict[str, str]]]:
        """Gets free/busy information for a calendar."""
        if not self._ensure_valid_credentials():
            logger.error("Failed to ensure valid credentials for calendar operation.")
            return None
        
        if not self.service:
            logger.error("Calendar service not available.")
            return None
        
        body = {
            "timeMin": start_time_iso,
            "timeMax": end_time_iso,
            "items": [{"id": calendar_id}]
        }
        try:
            logger.debug(f"Fetching freeBusy for {calendar_id} from {start_time_iso} to {end_time_iso}")
            events_result = self.service.freebusy().query(body=body).execute()
            calendar_busy_info = events_result.get('calendars', {}).get(calendar_id, {})
            busy_slots = calendar_busy_info.get('busy', []) # List of {'start': ..., 'end': ...}
            logger.info(f"Found {len(busy_slots)} busy slots for {calendar_id}.")
            return busy_slots
        except HttpError as e:
            logger.error(f"HttpError fetching free/busy for {calendar_id}: {e.resp.status} - {e._get_reason()}", exc_info=True)
            if e.resp.status == 404:
                 logger.error(f"Calendar with ID '{calendar_id}' not found.")
            return None
        except Exception as e:
            logger.error(f"Error fetching free/busy for {calendar_id}: {e}", exc_info=True)
            return None

    def create_event(self, summary: str, start_datetime_iso: str, end_datetime_iso: str, 
                     attendees: Optional[List[str]] = None, description: Optional[str] = None, 
                     calendar_id: str = 'primary') -> Optional[Dict[str, Any]]:
        """Creates an event on the calendar."""
        if not self.service:
            logger.error("Calendar service not available.")
            return None

        event = {
            'summary': summary,
            'description': description or '',
            'start': {
                'dateTime': start_datetime_iso,
                # 'timeZone': 'America/New_York', # Consider making timezone configurable or getting from system/user
            },
            'end': {
                'dateTime': end_datetime_iso,
                # 'timeZone': 'America/New_York',
            },
        }
        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]

        try:
            logger.info(f"Creating event '{summary}' from {start_datetime_iso} to {end_datetime_iso} on calendar {calendar_id}")
            created_event = self.service.events().insert(calendarId=calendar_id, body=event).execute()
            logger.info(f"Event created successfully: ID: {created_event.get('id')}, Link: {created_event.get('htmlLink')}")
            return created_event
        except HttpError as e:
            logger.error(f"HttpError creating event '{summary}': {e.resp.status} - {e._get_reason()}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Error creating event '{summary}': {e}", exc_info=True)
            return None

# Example usage (for testing this client directly)
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logger.info("Running CalendarClient direct test...")

    # Adjust path for direct execution to find src.config
    import sys
    if 'src' not in sys.path and 'src' not in os.getcwd(): # Be careful with cwd if script is in src
        # Assuming script is in src, parent is project root
        project_root_for_test = os.path.dirname(os.path.abspath(__file__))
        if os.path.basename(project_root_for_test) == 'src': # if script is in /src
            project_root_for_test = os.path.dirname(project_root_for_test)
        sys.path.insert(0, project_root_for_test) 
        logger.debug(f"Adjusted sys.path for direct execution: added {project_root_for_test}")

    from dotenv import load_dotenv
    # Load .env from project root, assuming this script is in /src
    # Determine project root based on this script's location if it's in /src
    current_script_path = os.path.abspath(__file__)
    project_dir = os.path.dirname(current_script_path) # This will be /src
    if os.path.basename(project_dir) == 'src':
        project_dir = os.path.dirname(project_dir) # This is project root
    
    dotenv_path = os.path.join(project_dir, '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path=dotenv_path)
        logger.debug(f"Loaded .env from {dotenv_path} for direct test.")
    else:
        logger.warning(f".env file not found at {dotenv_path} for direct test.")

    try:
        from src.config import GOOGLE_CALENDAR_TOKEN_PATH as CFG_TOKEN_PATH, \
                               GOOGLE_APP_CREDENTIALS_PATH as CFG_CREDS_PATH, \
                               MONITORED_EMAIL_ACCOUNT as CFG_MONITORED_ACCOUNT
        logger.debug("Successfully imported config variables for direct test.")
    except ImportError as e:
        logger.error(f"Could not import from src.config for direct test: {e}. Ensure PYTHONPATH or script location is correct.")
        sys.exit(1)

    monitored_account = CFG_MONITORED_ACCOUNT
    token_p = CFG_TOKEN_PATH # Uses the value from config, which reads from .env
    creds_p = CFG_CREDS_PATH # Uses the value from config

    if not monitored_account or not token_p or not creds_p:
        logger.error("MONITORED_EMAIL_ACCOUNT, GOOGLE_CALENDAR_TOKEN_PATH, or GOOGLE_APP_CREDENTIALS_PATH not in .env. Skipping test.")
    else:
        logger.info(f"Testing with account: {monitored_account}, token path: {token_p}")
        try:
            calendar_client = CalendarClient(email_address=monitored_account, token_path=token_p, credentials_path=creds_p)
            
            # Test get_availability
            now = datetime.utcnow()
            start_iso = now.isoformat() + 'Z'  # 'Z' indicates UTC
            end_iso = (now + timedelta(days=7)).isoformat() + 'Z'
            logger.info(f"\nTesting get_availability for next 7 days ({start_iso} to {end_iso})...")
            busy_slots = calendar_client.get_availability(start_iso, end_iso)
            if busy_slots is not None:
                logger.info(f"Busy slots: {json.dumps(busy_slots, indent=2)}")
            else:
                logger.error("Failed to get availability.")

            # Test create_event
            logger.info("\nTesting create_event...")
            event_start = (now + timedelta(days=1, hours=2)).replace(minute=0, second=0, microsecond=0)
            event_end = (event_start + timedelta(hours=1))
            event_summary = "Test Appointment via CalendarClient"
            created = calendar_client.create_event(
                summary=event_summary,
                start_datetime_iso=event_start.isoformat() + 'Z',
                end_datetime_iso=event_end.isoformat() + 'Z',
                attendees=[monitored_account] # Self-invite
            )
            if created:
                logger.info(f"Event '{event_summary}' created successfully. ID: {created.get('id')}")
            else:
                logger.error(f"Failed to create event '{event_summary}'.")

        except ValueError as ve:
            logger.error(f"Setup error for CalendarClient test: {ve}")
        except Exception as e:
            logger.error(f"Error during CalendarClient direct test: {e}", exc_info=True) 
# Enhanced API Client Template
# Generated from: /mnt/c/Users/Man/ultra/projects/karen/src/calendar_client.py
# Analysis cycle: 1

# src/calendar_client.py
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

from .config import GOOGLE_CALENDAR_TOKEN_PATH, GOOGLE_APP_CREDENTIALS_PATH # Assuming these will be in config

logger = logging.getLogger(__name__)

# Define the scopes needed for Google Calendar API
CALENDAR_SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events'
]

class CalendarClient:
    def __init__(self, email_address: str, token_path: str = GOOGLE_CALENDAR_TOKEN_PATH, credentials_path: str = GOOGLE_APP_CREDENTIALS_PATH):
        self.email_address = email_address # The email whose calendar we are accessing
        self.token_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), token_path) # Path relative to project root
        self.credentials_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), credentials_path)
        logger.debug(f"Initializing CalendarClient for {email_address} using token '{self.token_path}' and creds '{self.credentials_path}'")

        self.client_config = self._load_client_config()
        if not self.client_config:
            msg = f"Failed to load client configuration from {self.credentials_path}."
            logger.error(msg)
            raise ValueError(msg)

        self.creds = self._load_and_refresh_credentials()
        if not self.creds:
            msg = f"Failed to load/refresh Google OAuth credentials from {self.token_path} for calendar access."
            logger.error(msg)
            raise ValueError(msg)
        
        try:
            self.service = build('calendar', 'v3', credentials=self.creds)
            logger.info(f"Google Calendar service built successfully for {email_address}.")
        except Exception as e:
            logger.error(f"Failed to build Google Calendar service for {email_address}: {e}", exc_info=True)
            raise

    def _load_client_config(self) -> Optional[Dict[str, Any]]:
        logger.debug(f"Attempting to load client configuration from {self.credentials_path}")
        try:
            with open(self.credentials_path, 'r') as f:
                full_creds_json = json.load(f)
                client_config = full_creds_json.get('installed') or full_creds_json.get('web') # Support both types
            if not client_config or not all(k in client_config for k in ['client_id', 'client_secret', 'token_uri']):
                logger.error("Client credentials JSON is missing required keys (client_id, client_secret, token_uri).")
                return None
            return client_config
        except FileNotFoundError:
            logger.error(f"OAuth credentials file not found at {self.credentials_path}")
            return None
        except Exception as e:
            logger.error(f"Error loading client config from {self.credentials_path}: {e}", exc_info=True)
            return None

    def _load_and_refresh_credentials(self) -> Optional[Credentials]:
        creds = None
        if os.path.exists(self.token_path):
            try:
                creds = Credentials.from_authorized_user_file(self.token_path, CALENDAR_SCOPES)
            except Exception as e:
                logger.warning(f"Could not load credentials from {self.token_path} using scopes {CALENDAR_SCOPES}: {e}. Will try without scopes for refresh.")
                try:
                    creds = Credentials.from_authorized_user_file(self.token_path)
                except Exception as e2:
                    logger.error(f"Failed to load credentials from {self.token_path} even without scopes: {e2}")
                    creds = None
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info(f"Credentials for {self.email_address} calendar are expired. Attempting to refresh...")
                try:
                    creds.refresh(GoogleAuthRequest())
                    self._save_token(creds)
                    logger.info(f"Successfully refreshed and saved calendar credentials for {self.email_address}.")
                except google.auth.exceptions.RefreshError as e:
                    logger.error(f"Failed to refresh calendar credentials for {self.email_address}. Refresh token may be invalid or revoked. Re-auth needed. Error: {e}", exc_info=True)
                    # Potentially delete the bad token file here if re-auth is the only way
                    # os.remove(self.token_path)
                    return None # Must return None to indicate failure to get valid creds
                except Exception as e:
                    logger.error(f"Unexpected error refreshing calendar credentials for {self.email_address}: {e}", exc_info=True)
                    return None
            else:
                # This case means no token, or token invalid and no refresh_token or not expired (which is weird)
                # This path should ideally trigger re-authentication flow if this were interactive.
                # For an autonomous agent, this indicates a setup issue or revoked token.
                logger.error(f"No valid calendar credentials for {self.email_address} at {self.token_path}. Manual OAuth flow is needed to generate a new token with scopes: {CALENDAR_SCOPES}")
                return None # No valid credentials, and cannot refresh.
        
        if not creds or not creds.valid:
             logger.error(f"FINAL CHECK: Still no valid credentials for {self.email_address} calendar.")
             return None
        
        # Ensure all required scopes are present
        if not all(scope in creds.scopes for scope in CALENDAR_SCOPES):
            logger.warning(f"Calendar credentials for {self.email_address} are missing one or more required scopes. Current: {creds.scopes}, Required: {CALENDAR_SCOPES}. Operations may fail. Re-auth needed.")
            # Don't return None here, let it proceed but log warning. Some readonly ops might work.

        logger.info(f"Calendar credentials for {self.email_address} loaded/refreshed successfully.")
        return creds

    def _save_token(self, creds: Credentials):
        try:
            with open(self.token_path, 'w') as token_file:
                token_file.write(creds.to_json())
            logger.info(f"Calendar OAuth token data saved to {self.token_path} for {self.email_address}.")
        except Exception as e:
            logger.error(f"Failed to save calendar token to {self.token_path}: {e}", exc_info=True)

    # --- Calendar specific methods will go here ---
    def get_availability(self, start_time_iso: str, end_time_iso: str, calendar_id: str = 'primary') -> Optional[List[Dict[str, str]]]:
        """Gets free/busy information for a calendar."""
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

# TEMPLATE USAGE:
# 1. Replace class name with your service
# 2. Update API endpoints and methods
# 3. Modify OAuth scopes as needed
# 4. Add service-specific error handling

# scripts/test_calendar_client.py
import os
import sys
import logging
import json
from datetime import datetime, timedelta

# Add project root to sys.path to allow importing from src
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("test_calendar_client")

if __name__ == '__main__':
    logger.info("Running CalendarClient test script...")
    
    try:
        from src.config import MONITORED_EMAIL_ACCOUNT_CONFIG, GOOGLE_CALENDAR_TOKEN_PATH, GOOGLE_APP_CREDENTIALS_PATH
        from src.calendar_client import CalendarClient
        logger.info("Successfully imported CalendarClient and config variables.")
    except ImportError as e:
        logger.error(f"Failed to import modules: {e}. Ensure PYTHONPATH is set or script is run from project root context.", exc_info=True)
        sys.exit(1)
    
    monitored_account = MONITORED_EMAIL_ACCOUNT_CONFIG
    token_p = GOOGLE_CALENDAR_TOKEN_PATH 
    creds_p = GOOGLE_APP_CREDENTIALS_PATH

    if not monitored_account:
        logger.error("MONITORED_EMAIL_ACCOUNT_CONFIG not configured in .env or src/config.py. Skipping test.")
        sys.exit(1)
    if not token_p:
        logger.error("GOOGLE_CALENDAR_TOKEN_PATH not configured (via GOOGLE_CALENDAR_TOKEN_PATH_HELLO in .env or src/config.py defaults). Skipping test.")
        sys.exit(1)
    if not creds_p:
        logger.error("GOOGLE_APP_CREDENTIALS_PATH not configured in .env or src/config.py. Skipping test.")
        sys.exit(1)

    logger.info(f"Testing CalendarClient with account: {monitored_account}, token path: {token_p}, creds path: {creds_p}")
    
    try:
        # The CalendarClient expects token_path and credentials_path to be relative to project root if not absolute.
        # Config already resolves them to be effectively relative to project root or absolute from .env
        calendar_client = CalendarClient(email_address=monitored_account, 
                                         token_path=token_p, # This is the *name* of the token file, e.g. 'gmail_token_hello_calendar.json'
                                         credentials_path=creds_p) # This is the *name* of creds file, e.g. 'credentials.json'
        
        now = datetime.utcnow() # Test with UTC
        start_iso = now.isoformat() + 'Z'
        end_iso = (now + timedelta(days=7)).isoformat() + 'Z'
        
        logger.info(f"\nTesting get_availability for next 7 days ({start_iso} to {end_iso})...")
        busy_slots = calendar_client.get_availability(start_iso, end_iso)
        if busy_slots is not None:
            logger.info(f"Busy slots: {json.dumps(busy_slots, indent=2)}")
        else:
            logger.error("Failed to get availability.")

        logger.info("\nTesting create_event...")
        event_start_dt = (now + timedelta(days=2, hours=3)).replace(minute=0, second=0, microsecond=0)
        event_end_dt = (event_start_dt + timedelta(hours=1))
        event_summary = "Automated Test Appointment via CalendarClient"
        
        created_event_details = calendar_client.create_event(
            summary=event_summary,
            start_datetime_iso=event_start_dt.isoformat() + 'Z',
            end_datetime_iso=event_end_dt.isoformat() + 'Z',
            attendees=[monitored_account] 
        )
        if created_event_details:
            logger.info(f"Event '{event_summary}' created successfully. ID: {created_event_details.get('id')}")
        else:
            logger.error(f"Failed to create event '{event_summary}'.")

    except ValueError as ve:
        # This likely means token or credentials file issues from CalendarClient init
        logger.error(f"ValueError during CalendarClient test (check token/credentials files and paths): {ve}", exc_info=True)
    except Exception as e:
        logger.error(f"An unexpected error occurred during CalendarClient test: {e}", exc_info=True) 
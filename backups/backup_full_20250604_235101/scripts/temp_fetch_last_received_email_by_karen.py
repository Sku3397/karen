import os
import sys
from dotenv import load_dotenv
import logging
import json # For pretty printing email data
from datetime import datetime, timedelta, timezone # For filtering recent emails

# Add the project root to the sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Load environment variables
dotenv_path = os.path.join(project_root, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
    # print(f"Loaded .env from {dotenv_path}") # Quieter for loops
else:
    print(f"Warning: .env file not found at {dotenv_path}")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from src import config
    from src.email_client import EmailClient
    # logger.info("Successfully imported config and EmailClient.") # Quieter for loops
except ImportError as e:
    logger.error(f"Failed to import necessary modules: {e}", exc_info=True)
    sys.exit(1)

def fetch_specific_reply(account_email: str, token_path: str, expected_subject_prefix: str, since_minutes: int = 15):
    logger.info(f"Attempting to find reply starting with '{expected_subject_prefix}' in {account_email} in the last {since_minutes} minutes.")
    try:
        email_client = EmailClient(
            email_address=account_email,
            token_file_path=token_path
        )

        date_since_str = (datetime.now(timezone.utc) - timedelta(minutes=since_minutes)).strftime('%Y/%m/%d') # Use timezone-aware now
        search_criteria = f'after:{date_since_str}' 
        
        received_emails = email_client.fetch_emails(search_criteria=search_criteria, max_results=10)

        if not received_emails:
            logger.warning(f"No recent emails found for {account_email} matching criteria '{search_criteria}'.")
            return None

        found_reply = None
        for email_data in received_emails:
            subject = email_data.get('subject', '')
            if subject.startswith(expected_subject_prefix):
                logger.info(f"Found potential reply: Subject '{subject}'")
                found_reply = email_data
                break # Take the first match, which should be the most recent if sorted by date
        
        if found_reply:
            print(f"\n--- Found Reply in {account_email} ---")
            print(f"Subject: {found_reply.get('subject', 'N/A')}")
            print(f"Sender: {found_reply.get('sender', 'N/A')}")
            print(f"Date: {found_reply.get('date_iso', 'N/A')}")
            print(f"UID: {found_reply.get('uid', 'N/A')}")
            print("\nBody:")
            body_content = found_reply.get('body_text', '') or found_reply.get('body_html', '')
            print(body_content if body_content else 'N/A - Body not found in fetched data.')
            print("\n-------------------------------")
            # Ensure found_reply contains body for checking, even if it was N/A for printing
            if not body_content:
                logger.warning("Body content was empty in the found reply object from fetch_emails.")
                # We might need to explicitly add body_text and body_html to the dict if they are None to avoid check issues
                found_reply['body_text'] = found_reply.get('body_text', '')
                found_reply['body_html'] = found_reply.get('body_html', '')
            return found_reply
        else:
            logger.warning(f"Could not find an email with subject starting with '{expected_subject_prefix}' in the {len(received_emails)} fetched emails.")
            return None

    except Exception as e:
        logger.error(f"An error occurred while fetching reply for {account_email}: {e}", exc_info=True)
        return None

if __name__ == "__main__":
    # The customer query email had subject: "Question about fence repair - End-to-End Test"
    # The reply from Karen should have a subject like "Re: Question about fence repair - End-to-End Test"
    reply_subject_prefix = "Re: Question about fence repair - End-to-End Test"
    
    logger.info(f"Looking for Karen's reply to customer query, expecting subject starting with '{reply_subject_prefix}'")
    
    latest_reply = fetch_specific_reply(
        account_email=config.SECRETARY_EMAIL_ADDRESS, # Karen's replies will be in her own sent items / or received by her if she was the original sender
        token_path=config.SECRETARY_TOKEN_PATH_CONFIG,
        expected_subject_prefix=reply_subject_prefix,
        since_minutes=5 # Check last 5 minutes, should be sufficient
    )
    
    if latest_reply:
        body_text = latest_reply.get('body_text', '') 
        body_html = latest_reply.get('body_html', '')
        full_body_content_for_check = (body_text + " " + body_html).lower()
        
        # Define the unique phrase from the *newly loaded* system prompt
        expected_phrase_in_reply = "KAREN_SEES_THE_SEA_SHORE_V4_EDGE_CASE_TEST".lower()
        correct_phone = "757-354-4577"

        if not full_body_content_for_check.strip():
            logger.error("FAIL: Reply body was effectively empty after fetching.")
            phrase_found = False
            correct_phone_found = False
        else:
            phrase_found = expected_phrase_in_reply in full_body_content_for_check
            correct_phone_found = correct_phone in full_body_content_for_check

        if phrase_found:
            logger.info(f"PASS: Expected unique phrase '{expected_phrase_in_reply}' (from updated prompt) found in the reply.")
        else:
            logger.error(f"FAIL: Expected unique phrase '{expected_phrase_in_reply}' NOT found in the reply (or body was empty).")
        
        if correct_phone_found:
            logger.info(f"PASS: Correct phone number '{correct_phone}' found in the reply.")
        else:
            logger.error(f"FAIL: Correct phone number '{correct_phone}' NOT found in the reply (or body was empty).")
            
    else:
        logger.error(f"FAIL: Could not retrieve Karen's reply email with subject starting '{reply_subject_prefix}'.") 
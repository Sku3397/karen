import os
import sys
import logging
import json
from dotenv import load_dotenv
from datetime import datetime

# Add project root to sys.path to allow aletheiaimports if script is run from root
PROJECT_ROOT_FOR_SCRIPT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT_FOR_SCRIPT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_FOR_SCRIPT)

try:
    from src.email_client import EmailClient
    # Import necessary config variables directly, relying on .env for values
except ImportError as e:
    print(f"Error importing EmailClient: {e}")
    sys.exit(1)

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

NUM_EMAILS_TO_FETCH = 5 # Fetch the last 5 emails
# RECIPIENT_TO_FILTER_BY = "respectisbliss@gmail.com" # Commented out for broader search

def main():
    # Load .env file from project root (one level up from src/)
    dotenv_path = os.path.join(PROJECT_ROOT_FOR_SCRIPT, '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path=dotenv_path)
        logger.info(f"Loaded .env file from {dotenv_path}")
    else:
        logger.warning(f".env file not found at {dotenv_path}. Relying on environment variables if set.")

    # Use SECRETARY_EMAIL_ADDRESS and SECRETARY_TOKEN_PATH for Karen's actual sending account
    # These should be defined in your .env file
    actual_karen_email_address = os.getenv("SECRETARY_EMAIL_ADDRESS", "karensecretaryai@gmail.com")
    raw_token_file_name = os.getenv("SECRETARY_TOKEN_PATH", "gmail_token_karen.json") 
    actual_karen_token_file = raw_token_file_name.split('#')[0].strip() # Strip comments and whitespace

    if not actual_karen_email_address or not actual_karen_token_file:
        logger.error("SECRETARY_EMAIL_ADDRESS or SECRETARY_TOKEN_PATH not found in .env or defaults are missing.")
        return

    logger.info(f"Initializing EmailClient for Karen's sending account ({actual_karen_email_address}) with token file: '{actual_karen_token_file}'")
    
    # --- BEGIN ADDED DEBUGGING ---
    # Construct the full path similar to how EmailClient does (assuming EmailClient uses PROJECT_ROOT)
    # PROJECT_ROOT_FOR_SCRIPT is already defined as os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    full_token_path_in_script = os.path.join(PROJECT_ROOT_FOR_SCRIPT, actual_karen_token_file)
    logger.info(f"Script pre-check: Full path to token file being checked: {full_token_path_in_script}")
    if os.path.exists(full_token_path_in_script):
        logger.info(f"Script pre-check: SUCCESS - Token file '{full_token_path_in_script}' EXISTS according to os.path.exists().")
        try:
            with open(full_token_path_in_script, 'r') as f_test:
                logger.info(f"Script pre-check: SUCCESS - Able to open '{full_token_path_in_script}' for reading.")
                # Optionally, read a bit or log stats
                content_preview = f_test.read(50)
                logger.info(f"Script pre-check: Content preview (first 50 chars): '{content_preview[:50]}'")
        except Exception as e_open:
            logger.error(f"Script pre-check: ERROR - Token file '{full_token_path_in_script}' EXISTS, but FAILED to open for reading: {e_open}", exc_info=True)
    else:
        logger.error(f"Script pre-check: ERROR - Token file '{full_token_path_in_script}' DOES NOT EXIST according to os.path.exists().")
    # --- END ADDED DEBUGGING ---

    try:
        email_client = EmailClient(email_address=actual_karen_email_address, token_file_path=actual_karen_token_file)
    except Exception as e:
        logger.error(f"Failed to initialize EmailClient: {e}", exc_info=True)
        return

    logger.info(f"Fetching the last {NUM_EMAILS_TO_FETCH} emails sent by {actual_karen_email_address} (full content)...")
    
    try:
        email_details_list = email_client.fetch_last_n_sent_emails(
            n=NUM_EMAILS_TO_FETCH, 
            metadata_only=False # Fetch full content
        )
    except Exception as e:
        logger.error(f"An error occurred while fetching email: {e}", exc_info=True)
        email_details_list = None

    if not email_details_list:
        logger.info(f"No email found or an error occurred for {actual_karen_email_address}.")
        return

    logger.info(f"Details for the last {len(email_details_list)} emails sent by {actual_karen_email_address} found:\n")
    
    for i, email_details in enumerate(email_details_list):
        print(f"--- EMAIL {i+1} OF {len(email_details_list)} (FULL CONTENT) ---")
        print(f"  ID: {email_details.get('id')}")
        
        date_iso = email_details.get('date_iso')
        formatted_date = date_iso
        if date_iso:
            try:
                dt_object = datetime.fromisoformat(date_iso.replace('Z', '+00:00'))
                formatted_date = dt_object.strftime("%Y-%m-%d %H:%M:%S %Z")
            except ValueError:
                pass 
        print(f"  Sent Date: {formatted_date if formatted_date else 'N/A'}")

        print(f"  From: {email_details.get('sender')}") # Should be actual_karen_email_address
        print(f"  To: {email_details.get('recipient')}")
        print(f"  Subject: {email_details.get('subject')}")
        print(f"  Snippet: {email_details.get('snippet')}")
        print(f"--- Body ---\n{email_details.get('body_text', 'No body text found.')}")
        print("-----------------------------------\n")

if __name__ == "__main__":
    main() 
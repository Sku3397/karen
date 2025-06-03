import os
import sys
from dotenv import load_dotenv
from typing import Dict, Any, Optional, List
import logging
import json # For pretty printing email data

# Add the project root to the sys.path to allow imports from src
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Load environment variables
dotenv_path = os.path.join(project_root, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
    print(f"Loaded .env from {dotenv_path}")
else:
    print(f"Warning: .env file not found at {dotenv_path}")

# Configure a basic logger for this script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Re-import config and EmailClient after loading dotenv to ensure latest env vars are used
try:
    from src import config
    from src.email_client import EmailClient
    logger.info("Successfully imported config and EmailClient.")
except ImportError as e:
    logger.error(f"Failed to import necessary modules: {e}", exc_info=True)
    sys.exit(1)

def get_email_client_config(is_sending_client: bool) -> Dict[str, Any]:
    """Helper to get the correct email client configuration."""
    if is_sending_client:
        return {
            "email_address": config.MONITORED_EMAIL_ACCOUNT_CONFIG, # Karen's primary sending account
            "token_path": config.MONITORED_EMAIL_TOKEN_PATH_CONFIG,
            "smtp_server": config.SECRETARY_EMAIL_SMTP_SERVER,
            "smtp_port": config.SECRETARY_EMAIL_SMTP_PORT,
            "imap_server": config.SECRETARY_EMAIL_IMAP_SERVER,
            "imap_port": config.SECRETARY_EMAIL_IMAP_PORT
        }
    else: # For monitoring (reading)
        return {
            "email_address": config.MONITORED_EMAIL_ACCOUNT_CONFIG,
            "token_path": config.MONITORED_EMAIL_TOKEN_PATH_CONFIG,
            "smtp_server": config.SECRETARY_EMAIL_SMTP_SERVER,
            "smtp_port": config.SECRETARY_EMAIL_SMTP_PORT,
            "imap_server": config.SECRETARY_EMAIL_IMAP_SERVER,
            "imap_port": config.SECRETARY_EMAIL_IMAP_PORT
        }

def fetch_last_sent_email_from_karen():
    logger.info("Attempting to fetch the last email sent by Karen (via MONITORED_EMAIL_ACCOUNT).") # Clarified log for general use
    try:
        # Initialize the EmailClient for Karen's primary sending account (MONITORED_EMAIL_ACCOUNT)
        # This helper by default returns MONITORED_EMAIL_ACCOUNT for is_sending_client=True
        sending_client_cfg = get_email_client_config(is_sending_client=True)
        email_client = EmailClient(
            email_address=sending_client_cfg["email_address"], 
            token_file_path=sending_client_cfg["token_path"]
        )
        logger.info(f"EmailClient initialized for {sending_client_cfg['email_address']}.")

        # Fetch emails from the 'sent' folder, sorted by date descending, limit to 1
        # The query 'in:sent' is for sent mails
        # 'all' to get all emails, not just unread.
        # sort by date descending to get the latest.
        # max_results=1 for just the latest
        sent_emails = email_client.fetch_last_n_sent_emails(
            n=5 # Fetch the last 5 sent emails, no recipient filter
            # recipient_filter="test@example.com" # Removed dummy filter
        )

        if sent_emails:
            last_sent_email = sent_emails[0] # Still display the most recent of the filtered results
            print("\n--- Last Email Sent by Karen (using fetch_last_n_sent_emails, no recipient filter) ---")
            print(f"Subject: {last_sent_email.get('subject', 'N/A')}")
            print(f"Sender: {last_sent_email.get('sender', 'N/A')}")
            print(f"Recipient: {last_sent_email.get('recipient', 'N/A')}") # This might not be directly available
            print(f"Date: {last_sent_email.get('date_iso', 'N/A')}") # Corrected to use 'date_iso'
            print("\nBody:")
            # Corrected to use 'body_text' or 'body_html'
            body_content = last_sent_email.get('body_text') or last_sent_email.get('body_html')
            print(body_content if body_content else 'N/A')
            print("\n-------------------------------")
        else:
            print("No emails found in Karen's sent folder.")

    except Exception as e:
        logger.error(f"An error occurred while fetching Karen's last sent email: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    fetch_last_sent_email_from_karen() 
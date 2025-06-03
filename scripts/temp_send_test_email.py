import os
import sys
from dotenv import load_dotenv
import logging
# import asyncio # Not strictly needed for synchronous send_email

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Load .env
dotenv_path = os.path.join(project_root, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
    print(f"Loaded .env from {dotenv_path}")
else:
    print(f"Warning: .env file not found at {dotenv_path}")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from src.email_client import EmailClient
    from src import config # To get email accounts and token paths
    logger.info("Successfully imported EmailClient and config.")
except ImportError as e:
    logger.error(f"Failed to import EmailClient or config: {e}", exc_info=True)
    sys.exit(1)

def send_customer_query_to_monitor(subject: str, body: str):
    logger.info(f"Attempting to send a customer query email from {config.SECRETARY_EMAIL_ADDRESS} (acting as customer) to {config.MONITORED_EMAIL_ACCOUNT_CONFIG}")
    try:
        # Use SECRETARY_EMAIL_ADDRESS (karensecretaryai@gmail.com) as the sender for this test
        sender_email_address = config.SECRETARY_EMAIL_ADDRESS 
        sender_token_file = config.SECRETARY_TOKEN_PATH_CONFIG
        recipient_address = config.MONITORED_EMAIL_ACCOUNT_CONFIG # hello@757handy.com

        if not sender_email_address or not sender_token_file:
            logger.error("SECRETARY_EMAIL_ADDRESS or SECRETARY_TOKEN_PATH_CONFIG is not set.")
            sys.exit(1)
        
        logger.info(f"Using sender email: {sender_email_address} and token file: {sender_token_file}")

        email_client_sender = EmailClient(
            email_address=sender_email_address,
            token_file_path=sender_token_file 
        )
        logger.info(f"EmailClient initialized for sender {sender_email_address}.")
        
        logger.info(f"Sending customer query to: {recipient_address} with subject: '{subject}'")
        
        success = email_client_sender.send_email(
            to=recipient_address,
            subject=subject,
            body=body
        )

        if success:
            logger.info(f"Customer query email successfully sent from {sender_email_address} to {recipient_address}.")
            print(f"SUCCESS: Customer query email sent from {sender_email_address} to {recipient_address}.")
        else:
            logger.error(f"Failed to send customer query email from {sender_email_address} to {recipient_address}.")
            print(f"FAILURE: Failed to send customer query email from {sender_email_address} to {recipient_address}.")

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        print(f"ERROR: An exception occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    customer_subject = "Question about fence repair - End-to-End Test"
    customer_body = (
        "Hi Beach Handyman,\n\nI have a section of my fence that needs repair. Can you help with that?\n"
        "Looking forward to your reply.\n\nThanks,\nA Potential Customer"
    )
    send_customer_query_to_monitor(subject=customer_subject, body=customer_body) 
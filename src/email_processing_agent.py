import sys
import os
import time
import logging
from dotenv import load_dotenv
from datetime import datetime, timezone

# Load environment variables from .env file
load_dotenv()

# Adjust path to include the src directory for importing EmailClient
# Assumes this script is in the src/ directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# If this script is in src/, then PROJECT_ROOT is correct.
# If this script were in project_root/agents/, then PROJECT_ROOT needs os.path.join(..., '..')
sys.path.insert(0, PROJECT_ROOT) # Prepend project root to allow src.email_client import
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src')) # Ensure src is also in path

from src.email_client import EmailClient # Assuming email_client.py is in src/
from src.ai_responder import generate_response # Import the AI responder

SECRETARY_EMAIL_ADDRESS = os.getenv('SECRETARY_EMAIL_ADDRESS')
ADMIN_EMAIL_ADDRESS = os.getenv('ADMIN_EMAIL_ADDRESS') # Load admin email
POLLING_INTERVAL_SECONDS = int(os.getenv('POLLING_INTERVAL_SECONDS', 30))
MAX_EMAILS_PER_FETCH = int(os.getenv('MAX_EMAILS_PER_FETCH', 5))
LOG_DIR = os.path.join(PROJECT_ROOT, 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'email_agent_activity.log')

# Define senders/subjects to ignore (basic filtering)
IGNORE_SENDERS_CONTAINING = [
    'mailer-daemon@googlemail.com',
    'noreply',
    'no-reply'
]
IGNORE_SUBJECTS_CONTAINING = [
    'delivery status notification',
    'undeliverable',
    'auto-reply',
    'out of office'
]

AGENT_START_TIME = datetime.now(timezone.utc) # Store agent start time as timezone-aware UTC

def setup_logging():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    # Remove existing handlers to avoid duplicate logs if re-running in same session
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'), # Specify UTF-8 encoding
            logging.StreamHandler(sys.stdout) # Also print to console
        ]
    )

def main_loop():
    if not SECRETARY_EMAIL_ADDRESS:
        logging.error("Error: SECRETARY_EMAIL_ADDRESS not found. Agent cannot start.")
        return
    if not ADMIN_EMAIL_ADDRESS:
        logging.warning("Warning: ADMIN_EMAIL_ADDRESS not found. Startup notification will not be sent.")
    if not os.getenv('GEMINI_API_KEY'):
        logging.error("CRITICAL: GEMINI_API_KEY not found in .env. AI responses will fail. Agent stopping.")
        return

    logging.info(f"--- Email Processing Agent for {SECRETARY_EMAIL_ADDRESS} --- STARTED at {AGENT_START_TIME.isoformat()} ---")
    logging.info(f"Processing general incoming emails. Polling every {POLLING_INTERVAL_SECONDS} seconds.")
    logging.info(f"Activity will be logged to: {LOG_FILE}")

    client = None # Initialize client to None
    try:
        client = EmailClient(email_address=SECRETARY_EMAIL_ADDRESS)
        logging.info("EmailClient initialized successfully.")
        
        if ADMIN_EMAIL_ADDRESS and client: # Ensure client is not None before using
            startup_subject = f"Secretary Email Agent Started for {SECRETARY_EMAIL_ADDRESS}"
            startup_body = f"The AI Handyman Secretary email processing agent for {SECRETARY_EMAIL_ADDRESS} has started successfully at {AGENT_START_TIME.isoformat()}\nIt will only process emails received after this time."
            logging.info(f"Sending startup notification to admin: {ADMIN_EMAIL_ADDRESS}")
            client.send_email(to=ADMIN_EMAIL_ADDRESS, subject=startup_subject, body=startup_body)
    except ValueError as e:
        logging.error(f"CRITICAL: Failed to initialize EmailClient: {e}. Agent cannot start.")
        return
    except Exception as e:
        logging.error(f"CRITICAL: Unexpected error initializing EmailClient or sending startup email: {e}. Agent cannot start.", exc_info=True)
        return

    if not client:
        logging.error("CRITICAL: EmailClient was not initialized (likely due to an error caught above). Agent cannot proceed.")
        return

    while True:
        try:
            logging.info(f"Checking for unread emails received after {AGENT_START_TIME.isoformat()}...")
            unread_emails = client.fetch_emails(max_results=MAX_EMAILS_PER_FETCH)

            if not unread_emails:
                logging.info("No new unread emails found meeting criteria.")
            else:
                logging.info(f"Fetched {len(unread_emails)} unread emails. Filtering by date and content...")
                processed_count = 0
                for i, email_data in enumerate(unread_emails):
                    msg_id = email_data.get('id')
                    sender_full = email_data.get('sender', '')
                    subject = email_data.get('subject', '').lower() 
                    received_dt = email_data.get('received_date_dt')
                    body = email_data.get('body')

                    # Prepare subject for logging to avoid f-string issues
                    log_subject = email_data.get('subject', '') # Get original subject for logging
                    log_received_dt = received_dt.isoformat() if received_dt else 'N/A'
                    logging.info(f"  Inspecting Email #{i+1}: ID={msg_id}, From='{sender_full}', Subject='{log_subject}', Received='{log_received_dt}'")

                    # 1. Filter by Date
                    if received_dt is None:
                        logging.info(f"    Skipping email ID {msg_id}: No received date available.")
                        client.mark_email_as_read(message_id=msg_id) # Mark as read to avoid re-fetching
                        continue
                    
                    # Ensure received_dt is timezone-aware for comparison with AGENT_START_TIME
                    if received_dt.tzinfo is None:
                        received_dt = received_dt.replace(tzinfo=timezone.utc) # Assume UTC if naive

                    if received_dt < AGENT_START_TIME:
                        logging.info(f"    Skipping email ID {msg_id}: Received ({received_dt.isoformat()}) before agent start time ({AGENT_START_TIME.isoformat()}).")
                        client.mark_email_as_read(message_id=msg_id)
                        continue

                    # 2. Filter by Sender/Subject (Basic Spam/Auto-reply Filter)
                    sender_lower = sender_full.lower()
                    skip_email = False
                    for pattern in IGNORE_SENDERS_CONTAINING:
                        if pattern in sender_lower:
                            logging.info(f"    Skipping email ID {msg_id} from '{sender_full}': Sender matches ignore pattern '{pattern}'.")
                            skip_email = True
                            break
                    if skip_email:
                        client.mark_email_as_read(message_id=msg_id)
                        continue
                    
                    for pattern in IGNORE_SUBJECTS_CONTAINING:
                        if pattern in subject:
                            logging.info(f"    Skipping email ID {msg_id} with subject '{email_data.get('subject','')}': Subject matches ignore pattern '{pattern}'.")
                            skip_email = True
                            break
                    if skip_email:
                        client.mark_email_as_read(message_id=msg_id)
                        continue
                    
                    logging.info(f"  Processing Email ID {msg_id} from '{sender_full}'. Looks like a legitimate email received after agent start.")
                    processed_count += 1

                    # Extract simple email address from sender_full
                    sender_email_address = sender_full
                    if sender_full and '<' in sender_full and '>' in sender_full:
                        sender_email_address = sender_full[sender_full.find('<') + 1 : sender_full.find('>')]
                    
                    logging.info(f"  Generating AI response for email from '{sender_email_address}', subject: '{email_data.get('subject','')}'")
                    ai_response_text = generate_response(subject=email_data.get('subject',''), sender=sender_email_address, body=body if body else email_data.get('snippet', ''))
                    
                    if ai_response_text and not ai_response_text.startswith("Error:"):
                        reply_subject = f"Re: {email_data.get('subject','No Subject')}"
                        logging.info(f"    AI Response Generated. Sending reply to '{sender_email_address}' with subject '{reply_subject}'.")
                        logging.debug(f"    Reply Body: {ai_response_text}")
                        send_success = client.send_email(to=sender_email_address, subject=reply_subject, body=ai_response_text)
                        if send_success:
                            logging.info(f"      Successfully sent reply for email ID {msg_id}.")
                        else:
                            logging.warning(f"      Failed to send reply for email ID {msg_id}.")
                    else:
                        logging.warning(f"    No valid AI response generated or AI error for email ID {msg_id}. Response: '{ai_response_text}'. Not sending reply.")

                    logging.info(f"  Marking email ID {msg_id} as read after processing.")
                    mark_success = client.mark_email_as_read(message_id=msg_id)
                    if mark_success:
                        logging.info(f"    Successfully marked ID {msg_id} as read.")
                    else:
                        logging.warning(f"    Failed to mark ID {msg_id} as read.")
                
                if processed_count == 0 and len(unread_emails) > 0:
                    logging.info("All fetched unread emails were filtered out (too old or matched ignore patterns).")
            
            logging.info(f"Polling cycle complete. Sleeping for {POLLING_INTERVAL_SECONDS} seconds.")
            time.sleep(POLLING_INTERVAL_SECONDS)

        except KeyboardInterrupt:
            logging.info("Agent shutting down due to KeyboardInterrupt.")
            break
        except Exception as e:
            logging.error(f"An error occurred in the main loop: {e}", exc_info=True)
            logging.info(f"Loop will continue after a brief pause (1 minute) due to error.")
            time.sleep(60)

if __name__ == "__main__":
    setup_logging()
    main_loop() 
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
# Import necessary config variables
from src.config import (
    SECRETARY_EMAIL_ADDRESS,  # This is karensecretaryai@gmail.com
    SECRETARY_TOKEN_PATH_CONFIG,
    MONITORED_EMAIL_ACCOUNT_CONFIG, # This is hello@757handy.com
    MONITORED_EMAIL_TOKEN_PATH_CONFIG,
    ADMIN_EMAIL_ADDRESS,
    GEMINI_API_KEY # Used for check
)

POLLING_INTERVAL_SECONDS = int(os.getenv('POLLING_INTERVAL_SECONDS', 30))
MAX_EMAILS_PER_FETCH = int(os.getenv('MAX_EMAILS_PER_FETCH', 5))
LOG_DIR = os.path.join(PROJECT_ROOT, 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'email_agent_activity.log')
LLM_PROMPT_FILE = os.path.join(PROJECT_ROOT, 'src', 'llm_system_prompt.txt') # Path to the prompt file

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

INSTRUCTION_EMAIL_SUBJECT = "UPDATE PROMPT" # Changed from "UPDATE_KAREN_PROMPT"

AGENT_START_TIME = datetime.now(timezone.utc) # Store agent start time as timezone-aware UTC

def setup_logging():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    # Remove existing handlers to avoid duplicate logs if re-running in same session
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(module)s - %(message)s', # Added module
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'), # Specify UTF-8 encoding
            logging.StreamHandler(sys.stdout) # Also print to console
        ]
    )

def update_llm_prompt(new_prompt_text: str):
    """Writes the new prompt text to the LLM prompt file."""
    try:
        with open(LLM_PROMPT_FILE, 'w', encoding='utf-8') as f:
            f.write(new_prompt_text)
        logging.info(f"Successfully updated LLM system prompt in {LLM_PROMPT_FILE}")
        # Optionally, trigger LLMClient to reload prompt if it caches it and doesn't re-read per request
        # For now, LLMClient re-reads it when get_system_prompt() is called if not cached,
        # or _load_system_prompt() can be called if an instance is available.
        # The current LLMClient loads on init, so a restart of processes using it would be needed,
        # or LLMClient needs a reload method. The implemented LLMClient loads template on init,
        # but fills date dynamically. A full reload of the template isn't built-in yet.
        # For simplicity now, process restart or a future LLMClient enhancement would pick it up.
    except Exception as e:
        logging.error(f"Failed to update LLM system prompt file {LLM_PROMPT_FILE}: {e}", exc_info=True)

def process_instruction_emails(instruction_client: EmailClient):
    """Fetches and processes emails for updating the LLM prompt."""
    if not instruction_client:
        logging.warning("Instruction email client not available, skipping prompt update check.")
        return

    logging.info(f"Checking for instruction emails in {instruction_client.email_address}...")
    try:
        instruction_emails = instruction_client.fetch_emails(
            search_criteria=f'UNREAD subject:("{INSTRUCTION_EMAIL_SUBJECT}")', # Search for specific subject
            max_results=MAX_EMAILS_PER_FETCH
        )

        if not instruction_emails:
            logging.info(f"No new instruction emails found with subject '{INSTRUCTION_EMAIL_SUBJECT}'.")
            return

        logging.info(f"Found {len(instruction_emails)} potential instruction emails.")
        latest_instruction_email = None
        
        # Find the most recent valid instruction email
        for email_data in sorted(instruction_emails, key=lambda x: x.get('received_date_dt', datetime.min.replace(tzinfo=timezone.utc)), reverse=True):
            msg_id = email_data.get('id')
            subject = email_data.get('subject', '').lower()
            received_dt = email_data.get('received_date_dt')

            if received_dt and received_dt.tzinfo is None: # Ensure timezone aware
                received_dt = received_dt.replace(tzinfo=timezone.utc)

            if received_dt and received_dt < AGENT_START_TIME:
                logging.info(f"  Skipping instruction email ID {msg_id}: Received ({received_dt.isoformat()}) before agent start time.")
                instruction_client.mark_email_as_read(message_id=msg_id)
                continue

            if INSTRUCTION_EMAIL_SUBJECT.lower() in subject:
                latest_instruction_email = email_data
                logging.info(f"  Found valid instruction email ID {msg_id} from '{email_data.get('sender')}' with subject '{email_data.get('subject')}'. This is the latest.")
                break # Process only the newest one that meets criteria
            else:
                # This case should ideally not happen due to Gmail search_criteria, but good to log
                logging.info(f"  Email ID {msg_id} subject '{email_data.get('subject')}' did not match '{INSTRUCTION_EMAIL_SUBJECT}' despite search. Marking as read.")
                instruction_client.mark_email_as_read(message_id=msg_id)


        if latest_instruction_email:
            prompt_content = latest_instruction_email.get('body')
            email_id_to_mark = latest_instruction_email.get('id')
            sender_of_instruction = latest_instruction_email.get('sender', 'Unknown Sender') # Get sender for confirmation

            if prompt_content and email_id_to_mark:
                logging.info(f"Updating LLM prompt with content from email ID {email_id_to_mark} from {sender_of_instruction}.")
                logging.debug(f"New prompt content (first 100 chars): {prompt_content[:100]}...")
                update_llm_prompt(prompt_content)
                instruction_client.mark_email_as_read(message_id=email_id_to_mark)
                logging.info(f"Marked instruction email ID {email_id_to_mark} as read.")

                # Send confirmation email to ADMIN_EMAIL_ADDRESS
                if ADMIN_EMAIL_ADDRESS:
                    try:
                        confirmation_subject = "LLM System Prompt Updated Successfully"
                        confirmation_body = (
                            f"The LLM system prompt for Karen has been successfully updated.\n\n"
                            f"Instruction was received from: {sender_of_instruction}\n"
                            f"Email ID: {email_id_to_mark}\n"
                            f"Timestamp: {datetime.now(timezone.utc).isoformat()}\n\n"
                            f"The first 100 characters of the new prompt are:\n'{prompt_content[:100]}...'\n\n"
                            f"The change will take effect the next time the LLMClient is initialized or reloads its prompt (typically on application restart or new LLM query if designed to reload)."
                        )
                        logging.info(f"Sending prompt update confirmation to {ADMIN_EMAIL_ADDRESS} from {instruction_client.email_address}")
                        success = instruction_client.send_email(
                            to=ADMIN_EMAIL_ADDRESS,
                            subject=confirmation_subject,
                            body=confirmation_body
                        )
                        if success:
                            logging.info(f"Successfully sent prompt update confirmation to {ADMIN_EMAIL_ADDRESS}.")
                        else:
                            logging.warning(f"Failed to send prompt update confirmation to {ADMIN_EMAIL_ADDRESS}.")
                    except Exception as e_confirm:
                        logging.error(f"Error sending prompt update confirmation email: {e_confirm}", exc_info=True)
            else:
                logging.warning(f"Instruction email ID {email_id_to_mark} had no body content. Not updating prompt.")
                if email_id_to_mark:
                    instruction_client.mark_email_as_read(message_id=email_id_to_mark) # Still mark as read

        # Mark any other fetched emails (if any older ones were fetched by subject before date filtering) as read
        for email_data in instruction_emails:
            if email_data != latest_instruction_email: # Avoid double marking
                msg_id_old = email_data.get('id')
                if msg_id_old:
                    logging.info(f"  Marking older/processed instruction email ID {msg_id_old} as read.")
                    instruction_client.mark_email_as_read(message_id=msg_id_old)
                    
    except Exception as e:
        logging.error(f"Error processing instruction emails for {instruction_client.email_address}: {e}", exc_info=True)

def main_loop():
    # Validate essential configurations
    if not MONITORED_EMAIL_ACCOUNT_CONFIG:
        logging.error("Error: MONITORED_EMAIL_ACCOUNT_CONFIG not found. This is the primary email for Karen. Agent cannot start.")
        return
    if not MONITORED_EMAIL_TOKEN_PATH_CONFIG:
        logging.error(f"Error: MONITORED_EMAIL_TOKEN_PATH_CONFIG not found for {MONITORED_EMAIL_ACCOUNT_CONFIG}. Agent cannot start.")
        return
    if not SECRETARY_EMAIL_ADDRESS: # This is karensecretaryai@gmail.com
        logging.warning("Warning: SECRETARY_EMAIL_ADDRESS (for instruction emails) not found. Prompt updates via email will be disabled.")
    if not SECRETARY_TOKEN_PATH_CONFIG and SECRETARY_EMAIL_ADDRESS:
        logging.warning(f"Warning: SECRETARY_TOKEN_PATH_CONFIG not found for {SECRETARY_EMAIL_ADDRESS}. Prompt updates via email will be disabled.")
    if not ADMIN_EMAIL_ADDRESS:
        logging.warning("Warning: ADMIN_EMAIL_ADDRESS not found. Startup notification will not be sent.")
    if not GEMINI_API_KEY:
        logging.error("CRITICAL: GEMINI_API_KEY not found in .env. AI responses will fail. Agent stopping.")
        return

    logging.info(f"--- Email Processing Agent --- STARTED at {AGENT_START_TIME.isoformat()} ---")
    logging.info(f"Primary Email (Monitoring & Sending): {MONITORED_EMAIL_ACCOUNT_CONFIG}")
    logging.info(f"Instruction Email (Prompt Updates): {SECRETARY_EMAIL_ADDRESS if SECRETARY_EMAIL_ADDRESS else 'Disabled'}")
    logging.info(f"Polling every {POLLING_INTERVAL_SECONDS} seconds. Activity log: {LOG_FILE}")
    logging.info(f"LLM System Prompt File: {LLM_PROMPT_FILE}")


    primary_email_client = None
    instruction_email_client = None

    try:
        logging.info(f"Initializing EmailClient for primary account: {MONITORED_EMAIL_ACCOUNT_CONFIG} with token {MONITORED_EMAIL_TOKEN_PATH_CONFIG}")
        primary_email_client = EmailClient(
            email_address=MONITORED_EMAIL_ACCOUNT_CONFIG,
            token_file_path=MONITORED_EMAIL_TOKEN_PATH_CONFIG
        )
        logging.info(f"Primary EmailClient for {MONITORED_EMAIL_ACCOUNT_CONFIG} initialized successfully.")

        if ADMIN_EMAIL_ADDRESS and primary_email_client:
            startup_subject = f"Karen AI Agent Started for {MONITORED_EMAIL_ACCOUNT_CONFIG}"
            startup_body = f"The Karen AI email processing agent for {MONITORED_EMAIL_ACCOUNT_CONFIG} has started successfully at {AGENT_START_TIME.isoformat()}\nIt will process emails to this account and send replies from this account.\nIt will only process emails received after this time."
            logging.info(f"Sending startup notification to admin: {ADMIN_EMAIL_ADDRESS} from {MONITORED_EMAIL_ACCOUNT_CONFIG}")
            primary_email_client.send_email(to=ADMIN_EMAIL_ADDRESS, subject=startup_subject, body=startup_body)

    except ValueError as e:
        logging.error(f"CRITICAL: Failed to initialize primary EmailClient for {MONITORED_EMAIL_ACCOUNT_CONFIG}: {e}. Agent cannot start.", exc_info=True)
        return
    except Exception as e:
        logging.error(f"CRITICAL: Unexpected error initializing primary EmailClient ({MONITORED_EMAIL_ACCOUNT_CONFIG}) or sending startup email: {e}. Agent cannot start.", exc_info=True)
        return

    if SECRETARY_EMAIL_ADDRESS and SECRETARY_TOKEN_PATH_CONFIG:
        try:
            logging.info(f"Initializing EmailClient for instruction account: {SECRETARY_EMAIL_ADDRESS} with token {SECRETARY_TOKEN_PATH_CONFIG}")
            instruction_email_client = EmailClient(
                email_address=SECRETARY_EMAIL_ADDRESS,
                token_file_path=SECRETARY_TOKEN_PATH_CONFIG
            )
            logging.info(f"Instruction EmailClient for {SECRETARY_EMAIL_ADDRESS} initialized successfully.")
        except ValueError as e:
            logging.error(f"Failed to initialize instruction EmailClient for {SECRETARY_EMAIL_ADDRESS}: {e}. Prompt updates via email will be disabled.", exc_info=True)
        except Exception as e:
            logging.error(f"Unexpected error initializing instruction EmailClient ({SECRETARY_EMAIL_ADDRESS}): {e}. Prompt updates via email will be disabled.", exc_info=True)
    else:
        logging.info("Instruction email account or token path not configured. Prompt updates via email are disabled.")


    if not primary_email_client:
        logging.error("CRITICAL: Primary EmailClient was not initialized. Agent cannot proceed.")
        return

    while True:
        try:
            # 1. Process instruction emails first
            if instruction_email_client:
                process_instruction_emails(instruction_email_client)
            else:
                logging.debug("Instruction email client not configured, skipping instruction email check.")

            # 2. Process general incoming emails for the primary account
            logging.info(f"Checking for unread emails in primary account {MONITORED_EMAIL_ACCOUNT_CONFIG} received after {AGENT_START_TIME.isoformat()}...")
            # Using 'UNREAD' as search criteria, date filtering is done after fetching
            unread_emails = primary_email_client.fetch_emails(search_criteria='UNREAD', max_results=MAX_EMAILS_PER_FETCH)

            if not unread_emails:
                logging.info(f"No new unread emails found in {MONITORED_EMAIL_ACCOUNT_CONFIG}.")
            else:
                logging.info(f"Fetched {len(unread_emails)} unread emails from {MONITORED_EMAIL_ACCOUNT_CONFIG}. Filtering by date and content...")
                processed_count = 0
                for i, email_data in enumerate(unread_emails):
                    msg_id = email_data.get('id')
                    sender_full = email_data.get('sender', '')
                    subject = email_data.get('subject', '').lower()
                    received_dt = email_data.get('received_date_dt')
                    body = email_data.get('body')

                    log_subject = email_data.get('subject', '') 
                    log_received_dt = received_dt.isoformat() if received_dt else 'N/A'
                    logging.info(f"  Inspecting Email #{i+1} in {MONITORED_EMAIL_ACCOUNT_CONFIG}: ID={msg_id}, From='{sender_full}', Subject='{log_subject}', Received='{log_received_dt}'")

                    if received_dt is None:
                        logging.info(f"    Skipping email ID {msg_id}: No received date available.")
                        primary_email_client.mark_email_as_read(message_id=msg_id)
                        continue
                    
                    if received_dt.tzinfo is None:
                        received_dt = received_dt.replace(tzinfo=timezone.utc)

                    if received_dt < AGENT_START_TIME:
                        logging.info(f"    Skipping email ID {msg_id}: Received ({received_dt.isoformat()}) before agent start time ({AGENT_START_TIME.isoformat()}).")
                        primary_email_client.mark_email_as_read(message_id=msg_id)
                        continue

                    sender_lower = sender_full.lower()
                    skip_email = False
                    for pattern in IGNORE_SENDERS_CONTAINING:
                        if pattern in sender_lower:
                            logging.info(f"    Skipping email ID {msg_id} from '{sender_full}': Sender matches ignore pattern '{pattern}'.")
                            skip_email = True
                            break
                    if skip_email:
                        primary_email_client.mark_email_as_read(message_id=msg_id)
                        continue
                    
                    for pattern in IGNORE_SUBJECTS_CONTAINING:
                        if pattern in subject: # subject is already .lower()
                            logging.info(f"    Skipping email ID {msg_id} with subject '{email_data.get('subject','')}': Subject matches ignore pattern '{pattern}'.")
                            skip_email = True
                            break
                    if skip_email:
                        primary_email_client.mark_email_as_read(message_id=msg_id)
                        continue
                    
                    # Prevent Karen from replying to herself if an email is from MONITORED_EMAIL_ACCOUNT_CONFIG
                    # This is a basic loop prevention.
                    sender_email_address_plain = sender_full
                    if '<' in sender_full and '>' in sender_full:
                        sender_email_address_plain = sender_full[sender_full.find('<') + 1 : sender_full.find('>')]
                    
                    if sender_email_address_plain.lower() == MONITORED_EMAIL_ACCOUNT_CONFIG.lower():
                        logging.info(f"    Skipping email ID {msg_id} from '{sender_full}': Email is from Karen's own primary address ({MONITORED_EMAIL_ACCOUNT_CONFIG}). Marking as read.")
                        primary_email_client.mark_email_as_read(message_id=msg_id)
                        continue

                    logging.info(f"  Processing Email ID {msg_id} from '{sender_full}' in {MONITORED_EMAIL_ACCOUNT_CONFIG}. Looks like a legitimate email received after agent start.")
                    processed_count += 1
                    
                    logging.info(f"  Generating AI response for email from '{sender_email_address_plain}', subject: '{email_data.get('subject','')}'")
                    ai_response_text = generate_response(subject=email_data.get('subject',''), sender=sender_email_address_plain, body=body if body else email_data.get('snippet', ''))
                    
                    if ai_response_text and not ai_response_text.startswith("Error:"):
                        reply_subject = f"Re: {email_data.get('subject','No Subject')}"
                        logging.info(f"    AI Response Generated. Sending reply from {MONITORED_EMAIL_ACCOUNT_CONFIG} to '{sender_email_address_plain}' with subject '{reply_subject}'.")
                        logging.debug(f"    Reply Body: {ai_response_text[:200]}...") # Log snippet of reply
                        send_success = primary_email_client.send_email(to=sender_email_address_plain, subject=reply_subject, body=ai_response_text)
                        if send_success:
                            logging.info(f"      Successfully sent reply for email ID {msg_id} from {MONITORED_EMAIL_ACCOUNT_CONFIG}.")
                        else:
                            logging.warning(f"      Failed to send reply for email ID {msg_id} from {MONITORED_EMAIL_ACCOUNT_CONFIG}.")
                    else:
                        logging.warning(f"    No valid AI response generated or AI error for email ID {msg_id}. Response: '{ai_response_text}'. Not sending reply.")

                    logging.info(f"  Marking email ID {msg_id} as read in {MONITORED_EMAIL_ACCOUNT_CONFIG} after processing.")
                    mark_success = primary_email_client.mark_email_as_read(message_id=msg_id) # Use primary_email_client
                    if mark_success:
                        logging.info(f"    Successfully marked ID {msg_id} as read.")
                    else:
                        logging.warning(f"    Failed to mark ID {msg_id} as read.")
                
                if processed_count == 0 and len(unread_emails) > 0:
                    logging.info(f"All fetched unread emails from {MONITORED_EMAIL_ACCOUNT_CONFIG} were filtered out (too old, self-sent, or matched ignore patterns).")
            
            logging.info(f"Polling cycle complete for {MONITORED_EMAIL_ACCOUNT_CONFIG}. Sleeping for {POLLING_INTERVAL_SECONDS} seconds.")
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
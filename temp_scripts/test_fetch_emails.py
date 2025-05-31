import sys
import os
import time # Added for sleep
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Adjust path to include the src directory for importing EmailClient
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(PROJECT_ROOT, 'src'))

from email_client import EmailClient
# from config.settings import SECRETARY_EMAIL_ADDRESS, ADMIN_EMAIL_ADDRESS # Replaced by dotenv

SECRETARY_EMAIL_ADDRESS = os.getenv('SECRETARY_EMAIL_ADDRESS')
ADMIN_EMAIL_ADDRESS = os.getenv('ADMIN_EMAIL_ADDRESS')

if not SECRETARY_EMAIL_ADDRESS:
    print("Error: SECRETARY_EMAIL_ADDRESS not found in .env file or environment variables.")
    sys.exit(1)

def run_focused_email_fetch_test():
    print(f"Initializing EmailClient for {SECRETARY_EMAIL_ADDRESS}...")
    try:
        client = EmailClient(email_address=SECRETARY_EMAIL_ADDRESS)
    except ValueError as e:
        print(f"Failed to initialize EmailClient: {e}")
        return

    print("\n--- Focused Test: First fetch for up to 2 unread emails ---")
    # Fetch a small number of unread emails
    initial_unread_emails = client.fetch_emails(max_results=2)
    
    if not initial_unread_emails:
        print("No unread emails found for the focused test. Please send an email to {SECRETARY_EMAIL_ADDRESS}.")
        return

    print(f"Fetched {len(initial_unread_emails)} unread emails for focused test:")
    ids_to_mark = []
    for i, email_data in enumerate(initial_unread_emails):
        ids_to_mark.append(email_data.get('id'))
        print(f"  Email #{i+1}: ID: {email_data.get('id')}, Subject: {email_data.get('subject')}")
        print(f"    Sender: {email_data.get('sender')}, Snippet: {email_data.get('snippet')}")

    if not ids_to_mark:
        print("No specific emails to mark as read in this focused test run.")
        return

    print("\n--- Marking fetched emails as read ---")
    for msg_id in ids_to_mark:
        print(f"  Marking email {msg_id} as read...")
        success = client.mark_email_as_read(message_id=msg_id)
        if success:
            print(f"    Successfully marked {msg_id} as read.")
        else:
            print(f"    Failed to mark {msg_id} as read.")

    print("\n--- Pausing for 10 seconds to allow Gmail to process changes... ---")
    time.sleep(10)

    print("\n--- Focused Test: Second fetch to verify marking ---")
    remaining_unread_emails = client.fetch_emails(max_results=10) # Fetch more to see context

    if not remaining_unread_emails:
        print("No unread emails found after marking and pausing. Test successful for marked IDs.")
        return

    print(f"Found {len(remaining_unread_emails)} unread emails after marking and pause:")
    marked_ids_still_unread = 0
    for email_data in remaining_unread_emails:
        current_id = email_data.get('id')
        print(f"  Found Unread: ID: {current_id}, Subject: {email_data.get('subject')}")
        if current_id in ids_to_mark:
            print(f"    WARNING: Email ID {current_id} (which was marked as read) is STILL in the unread list!")
            marked_ids_still_unread += 1
            
    if marked_ids_still_unread == 0:
        print("SUCCESS: None of the specifically marked emails appeared in the second unread fetch.")
    else:
        print(f"FAILURE: {marked_ids_still_unread} of the specifically marked emails were still found in the unread list.")

if __name__ == "__main__":
    # Before running, ensure you have sent one or more test emails to SECRETARY_EMAIL_ADDRESS
    # that are currently unread in the Gmail inbox.
    print("Starting FOCUSED email fetch and mark-as-read test...")
    print(f"Target Secretary Email: {SECRETARY_EMAIL_ADDRESS}")
    print("Please ensure there are unread emails in this inbox for testing.")
    run_focused_email_fetch_test() 
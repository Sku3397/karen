"""
Mock Email Client for testing purposes.
Simulates fetching and sending emails without actual network calls.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class MockEmailClient:
    def __init__(self, smtp_server, smtp_port, imap_server, email_address, password):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.imap_server = imap_server
        self.email_address = email_address # Secretary email
        self.password = password
        
        self.mock_inbox: List[Dict[str, Any]] = []
        self.sent_emails: List[Dict[str, Any]] = []
        self.seen_emails_uids: List[str] = []
        
        logger.info(f"MockEmailClient initialized for {email_address}")

    def populate_inbox(self, emails: List[Dict[str, Any]]):
        """Populates the mock inbox with predefined emails."""
        self.mock_inbox = emails
        logger.info(f"Mock inbox populated with {len(emails)} emails.")

    def send_email(self, to: str, subject: str, body: str, attachments: Optional[List[str]] = None) -> bool:
        email_data = {
            'to': to,
            'from': self.email_address, # Should be the secretary's email
            'subject': subject,
            'body': body,
            'attachments': attachments or []
        }
        self.sent_emails.append(email_data)
        logger.info(f"MockEmailClient: Simulated sending email to {to} with subject '{subject}'")
        return True

    def fetch_emails(self, mailbox: str = 'inbox', search_criteria: str = 'UNSEEN', last_n_days: Optional[int] = None) -> List[Dict[str, Any]]:
        logger.info(f"MockEmailClient: Fetching emails. Mailbox: {mailbox}, Criteria: {search_criteria}, Last N Days: {last_n_days}")
        
        if not self.mock_inbox:
            logger.info("Mock inbox is empty.")
            return []

        results = []
        now = datetime.now()

        for i, email_data in enumerate(self.mock_inbox):
            # Ensure basic fields for processing, add a default UID if missing
            email_data.setdefault('uid', f"mock_uid_{i+1}")
            email_data.setdefault('id', email_data['uid']) # Message-ID fallback
            email_data.setdefault('from', 'testsender@example.com')
            email_data.setdefault('subject', 'Mock Subject')
            email_data.setdefault('body', 'Mock body content.')
            email_data.setdefault('date', now) # Add a date field for filtering

            match = False
            if last_n_days is not None and last_n_days > 0:
                email_date = email_data.get('date', now)
                if isinstance(email_date, str): # If date is string, try to parse
                    try:
                        email_date = datetime.fromisoformat(email_date.replace('Z', '+00:00'))
                    except ValueError: # Fallback if parse fails
                        email_date = now 
                
                if now - email_date <= timedelta(days=last_n_days):
                    match = True # Matches if within date range
            elif search_criteria == 'UNSEEN':
                # Simple UNSEEN simulation: if not in seen_emails_uids
                if email_data['uid'] not in self.seen_emails_uids:
                    match = True
            elif search_criteria == 'ALL': # For fetching all emails regardless of seen status or date (unless overridden by last_n_days)
                match = True
            else: # Add more sophisticated criteria matching if needed
                match = True 

            if match:
                results.append(email_data.copy()) # Return a copy

        logger.info(f"MockEmailClient: Found {len(results)} emails matching criteria.")
        return results

    def mark_email_as_seen(self, uid: str, folder: str = 'INBOX') -> bool:
        if any(e['uid'] == uid for e in self.mock_inbox):
            if uid not in self.seen_emails_uids:
                self.seen_emails_uids.append(uid)
            logger.info(f"MockEmailClient: Marked email UID {uid} as Seen.")
            return True
        logger.warning(f"MockEmailClient: UID {uid} not found in mock inbox to mark as seen.")
        return False

    def clear_state(self):
        """Clears mock inbox, sent emails, and seen UIDs for fresh tests."""
        self.mock_inbox = []
        self.sent_emails = []
        self.seen_emails_uids = []
        logger.info("MockEmailClient state cleared.")

# Example Usage (for clarity, not part of the class itself)
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    mock_client = MockEmailClient("smtp.example.com", 587, "imap.example.com", "secretary@example.com", "password")
    
    sample_emails = [
        {
            'uid': 'uid1', 'id': '<msg1@example.com>', 'from': 'admin@example.com', 
            'subject': 'TASK: Fix the system', 'body': 'The main server is down.',
            'date': datetime.now() - timedelta(days=1)
        },
        {
            'uid': 'uid2', 'id': '<msg2@example.com>', 'from': 'customer@example.com', 
            'subject': 'Inquiry about service', 'body': 'Hello, I need help with plumbing.',
            'date': datetime.now() - timedelta(days=3)
        },
        {
            'uid': 'uid3', 'id': '<msg3@example.com>', 'from': 'another_customer@example.com', 
            'subject': 'Urgent: Water Leak', 'body': 'TASK: Urgent water leak at 123 Main St.', # Customer can also create tasks
            'date': datetime.now() - timedelta(days=8) # This one is older than 7 days
        },
    ]
    mock_client.populate_inbox(sample_emails)
    
    # Test fetching last 7 days
    fetched_recent = mock_client.fetch_emails(last_n_days=7)
    print(f"Fetched {len(fetched_recent)} recent emails (last 7 days):")
    for e in fetched_recent: print(f" - {e['subject']}")

    # Test fetching UNSEEN (assuming uid1 was marked seen before)
    mock_client.mark_email_as_seen('uid1')
    fetched_unseen = mock_client.fetch_emails(search_criteria='UNSEEN')
    print(f"Fetched {len(fetched_unseen)} unseen emails:")
    for e in fetched_unseen: print(f" - {e['subject']} (UID: {e['uid']})")

    mock_client.send_email("admin@example.com", "Test Sent", "This is a test email body.")
    print("Sent emails:", mock_client.sent_emails)
    print("Seen UIDs:", mock_client.seen_emails_uids) 
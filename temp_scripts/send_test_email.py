import sys
import os
from datetime import datetime

# Add src to path to import EmailClient
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from email_client import EmailClient # This will now be the Gmail API version
from dotenv import load_dotenv

# Load environment variables from .env file in the project root
dotenv_path = os.path.join(os.path.dirname(__file__), '../.env')
load_dotenv(dotenv_path=dotenv_path)

# For Gmail API version, EmailClient only needs the user's email address for 'me' context
EMAIL_ADDRESS = os.getenv('SECRETARY_EMAIL_ADDRESS')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL_ADDRESS') # This is the recipient

if not EMAIL_ADDRESS or not ADMIN_EMAIL:
    missing = []
    if not EMAIL_ADDRESS: missing.append("'SECRETARY_EMAIL_ADDRESS' (for Gmail API 'me')")
    if not ADMIN_EMAIL: missing.append("'ADMIN_EMAIL_ADDRESS' (recipient)")
    print(f"Error: Missing environment variables: {', '.join(missing)}. Please check your .env file.")
    sys.exit(1)

print(f"Attempting to send test email from {EMAIL_ADDRESS} (via Gmail API) to {ADMIN_EMAIL}.")

try:
    # EmailClient now only takes email_address
    client = EmailClient(email_address=EMAIL_ADDRESS)
    
    subject = f"Gmail API Test Email - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    body = "This is a test email sent using the Gmail API via the EmailClient."
    
    if client.send_email(to=ADMIN_EMAIL, subject=subject, body=body):
        print("Test email sent successfully via Gmail API!")
        sys.exit(0)
    else:
        print("Failed to send test email via Gmail API. Review output from EmailClient above.")
        sys.exit(1)

except ValueError as ve:
    print(f"Configuration error: {ve}") # E.g. if EmailClient init fails due to bad creds
    sys.exit(1)
except Exception as e:
    print(f"An unexpected error occurred in the test script: {e}")
    sys.exit(1) 
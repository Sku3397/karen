#!/usr/bin/env python3
"""
Send Test Email
Sends a test email to the monitored account for pipeline testing
"""

import os
import sys
import logging
from datetime import datetime

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from src.email_client import EmailClient
from src.config import SECRETARY_EMAIL_ADDRESS, MONITORED_EMAIL_ACCOUNT

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def send_test_email(email_type="basic"):
    """Send a test email to the monitored account"""
    
    email_templates = {
        "basic": {
            "subject": "Test: Need plumbing quote",
            "body": "Hi, my kitchen sink is leaking. Can you provide a quote for repair? I'm available tomorrow afternoon. Thank you!"
        },
        "emergency": {
            "subject": "EMERGENCY: Water leak in basement!",
            "body": "I have a major water leak in my basement that needs immediate attention. Water is everywhere! Please help ASAP. My address is 123 Main St, Norfolk VA 23505."
        },
        "appointment": {
            "subject": "Schedule HVAC maintenance",
            "body": "I need to schedule annual maintenance for my heating system. I'm available next week Tuesday or Wednesday morning. Please let me know what times work. Address: 456 Oak Ave, Virginia Beach VA 23451."
        },
        "electrical": {
            "subject": "Electrical outlet not working",
            "body": "My kitchen GFCI outlet stopped working and won't reset. No power to any outlets on that circuit. Can you diagnose and fix this issue?"
        },
        "installation": {
            "subject": "Install new ceiling fan",
            "body": "I want to install a new ceiling fan in my living room. I already have the fan purchased. When can you come install it? I'm flexible on timing."
        }
    }
    
    if email_type not in email_templates:
        print(f"❌ Unknown email type: {email_type}")
        print(f"Available types: {', '.join(email_templates.keys())}")
        return False
    
    template = email_templates[email_type]
    
    print(f"📧 Sending {email_type} test email...")
    print(f"   From: {SECRETARY_EMAIL_ADDRESS}")
    print(f"   To: {MONITORED_EMAIL_ACCOUNT}")
    print(f"   Subject: {template['subject']}")
    print(f"   Body: {template['body'][:100]}...")
    
    try:
        # Create email client for secretary account
        client = EmailClient(SECRETARY_EMAIL_ADDRESS, profile='gmail_secretary')
        
        # Send the test email
        result = client.send_email(
            to_email=MONITORED_EMAIL_ACCOUNT,
            subject=template['subject'],
            body=template['body']
        )
        
        if result:
            print("✅ Test email sent successfully!")
            print(f"📅 Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("\n💡 Next steps:")
            print("   1. Wait 1-2 minutes for email delivery")
            print("   2. Run email processing: python quick_email_test.py")
            print("   3. Check for AI response in karensecretaryai@gmail.com")
            return True
        else:
            print("❌ Failed to send test email")
            return False
            
    except Exception as e:
        logger.error(f"Failed to send test email: {e}", exc_info=True)
        print(f"❌ Error sending email: {e}")
        return False

def main():
    """Main function with command line argument handling"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Send test email to Karen AI pipeline")
    parser.add_argument(
        'email_type', 
        nargs='?', 
        default='basic',
        choices=['basic', 'emergency', 'appointment', 'electrical', 'installation'],
        help='Type of test email to send (default: basic)'
    )
    
    args = parser.parse_args()
    
    print("📬 Karen AI Email Pipeline - Test Email Sender")
    print("=" * 50)
    
    success = send_test_email(args.email_type)
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Monitor Email Responses
Monitors and displays recent email activity for pipeline testing
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from src.email_client import EmailClient
from src.config import SECRETARY_EMAIL_ADDRESS, MONITORED_EMAIL_ACCOUNT, USE_MOCK_EMAIL_CLIENT

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def monitor_incoming_emails():
    """Monitor incoming emails to the monitored account"""
    print("\n📥 INCOMING EMAILS (Last 24 hours)")
    print("-" * 50)
    
    try:
        if USE_MOCK_EMAIL_CLIENT:
            print("🔧 Mock mode enabled - check mock logs for incoming emails")
            return
        
        # Monitor client for incoming emails
        monitor_client = EmailClient(MONITORED_EMAIL_ACCOUNT, profile='gmail_monitor')
        
        # Get recent emails
        recent_emails = monitor_client.get_recent_emails(limit=10)
        
        if not recent_emails:
            print("📭 No recent emails found")
            return
        
        print(f"📬 Found {len(recent_emails)} recent emails:")
        
        for i, email in enumerate(recent_emails, 1):
            subject = email.get('subject', 'No Subject')
            sender = email.get('from', 'Unknown Sender')
            timestamp = email.get('timestamp', 'Unknown Time')
            snippet = email.get('snippet', '')[:100]
            
            print(f"\n{i}. From: {sender}")
            print(f"   Subject: {subject}")
            print(f"   Time: {timestamp}")
            print(f"   Preview: {snippet}...")
            
    except Exception as e:
        logger.error(f"Failed to monitor incoming emails: {e}", exc_info=True)
        print(f"❌ Error monitoring incoming emails: {e}")

def monitor_outgoing_responses():
    """Monitor outgoing responses from the secretary account"""
    print("\n📤 OUTGOING RESPONSES (Last 24 hours)")
    print("-" * 50)
    
    try:
        if USE_MOCK_EMAIL_CLIENT:
            print("🔧 Mock mode enabled - check mock logs for outgoing responses")
            return
        
        # Secretary client for outgoing emails
        secretary_client = EmailClient(SECRETARY_EMAIL_ADDRESS, profile='gmail_secretary')
        
        # Get recent sent emails
        sent_emails = secretary_client.get_recent_emails(folder='SENT', limit=10)
        
        if not sent_emails:
            print("📭 No recent sent emails found")
            return
        
        print(f"📮 Found {len(sent_emails)} recent sent emails:")
        
        for i, email in enumerate(sent_emails, 1):
            subject = email.get('subject', 'No Subject')
            recipient = email.get('to', 'Unknown Recipient')
            timestamp = email.get('timestamp', 'Unknown Time')
            snippet = email.get('snippet', '')[:100]
            
            print(f"\n{i}. To: {recipient}")
            print(f"   Subject: {subject}")
            print(f"   Time: {timestamp}")
            print(f"   Preview: {snippet}...")
            
    except Exception as e:
        logger.error(f"Failed to monitor outgoing emails: {e}", exc_info=True)
        print(f"❌ Error monitoring outgoing emails: {e}")

def check_system_status():
    """Check the overall system status"""
    print("\n🔍 SYSTEM STATUS CHECK")
    print("-" * 50)
    
    try:
        # Test communication agent
        from src.celery_app import get_communication_agent_instance
        
        print("🤖 Testing communication agent...")
        agent = get_communication_agent_instance()
        print(f"✅ Communication agent: {type(agent)}")
        
        # Test email clients
        print("\n📧 Testing email clients...")
        
        if not USE_MOCK_EMAIL_CLIENT:
            # Test secretary client
            secretary_client = EmailClient(SECRETARY_EMAIL_ADDRESS, profile='gmail_secretary')
            print(f"✅ Secretary client: {secretary_client.email_address}")
            
            # Test monitor client
            monitor_client = EmailClient(MONITORED_EMAIL_ACCOUNT, profile='gmail_monitor')
            print(f"✅ Monitor client: {monitor_client.email_address}")
        else:
            print("🔧 Mock email clients enabled")
        
        # Test calendar integration
        try:
            from src.calendar_client import CalendarClient
            calendar_client = CalendarClient(SECRETARY_EMAIL_ADDRESS)
            print("✅ Calendar client initialized")
        except Exception as e:
            print(f"⚠️  Calendar client issue: {e}")
        
        print("\n✅ System status check completed")
        
    except Exception as e:
        logger.error(f"System status check failed: {e}", exc_info=True)
        print(f"❌ System status check failed: {e}")

def monitor_pipeline_activity(duration_minutes=5):
    """Monitor pipeline activity for a specified duration"""
    print(f"\n👀 MONITORING PIPELINE ACTIVITY ({duration_minutes} minutes)")
    print("=" * 60)
    
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=duration_minutes)
    
    print(f"🚀 Monitoring started: {start_time.strftime('%H:%M:%S')}")
    print(f"⏰ Will stop at: {end_time.strftime('%H:%M:%S')}")
    print("\n💡 Send test emails using: python send_test_email.py")
    print("💡 Process emails using: python quick_email_test.py")
    
    try:
        while datetime.now() < end_time:
            current_time = datetime.now()
            remaining = end_time - current_time
            
            print(f"\n⏱️  {current_time.strftime('%H:%M:%S')} - {remaining.seconds//60}m {remaining.seconds%60}s remaining")
            
            # Check for new activity
            monitor_incoming_emails()
            monitor_outgoing_responses()
            
            # Wait before next check
            print("\n⏳ Waiting 30 seconds before next check...")
            time.sleep(30)
        
        print(f"\n🏁 Monitoring completed at {datetime.now().strftime('%H:%M:%S')}")
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Monitoring stopped by user at {datetime.now().strftime('%H:%M:%S')}")

def main():
    """Main function with command line options"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor Karen AI email pipeline activity")
    parser.add_argument('--monitor', '-m', type=int, metavar='MINUTES', 
                       help='Monitor pipeline activity for specified minutes')
    parser.add_argument('--status', '-s', action='store_true',
                       help='Check system status only')
    
    args = parser.parse_args()
    
    print("📊 Karen AI Email Pipeline - Activity Monitor")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if args.status:
        check_system_status()
    elif args.monitor:
        check_system_status()
        monitor_pipeline_activity(args.monitor)
    else:
        # Default: show current status
        check_system_status()
        monitor_incoming_emails()
        monitor_outgoing_responses()
        
        print(f"\n💡 Usage tips:")
        print(f"   python {sys.argv[0]} --status          # Check system status")
        print(f"   python {sys.argv[0]} --monitor 10      # Monitor for 10 minutes")
        print(f"   python send_test_email.py emergency   # Send test email")
        print(f"   python quick_email_test.py            # Process emails")

if __name__ == "__main__":
    main()
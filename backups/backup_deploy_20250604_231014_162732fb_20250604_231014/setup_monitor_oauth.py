#!/usr/bin/env python3
"""
OAuth Setup for Karen's Dual Gmail Configuration
- karensecretaryai@gmail.com: For SENDING emails (noreply)
- hello@757handy.com: For MONITORING incoming emails

This script sets up OAuth for the hello@757handy.com account.
"""

import json
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import webbrowser

# Gmail API scopes needed (Readonly might be enough for monitoring, but keeping others for flexibility)
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.compose', # For "mark as read/seen" if needed by modify
    'https://www.googleapis.com/auth/gmail.send', # Should not be used by this account, but included for scope consistency
    'https://www.googleapis.com/auth/gmail.modify' # For marking emails as read/unread
]

# File paths
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'gmail_token_monitor.json'  # Token for the monitoring account
MONITORING_ACCOUNT_EMAIL = 'hello@757handy.com'

def setup_oauth():
    """Set up OAuth for hello@757handy.com"""
    print(f"🔐 Setting up OAuth for Monitoring Gmail Account ({MONITORING_ACCOUNT_EMAIL})")
    print("=" * 60)
    
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"❌ Error: {CREDENTIALS_FILE} not found!")
        print("Please ensure the OAuth credentials file is in the current directory.")
        return False
    
    creds = None
    
    if os.path.exists(TOKEN_FILE):
        print(f"📂 Found existing token file: {TOKEN_FILE}")
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            if creds and creds.valid:
                print("✅ Existing credentials are valid!")
                return test_gmail_access(creds)
        except Exception as e:
            print(f"⚠️  Error loading existing token: {e}")
            print("Will create new token...")
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired credentials...")
            try:
                creds.refresh(Request())
                print("✅ Credentials refreshed successfully!")
            except Exception as e:
                print(f"❌ Failed to refresh credentials: {e}")
                creds = None
        
        if not creds:
            print("🌐 Starting OAuth flow...")
            print(f"📧 IMPORTANT: Sign in with {MONITORING_ACCOUNT_EMAIL} when prompted!")
            print("-" * 60)
            
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, SCOPES)
                
                creds = flow.run_local_server(
                    port=0, # Dynamically choose port
                    open_browser=True,
                    bind_addr='localhost'
                )
                print("✅ OAuth flow completed successfully!")
                
            except Exception as e:
                print(f"❌ OAuth flow failed: {e}")
                return False
    
    if creds:
        try:
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
            print(f"💾 Token saved to {TOKEN_FILE}")
            
            return test_gmail_access(creds)
            
        except Exception as e:
            print(f"❌ Error saving token: {e}")
            return False
    
    return False

def test_gmail_access(creds):
    """Test Gmail API access and verify account"""
    print("\n🧪 Testing Gmail API access...")
    try:
        service = build('gmail', 'v1', credentials=creds)
        
        profile = service.users().getProfile(userId='me').execute()
        email_address = profile.get('emailAddress', 'Unknown')
        
        print(f"✅ Successfully connected to Gmail!")
        print(f"📧 Authenticated account: {email_address}")
        
        if email_address.lower() == MONITORING_ACCOUNT_EMAIL.lower():
            print("✅ Correct account! Karen can now monitor emails from this account.")
        else:
            print(f"⚠️  Warning: Expected {MONITORING_ACCOUNT_EMAIL} but got {email_address}")
        
        labels_result = service.users().labels().list(userId='me').execute()
        labels = labels_result.get('labels', [])
        print(f"📁 Found {len(labels)} labels - Gmail API is working!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Gmail access: {e}")
        return False

def main():
    print("🤖 Karen's Gmail OAuth Setup for MONITORED Account")
    print("📋 This script will authorize access to:")
    print(f"   • {MONITORING_ACCOUNT_EMAIL} (for MONITORING emails)")
    print()
    
    success = setup_oauth()
    
    if success:
        print(f"\n🎉 SUCCESS! OAuth setup completed for {MONITORING_ACCOUNT_EMAIL}.")
        print(f"\n📄 Token saved as: {TOKEN_FILE}")
        print("🔐 Keep this file secure!")
    else:
        print(f"\n❌ OAuth setup for {MONITORING_ACCOUNT_EMAIL} failed. Please check errors and try again.")

if __name__ == "__main__":
    main() 
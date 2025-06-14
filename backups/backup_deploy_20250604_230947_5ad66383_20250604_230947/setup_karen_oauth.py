#!/usr/bin/env python3
"""
OAuth Setup for Karen's Dual Gmail Configuration
- karensecretaryai@gmail.com: For SENDING emails (noreply)
- hello@757handy.com: For MONITORING incoming emails

This script sets up OAuth for the karensecretaryai@gmail.com account.
"""

import json
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import webbrowser

# Gmail API scopes needed
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.compose', 
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]

# File paths
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'gmail_token_karen.json'  # Different name for Karen's sending account

def setup_oauth():
    """Set up OAuth for karensecretaryai@gmail.com"""
    print("🔐 Setting up OAuth for Karen's Gmail Sending Account")
    print("=" * 60)
    
    # Check if credentials file exists
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"❌ Error: {CREDENTIALS_FILE} not found!")
        print("Please ensure the OAuth credentials file is in the current directory.")
        return False
    
    creds = None
    
    # Load existing token if available
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
    
    # If no valid credentials, start OAuth flow
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
            print("📧 IMPORTANT: Sign in with karensecretaryai@gmail.com when prompted!")
            print("-" * 60)
            
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, SCOPES)
                
                # Use localhost without port to match configured redirect URI
                creds = flow.run_local_server(
                    port=0,
                    open_browser=True,
                    bind_addr='localhost'
                )
                print("✅ OAuth flow completed successfully!")
                
            except Exception as e:
                print(f"❌ OAuth flow failed: {e}")
                return False
    
    # Save credentials
    if creds:
        try:
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
            print(f"💾 Token saved to {TOKEN_FILE}")
            
            # Test the connection
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
        
        # Get profile to verify which account we're connected to
        profile = service.users().getProfile(userId='me').execute()
        email_address = profile.get('emailAddress', 'Unknown')
        
        print(f"✅ Successfully connected to Gmail!")
        print(f"📧 Authenticated account: {email_address}")
        
        if email_address == 'karensecretaryai@gmail.com':
            print("✅ Correct account! Karen can now send emails.")
        else:
            print(f"⚠️  Warning: Expected karensecretaryai@gmail.com but got {email_address}")
        
        # Test sending capability by getting labels
        labels_result = service.users().labels().list(userId='me').execute()
        labels = labels_result.get('labels', [])
        print(f"📁 Found {len(labels)} labels - Gmail API is working!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Gmail access: {e}")
        return False

def main():
    print("🤖 Karen's Gmail OAuth Setup")
    print("📋 Configuration Plan:")
    print("   • karensecretaryai@gmail.com → SENDING emails (this setup)")
    print("   • hello@757handy.com → MONITORING emails (separate setup)")
    print("   • Replies will be directed to hello@757handy.com")
    print()
    
    success = setup_oauth()
    
    if success:
        print("\n🎉 SUCCESS! OAuth setup completed for Karen's sending account.")
        print("\n📋 Next Steps:")
        print("1. ✅ karensecretaryai@gmail.com is ready for SENDING")
        print("2. 🔄 Need to set up monitoring for hello@757handy.com")
        print("3. 🔧 Update Karen's configuration to use dual email setup")
        
        print(f"\n📄 Token saved as: {TOKEN_FILE}")
        print("🔐 Keep this file secure - it contains your OAuth credentials!")
    else:
        print("\n❌ OAuth setup failed. Please check the errors above and try again.")
        print("\n💡 Common issues:")
        print("   • Make sure you sign in with karensecretaryai@gmail.com")
        print("   • Check that Gmail API is enabled in Google Cloud Console")
        print("   • Verify redirect URIs are configured correctly")

if __name__ == "__main__":
    main() 
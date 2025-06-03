#!/usr/bin/env python3
"""
OAuth Setup for Google Calendar access for hello@757handy.com
"""

import json
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import webbrowser # Not strictly needed for run_local_server if open_browser=True, but good to have

# Google Calendar API scopes needed
SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events'
]

# File paths
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'gmail_token_hello_calendar.json'  # Token for the calendar associated with the monitoring account
CALENDAR_ACCOUNT_EMAIL = 'hello@757handy.com'

def setup_oauth():
    """Set up OAuth for hello@757handy.com's Google Calendar"""
    print(f"🔐 Setting up OAuth for Google Calendar Account ({CALENDAR_ACCOUNT_EMAIL})")
    print("=" * 70)
    
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"❌ Error: {CREDENTIALS_FILE} not found!")
        print("Please ensure the OAuth client secret file (credentials.json) is in the current directory.")
        return False
    
    creds = None
    
    if os.path.exists(TOKEN_FILE):
        print(f"📂 Found existing token file: {TOKEN_FILE}")
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            if creds and creds.valid:
                print("✅ Existing credentials are valid!")
                return test_calendar_access(creds)
            elif creds and creds.expired and creds.refresh_token:
                 print("🔄 Credentials require refresh.")
            else:
                print("⚠️ Existing token is invalid or missing scopes. Will attempt to re-create.")
                creds = None # Force re-creation
        except Exception as e:
            print(f"⚠️  Error loading existing token: {e}")
            print("Will create new token...")
            creds = None
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired credentials...")
            try:
                creds.refresh(Request())
                print("✅ Credentials refreshed successfully!")
            except Exception as e:
                print(f"❌ Failed to refresh credentials: {e}")
                print("Proceeding to full OAuth flow.")
                creds = None
        
        if not creds: # This means either no token file, or existing token was invalid/unrefreshable
            print("🌐 Starting OAuth flow for Google Calendar...")
            print(f"📧 IMPORTANT: Sign in with {CALENDAR_ACCOUNT_EMAIL} when prompted in your browser!")
            print("   Ensure you grant permissions for 'View events on all your calendars' and 'Make changes to events on all your calendars'.")
            print("-" * 70)
            
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, SCOPES)
                
                # run_local_server will attempt to open the browser automatically.
                # It hosts a temporary local server to receive the auth code.
                creds = flow.run_local_server(
                    port=0, # Dynamically choose an available port
                    open_browser=True,
                    bind_addr='localhost',
                    authorization_prompt_message="Please visit this URL: {url}", # Default is fine
                    success_message="OAuth2 flow was successful. You may close this browser tab." # Default is fine
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
            
            return test_calendar_access(creds)
            
        except Exception as e:
            print(f"❌ Error saving token: {e}")
            return False
    
    return False

def test_calendar_access(creds):
    """Test Google Calendar API access and verify account"""
    print("\n🧪 Testing Google Calendar API access...")
    try:
        service = build('calendar', 'v3', credentials=creds)
        
        # Get user's primary calendar info as a basic test
        calendar_list_entry = service.calendarList().get(calendarId='primary').execute()
        authenticated_calendar_id = calendar_list_entry.get('id', 'Unknown')
        
        print(f"✅ Successfully connected to Google Calendar API!")
        print(f"📧 Primary calendar ID for authenticated account: {authenticated_calendar_id}")
        
        if authenticated_calendar_id.lower() == CALENDAR_ACCOUNT_EMAIL.lower():
            print(f"✅ Correct account ({CALENDAR_ACCOUNT_EMAIL}) for calendar access confirmed.")
        else:
            # For non-primary calendars, this might not match directly if user has many calendars
            # but for 'primary', it should match the user's email.
            print(f"ℹ️  Note: Authenticated primary calendar ID is '{authenticated_calendar_id}'. This should generally match '{CALENDAR_ACCOUNT_EMAIL}'.")
        
        # Further test: list some events from the primary calendar (optional, can be noisy)
        # events_result = service.events().list(calendarId='primary', maxResults=5, singleEvents=True, orderBy='startTime').execute()
        # events = events_result.get('items', [])
        # print(f"📅 Found {len(events)} upcoming events in primary calendar (sample check) - API is working!")
        print("✅ Google Calendar API access seems to be working!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Google Calendar access: {e}")
        return False

def main():
    print("🤖 Google Calendar OAuth Setup")
    print("📋 This script will authorize access for the application to manage calendars for:")
    print(f"   • {CALENDAR_ACCOUNT_EMAIL}")
    print()
    
    success = setup_oauth()
    
    if success:
        print(f"\n🎉 SUCCESS! OAuth setup for Google Calendar completed for {CALENDAR_ACCOUNT_EMAIL}.")
        print(f"\n📄 Token saved as: {TOKEN_FILE}")
        print("🔐 Keep this file secure!")
    else:
        print(f"\n❌ OAuth setup for Google Calendar for {CALENDAR_ACCOUNT_EMAIL} failed. Please check errors and try again.")

if __name__ == "__main__":
    main() 
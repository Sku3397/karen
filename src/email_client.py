# EmailClient: Handles sending and fetching emails, now using Gmail API for sending.
import email
from email.mime.text import MIMEText
from typing import List, Optional, Dict, Any
import json
import time
import os
import base64
from datetime import datetime # Credentials object expects datetime for expiry
import logging # Added

# Google API Client libraries
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleAuthRequest
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Define paths relative to the project root, assuming this file is in src/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CREDENTIALS_FILE_PATH = os.path.join(PROJECT_ROOT, 'credentials.json')
TOKEN_FILE_PATH = os.path.join(PROJECT_ROOT, 'gmail_token.json')

# Define the scopes needed.
SCOPES = ['https://www.googleapis.com/auth/gmail.send',
          'https://www.googleapis.com/auth/gmail.compose',
          'https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/gmail.modify']

logger = logging.getLogger(__name__) # Added

class EmailClient:
    def __init__(self, email_address: str):
        self.email_address = email_address
        logger.debug(f"Initializing EmailClient for {email_address}")
        self.creds = self._load_and_refresh_credentials()

        if not self.creds:
            logger.error("Failed to load or refresh Google OAuth credentials during init.")
            raise ValueError("Failed to load or refresh Google OAuth credentials.")
        logger.info("EmailClient initialized successfully.")

    def _load_and_refresh_credentials(self) -> Optional[Credentials]:
        logger.debug("Attempting to load and refresh credentials...")
        creds = None
        client_config = None

        try:
            with open(CREDENTIALS_FILE_PATH, 'r') as f:
                full_creds_json = json.load(f)
                client_config = full_creds_json.get('installed')
            logger.debug(f"Successfully loaded credentials from {CREDENTIALS_FILE_PATH}")
        except FileNotFoundError:
            logger.error(f"OAuth credentials.json file not found at {CREDENTIALS_FILE_PATH}", exc_info=True)
            return None
        except json.JSONDecodeError:
            logger.error(f"Could not decode JSON from {CREDENTIALS_FILE_PATH}", exc_info=True)
            return None
        
        if not client_config or not client_config.get('client_id') or not client_config.get('client_secret') or not client_config.get('token_uri'):
            logger.error("credentials.json is missing client_id, client_secret, or token_uri.")
            return None

        if os.path.exists(TOKEN_FILE_PATH):
            logger.debug(f"Token file found at {TOKEN_FILE_PATH}. Attempting to load.")
            try:
                with open(TOKEN_FILE_PATH, 'r') as token_file:
                    token_data = json.load(token_file)
                
                expiry_seconds = token_data.get('expiry_date')
                if expiry_seconds:
                    if expiry_seconds > time.time() * 500: # Heuristic for ms
                        expiry_seconds = expiry_seconds / 1000.0
                        token_data['expiry_date'] = expiry_seconds
                        logger.debug("Normalized token expiry from ms to s.")
                
                loaded_scopes_raw = token_data.get('scopes')
                final_scopes = SCOPES # Default
                if isinstance(loaded_scopes_raw, str):
                    final_scopes = loaded_scopes_raw.split()
                elif isinstance(loaded_scopes_raw, list):
                    final_scopes = loaded_scopes_raw
                logger.debug(f"Using scopes: {final_scopes}")

                creds = Credentials(
                    token=token_data.get('access_token'),
                    refresh_token=token_data.get('refresh_token'),
                    token_uri=client_config.get('token_uri'), 
                    client_id=client_config.get('client_id'), 
                    client_secret=client_config.get('client_secret'), 
                    scopes=final_scopes
                )
                if expiry_seconds and creds: 
                    creds.expiry = datetime.fromtimestamp(expiry_seconds)
                    logger.debug(f"Credentials expiry set to: {creds.expiry}")

            except json.JSONDecodeError:
                logger.error(f"Error decoding token file {TOKEN_FILE_PATH}.", exc_info=True)
            except Exception as e:
                logger.error(f"Error loading token from {TOKEN_FILE_PATH}: {e}.", exc_info=True)
        else:
            logger.info(f"Token file {TOKEN_FILE_PATH} not found.")
        
        if not creds or not creds.valid:
            logger.warning("Credentials not loaded or not valid. Checking if refreshable.")
            if creds and creds.expired and creds.refresh_token:
                logger.info("Credentials expired, attempting to refresh...")
                try:
                    creds.refresh(GoogleAuthRequest())
                    logger.info("Credentials refreshed successfully.")
                    self._save_token_from_creds(creds)
                except Exception as e:
                    logger.error(f"Failed to refresh credentials: {e}. Please re-run OAuth setup.", exc_info=True)
                    return None 
            else:
                logger.error("Error: No valid credentials or cannot refresh. Please re-run OAuth setup script.")
                return None
        else:
            logger.debug("Credentials loaded and are valid.")
        
        if os.path.exists(TOKEN_FILE_PATH) and creds and creds.valid:
             with open(TOKEN_FILE_PATH, 'r') as token_file_check:
                token_data_check = json.load(token_file_check)
             if isinstance(token_data_check.get('expiry_date'), (int, float)) and token_data_check.get('expiry_date', 0) > time.time() * 500:
                 logger.info("Re-saving token file with expiry_date in seconds after initial load/normalization.")
                 self._save_token_from_creds(creds)

        logger.debug("Credential loading and refresh process completed.")
        return creds

    def _save_token_from_creds(self, creds: Credentials):
        logger.debug(f"Saving OAuth token data to {TOKEN_FILE_PATH}")
        token_data = {
            'access_token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }
        if creds.expiry:
            token_data['expiry_date'] = creds.expiry.timestamp()
            logger.debug(f"Token expiry to be saved: {creds.expiry.timestamp()}")
        
        try:
            with open(TOKEN_FILE_PATH, 'w') as f:
                json.dump(token_data, f, indent=2)
            logger.info(f"OAuth token data saved to {TOKEN_FILE_PATH}.")
        except Exception as e:
            logger.error(f"Error saving OAuth token data: {e}", exc_info=True)

    def send_email(self, to: str, subject: str, body: str, attachments: Optional[List[str]] = None) -> bool:
        logger.debug(f"Attempting to send email to: {to}, subject: {subject[:50]}...")
        if not self.creds or not self.creds.valid:
            logger.warning("Cannot send email: invalid or missing credentials. Attempting to reload/refresh.")
            reloaded_creds = self._load_and_refresh_credentials()
            if not reloaded_creds or not reloaded_creds.valid:
                logger.error("Failed to obtain valid credentials after attempting reload/refresh for send_email.")
                return False
            self.creds = reloaded_creds
            logger.info("Credentials reloaded/refreshed successfully for send_email.")

        try:
            service = build('gmail', 'v1', credentials=self.creds)
            msg = MIMEText(body)
            msg['To'] = to
            msg['From'] = self.email_address
            msg['Subject'] = subject
            
            encoded_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            message_body = {'raw': encoded_message}

            logger.debug("Sending message via Gmail API...")
            sent_message = service.users().messages().send(userId='me', body=message_body).execute()
            logger.info(f"Message sent successfully via Gmail API. Message ID: {sent_message['id']}")
            return True
        except HttpError as error:
            error_content = error.content.decode() if isinstance(error.content, bytes) else error.content
            logger.error(f"Gmail API error occurred: {error}. Details: {error_content}", exc_info=True)
            if error.resp.status == 401:
                logger.error("Authentication error (401). Token may be invalid or revoked. Try re-authenticating.")
            elif error.resp.status == 403:
                logger.error("Permission error (403). Ensure Gmail API is enabled and scopes are correct.")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred during send_email: {e}", exc_info=True)
            return False

    def fetch_emails(self, search_criteria: str = 'UNREAD', last_n_days: Optional[int] = None, max_results: int = 10) -> List[Dict[str, Any]]:
        logger.debug(f"Fetching emails with criteria: '{search_criteria}', last_n_days: {last_n_days}, max_results: {max_results}")
        if not self.creds or not self.creds.valid:
            logger.warning("Cannot fetch emails: invalid or missing credentials. Attempting to reload/refresh.")
            reloaded_creds = self._load_and_refresh_credentials()
            if not reloaded_creds or not reloaded_creds.valid:
                logger.error("Failed to obtain valid credentials for fetching emails.")
                return []
            self.creds = reloaded_creds
            logger.info("Credentials reloaded/refreshed successfully for fetch_emails.")
        
        try:
            service = build('gmail', 'v1', credentials=self.creds)
            
            query = search_criteria # Default query
            if last_n_days and last_n_days > 0:
                after_date = (datetime.now() - timedelta(days=last_n_days)).strftime("%Y/%m/%d")
                query = f'after:{after_date}' # Overrides search_criteria if last_n_days is set
                logger.debug(f"Using date-based query for fetch_emails: {query}")
            
            logger.debug(f"Executing Gmail API list with query: '{query}', maxResults: {max_results}")
            results = service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
            messages = results.get('messages', [])

            if not messages:
                logger.info("No messages found matching criteria.")
                return []
            
            logger.info(f"Found {len(messages)} messages. Fetching details...")
            emails_data = []
            for msg_summary in messages:
                msg_id = msg_summary['id']
                logger.debug(f"Fetching details for message ID: {msg_id}")
                msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
                
                payload = msg.get('payload', {})
                headers = payload.get('headers', [])
                
                email_item = {
                    'id': msg_id,
                    'threadId': msg.get('threadId'),
                    'snippet': msg.get('snippet'),
                    'sender': '',
                    'subject': '',
                    'body_plain': '',
                    'body_html': '',
                    'body': '', 
                    'date_str': '', 
                    'received_date_dt': None,
                    'uid': msg_id # Gmail API uses 'id' as the unique identifier, equivalent to UID in IMAP context here
                }

                internal_date_ms_str = msg.get('internalDate')
                if internal_date_ms_str:
                    try:
                        internal_date_ms = int(internal_date_ms_str)
                        email_item['received_date_dt'] = datetime.fromtimestamp(internal_date_ms / 1000.0)
                    except ValueError:
                        logger.warning(f"Could not parse internalDate '{internal_date_ms_str}' for message ID {msg_id}")
                
                # Extract headers
                for header in headers:
                    name = header.get('name', '').lower()
                    value = header.get('value', '')
                    if name == 'from':
                        email_item['sender'] = value
                    elif name == 'subject':
                        email_item['subject'] = value
                    elif name == 'date':
                        email_item['date_str'] = value
                
                # Extract body parts
                parts = payload.get('parts', [])
                if not parts: # Simple message, body is in payload itself
                    body_data_encoded = payload.get('body', {}).get('data')
                    if body_data_encoded:
                        decoded_body = base64.urlsafe_b64decode(body_data_encoded).decode('utf-8', errors='replace')
                        mime_type = payload.get('mimeType', '')
                        if 'text/plain' in mime_type:
                            email_item['body_plain'] = decoded_body
                        elif 'text/html' in mime_type:
                            email_item['body_html'] = decoded_body
                        email_item['body'] = decoded_body # Default to whatever was found
                else: # Multipart message
                    for part in parts:
                        part_mime_type = part.get('mimeType', '')
                        body_data_encoded = part.get('body', {}).get('data')
                        if body_data_encoded:
                            try:
                                decoded_part_body = base64.urlsafe_b64decode(body_data_encoded).decode('utf-8', errors='replace')
                                if 'text/plain' in part_mime_type:
                                    email_item['body_plain'] += decoded_part_body
                                elif 'text/html' in part_mime_type:
                                    email_item['body_html'] += decoded_part_body
                            except Exception as decode_err:
                                logger.warning(f"Could not decode part for email {msg_id}, mime_type: {part_mime_type}. Error: {decode_err}")
                        
                        # For multipart/alternative, often there are nested parts
                        if 'parts' in part:
                            for sub_part in part.get('parts', []):
                                sub_part_mime_type = sub_part.get('mimeType', '')
                                sub_body_data_encoded = sub_part.get('body', {}).get('data')
                                if sub_body_data_encoded:
                                    try:
                                        decoded_sub_part_body = base64.urlsafe_b64decode(sub_body_data_encoded).decode('utf-8', errors='replace')
                                        if 'text/plain' in sub_part_mime_type:
                                            email_item['body_plain'] += decoded_sub_part_body
                                        elif 'text/html' in sub_part_mime_type:
                                            email_item['body_html'] += decoded_sub_part_body
                                    except Exception as sub_decode_err:
                                        logger.warning(f"Could not decode sub-part for email {msg_id}, mime_type: {sub_part_mime_type}. Error: {sub_decode_err}")

                if email_item['body_plain']:
                    email_item['body'] = email_item['body_plain']
                elif email_item['body_html']:
                    email_item['body'] = email_item['body_html'] # Fallback to HTML if no plain text
                else:
                    logger.debug(f"No plain or HTML body found for message {msg_id}, snippet: {email_item['snippet']}")

                emails_data.append(email_item)
            logger.info(f"Successfully fetched details for {len(emails_data)} emails.")
            return emails_data

        except HttpError as error:
            error_content = error.content.decode() if isinstance(error.content, bytes) else error.content
            logger.error(f"Gmail API error during fetch_emails: {error}. Details: {error_content}", exc_info=True)
            return []
        except Exception as e:
            logger.error(f"Unexpected error during fetch_emails: {e}", exc_info=True)
            return []

    def mark_email_as_seen(self, uid: str) -> bool: # Changed message_id to uid for clarity
        logger.debug(f"Attempting to mark email UID {uid} as Seen (remove UNREAD label).")
        if not self.creds or not self.creds.valid:
            logger.warning("Cannot mark email as seen: invalid or missing credentials. Attempting to reload/refresh.")
            reloaded_creds = self._load_and_refresh_credentials()
            if not reloaded_creds or not reloaded_creds.valid:
                logger.error("Failed to obtain valid credentials for marking email as seen.")
                return False
            self.creds = reloaded_creds
            logger.info("Credentials reloaded/refreshed successfully for mark_email_as_seen.")

        try:
            service = build('gmail', 'v1', credentials=self.creds)
            # To mark as seen, we remove the 'UNREAD' label.
            modify_request_body = {'removeLabelIds': ['UNREAD']}
            service.users().messages().modify(userId='me', id=uid, body=modify_request_body).execute()
            logger.info(f"Successfully marked email UID {uid} as Seen.")
            return True
        except HttpError as error:
            error_content = error.content.decode() if isinstance(error.content, bytes) else error.content
            logger.error(f"Gmail API error marking email UID {uid} as seen: {error}. Details: {error_content}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Unexpected error marking email UID {uid} as seen: {e}", exc_info=True)
            return False

    def mark_email_as_read(self, message_id: str) -> bool:
        # This is an alias for mark_email_as_seen, as Gmail uses UNREAD label
        logger.debug(f"mark_email_as_read called for {message_id}, aliasing to mark_email_as_seen.")
        return self.mark_email_as_seen(uid=message_id)

# EmailClient: Secure email handling with OAuth token management
import email
from email.mime.text import MIMEText
from typing import List, Optional, Dict, Any
import json
import time
import os
import base64
from datetime import datetime, timedelta
import logging

# Google API Client libraries
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleAuthRequest
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import google.auth.exceptions

# Import enhanced OAuth token manager for secure token handling
from .token_manager import get_credentials_with_auto_refresh

# Define paths relative to the project root, assuming this file is in src/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

logger = logging.getLogger(__name__)

class EmailClient:
    def __init__(self, email_address: str, token_file_path: str = None, profile: str = 'gmail_secretary'):
        """
        Initialize EmailClient with secure OAuth token management
        
        Args:
            email_address: Email address for the client
            token_file_path: Legacy parameter, ignored (for backward compatibility)
            profile: OAuth profile to use ('gmail_secretary' or 'gmail_monitor')
        """
        self.email_address = email_address
        self.profile = profile
        
        # Legacy compatibility - warn if token_file_path is provided
        if token_file_path:
            logger.warning(f"token_file_path parameter is deprecated. Using secure token manager instead.")
        
        logger.info(f"Initializing secure EmailClient for {email_address} with profile {profile}")
        
        self._label_id_cache: Dict[str, Optional[str]] = {}
        
        # Use secure token manager for credentials
        self.creds = self._get_secure_credentials()
        
        if not self.creds:
            logger.error(f"Failed to obtain secure OAuth credentials for {email_address}")
            raise ValueError(f"Failed to obtain secure OAuth credentials for {email_address}")
        
        logger.info(f"Secure EmailClient for {email_address} initialized successfully")

    def _get_secure_credentials(self) -> Optional[Credentials]:
        """Get secure OAuth credentials using the enhanced token manager"""
        try:
            logger.debug(f"Requesting secure credentials for {self.email_address} with profile {self.profile}")
            
            # Use the enhanced token manager with automatic refresh
            creds = get_credentials_with_auto_refresh(self.profile, self.email_address)
            
            if creds and creds.valid:
                logger.info(f"Secure credentials obtained for {self.email_address}")
                return creds
            else:
                logger.error(f"Failed to obtain valid secure credentials for {self.email_address}")
                return None
                
        except Exception as e:
            logger.error(f"Error obtaining secure credentials for {self.email_address}: {e}", exc_info=True)
            return None
    
    def refresh_credentials(self) -> bool:
        """Refresh credentials using the enhanced token manager"""
        try:
            logger.info(f"Refreshing credentials for {self.email_address}")
            
            # Get fresh credentials from enhanced token manager
            new_creds = get_credentials_with_auto_refresh(self.profile, self.email_address)
            
            if new_creds and new_creds.valid:
                self.creds = new_creds
                logger.info(f"Credentials refreshed successfully for {self.email_address}")
                return True
            else:
                logger.error(f"Failed to refresh credentials for {self.email_address}")
                return False
                
        except Exception as e:
            logger.error(f"Error refreshing credentials for {self.email_address}: {e}", exc_info=True)
            return False
    
    def _ensure_valid_credentials(self) -> bool:
        """Ensure credentials are valid, refresh if necessary"""
        if not self.creds or not self.creds.valid:
            logger.warning(f"Invalid credentials detected for {self.email_address}, attempting refresh")
            return self.refresh_credentials()
        return True

    def _get_label_id(self, label_name: str) -> Optional[str]:
        """Fetches the ID of a label by its name. Caches results."""
        if label_name in self._label_id_cache:
            return self._label_id_cache[label_name]

        if not self._ensure_valid_credentials():
            logger.error(f"Cannot fetch label ID for '{label_name}': failed to ensure valid credentials.")
            return None
        try:
            service = build('gmail', 'v1', credentials=self.creds)
            results = service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            for label in labels:
                if label['name'].lower() == label_name.lower():
                    logger.info(f"Found label ID for '{label_name}': {label['id']}")
                    self._label_id_cache[label_name] = label['id']
                    return label['id']
            
            # --- BEGIN ADDED DEBUG LOGGING ---
            all_retrieved_label_names = [l.get('name') for l in labels if l.get('name')]
            logger.warning(f"Label '{label_name}' not found for user {self.email_address}. "
                           f"Available labels from API: {all_retrieved_label_names}")
            # --- END ADDED DEBUG LOGGING ---
            
            self._label_id_cache[label_name] = None # Cache miss
            return None
        except HttpError as error:
            logger.error(f"Failed to fetch labels to find ID for '{label_name}': {error}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching label ID for '{label_name}': {e}", exc_info=True)
            return None

    def _save_token_from_creds(self, creds: Credentials):
        logger.debug(f"Saving OAuth token data to {self.token_file_path} for {self.email_address}")
        # Use creds.to_json() for standard format if possible, or build manually
        token_data = {
            'token': creds.token, # access_token is just .token
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }
        if creds.expiry: # Expiry is a datetime object
            # google-auth-oauthlib stores expiry as ISO string, e.g., creds.to_json()
            # For consistency with that, either use creds.to_json() or store similarly.
            # Storing as timestamp is also fine if loading handles it.
            token_data['expiry_date'] = creds.expiry.timestamp() # Save as timestamp
            # token_data['expiry'] = creds.expiry.isoformat() # Alternative: ISO string format
            logger.debug(f"Token expiry to be saved: {token_data['expiry_date']} (timestamp)")
        
        try:
            with open(self.token_file_path, 'w') as f:
                json.dump(token_data, f, indent=2)
            logger.info(f"OAuth token data saved to {self.token_file_path} for {self.email_address}.")
        except Exception as e:
            logger.error(f"Error saving OAuth token data to {self.token_file_path}: {e}", exc_info=True)

    def send_email(self, to: str, subject: str, body: str, attachments: Optional[List[str]] = None) -> bool:
        logger.debug(f"Attempting to send email to: {to}, subject: {subject[:50]}...")
        if not self.creds or not self.creds.valid:
            logger.warning("Cannot send email: invalid or missing credentials. Attempting to reload/refresh.")
            # Pass client_config here
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

    def fetch_emails(self, search_criteria: str = 'UNREAD', 
                     last_n_days: Optional[int] = None, 
                     newer_than: Optional[str] = None, # Added newer_than parameter
                     max_results: int = 10) -> List[Dict[str, Any]]:
        logger.debug(f"Fetching emails with criteria: '{search_criteria}', last_n_days: {last_n_days}, newer_than: {newer_than}, max_results: {max_results}")
        if not self.creds or not self.creds.valid:
            logger.warning("Cannot fetch emails: invalid or missing credentials. Attempting to reload/refresh.")
            # Pass client_config here
            reloaded_creds = self._load_and_refresh_credentials()
            if not reloaded_creds or not reloaded_creds.valid:
                logger.error("Failed to obtain valid credentials for fetching emails.")
                return []
            self.creds = reloaded_creds
            logger.info("Credentials reloaded/refreshed successfully for fetch_emails.")
        
        try:
            service = build('gmail', 'v1', credentials=self.creds)
            
            query_parts = []
            if search_criteria:
                query_parts.append(search_criteria)

            if newer_than:
                # Gmail supports "newer_than:1h", "newer_than:2d", etc.
                query_parts.append(f"newer_than:{newer_than}")
            elif last_n_days and last_n_days > 0:
                # This will only be used if newer_than is not specified
                after_date = (datetime.now() - timedelta(days=last_n_days)).strftime("%Y/%m/%d")
                query_parts.append(f'after:{after_date}')
            
            final_query = " ".join(query_parts).strip()
            if not final_query: # Default to UNREAD if nothing else specified
                final_query = "UNREAD"
                logger.debug(f"Query was empty, defaulting to 'UNREAD'")


            logger.debug(f"Executing Gmail query: '{final_query}'")
            # Fetch messages
            response = service.users().messages().list(userId='me', q=final_query, maxResults=max_results).execute()
            messages = response.get('messages', [])

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

    def mark_email_as_processed(self, uid: str, label_to_add: Optional[str] = None) -> bool:
        """Marks an email as processed: adds a specified label and marks it as read (removes UNREAD)."""
        logger.debug(f"Attempting to mark email UID {uid} as processed. Label to add: {label_to_add}")
        if not self.creds or not self.creds.valid:
            logger.warning(f"Cannot mark email UID {uid} as processed: invalid or missing credentials.")
            return False

        body_payload = {
            'removeLabelIds': ['UNREAD'] # Always mark as read
        }
        label_id_to_add = None

        if label_to_add:
            label_id_to_add = self._get_label_id(label_to_add)
            if label_id_to_add:
                body_payload['addLabelIds'] = [label_id_to_add]
            else:
                logger.warning(f"Label '{label_to_add}' not found, cannot add it to email UID {uid}. Will only mark as read.")

        if not body_payload.get('addLabelIds') and not body_payload.get('removeLabelIds'):
            logger.info(f"No actions to perform for email UID {uid} in mark_email_as_processed (no label to add, already not UNREAD?).")
            return True # Or False, depending on desired outcome for no-op

        try:
            service = build('gmail', 'v1', credentials=self.creds)
            service.users().messages().modify(userId='me', id=uid, body=body_payload).execute()
            log_message = f"Successfully processed email UID {uid}: marked as read"
            if label_id_to_add:
                log_message += f" and added label '{label_to_add}' (ID: {label_id_to_add})."
            else:
                log_message += "."
            logger.info(log_message)
            return True
        except HttpError as error:
            logger.error(f"Failed to modify email UID {uid} (mark as processed/read): {error}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred while marking email UID {uid} as processed: {e}", exc_info=True)
            return False

    def mark_email_as_seen(self, uid: str) -> bool: # Changed message_id to uid for clarity
        logger.debug(f"Attempting to mark email UID {uid} as Seen (remove UNREAD label).")
        if not self.creds or not self.creds.valid:
            logger.warning("Cannot mark email as seen: invalid or missing credentials. Attempting to reload/refresh.")
            # Pass client_config here
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

    def send_self_test_email(self, subject_prefix="AI Self-Test"):
        """Sends a test email from the account associated with this EmailClient instance to itself."""
        logger.info(f"send_self_test_email called for {self.email_address} with subject_prefix: '{subject_prefix}'")
        
        recipient = self.email_address  # Send to self (the account this client is for)
        subject = f"{subject_prefix}: Ping from Karen ({self.email_address}) {time.strftime('%Y-%m-%d %H:%M:%S')}"
        body = (
            f"This is an automated test email sent by the EmailClient for {self.email_address} to itself.\n\n"
            f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}"
            f"Purpose: Verify email sending capability for this specific account and token."
        )
        
        logger.info(f"Attempting to send self-test email to {recipient} (self) with subject: {subject}")
        try:
            success = self.send_email(to=recipient, subject=subject, body=body)
            
            if success:
                logger.info(f"Self-test email successfully dispatched to {recipient} (self).")
                return True
            else:
                logger.error(f"Failed to send self-test email to {recipient} (self): send_email returned False")
                return False
        except Exception as e:
            logger.error(f"Failed to send self-test email to {recipient} (self): {e}", exc_info=True)
            return False

    def send_designated_test_email(self, recipient_address: str, subject_prefix="AI Designated Test"):
        """Sends a test email from the account associated with this EmailClient instance to a specified recipient."""
        logger.info(f"send_designated_test_email called for {self.email_address} to send to {recipient_address} with subject_prefix: '{subject_prefix}'")
        
        subject = f"{subject_prefix}: Test from Karen ({self.email_address}) to ({recipient_address}) {time.strftime('%Y-%m-%d %H:%M:%S')}"
        body = (
            f"This is an automated test email sent by the EmailClient for {self.email_address} to {recipient_address}.\n\n"
            f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}"
            f"Purpose: Verify email sending capability from {self.email_address} to an external/designated recipient."
        )
        
        logger.info(f"Attempting to send designated test email from {self.email_address} to {recipient_address} with subject: {subject}")
        try:
            success = self.send_email(to=recipient_address, subject=subject, body=body)
            
            if success:
                logger.info(f"Designated test email successfully dispatched from {self.email_address} to {recipient_address}.")
                return True
            else:
                logger.error(f"Failed to send designated test email from {self.email_address} to {recipient_address}: send_email returned False")
                return False
        except Exception as e:
            logger.error(f"Failed to send designated test email from {self.email_address} to {recipient_address}: {e}", exc_info=True)
            return False

    def fetch_last_n_sent_emails(self, n: int = 1, recipient_filter: Optional[str] = None, metadata_only: bool = False) -> List[Dict[str, Any]]:
        """
        Fetches the last N email(s) from the '[Gmail]/Sent Mail' folder, optionally filtering by recipient and fetching metadata only.

        Args:
            n: The number of recent sent emails to fetch.
            recipient_filter: Optional email address string. If provided, only emails sent to this recipient will be returned.
            metadata_only: If True, fetches only metadata (headers, snippet). If False, fetches full content.

        Returns:
            A list of dictionaries, where each dictionary contains details of a sent email,
            or an empty list if no emails are found or an error occurs.
        """
        fetch_type = "metadata" if metadata_only else "full content"
        logger.info(f"Fetching {fetch_type} for the last {n} sent email(s) for {self.email_address}{f' to {recipient_filter}' if recipient_filter else ''}...")
        if not self.creds or not self.creds.valid:
            logger.warning("Cannot fetch sent emails: invalid or missing credentials. Attempting to reload/refresh.")
            reloaded_creds = self._load_and_refresh_credentials()
            if not reloaded_creds or not reloaded_creds.valid:
                logger.error("Failed to obtain valid credentials after attempting reload/refresh for fetch_last_n_sent_emails.")
                return []
            self.creds = reloaded_creds
            logger.info("Credentials reloaded/refreshed successfully for fetch_last_n_sent_emails.")

        emails_details = []
        try:
            service = build('gmail', 'v1', credentials=self.creds)
            
            query_parts = ['in:sent']
            if recipient_filter:
                query_parts.append(f'to:{recipient_filter}')
            search_query = ' '.join(query_parts)
            logger.debug(f"Using Gmail search query: '{search_query}'")
            
            results = service.users().messages().list(userId='me', q=search_query, maxResults=n).execute()
            messages = results.get('messages', [])

            if not messages:
                logger.info(f"No sent emails found matching criteria for {self.email_address}{f' to {recipient_filter}' if recipient_filter else ''}.")
                return []

            logger.info(f"Found {len(messages)} candidate sent message(s). Processing up to {n} of them.")

            for msg_ref in messages[:n]: 
                msg_id = msg_ref['id']
                thread_id = msg_ref['threadId']
                try:
                    api_format = 'metadata' if metadata_only else 'full'
                    msg = service.users().messages().get(userId='me', id=msg_id, format=api_format).execute()
                    
                    payload = msg.get('payload', {}) # Payload is present in metadata format too
                    headers = payload.get('headers', [])
                    
                    email_data = {
                        'id': msg_id,
                        'threadId': thread_id,
                        'snippet': msg.get('snippet', ''), # Snippet is available in metadata
                        'subject': None,
                        'sender': self.email_address, 
                        'recipient': None, 
                        'date_utc_timestamp': None,
                        'date_iso': None, 
                        'body_text': None, # Will be None if metadata_only is True
                        'body_html': None  # Will be None if metadata_only is True
                    }

                    for header in headers:
                        name = header.get('name', '').lower()
                        if name == 'subject':
                            email_data['subject'] = header.get('value', '')
                        elif name == 'to': 
                            email_data['recipient'] = header.get('value', '')
                        # Date from headers can be inconsistent, internalDate is better
                    
                    internal_date_ms = msg.get('internalDate')
                    if internal_date_ms:
                        internal_date_ts = int(internal_date_ms) / 1000
                        email_data['date_utc_timestamp'] = internal_date_ts
                        try:
                            email_data['date_iso'] = datetime.utcfromtimestamp(internal_date_ts).isoformat() + "Z"
                        except Exception as date_e:
                            logger.warning(f"Could not format internalDate {internal_date_ts} to ISO string: {date_e}")

                    if not metadata_only:
                        if 'parts' in payload:
                            for part in payload['parts']:
                                mime_type = part.get('mimeType', '')
                                body_data_content = part.get('body', {}).get('data') # Renamed to avoid conflict
                                if body_data_content:
                                    decoded_data = base64.urlsafe_b64decode(body_data_content).decode('utf-8', errors='replace')
                                    if mime_type == 'text/plain' and not email_data['body_text']:
                                        email_data['body_text'] = decoded_data
                                    elif mime_type == 'text/html':
                                        email_data['body_html'] = decoded_data
                            if email_data['body_html'] and not email_data['body_text']:
                                 email_data['body_text'] = "HTML body content (no plain text part found)."
                        elif 'data' in payload.get('body', {}): 
                            body_data_content = payload['body']['data'] # Renamed
                            decoded_data = base64.urlsafe_b64decode(body_data_content).decode('utf-8', errors='replace')
                            email_data['body_text'] = decoded_data
                    
                    emails_details.append(email_data)
                    logger.debug(f"Successfully processed sent email ID {msg_id} (metadata_only={metadata_only}). Subject: {email_data.get('subject', 'N/A')[:50]}...")
                    if len(emails_details) >= n:
                        break 

                except HttpError as error_msg_get:
                    logger.error(f"HttpError fetching details for sent message ID {msg_id}: {error_msg_get}", exc_info=True)
                except Exception as e_msg_get:
                    logger.error(f"Error processing details for sent message ID {msg_id}: {e_msg_get}", exc_info=True)
            
            logger.info(f"Successfully fetched details for {len(emails_details)} sent email(s).")
            return emails_details

        except HttpError as error_list:
            logger.error(f"HttpError fetching sent email list: {error_list}", exc_info=True)
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching last {n} sent emails: {e}", exc_info=True)
            return []

# Example usage (for testing, if run directly)
if __name__ == '__main__':
    # This is for basic testing of the EmailClient
    # Ensure KAREN_GMAIL_TOKEN_PATH (or other token) and credentials.json are set up
    from dotenv import load_dotenv
    import sys

    # Simplified .env loading for direct script test
    # Assumes .env is in project root, and this script is in src/
    dotenv_path = os.path.join(PROJECT_ROOT, '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path=dotenv_path)
        print(f"Loaded .env from {dotenv_path} for EmailClient testing.")
    else:
        print(f"Warning: .env file not found at {dotenv_path} for EmailClient testing.")

    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

    # Test with the secretary (Karen) account credentials
    karen_email = os.getenv("SECRETARY_EMAIL_ADDRESS", "karensecretaryai@gmail.com") # Default if not in .env
    karen_token_file = os.getenv("SECRETARY_TOKEN_PATH", "gmail_token_karen.json")
    
    # Test with the monitoring (hello@757handy.com) account credentials
    monitor_email = os.getenv("MONITORED_EMAIL_ACCOUNT", "hello@757handy.com")
    monitor_token_file = os.getenv("MONITORED_EMAIL_TOKEN_PATH", "gmail_token_monitor.json")


    if not os.path.exists(CREDENTIALS_FILE_PATH):
        logger.error(f"CRITICAL: credentials.json not found at {CREDENTIALS_FILE_PATH}. Cannot run test.")
    else:
        try:
            logger.info(f"--- TESTING {karen_email} (token: {karen_token_file}) ---")
            client_karen = EmailClient(email_address=karen_email, token_file_path=karen_token_file)
            
            # Test fetching last N sent emails
            last_few_sent = client_karen.fetch_last_n_sent_emails(n=3)
            if last_few_sent:
                print(f"\n--- Last {len(last_few_sent)} Emails Sent by {karen_email} ---")
                for i, email_detail in enumerate(last_few_sent):
                    print(f"Email {i+1}:")
                    print(f"  ID: {email_detail.get('id')}")
                    print(f"  To: {email_detail.get('recipient')}")
                    print(f"  Subject: {email_detail.get('subject')}")
                    print(f"  Date: {email_detail.get('date_iso')}")
                    print(f"  Snippet: {email_detail.get('snippet')}")
                    # print(f"  Body: {email_detail.get('body_text', '')[:100]}...")
                    print("---")
            else:
                print(f"No sent emails found for {karen_email} or error fetching them.")

            # Test sending an email
            # test_to_email = "your_other_email@example.com" # CHANGE THIS FOR TESTING
            # print(f"\nAttempting to send a test email to {test_to_email} from {karen_email}...")
            # success = client_karen.send_email(test_to_email, "EmailClient Test Message", "This is a test email from EmailClient.")
            # if success:
            #     print("Test email sent successfully.")
            # else:
            #     print("Failed to send test email.")

            # Test fetching emails (e.g., unread)
            # print(f"\nFetching UNREAD emails for {karen_email}...")
            # unread_emails = client_karen.fetch_emails(search_criteria='is:unread', max_results=5)
            # if unread_emails:
            #     print(f"Found {len(unread_emails)} unread emails for {karen_email}:")
            #     for em in unread_emails:
            #         print(f"  From: {em.get('sender')}, Subject: {em.get('subject')}, UID: {em.get('uid')}")
            # else:
            #     print(f"No unread emails found for {karen_email}.")


            logger.info(f"--- TESTING {monitor_email} (token: {monitor_token_file}) ---")
            client_monitor = EmailClient(email_address=monitor_email, token_file_path=monitor_token_file)
            last_monitor_sent = client_monitor.fetch_last_n_sent_emails(n=2)
            if last_monitor_sent:
                print(f"\n--- Last {len(last_monitor_sent)} Emails Sent by {monitor_email} ---")
                for i, email_detail in enumerate(last_monitor_sent):
                    print(f"Email {i+1}:")
                    print(f"  To: {email_detail.get('recipient')}")
                    print(f"  Subject: {email_detail.get('subject')}")
                print("---")

        except ValueError as ve:
            logger.error(f"ValueError during EmailClient test setup: {ve}")
        except Exception as e:
            logger.error(f"An error occurred during EmailClient test: {e}", exc_info=True)

from ..email_client import EmailClient
from ..mock_email_client import MockEmailClient
from .sms_handler import SMSHandler
from .voice_transcription_handler import VoiceTranscriptionHandler
from typing import Dict, Any, Optional
import logging
import re
from fastapi import HTTPException

# Import the actual schemas
from ..schemas.task import TaskCreateSchema, TaskDetailsSchema # TaskResponseSchema if needed for return types

# Import config for testing flag
from ..config import USE_MOCK_EMAIL_CLIENT

# Import LLMClient
from ..llm_client import LLMClient # Added

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG) # Ensure DEBUG level for this logger

class CommunicationAgent:
    def __init__(self, 
                 email_client_cfg: Dict[str, Any],
                 sms_cfg: Dict[str, Any], 
                 transcription_cfg: Optional[Dict[str, Any]],
                 admin_email: str,
                 task_manager_instance: Any): # Added task_manager_instance
        
        logger.debug(f"Initializing CommunicationAgent. USE_MOCK_EMAIL_CLIENT: {USE_MOCK_EMAIL_CLIENT}")
        self.secretary_email_address = email_client_cfg.get('SECRETARY_EMAIL_ADDRESS') # Store for checking self-sent emails
        if USE_MOCK_EMAIL_CLIENT:
            logger.warning("Using MockEmailClient for testing purposes.")
            self.email_client = MockEmailClient(
                smtp_server=email_client_cfg.get('SECRETARY_EMAIL_SMTP_SERVER'),
                smtp_port=email_client_cfg.get('SECRETARY_EMAIL_SMTP_PORT'),
                imap_server=email_client_cfg.get('SECRETARY_EMAIL_IMAP_SERVER'),
                email_address=email_client_cfg.get('SECRETARY_EMAIL_ADDRESS', 'mock_secretary@example.com'),
                password=email_client_cfg.get('SECRETARY_EMAIL_PASSWORD', 'mock_password')
            )
            logger.debug("MockEmailClient instantiated.")
        else:
            logger.debug("Attempting to instantiate real EmailClient.")
            self.email_client = EmailClient(
                # smtp_server=email_client_cfg.get('SECRETARY_EMAIL_SMTP_SERVER'), # Not used by Gmail API client
                # smtp_port=email_client_cfg.get('SECRETARY_EMAIL_SMTP_PORT'),   # Not used
                # imap_server=email_client_cfg.get('SECRETARY_EMAIL_IMAP_SERVER'), # Not used
                email_address=email_client_cfg.get('SECRETARY_EMAIL_ADDRESS')
                # password=email_client_cfg.get('SECRETARY_EMAIL_PASSWORD') # Not used, Gmail API uses OAuth token
            )
            logger.debug(f"Real EmailClient instantiated for {email_client_cfg.get('SECRETARY_EMAIL_ADDRESS')}.")
            
        self.sms_handler = SMSHandler(**sms_cfg) if sms_cfg and sms_cfg.get('account_sid') else None
        if self.sms_handler:
            logger.debug("SMSHandler instantiated.")
        else:
            logger.debug("SMSHandler not instantiated (no config or account_sid).")
        
        if transcription_cfg and transcription_cfg.get('language_code'): # Assuming language_code is essential
            self.voice_handler = VoiceTranscriptionHandler(**transcription_cfg)
            logger.debug("VoiceTranscriptionHandler instantiated.")
        else:
            self.voice_handler = None
            logger.info("VoiceTranscriptionHandler not initialized (no config or language_code).")

        self.admin_email = admin_email
        self.task_manager = task_manager_instance 
        self.processed_email_ids = set()

        # Initialize LLMClient
        try:
            self.llm_client = LLMClient()
            logger.info("LLMClient initialized successfully within CommunicationAgent.")
        except ValueError as e:
            logger.error(f"Failed to initialize LLMClient in CommunicationAgent: {e}")
            self.llm_client = None
        
        logger.debug(f"CommunicationAgent initialized. Admin email: {admin_email}")

    def send_admin_email(self, subject: str, body: str) -> bool:
        if not self.admin_email:
            logger.error("Admin email address not configured. Cannot send email.")
            return False
        logger.debug(f"Attempting to send email to admin ({self.admin_email}): Subject: {subject[:50]}...")
        try:
            success = self.email_client.send_email(to=self.admin_email, subject=subject, body=body)
            if success:
                logger.info(f"Successfully sent email to admin: {subject[:50]}...")
            else:
                logger.error(f"Failed to send email to admin: {subject[:50]}...")
            return success
        except Exception as e:
            logger.error(f"Exception in send_admin_email: {e}", exc_info=True)
            return False

    def check_and_process_incoming_tasks(self, process_last_n_days: Optional[int] = None):
        logger.debug(f"Starting check_and_process_incoming_tasks. Process last {process_last_n_days} days. Email: {self.email_client.email_address if self.email_client else 'N/A'}")
        try:
            search_criteria_for_fetch = 'UNSEEN'
            query_details = f"criteria '{search_criteria_for_fetch}'"
            if process_last_n_days is not None and process_last_n_days > 0:
                logger.debug(f"Fetching all emails from the last {process_last_n_days} days.")
                # The email_client's fetch_emails will construct the date-based search query
                emails = self.email_client.fetch_emails(last_n_days=process_last_n_days) 
                query_details = f"last {process_last_n_days} days"
            else:
                logger.debug(f"Fetching UNSEEN emails only.")
                emails = self.email_client.fetch_emails(search_criteria=search_criteria_for_fetch)
            
            if not emails:
                logger.info(f"No new emails found for {query_details}.")
                return

            logger.info(f"Found {len(emails)} email(s) for {query_details}.")

            for email_data in emails:
                email_subject = email_data.get('subject', '')
                email_body = email_data.get('body', '')
                email_from = email_data.get('sender', '') # Changed from 'from' to 'sender' to match EmailClient output
                message_id = email_data.get('id') 
                email_uid = email_data.get('uid') # 'uid' is set to message 'id' in EmailClient for Gmail

                logger.debug(f"Processing email UID: {email_uid}, From: {email_from}, Subject: {email_subject[:50]}...")

                if not message_id or not email_uid:
                    logger.warning(f"Email data missing 'id' or 'uid'. Skipping. UID: {email_uid}, ID: {message_id}")
                    continue

                if message_id in self.processed_email_ids:
                    logger.debug(f"Skipping already processed email ID: {message_id}, Subject: {email_subject[:50]}...")
                    continue

                # Avoid processing emails sent by the secretary itself to prevent loops
                if email_from and self.secretary_email_address and email_from.lower() == self.secretary_email_address.lower():
                    logger.info(f"Skipping email UID {email_uid} from self ({email_from}). Subject: {email_subject[:50]}...")
                    self.processed_email_ids.add(message_id) # Mark as processed to avoid re-checking
                    if email_uid: # Mark as seen even if from self
                        self.email_client.mark_email_as_seen(uid=email_uid)
                    continue

                # Generate LLM response for the email
                llm_reply_body = "Could not generate a response at this time." # Default reply
                if self.llm_client:
                    prompt = (
                        f"You are an AI Handyman Secretary Assistant. Respond to the following email in a helpful and professional manner. "\
                        f"If it's a new query, acknowledge it. If it's a follow-up, consider previous context if available (though not provided in this prompt). "\
                        f"Keep responses concise. Do not try to create tasks unless explicitly asked with 'TASK:'.\\n\\n"\
                        f"Sender: {email_from}\\n" \
                        f"Subject: {email_subject}\\n\\n" \
                        f"Body:\\n{email_body}\\n\\n" \
                        f"Assistant Reply:"\
                    )
                    try:
                        logger.info(f"Generating LLM reply for email UID {email_uid} from {email_from}")
                        llm_reply_body = self.llm_client.generate_text(prompt)
                        logger.info(f"LLM reply generated for email UID {email_uid}. Length: {len(llm_reply_body)}")
                    except Exception as e:
                        logger.error(f"Error generating LLM reply for email UID {email_uid}: {e}", exc_info=True)
                        llm_reply_body = f"I encountered an error trying to process your request fully. The admin has been notified. (Error: {str(e)[:100]})"
                else:
                    logger.warning(f"LLMClient not available. Cannot generate reply for email UID {email_uid}.")
                    llm_reply_body = "The AI response system is currently unavailable. An administrator has been notified."

                # Send the LLM-generated reply to the original sender
                reply_subject = f"Re: {email_subject}"
                if email_from: # Ensure there's a sender to reply to
                    logger.info(f"Sending LLM reply to {email_from} for email UID {email_uid}. Subject: {reply_subject[:50]}...")
                    send_success = self.email_client.send_email(to=email_from, subject=reply_subject, body=llm_reply_body)
                    if send_success:
                        logger.info(f"Successfully sent LLM reply to {email_from} for email UID {email_uid}.")
                    else:
                        logger.error(f"Failed to send LLM reply to {email_from} for email UID {email_uid}. Notifying admin.")
                        self.send_admin_email(
                            subject=f"Failed to send LLM reply to {email_from} (UID {email_uid})", \
                            body=f"Original Email Subject: {email_subject}\\nOriginal Email Body:\\n{email_body}\\n\\nGenerated LLM Reply (failed to send):\\n{llm_reply_body}"\
                        )
                else:
                    logger.warning(f"No sender found for email UID {email_uid}. Cannot send LLM reply.")

                # Existing task creation logic (can be run after or in parallel)
                task_description = None
                logger.debug(f"Attempting to extract task from email UID {email_uid} (subject or body).")
                if email_subject and "TASK:".lower() in email_subject.lower():
                    task_description = email_subject.lower().split("task:", 1)[1].strip()
                    logger.debug(f"Task extracted from subject: '{task_description}'")
                elif email_body:
                    match = re.search(r"TASK:(.*?)(?=\n\n|$)", email_body, re.IGNORECASE | re.DOTALL)
                    if match:
                        task_description = match.group(1).strip()
                        logger.debug(f"Task extracted from body: '{task_description}'")
                
                if task_description:
                    logger.info(f"Extracted task: '{task_description}' from email UID {email_uid}")
                    admin_notification_subject = f"Task Identified: {task_description[:30]}... (from {email_from})"
                    admin_notification_body = f"A task was identified from an email by {email_from} (UID: {email_uid}):\\n\\nTask: {task_description}\\nOriginal Subject: {email_subject}\\n\\nAttempting to create task in TaskManager..."
                    try:
                        task_details_obj = TaskDetailsSchema(description=task_description)
                        parsed_from_email = re.search(r'[\w\.-]+@[\w\.-]+', email_from)
                        created_by_email = parsed_from_email.group(0) if parsed_from_email else email_from
                        logger.debug(f"Task creator identified as: {created_by_email}")

                        create_task_req = TaskCreateSchema(details=task_details_obj, created_by=created_by_email)
                        logger.debug(f"Attempting to create task with TaskManager: {create_task_req.model_dump_json(indent=2)}")
                        
                        task_response = self.task_manager.create_task(create_task_req)
                        llm_suggestion_text = "No LLM suggestion available for task."
                        
                        if task_response and hasattr(task_response, 'id') and task_response.id:
                            logger.info(f"Task creation successful (ID: {task_response.id}). Task: '{task_description}'")
                            admin_notification_body += f"\n\nTask successfully created with ID: {task_response.id}."
                            # Attempt to get LLM suggestion for task (separate from email reply LLM)
                            logger.debug(f"Attempting to generate LLM suggestion for new task ID: {task_response.id}")
                            suggestion = self.task_manager.generate_llm_suggestion_for_task(task_response.id)
                            if suggestion:
                                logger.info(f"LLM task suggestion received for task {task_response.id}: '{suggestion[:100]}...'")
                                llm_suggestion_text = suggestion
                                admin_notification_body += f"\nAI Suggestion for task: {llm_suggestion_text}"
                            else:
                                logger.warning(f"Could not generate LLM task suggestion for task {task_response.id}.")
                                admin_notification_body += "\nCould not generate LLM task suggestion."
                        else:
                            error_message = getattr(task_response, 'message', "Unknown error during task creation response")
                            logger.error(f"Task creation failed (no valid ID in response) for: '{task_description}'. Response error: {error_message}")
                            admin_notification_body += f"\n\nTask creation FAILED. Error: {error_message}"

                    except HTTPException as http_exc:
                        logger.error(f"HTTPException during task creation for '{task_description}': {http_exc.detail}", exc_info=True)
                        admin_notification_body += f"\n\nTask creation FAILED due to HTTPError: {http_exc.detail}"
                    except Exception as e:
                        logger.error(f"Exception during task creation for '{task_description}': {e}", exc_info=True)
                        admin_notification_body += f"\n\nTask creation FAILED due to Exception: {str(e)}"

                    # Send admin notification about task creation attempt
                    self.send_admin_email(subject=admin_notification_subject, body=admin_notification_body)
                else:
                    # If no task was explicitly extracted, this was handled by the general LLM reply earlier.
                    # We can send a simpler admin note that an email was processed.
                    self.send_admin_email(
                        subject=f"Email Processed (No Task Keyword): {email_subject[:30]}... (from {email_from})",
                        body=f"Email from {email_from} (UID: {email_uid}) was processed and an LLM reply was attempted.\\nSubject: {email_subject}\\nBody:\\n{email_body}\\n\\nLLM Reply Sent:\\n{llm_reply_body}"\
                    )

                self.processed_email_ids.add(message_id)
                logger.debug(f"Added email ID {message_id} to processed_email_ids. Total processed: {len(self.processed_email_ids)}")
                
                if email_uid:
                    logger.debug(f"Attempting to mark email UID {email_uid} as Seen.")
                    if self.email_client.mark_email_as_seen(uid=email_uid):
                        logger.info(f"Successfully marked email UID {email_uid} as Seen.")
                    else:
                        logger.warning(f"Failed to mark email UID {email_uid} as Seen.")
                else:
                    logger.warning(f"Cannot mark email as seen, UID not found for email with id: {message_id}")

        except Exception as e:
            logger.error(f"Unhandled exception in check_and_process_incoming_tasks: {e}", exc_info=True)
            self.send_admin_email(subject="Critical Email Processing Error", body=f"The email processing agent encountered a critical error in check_and_process_incoming_tasks: {str(e)}")

    def process_sms(self, to_number: str, message: str) -> Optional[str]:
        logger.debug(f"Processing SMS to {to_number}: {message[:30]}...")
        if self.sms_handler:
            return self.sms_handler.send_sms(to_number, message)
        logger.warning("SMS handler not initialized, cannot send SMS.")
        return None

    def process_voice_transcription(self, audio_bytes: bytes) -> Optional[str]:
        logger.debug(f"Processing voice transcription for audio of length {len(audio_bytes)} bytes.")
        if self.voice_handler:
            return self.voice_handler.transcribe_audio(audio_bytes)
        logger.warning("Voice handler not initialized, cannot transcribe audio.")
        return None

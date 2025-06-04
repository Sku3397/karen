from ..email_client import EmailClient
from ..mock_email_client import MockEmailClient
from .sms_handler import SMSHandler
from .voice_transcription_handler import VoiceTranscriptionHandler
from typing import Dict, Any, Optional, List
import logging
import re
from fastapi import HTTPException
import time
import os
from datetime import datetime, timedelta, timezone
import dateutil.parser # For robust date/time parsing
import pytz # For timezone handling
import asyncio # Added for running async methods from sync context if needed

# Import the actual schemas
from ..schemas.task import TaskCreateSchema, TaskDetailsSchema # TaskResponseSchema if needed for return types

# Import config for testing flag
from ..config import USE_MOCK_EMAIL_CLIENT

# Import LLMClient
from ..llm_client import LLMClient # Added

# Import enhanced response engine
from ..handyman_response_engine import HandymanResponseEngine

# Import new client and its scopes
from src.calendar_client import CalendarClient, CALENDAR_SCOPES

# Import task manager - remove unused Task and TaskStatus
from src.task_manager import TaskManager #, Task, TaskStatus # Removed Task, TaskStatus

# Import config
from src.config import (
    ADMIN_EMAIL_ADDRESS,
    SECRETARY_EMAIL_ADDRESS, 
    MONITORED_EMAIL_ACCOUNT_CONFIG,
    GOOGLE_CALENDAR_TOKEN_PATH,
    GOOGLE_APP_CREDENTIALS_PATH
)

# Import the new utility function
from src.datetime_utils import parse_datetime_from_details

# Import memory system
from src.memory_client import store_email_memory, get_conversation_context

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG) # Ensure DEBUG level for this logger

class CommunicationAgent:
    def __init__(self, 
                 sending_email_cfg: Dict[str, Any], # Renamed for clarity
                 monitoring_email_cfg: Dict[str, Any], # New config for monitoring account
                 sms_cfg: Dict[str, Any], 
                 transcription_cfg: Optional[Dict[str, Any]],
                 admin_email: str,
                 task_manager_instance: Any):
        
        logger.debug(f"Initializing CommunicationAgent. USE_MOCK_EMAIL_CLIENT: {USE_MOCK_EMAIL_CLIENT}")
        self.secretary_email_address = sending_email_cfg.get('SECRETARY_EMAIL_ADDRESS') # This is the sending (Karen's) email
        self.monitoring_email_address = monitoring_email_cfg.get('MONITORED_EMAIL_ACCOUNT')

        if USE_MOCK_EMAIL_CLIENT:
            logger.warning("Using MockEmailClient for testing purposes for both sending and monitoring.")
            # Mock client would need to simulate two accounts or be used carefully.
            # For simplicity, one mock client might be used, or this section expanded.
            self.sending_email_client = MockEmailClient(
                email_address=self.secretary_email_address,
                # ... other mock params ...
            )
            self.monitoring_email_client = self.sending_email_client # Or a separate mock instance
            logger.debug("MockEmailClients instantiated.")
        else:
            logger.debug("Attempting to instantiate real EmailClients.")
            # Sending Client (Karen)
            sending_token_path = sending_email_cfg.get('SECRETARY_TOKEN_PATH', 'gmail_token_karen.json') # Default path for Karen
            self.sending_email_client = EmailClient(
                email_address=self.secretary_email_address,
                token_file_path=sending_token_path
            )
            logger.debug(f"Real EmailClient (sending) instantiated for {self.secretary_email_address} using {sending_token_path}.")

            # Monitoring Client (hello@757handy.com)
            monitoring_token_path = monitoring_email_cfg.get('MONITORED_EMAIL_TOKEN_PATH', 'gmail_token_monitor.json')
            self.monitoring_email_client = EmailClient(
                email_address=self.monitoring_email_address,
                token_file_path=monitoring_token_path
            )
            logger.debug(f"Real EmailClient (monitoring) instantiated for {self.monitoring_email_address} using {monitoring_token_path}.")
            
        self.sms_handler = SMSHandler(**sms_cfg) if sms_cfg and sms_cfg.get('account_sid') else None
        if self.sms_handler:
            logger.debug("SMSHandler instantiated.")
        else:
            logger.debug("SMSHandler not instantiated (no config or account_sid).")
        
        if transcription_cfg and transcription_cfg.get('language_code'):
            self.voice_handler = VoiceTranscriptionHandler(**transcription_cfg)
            logger.debug("VoiceTranscriptionHandler instantiated.")
        else:
            self.voice_handler = None
            logger.info("VoiceTranscriptionHandler not initialized (no config or language_code).")

        self.admin_email = admin_email
        self.task_manager = task_manager_instance 
        # self.processed_email_ids = set() # Replaced by Karen_Processed label

        try:
            self.llm_client = LLMClient()
            logger.info("LLMClient initialized successfully within CommunicationAgent.")
        except ValueError as e:
            logger.error(f"Failed to initialize LLMClient in CommunicationAgent: {e}")
            self.llm_client = None
        
        self.response_engine = HandymanResponseEngine(
            business_name="Beach Handyman",
            service_area="Virginia Beach area", 
            phone="757-354-4577",
            llm_client=self.llm_client 
        )
        logger.info("HandymanResponseEngine initialized successfully.")
        logger.debug(f"CommunicationAgent initialized. Admin email: {admin_email}")

        # Initialize CalendarClient for the monitored account (hello@757handy.com)
        self.calendar_client: Optional[CalendarClient] = None
        if self.monitoring_email_address == MONITORED_EMAIL_ACCOUNT_CONFIG: # Only init for the main account
            try:
                logger.info(f"Attempting to initialize CalendarClient for {self.monitoring_email_address}...")
                self.calendar_client = CalendarClient(
                    email_address=self.monitoring_email_address,
                    token_path=GOOGLE_CALENDAR_TOKEN_PATH, # From config
                    credentials_path=GOOGLE_APP_CREDENTIALS_PATH # From config
                )
                logger.info(f"CalendarClient initialized successfully for {self.monitoring_email_address}.")
            except ValueError as ve:
                logger.error(f"Failed to initialize CalendarClient for {self.monitoring_email_address} due to ValueError: {ve}. Calendar functions will be unavailable. Ensure token {GOOGLE_CALENDAR_TOKEN_PATH} is valid with scopes: {CALENDAR_SCOPES}")
            except Exception as e:
                logger.error(f"Unexpected error initializing CalendarClient for {self.monitoring_email_address}: {e}. Calendar functions will be unavailable.", exc_info=True)
        else:
            logger.warning(f"CalendarClient not initialized; monitored_email_address '{self.monitoring_email_address}' does not match MONITORED_EMAIL_ACCOUNT_CONFIG '{MONITORED_EMAIL_ACCOUNT_CONFIG}'.")

    def send_admin_email(self, subject: str, body: str) -> bool:
        if not self.admin_email:
            logger.error("Admin email address not configured. Cannot send email.")
            return False
        logger.debug(f"Attempting to send email to admin ({self.admin_email}) using sending_email_client: Subject: {subject[:50]}...")
        try:
            # Use the sending_email_client (Karen's account)
            success = self.sending_email_client.send_email(to=self.admin_email, subject=subject, body=body)
            if success:
                logger.info(f"Successfully sent email to admin: {subject[:50]}...")
            else:
                logger.error(f"Failed to send email to admin: {subject[:50]}...")
            return success
        except Exception as e:
            logger.error(f"Exception in send_admin_email: {e}", exc_info=True)
            return False

    async def check_and_process_incoming_tasks(self, process_last_n_days: Optional[int] = None):
        # Use monitoring_email_client for fetching
        logger.debug(f"Starting async check_and_process_incoming_tasks for {self.monitoring_email_address}. Process last {process_last_n_days} days.")
        KAREN_PROCESSED_LABEL = "Karen_Processed" # Define label name
        try:
            # Search for emails NOT having the "Karen_Processed" label.
            search_criteria_for_fetch = f'-label:{KAREN_PROCESSED_LABEL}'
            query_details = f"criteria '{search_criteria_for_fetch}' for {self.monitoring_email_address}"
            
            if process_last_n_days is not None and process_last_n_days > 0:
                date_n_days_ago = (datetime.now() - timedelta(days=process_last_n_days)).strftime('%Y/%m/%d')
                search_criteria_for_fetch = f'after:{date_n_days_ago} -label:{KAREN_PROCESSED_LABEL}'
                logger.debug(f"Fetching emails from the last {process_last_n_days} days from {self.monitoring_email_address} that are not labeled '{KAREN_PROCESSED_LABEL}'. Query: {search_criteria_for_fetch}")
                emails = self.monitoring_email_client.fetch_emails(search_criteria=search_criteria_for_fetch)
                query_details = f"last {process_last_n_days} days (not labeled {KAREN_PROCESSED_LABEL}) from {self.monitoring_email_address}"
            else:
                logger.debug(f"Fetching emails (not labeled {KAREN_PROCESSED_LABEL}) from {self.monitoring_email_address}. Query: {search_criteria_for_fetch}")
                emails = self.monitoring_email_client.fetch_emails(search_criteria=search_criteria_for_fetch)
            
            if not emails:
                logger.info(f"No new emails found for {query_details}.")
                return

            logger.info(f"Found {len(emails)} email(s) for {query_details}.")

            for email_data in emails:
                email_subject = email_data.get('subject', '')
                email_body = email_data.get('body', '')
                email_from = email_data.get('sender', '')
                message_id = email_data.get('id') 
                email_uid = email_data.get('uid')

                logger.debug(f"Processing email UID: {email_uid} from {self.monitoring_email_address}, Sender: {email_from}, Subject: {email_subject[:50]}...")

                if not message_id or not email_uid:
                    logger.warning(f"Email data missing 'id' or 'uid'. Skipping. UID: {email_uid}, ID: {message_id}")
                    continue

                # --- STARTUP SELF-TEST CHECK ---
                is_from_secretary_for_test = email_from and self.secretary_email_address and email_from.lower().startswith(self.secretary_email_address.lower())
                is_startup_test_subject = email_subject.startswith("STARTUP SELF-TEST: Ping from Karen")

                if is_from_secretary_for_test and is_startup_test_subject:
                    logger.info(f"STARTUP SELF-TEST: Received ping email UID {email_uid} from {email_from} with subject '{email_subject}'.")
                    confirmation_subject = f"SUCCESS: Startup Self-Test Acknowledged - {email_subject}"
                    confirmation_body = (
                        f"This is an automated confirmation that the startup self-test email was successfully received and processed in the '{self.monitoring_email_address}' inbox.\n\n"
                        f"Original Test Email Subject: {email_subject}\n"
                        f"Received from: {email_from}\n"
                        f"Processed at: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}"
                    )
                    try:
                        logger.info(f"STARTUP SELF-TEST: Sending confirmation from {self.monitoring_email_address} to admin {self.admin_email}.")
                        success = self.monitoring_email_client.send_email(
                            to=self.admin_email,
                            subject=confirmation_subject,
                            body=confirmation_body
                        )
                        if success:
                            logger.info(f"STARTUP SELF-TEST: Confirmation email successfully sent to admin.")
                        else:
                            logger.error(f"STARTUP SELF-TEST: Failed to send confirmation email to admin.")
                    except Exception as e_test_conf:
                        logger.error(f"STARTUP SELF-TEST: Exception while sending confirmation email: {e_test_conf}", exc_info=True)
                    
                    if email_uid:
                        self.monitoring_email_client.mark_email_as_processed(uid=email_uid, label_to_add=KAREN_PROCESSED_LABEL)
                    continue
                # --- END STARTUP SELF-TEST CHECK ---

                if email_from and self.monitoring_email_address and email_from.lower().startswith(self.monitoring_email_address.lower()):
                    logger.info(f"Skipping email UID {email_uid} from the monitoring account ({email_from}) to itself. Subject: {email_subject[:50]}...")
                    if email_uid:
                         self.monitoring_email_client.mark_email_as_processed(uid=email_uid, label_to_add=KAREN_PROCESSED_LABEL)
                    continue

                llm_reply_body = "Could not generate a response at this time."
                email_classification = None
                
                # Get conversation context from memory system
                conversation_context = {}
                try:
                    conversation_context = await get_conversation_context(email_from, self.monitoring_email_address)
                    if conversation_context.get('message_count', 0) > 0:
                        logger.info(f"Found existing conversation history for {email_from}: {conversation_context.get('message_count')} messages, last interaction: {conversation_context.get('last_interaction')}")
                except Exception as e:
                    logger.warning(f"Failed to get conversation context for email UID {email_uid}: {e}")
                
                if self.llm_client and self.response_engine:
                    try:
                        logger.info(f"Generating enhanced handyman response for email UID {email_uid} from {email_from} (received in {self.monitoring_email_address})")
                        
                        # Enhance response generation with conversation context
                        if conversation_context.get('message_count', 0) > 0:
                            context_info = f"Previous conversation context: {conversation_context.get('conversation_summary', 'No summary available')}. Recent topics: {', '.join(conversation_context.get('recent_topics', []))[:100]}"
                            logger.debug(f"Adding conversation context to response generation for UID {email_uid}: {context_info}")
                        
                        llm_reply_body, email_classification = await self.response_engine.generate_response_async(
                            email_from, email_subject, email_body
                        )
                        logger.info(f"Enhanced response generated for email UID {email_uid}. Length: {len(llm_reply_body)}, Classification: {email_classification}")
                    except Exception as e:
                        logger.error(f"Error generating enhanced response for email UID {email_uid}: {e}", exc_info=True)
                        llm_reply_body = f"I encountered an error trying to process your request fully. The admin has been notified. (Error: {str(e)[:100]})"
                else:
                    logger.warning(f"LLMClient or ResponseEngine not available. Cannot generate reply for email UID {email_uid}.")
                    llm_reply_body = "The AI response system is currently unavailable. An administrator has been notified."

                reply_subject = f"Re: {email_subject}"
                if email_from:
                    logger.info(f"Sending LLM reply via {self.secretary_email_address} to {email_from} for email UID {email_uid}. Subject: {reply_subject[:50]}...")
                    send_success = self.sending_email_client.send_email(to=email_from, subject=reply_subject, body=llm_reply_body)
                    if send_success:
                        logger.info(f"Successfully sent LLM reply to {email_from} for email UID {email_uid}.")
                    else:
                        logger.error(f"Failed to send LLM reply to {email_from} for email UID {email_uid}. Notifying admin.")
                        admin_subject_fail = f"[URGENT] Failed to send LLM reply to {email_from} (UID {email_uid})"
                        admin_body_fail = f"""Original Email (from {self.monitoring_email_address}):
From: {email_from}
Subject: {email_subject}
Body:
{email_body}

Generated LLM Reply (failed to send from {self.secretary_email_address}):
{llm_reply_body}"""
                        self.send_admin_email(subject=admin_subject_fail, body=admin_body_fail)
                else:
                    logger.warning(f"No sender found for email UID {email_uid}. Cannot send LLM reply.")

                # ---- RESTORED TASK PROCESSING LOGIC ----
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
                    admin_notification_body = f"A task was identified from an email by {email_from} (UID: {email_uid}, monitored account: {self.monitoring_email_address}):\n\nTask: {task_description}\nOriginal Subject: {email_subject}\n\nAttempting to create task in TaskManager..."
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
                    self.send_admin_email(subject=admin_notification_subject, body=admin_notification_body)
                else: # No specific "TASK:" found, send general admin notification
                    priority = self.response_engine.get_priority_level(email_classification) if email_classification else "LOW"
                    services_list = email_classification.get('services_mentioned', []) if email_classification else []
                    services = ", ".join(services_list) if services_list else "None"
                    
                    admin_subject_no_task = f"[{priority}] Email Processed (No Specific Task): {email_subject[:25]}... (from {email_from})"
                    admin_body_no_task = f"""Email from {email_from} (UID: {email_uid}, monitored: {self.monitoring_email_address}) was processed and LLM response sent via {self.secretary_email_address}.

Subject: {email_subject}
Classification: {email_classification}
Services: {services}
Reply Sent: {llm_reply_body[:200]}..."""
                    self.send_admin_email(subject=admin_subject_no_task, body=admin_body_no_task)
                # ---- END RESTORED TASK PROCESSING LOGIC ----

                # Store conversation in memory system
                try:
                    conversation_id = await store_email_memory(email_data, llm_reply_body if email_from else None)
                    if conversation_id:
                        logger.debug(f"Stored email conversation in memory system for UID {email_uid}, conversation ID: {conversation_id}")
                except Exception as e:
                    logger.warning(f"Failed to store email conversation in memory for UID {email_uid}: {e}")

                # Mark email as processed in the monitored inbox
                if email_uid:
                    logger.debug(f"Marking email UID {email_uid} as processed in {self.monitoring_email_address} with label '{KAREN_PROCESSED_LABEL}'.")
                    self.monitoring_email_client.mark_email_as_processed(uid=email_uid, label_to_add=KAREN_PROCESSED_LABEL)
                
            logger.debug(f"Finished checking and processing incoming tasks for {self.monitoring_email_address}.")

        except Exception as e:
            logger.error(f"Error in check_and_process_incoming_tasks for {self.monitoring_email_address}: {e}", exc_info=True)
            import traceback # Import traceback module
            tb_str = traceback.format_exc() # Get traceback string
            self.send_admin_email(
                subject=f"[URGENT] Error in Email Processing Loop for {self.monitoring_email_address}", 
                body=f"An unexpected error occurred in check_and_process_incoming_tasks for {self.monitoring_email_address}:\n\n{str(e)}\n\nTraceback:\n{tb_str}"
            )

    def check_and_process_instruction_emails(self, 
                                             process_last_n_days: Optional[int] = None, 
                                             newer_than_duration: Optional[str] = None,
                                             override_search_criteria_for_duration_fetch: bool = False):
        """Checks the secretary_email_address for instruction emails (e.g., UPDATE PROMPT).
        
        Args:
            process_last_n_days: Check emails from the last N days. Mutually exclusive with newer_than_duration.
            newer_than_duration: Check emails newer than this duration (e.g., '1h', '2d'). Mutually exclusive with process_last_n_days.
            override_search_criteria_for_duration_fetch: If True and newer_than_duration is set, the primary search_criteria (like UNSEEN) will be ignored for the fetch.
        """
        if USE_MOCK_EMAIL_CLIENT:
            logger.info("Skipping instruction email check in mock mode.")
            return

        if process_last_n_days is not None and newer_than_duration is not None:
            logger.error("process_last_n_days and newer_than_duration are mutually exclusive. Please provide only one.")
            # Or raise an error: raise ValueError("process_last_n_days and newer_than_duration are mutually exclusive.")
            return

        log_fetch_details = ""
        if newer_than_duration:
            log_fetch_details = f"newer than {newer_than_duration}"
        elif process_last_n_days:
            log_fetch_details = f"for the last {process_last_n_days} days"
        else:
            # Default to last 1 day if neither is specified, or make it an error
            process_last_n_days = 1 # Default behavior
            log_fetch_details = f"for the last {process_last_n_days} day (default)"

        logger.info(f"Checking instruction emails in {self.secretary_email_address} {log_fetch_details}.")
        try:
            ADMIN_EMAIL_SUBJECT_PROMPT_UPDATE = "UPDATE PROMPT"
            KAREN_PROCESSED_LABEL = "Karen_Processed"
            base_search_criteria = f'subject:("{ADMIN_EMAIL_SUBJECT_PROMPT_UPDATE}") -label:{KAREN_PROCESSED_LABEL}'
            actual_search_criteria = base_search_criteria # Default to base

            override_active = override_search_criteria_for_duration_fetch and process_last_n_days is not None

            if override_active:
                date_n_days_ago_override = (datetime.now() - timedelta(days=process_last_n_days)).strftime('%Y/%m/%d')
                actual_search_criteria = f'after:{date_n_days_ago_override} subject:("{ADMIN_EMAIL_SUBJECT_PROMPT_UPDATE}") -label:{KAREN_PROCESSED_LABEL}'
                logger.info(f"Instruction email check (override active): using search_criteria: '{actual_search_criteria}' for last {process_last_n_days} days")
            
            # This elif handles newer_than_duration, which was previously part of the definition of actual_search_criteria
            # This structure ensures that only one date-based filter (override_active or newer_than_duration) is applied if both are somehow passed.
            elif newer_than_duration: # E.g., "1h", "2d"
                try:
                    num = int(newer_than_duration[:-1])
                    unit = newer_than_duration[-1].lower()
                    if unit == 'h':
                        delta = timedelta(hours=num)
                    elif unit == 'd':
                        delta = timedelta(days=num)
                    else:
                        raise ValueError("Invalid duration unit for newer_than_duration")
                    
                    date_threshold = (datetime.now() - delta).strftime('%Y/%m/%d')
                    # Corrected to use newer_than for precision if desired, or stick to after: for simplicity as currently implemented
                    # For now, keeping consistent with existing 'after:' logic from newer_than_duration conversion
                    actual_search_criteria = f'after:{date_threshold} subject:("{ADMIN_EMAIL_SUBJECT_PROMPT_UPDATE}") -label:{KAREN_PROCESSED_LABEL}'
                    logger.info(f"Instruction email check (newer_than active): using search_criteria: '{actual_search_criteria}' for emails newer than {newer_than_duration}")
                except ValueError as e_dur:
                    logger.error(f"Invalid newer_than_duration format: {newer_than_duration}. Error: {e_dur}. Defaulting to base criteria: '{base_search_criteria}'.")
                    actual_search_criteria = base_search_criteria
            
            # This handles the case where process_last_n_days is given but not as an override_search_criteria_for_duration_fetch scenario
            # (e.g. default periodic check with process_last_n_days=1)
            elif process_last_n_days is not None and process_last_n_days > 0 and not override_active:
                 date_n_days_ago = (datetime.now() - timedelta(days=process_last_n_days)).strftime('%Y/%m/%d')
                 actual_search_criteria = f'after:{date_n_days_ago} subject:("{ADMIN_EMAIL_SUBJECT_PROMPT_UPDATE}") -label:{KAREN_PROCESSED_LABEL}'
                 logger.info(f"Instruction email check (periodic with process_last_n_days): using '{actual_search_criteria}' for last {process_last_n_days} days.")

            else: # Regular periodic check, using the base_search_criteria (subject and -label)
                 logger.info(f"Instruction email check (standard periodic): using base search_criteria: '{actual_search_criteria}'.")


            if not self.sending_email_client:
                logger.error("sending_email_client (for instruction emails) is not initialized. Cannot fetch instruction emails.")
                return

            # Use sending_email_client (karensecretaryai@gmail.com) to fetch its own emails
            emails = self.sending_email_client.fetch_emails(
                search_criteria=actual_search_criteria, 
                last_n_days=None, 
                newer_than=None
            )

            if not emails:
                logger.info(f"No new instruction emails found in {self.secretary_email_address}.")
                return

            logger.info(f"Found {len(emails)} potential instruction email(s) in {self.secretary_email_address}.")

            # Determine the correct path to llm_system_prompt.txt relative to this file
            # Assuming this agent.py is in src/communication_agent/ and prompt is in src/
            current_dir = os.path.dirname(os.path.abspath(__file__))
            prompt_file_path = os.path.join(os.path.dirname(current_dir), 'llm_system_prompt.txt') # Goes up one level from communication_agent to src/
            logger.debug(f"Target system prompt file path for updates: {prompt_file_path}")

            for email_data in emails:
                email_subject = email_data.get('subject', '').strip()
                email_body = email_data.get('body', '')
                email_from = email_data.get('sender', '')
                message_id = email_data.get('id')
                email_uid = email_data.get('uid')

                logger.debug(f"Processing potential instruction email UID: {email_uid} from {email_from}, Subject: '{email_subject}'")

                if "UPDATE PROMPT" in email_subject:
                    logger.info(f"Found 'UPDATE PROMPT' instruction email UID {email_uid} from {email_from}.")
                    new_prompt_content = email_body.strip()
                    if not new_prompt_content:
                        logger.warning(f"'UPDATE PROMPT' email UID {email_uid} has an empty body. Skipping update.")
                        self.send_admin_email(
                            subject=f"[WARN] Empty Prompt Update Skipped (UID {email_uid})",
                            body=f"The 'UPDATE PROMPT' email from {email_from} (UID: {email_uid}, received in {self.secretary_email_address}) had an empty body and was skipped."
                        )
                        if email_uid:
                            self.sending_email_client.mark_email_as_processed(uid=email_uid, label_to_add="Karen_Processed")
                        continue
                    
                    try:
                        with open(prompt_file_path, 'w') as f:
                            f.write(new_prompt_content)
                        logger.info(f"Successfully updated {prompt_file_path} with new prompt from email UID {email_uid}.")
                        
                        # Send confirmation email from hello@757handy.com
                        confirmation_subject = "SUCCESS: System Prompt Updated"
                        confirmation_body = f"The system prompt (llm_system_prompt.txt) has been successfully updated via an instruction email from {email_from} (UID {email_uid} in {self.secretary_email_address}).\n\nNew prompt content:\n---\n{new_prompt_content}"
                        
                        logger.info(f"Sending prompt update confirmation from {self.monitoring_email_address} to admin {self.admin_email}.")
                        self.monitoring_email_client.send_email(to=self.admin_email, subject=confirmation_subject, body=confirmation_body)
                        
                        # Reload the prompt in the shared LLMClient instance
                        if self.llm_client:
                            self.llm_client._load_system_prompt()
                            logger.info("LLMClient system prompt reloaded after update.")
                            
                    except Exception as e_update:
                        logger.error(f"Failed to write new prompt to {prompt_file_path} or send confirmation for UID {email_uid}: {e_update}", exc_info=True)
                        self.send_admin_email(
                            subject=f"[ERROR] Prompt Update Failed (UID {email_uid})",
                            body=f"Failed to update the system prompt from email by {email_from} (UID: {email_uid}, received in {self.secretary_email_address}). Error: {e_update}"
                        )
                else:
                    logger.debug(f"Email UID {email_uid} in {self.secretary_email_address} is not a recognized instruction. Subject: '{email_subject}'")
                
                # Mark as seen regardless of whether it was a valid instruction or not, to avoid reprocessing
                if email_uid:
                    self.sending_email_client.mark_email_as_processed(uid=email_uid, label_to_add="Karen_Processed")
        
        except Exception as e_fetch:
            logger.error(f"Error fetching or processing instruction emails from {self.secretary_email_address}: {e_fetch}", exc_info=True)
            self.send_admin_email(
                subject=f"[URGENT] Error in Instruction Email Processing Loop for {self.secretary_email_address}", 
                body=f"An unexpected error occurred in check_and_process_instruction_emails for {self.secretary_email_address}:\n\n{str(e_fetch)}"
            )

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

    async def get_calendar_availability(self, start_date: datetime, end_date: datetime) -> Optional[List[Dict[str, str]]]:
        if not self.calendar_client:
            logger.warning("Calendar client not available for get_calendar_availability.")
            return None
        try:
            start_iso = start_date.isoformat() + 'Z'
            end_iso = end_date.isoformat() + 'Z'
            return self.calendar_client.get_availability(start_iso, end_iso)
        except Exception as e:
            logger.error(f"Error getting calendar availability: {e}", exc_info=True)
            return None

    async def create_calendar_event(self, summary: str, start_datetime: datetime, end_datetime: datetime, attendees: List[str]) -> Optional[Dict[str, Any]]:
        if not self.calendar_client:
            logger.warning("Calendar client not available for create_calendar_event.")
            return None
        try:
            start_iso = start_datetime.isoformat() + 'Z'
            end_iso = end_datetime.isoformat() + 'Z'
            return self.calendar_client.create_event(summary, start_iso, end_iso, attendees)
        except Exception as e:
            logger.error(f"Error creating calendar event: {e}", exc_info=True)
            return None

    async def process_single_email(self, email_data: dict, task_id: Optional[str] = None):
        email_subject = email_data.get('subject', '[No Subject]')
        email_body_text = email_data.get('body_text', '') # Prefer text for LLM
        email_body_html = email_data.get('body_html', '')
        email_content_for_processing = email_body_text if email_body_text else email_body_html
        email_from = email_data.get('sender')
        email_uid = email_data.get('uid')
        reply_to_address = email_from

        logger.info(f"Processing email UID {email_uid} from '{email_from}' with subject '{email_subject[:50]}...'")

        if not self.llm_client or not self.response_engine:
            logger.error(f"LLMClient or HandymanResponseEngine not initialized. Cannot process email UID {email_uid}.")
            return

        intent = await self.response_engine.determine_intent(email_content_for_processing, email_subject)
        logger.info(f"Determined intent for email UID {email_uid}: {intent}")

        reply_subject_prefix = "Re: "
        generated_reply_body = "Thank you for your email. We will get back to you shortly."

        if intent == "schedule_appointment":
            if not self.calendar_client:
                logger.warning(f"Calendar intent detected for UID {email_uid}, but CalendarClient is not available. Falling back to standard response.")
                classification = self.response_engine.classify_email_type(email_subject, email_content_for_processing)
                prompt = self.response_engine.generate_enhanced_prompt(email_from, email_subject, email_content_for_processing, classification)
                generated_reply_body = await self.llm_client.generate_text_async(prompt)
            else: # Calendar client is available
                logger.info(f"Attempting to extract appointment details for UID {email_uid}...")
                extracted_details = await self.response_engine.extract_appointment_details(email_content_for_processing, email_subject)
                
                if extracted_details:
                    logger.info(f"Extracted appointment details for UID {email_uid}: {extracted_details}")
                    req_date_str = extracted_details.get("requested_date")
                    req_time_str = extracted_details.get("requested_time")
                    service_desc = extracted_details.get("service_description", "handyman service")
                    duration_hours = extracted_details.get("estimated_duration_hours", 1.0)
                    if not isinstance(duration_hours, (int, float)) or duration_hours <= 0:
                        duration_hours = 1.0

                    # Use the imported utility function
                    requested_start_dt_utc = parse_datetime_from_details(req_date_str, req_time_str, service_desc)

                    if requested_start_dt_utc:
                        requested_end_dt_utc = requested_start_dt_utc + timedelta(hours=duration_hours)
                        logger.info(f"Calculated UTC event window for UID {email_uid}: START {requested_start_dt_utc.isoformat()}, END {requested_end_dt_utc.isoformat()}")

                        # For checking availability, it's often better to check a wider window on the specific day
                        # Convert UTC start time to business timezone to determine the local day
                        try:
                            business_tz = pytz.timezone("America/New_York") # Should be from config
                            local_requested_start_day = requested_start_dt_utc.astimezone(business_tz).date()
                        except pytz.exceptions.UnknownTimeZoneError:
                            logger.error("Business timezone for availability check is unknown. Using UTC date.")
                            local_requested_start_day = requested_start_dt_utc.date()
                        
                        # Availability window: Start of the local day in UTC, to end of the local day in UTC
                        check_availability_start_utc = datetime(local_requested_start_day.year, local_requested_start_day.month, local_requested_start_day.day, tzinfo=business_tz).astimezone(pytz.utc)
                        check_availability_end_utc = (check_availability_start_utc.astimezone(business_tz) + timedelta(days=1)).astimezone(pytz.utc)

                        logger.info(f"Checking calendar availability for '{service_desc}' for UID {email_uid} between {check_availability_start_utc.isoformat()} and {check_availability_end_utc.isoformat()} (local day in UTC)")
                        busy_slots = await self.get_calendar_availability(check_availability_start_utc, check_availability_end_utc)
                        
                        is_slot_free = True
                        if busy_slots is not None:
                            for busy_slot in busy_slots:
                                busy_start_utc = dateutil.parser.isoparse(busy_slot['start'])
                                busy_end_utc = dateutil.parser.isoparse(busy_slot['end'])
                                if max(requested_start_dt_utc, busy_start_utc) < min(requested_end_dt_utc, busy_end_utc):
                                    is_slot_free = False
                                    logger.warning(f"Requested slot for UID {email_uid} ({requested_start_dt_utc} - {requested_end_dt_utc}) conflicts with busy slot: {busy_start_utc} - {busy_end_utc}")
                                    break
                        else:
                            logger.warning(f"Could not determine availability for UID {email_uid} (get_availability returned None). Will ask user for preferences.")
                            is_slot_free = False

                        if is_slot_free:
                            event_summary = f"{service_desc} - {email_from}"
                            attendees_list = [email_from, self.monitoring_email_address]
                            created_event = await self.create_calendar_event(summary=event_summary, start_datetime=requested_start_dt_utc, end_datetime=requested_end_dt_utc, attendees=attendees_list)
                            if created_event:
                                local_start_time_str = requested_start_dt_utc.astimezone(business_tz).strftime('%A, %B %d, %Y at %I:%M %p %Z')
                                generated_reply_body = f"Great news! I've successfully scheduled your appointment for '{service_desc}' on {local_start_time_str}. You should receive a calendar invitation shortly. We look forward to helping you!"
                                logger.info(f"Successfully created calendar event for UID {email_uid}. ID: {created_event.get('id')}")
                            else:
                                local_start_time_str = requested_start_dt_utc.astimezone(business_tz).strftime('%A, %B %d, %Y at %I:%M %p %Z')
                                generated_reply_body = f"I found an available slot for '{service_desc}' on {local_start_time_str}, but I ran into an issue booking it. Please call us at {self.response_engine.phone} to finalize, or suggest another time."
                                logger.error(f"Failed to create calendar event for UID {email_uid} even though slot seemed free.")
                        else: # Slot not free or availability unknown
                             local_start_time_str = requested_start_dt_utc.astimezone(business_tz).strftime('%A, %B %d, %Y at %I:%M %p %Z')
                             logger.info(f"Slot not available or availability unknown for UID {email_uid} for {service_desc} at {local_start_time_str}.")
                             prompt_context = f"The customer (email UID {email_uid}, from {email_from}) requested an appointment for '{service_desc}' around {req_date_str} {req_time_str} (parsed as {local_start_time_str}). This time slot is NOT available or availability could not be confirmed. Politely inform the customer, ask for alternative preferred times/days, and mention Matt can also check the schedule. Our business hours are {self.response_engine.business_hours}. Offer phone call {self.response_engine.phone}."
                             generated_reply_body = await self.llm_client.generate_text_async(f"{self.llm_client.system_prompt}\\n\\nRespond to the following situation: {prompt_context}")
                    else: # Could not parse date/time from extracted details
                        logger.warning(f"Could not parse date/time from extracted details for UID {email_uid}: {extracted_details}. Asking for clarification.")
                        prompt_context = f"The customer (email UID {email_uid}, from {email_from}) asked to schedule an appointment for '{extracted_details.get('service_description', 'a service')}', but the date/time was unclear. Politely ask them to clarify their preferred date and time (e.g., 'next Tuesday morning', 'July 15th around 2 PM'). Our business hours are {self.response_engine.business_hours}. Offer phone call {self.response_engine.phone}."
                        generated_reply_body = await self.llm_client.generate_text_async(f"{self.llm_client.system_prompt}\\n\\nRespond to the following situation: {prompt_context}")
                else: # Could not extract details at all
                    logger.warning(f"Could not extract any appointment details for UID {email_uid}. Asking for more info.")
                    prompt_context = f"The customer (email UID {email_uid}, from {email_from}) seems to be asking about scheduling an appointment, but I couldn't quite understand the details. Politely ask for: what service they need, preferred date/time, and the service address. Our business hours are {self.response_engine.business_hours}. Offer phone call {self.response_engine.phone}."
                    generated_reply_body = await self.llm_client.generate_text_async(f"{self.llm_client.system_prompt}\\n\\nRespond to the following situation: {prompt_context}")
        
        elif intent == "quote_request" or intent == "general_inquiry" or intent == "emergency_inquiry":
            logger.info(f"Handling intent '{intent}' with standard LLM response generation for UID {email_uid}.")
            llm_reply, email_classif = await self.response_engine.generate_response_async(email_from, email_subject, email_content_for_processing)
            generated_reply_body = llm_reply
        else: # Unknown intent, or fallback
            logger.warning(f"Unknown intent '{intent}' or fallback for UID {email_uid}. Generating a generic response.")
            prompt_context = f"Customer email from {email_from}, Subject: {email_subject}. Body: {email_content_for_processing}. Respond politely and professionally, ask for clarification if needed, or state that Matt will review and get back to them. Provide phone number {self.response_engine.phone}."
            generated_reply_body = await self.llm_client.generate_text_async(f"{self.llm_client.system_prompt}\\n\\nRespond to the following situation: {prompt_context}")

        final_reply_subject = f"{reply_subject_prefix}{email_subject}"
        if reply_to_address:
            logger.info(f"Sending final reply via {self.secretary_email_address} to {reply_to_address} for UID {email_uid}. Subject: {final_reply_subject[:50]}...")
            send_success = self.sending_email_client.send_email(to=reply_to_address, subject=final_reply_subject, body=generated_reply_body)
            if send_success:
                logger.info(f"Successfully sent final reply to {reply_to_address} for UID {email_uid}.")
            else:
                logger.error(f"Failed to send final reply to {reply_to_address} for UID {email_uid}. Notifying admin.")
                # Admin notification logic here if needed, similar to check_and_process_incoming_tasks
        else:
            logger.warning(f"No reply-to address determined for UID {email_uid}. Cannot send reply.")

        logger.info(f"Finished processing single email UID {email_uid}.")

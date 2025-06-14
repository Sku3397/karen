# Testing Karen AI Assistant

This document outlines the testing strategy and procedures for the Karen AI Handyman Secretary Assistant.

## 1. Overview

Testing focuses on the core backend functionality: email processing, LLM interaction, Celery task execution, instruction handling, and Google Calendar integration.

## 2. Environment Setup for Testing

- **Python Virtual Environment:**
  Ensure you have a Python virtual environment set up and activated as described in the main `README.md`.
  ```powershell
  # From the project root (expected to be named 'karen/')
  python -m venv .venv
  .\\.venv\\Scripts\\Activate.ps1 # On Windows
  # source .venv/bin/activate    # On macOS/Linux
  pip install -r src/requirements.txt
  pip install pytest # If not already in requirements
  ```
- **`.env` Configuration for Testing:**
  - **Using Mock Services:** For most tests, especially unit and some integration tests, you can use mock services to avoid live API calls and associated costs/side-effects.
    ```env
    USE_MOCK_EMAIL_CLIENT=True
    # USE_MOCK_CALENDAR_CLIENT=True # (If/when a mock calendar client is implemented)
    ```
    Ensure `MockEmailClient` in `src/mock_email_client.py` (and potentially a future `MockCalendarClient`) adequately simulates behaviors of live clients.
  - **Live Testing (Use with Caution):** For end-to-end integration tests with live Gmail, Gemini, and Google Calendar APIs:
    ```env
    USE_MOCK_EMAIL_CLIENT=False
    # USE_MOCK_CALENDAR_CLIENT=False
    ```
    Ensure `credentials.json`, valid `gmail_token_karen.json`, `gmail_token_monitor.json`, `GOOGLE_APP_CREDENTIALS_PATH` (pointing to `credentials.json`), `CALENDAR_ID`, and `GEMINI_API_KEY` are correctly configured in `.env` and the project root as per `README.md`.
- **Redis:** Ensure your Redis server (specified in `CELERY_BROKER_URL`) is running.
- **Network Access:** For live tests, ensure your environment has outbound internet access to Google APIs (Gmail, Gemini, Calendar) and that no firewalls are blocking these connections or the Redis port.

## 3. Running Unit Tests

The project may contain unit tests for individual modules and functions. `pytest` is the preferred test runner.
- **Location:** Python unit tests are typically located in the `tests/` directory (e.g., `tests/unit/test_email_client.py`, `tests/integration/test_communication_agent.py`).
- **Execution:**
  Use `pytest` to discover and run tests from the project root (`karen/`):
  ```powershell
  pytest
  ```
  Or to run specific test files or tests:
  ```powershell
  pytest tests/unit/test_datetime_utils.py
  pytest tests/integration/test_communication_agent.py::TestCommunicationAgent::test_process_customer_email
  ```
- **Utility Test Scripts:** Several scripts in the `scripts/` directory can also be used for manual testing of specific components:
    - `scripts/test_calendar_client.py`
    - `scripts/test_datetime_parser.py`
    - `scripts/temp_send_test_email.py`
    - `scripts/temp_fetch_last_received_email_by_karen.py`

## 4. Running Integration Tests / End-to-End Scenarios

These tests verify the interaction between different components of the system. Ensure Celery Worker and Beat are running using the commands from `README.md` (e.g., `.venv/Scripts/python.exe -m celery -A src.celery_app:celery_app worker ... >> celery_worker_debug_logs_new.txt 2>&1` and beat equivalent) before starting these scenarios.

### Scenario 1: Incoming Customer Email Processing (Standard Inquiry)

**Objective:** Verify that a standard customer inquiry email sent to `MONITORED_EMAIL_ACCOUNT` (`hello@757handy.com`) is correctly processed, an LLM reply is generated and sent, and the email is marked.

**Steps:**
1.  **Configure:**
    - Set `USE_MOCK_EMAIL_CLIENT=False` in `.env` for a full live test.
    - Ensure Celery Worker and Beat are running (logs going to `celery_worker_debug_logs_new.txt` and `celery_beat_logs_new.txt`).
2.  **Action:** Send a test email *to* `hello@757handy.com` from an external email account.
    - Subject: e.g., "Quote for kitchen backsplash"
    - Body: e.g., "Hi, I'd like to get a quote for a new kitchen backsplash. My phone number is 555-123-4567."
3.  **Verification:**
    - **Celery Logs:**
        - Monitor `celery_beat_logs_new.txt`: Ensure `check-secretary-emails-every-1-minute` (task `check_emails_task`) is being scheduled.
        - Monitor `celery_worker_debug_logs_new.txt`:
            - Look for the task execution for `check_emails_task`.
            - Confirm receipt of the email from `hello@757handy.com`.
            - Check for logs indicating LLM interaction (`HandymanResponseEngine`, `LLMClient`).
            - Confirm a reply is logged as being sent from `karensecretaryai@gmail.com`.
            - Confirm the email in `hello@757handy.com` is marked with the `Karen_Processed` label.
    - **Email Accounts:**
        - Check the inbox of the original sender: A reply from `karensecretaryai@gmail.com` should arrive.
        - Check `hello@757handy.com`: The test email should now have the "Karen_Processed" label and be marked as read.
        - Check `ADMIN_EMAIL_ADDRESS`: A notification email regarding the processed email should arrive.
    - **`llm_system_prompt.txt`:** Should remain unchanged.

### Scenario 2: System Prompt Update Instruction

**Objective:** Verify that an "UPDATE PROMPT" email sent to `SECRETARY_EMAIL_ADDRESS` (`karensecretaryai@gmail.com`) correctly updates `src/llm_system_prompt.txt`.

**Steps:**
1.  **Configure:**
    - `USE_MOCK_EMAIL_CLIENT=False` in `.env`.
    - Celery Worker and Beat running.
2.  **Action:** Send an email *to* `karensecretaryai@gmail.com` (can be from `hello@757handy.com` or external).
    - Subject: `  UPDATE PROMPT   ` (Leading/trailing spaces are handled; matching is case-insensitive for the core phrase "UPDATE PROMPT").
    - Body: The new desired system prompt content. E.g., "You are an exceptionally helpful and cheerful assistant."
3.  **Verification:**
    - **Celery Logs:**
        - Monitor `celery_beat_logs_new.txt`: Ensure `check-instruction-emails-every-2-minutes` (task `check_instruction_emails_task`) is scheduled.
        - Monitor `celery_worker_debug_logs_new.txt`:
            - Look for the task execution for `check_instruction_emails_task`.
            - Confirm receipt of the "UPDATE PROMPT" email.
            - Log messages indicating `llm_system_prompt.txt` is being updated.
            - Log message indicating the `LLMClient` is reloading the prompt.
            - Confirm the "UPDATE PROMPT" email is marked with `Karen_Processed`.
    - **File System:**
        - Check `src/llm_system_prompt.txt`. Content should match the email body.
    - **Email Accounts:**
        - Check `ADMIN_EMAIL_ADDRESS`: A confirmation email about the prompt update (sent from `hello@757handy.com`) should arrive.
        - Check `karensecretaryai@gmail.com`: The "UPDATE PROMPT" email should have `Karen_Processed` label and be marked as read.

### Scenario 3: Appointment Request via Email (Calendar Integration)

**Objective:** Verify that an email requesting an appointment sent to `MONITORED_EMAIL_ACCOUNT` triggers calendar interaction.

**Steps:**
1.  **Configure:**
    - `USE_MOCK_EMAIL_CLIENT=False` in `.env`.
    - Ensure `GOOGLE_CALENDAR_TOKEN_PATH` and `CALENDAR_ID` are correctly set in `.env`.
    - Celery Worker and Beat running.
    - (Optional) Have the Google Calendar for `hello@757handy.com` open to observe changes.
2.  **Action:** Send a test email *to* `hello@757handy.com` from an external account.
    - Subject: "Need to schedule fence repair"
    - Body: "Hi Karen, I'd like to schedule a time for someone to look at my fence. Is next Tuesday morning available? Or perhaps Wednesday afternoon? My number is 555-987-6543."
3.  **Verification:**
    - **Celery Logs (`celery_worker_debug_logs_new.txt`):**
        - Confirm `check_emails_task` processes the email.
        - Logs from `HandymanResponseEngine` indicating "appointment_request" intent.
        - Logs showing extracted details (e.g., proposed times like "next Tuesday morning").
        - Logs from `CalendarClient` attempting to check availability for the parsed dates/times.
        - Logs indicating an attempt to create a calendar event if availability is found or a reply suggesting alternatives if not (depending on implemented logic in `HandymanResponseEngine` and `CalendarClient`).
    - **Email Accounts:**
        - Check sender's inbox for a reply from Karen. The reply content should reflect the calendar interaction (e.g., confirming an appointment, suggesting times, or asking for clarification).
        - Check `ADMIN_EMAIL_ADDRESS` for a notification.
    - **Google Calendar (for `hello@757handy.com`):**
        - If the logic is implemented to create events, a new event corresponding to the request should appear on the calendar.

## 5. Troubleshooting Tests

- **Tasks not running:**
    - Verify Redis server is running and accessible (check connection, port 6379).
    - Check `celery_beat_logs_new.txt`: Are tasks being scheduled (e.g., "Scheduler: Sending due task...")?
    - Check `celery_worker_debug_logs_new.txt`:
        - Is the worker connected to the broker (Redis)?
        - Are there any errors during worker startup or task reception (e.g., `ModuleNotFoundError`)?
        - Is the task ID logged by Beat appearing in the worker logs?
    - Ensure `--pool=solo` is used for the worker command on Windows if issues persist with other pools.
    - Check for `celerybeat.pid` issues if Beat fails to start; delete it if necessary (see `README.md` for stop commands that include this).
- **Emails not being sent/received (Live Mode):**
    - Double-check `.env` variables: `SECRETARY_EMAIL_ADDRESS`, `MONITORED_EMAIL_ACCOUNT`, `ADMIN_EMAIL_ADDRESS`, `SECRETARY_TOKEN_PATH`, `MONITORED_EMAIL_TOKEN_PATH`, `GOOGLE_APP_CREDENTIALS_PATH`.
    - Ensure `credentials.json` and the correct `gmail_token_*.json` files are present and valid. Re-run `setup_*.py` scripts if tokens are suspected to be expired/invalid.
    - Verify OAuth Consent Screen in GCP is set to "Publishing status: Testing" and your test email accounts are listed as "Test users".
    - Check Gmail API quotas in GCP.
- **Calendar API Errors:**
    - Ensure `GOOGLE_CALENDAR_TOKEN_PATH` (usually same as `MONITORED_EMAIL_TOKEN_PATH`) is valid and has calendar scopes.
    - Verify `CALENDAR_ID` in `.env` is correct (e.g., `primary` or a specific calendar's email address).
    - Check Google Calendar API is enabled in GCP and quotas.
    - Look for specific error messages from `CalendarClient` in `celery_worker_debug_logs_new.txt`.
- **LLM not responding as expected:**
    - Verify `GEMINI_API_KEY` in `.env`.
    - Check `src/llm_system_prompt.txt` content.
    - Look for API error messages from `LLMClient` in `celery_worker_debug_logs_new.txt` (e.g., 429 Too Many Requests, authentication errors).
- **Labels not applied:**
    - Ensure the `Karen_Processed` label exists in both Gmail accounts. The system attempts to find it by name; it does not create it.
    - Check worker logs for errors from `EmailClient._get_label_id()` or `EmailClient.mark_email_as_processed()`.

## 6. Test Data Management
- For live tests, be mindful that test emails will be processed and will reside in the test Gmail accounts. Calendar events may also be created.
- Periodically clean up test emails, the `Karen_Processed` label, and test calendar events, or use dedicated test accounts that can be easily reset.

---

This guide provides a starting point for testing the Karen AI assistant. Adapt and expand upon these scenarios as the application evolves. 
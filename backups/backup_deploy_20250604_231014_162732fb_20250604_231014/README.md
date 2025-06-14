# Karen AI Handyman Secretary Assistant

## Overview

Karen is an AI-powered secretary assistant designed for handyman businesses. It automates email communication by monitoring an inbox for customer inquiries, using a Large Language Model (LLM) to understand requests (including scheduling appointments by checking Google Calendar availability), generate appropriate responses, and then sending those responses to customers. It also provides notifications to the business admin.

**Core Functionality:**
- Monitors a specified Gmail account (`hello@757handy.com` by default) for incoming customer emails.
- Uses an LLM (Google Gemini) to analyze email content, classify inquiries (e.g., quote request, service request, appointment scheduling, emergency), and generate human-like responses.
- Integrates with Google Calendar for the monitored email account to check availability and create appointments.
- Sends replies to customers from a dedicated Gmail account (`karensecretaryai@gmail.com` by default).
- Notifies the admin (`sku3397@icloud.com` by default) about processed emails and any errors encountered.
- Utilizes Celery for asynchronous task processing (email fetching, LLM interaction, calendar operations, email sending) and Celery Beat for scheduling regular email checks.
- Built with Python, FastAPI for potential API endpoints (though current core logic is Celery-driven), Google Cloud services (Gmail API, Gemini API, Calendar API), and `dateutil` for robust datetime parsing.

## Project Structure

The project root directory is expected to be named `karen`.

```
karen/
├── .env                  # Environment variables (API keys, email accounts, etc.) - CRITICAL, MUST BE CONFIGURED
├── .gitignore            # Specifies intentionally untracked files that Git should ignore
├── credentials.json      # Google OAuth Client ID and Secret (for all Google services)
├── gmail_token_karen.json # OAuth token for the sending email account (karensecretaryai@gmail.com)
├── gmail_token_monitor.json # OAuth token for the monitoring email account (hello@757handy.com)
├── manage.py             # Django manage.py (primarily for Celery Beat with Django-Celery-Beat)
├── pytest.ini            # Configuration for pytest
├── README.md             # This file
├── setup_karen_oauth.py  # Script to generate/refresh gmail_token_karen.json
├── setup_monitor_oauth.py # Script to generate/refresh gmail_token_monitor.json
├── src/
│   ├── __init__.py
│   ├── calendar_client.py # Client for interacting with Google Calendar API
│   ├── celery_app.py     # Celery application setup, task definitions, and scheduling
│   ├── communication_agent/ # Contains the CommunicationAgent and its handlers
│   │   ├── __init__.py
│   │   ├── agent.py      # Core logic for CommunicationAgent (email processing, LLM interaction)
│   │   ├── sms_handler.py # Placeholder/basic SMS handling
│   │   └── voice_transcription_handler.py # Placeholder/basic voice transcription
│   ├── config/
│   │   └── karen-437100-firebase-adminsdk-fbsvc-e1f59fc29d.json # Example service account key (if Firebase is used)
│   ├── config.py         # General application configuration settings (email accounts, API paths)
│   ├── datetime_utils.py # Utilities for parsing and handling datetime strings
│   ├── django_settings.py # Minimal Django settings for Celery Beat
│   ├── email_client.py   # Handles Gmail API interactions (sending, fetching, marking emails)
│   ├── handyman_response_engine.py # Logic for classifying emails, crafting LLM prompts, and calendar interaction
│   ├── llm_client.py     # Client for interacting with the Gemini LLM API
│   ├── llm_system_prompt.txt # Contains the base system prompt for the LLM
│   ├── main.py           # Main application entry point (can start FastAPI, but Celery usually run separately)
│   ├── mock_email_client.py # Mock EmailClient for testing without live Gmail API calls
│   ├── requirements.txt  # Python package dependencies
│   └── schemas/          # Pydantic schemas for data validation (e.g., tasks)
│       ├── __init__.py
│       └── task.py
└── tests/                  # Unit and integration tests (currently minimal)
    └── ...

Logs (typically redirected from Celery commands, ensure these are in .gitignore if not committed):
- celery_worker_debug_logs_new.txt # Detailed logs from the Celery worker process
- celery_beat_logs_new.txt         # Logs from the Celery Beat scheduler process
- celerybeat-schedule.sqlite3     # Database for Django-Celery-Beat (stores schedule state)

Other logs that might be generated depending on usage:
- fastapi_logs.txt                # Logs from the FastAPI application (if run and configured)
- main_app_console_output.log     # Console output from `python -m src.main` if redirected
```

## Setup and Configuration

### 1. Prerequisites
- Python 3.9+
- pip (Python package installer)
- Redis (for Celery broker and result backend) - Ensure Redis server is running.
- Access to a Google Cloud Platform (GCP) project.
- Docker (optional, but helpful for managing Redis, especially if you don't have a system-wide Redis installation).

### 2. Clone the Repository
If the repository is not already named `karen`, it's recommended to clone it into a directory named `karen` or rename the project's root directory to `karen` post-cloning to align with internal path expectations and user rules.
```bash
git clone <repository_url> karen
cd karen
# OR if already cloned as AI_Handyman_Secretary_Assistant, consider renaming the folder to 'karen'
```

### 3. Set up Virtual Environment
It's highly recommended to use a virtual environment:
```bash
python -m venv .venv
# On Windows
.venv\\Scripts\\activate
# On macOS/Linux
source .venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r src/requirements.txt
```
This will install all necessary packages, including `google-api-python-client`, `google-auth-oauthlib`, `celery`, `redis`, `django-celery-beat`, `google-generativeai`, `python-dateutil`, etc.

### 5. Google Cloud Project Setup & Credentials

#### a. Enable APIs:
In your GCP console, ensure the following APIs are enabled for your project:
- Gmail API
- Vertex AI API (or the specific API for Gemini, e.g., Generative Language API)
- Google Calendar API
- (Optional, if used) Google Cloud Speech-to-Text API
- (Optional, if used) Firebase related APIs (e.g., Firestore API)

#### b. Create OAuth 2.0 Client ID Credentials:
- Go to "APIs & Services" > "Credentials".
- Click "Create Credentials" > "OAuth client ID".
- Select "Desktop app" for the application type.
- Name it (e.g., "Karen Gmail Desktop Client").
- Download the JSON file. **Rename this file to `credentials.json` and place it in the project root directory (`karen/`).** This file is used by OAuth setup scripts for Gmail and Calendar.

#### c. Firebase Service Account (Currently Optional/Disabled):
- The project includes references to Firebase/Firestore (e.g., for `TaskManagerAgent`). However, this integration is **currently not fully operational** due to missing dependencies (`firestore_models`) that were commented out to resolve startup issues.
- If you intend to re-enable or use Firebase/Firestore:
    - Ensure `google-cloud-firestore` is added to `src/requirements.txt` and installed.
    - Create a service account key: Go to "Project settings" > "Service accounts" in the Firebase console or "IAM & Admin" > "Service Accounts" in GCP. Create a new service account or use an existing one. Generate a new JSON private key and download it.
    - Place this key in `src/config/` (e.g., `src/config/your-firebase-service-account-key.json`).
    - Update `FIREBASE_SERVICE_ACCOUNT_KEY_PATH` and `GOOGLE_APPLICATION_CREDENTIALS` in the `.env` file.
    - Uncomment the relevant code in `src/task_manager.py` and other related files.

### 6. Configure Environment Variables (`.env` file)
Create a `.env` file in the project root (`karen/`) by copying `.env.example` or creating it from scratch.
Fill in the following critical values:

```env
# Twilio Credentials (if SMS functionality is fully implemented and used)
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token

# Google Cloud Credentials
GOOGLE_PROJECT_ID=your_gcp_project_id # e.g., karen-437100
# Path to the OAuth 2.0 Client ID JSON file (downloaded from GCP)
GOOGLE_APP_CREDENTIALS_PATH=credentials.json # Path relative to project root

# Firebase/Firestore (Update path if different from default, currently optional)
FIREBASE_SERVICE_ACCOUNT_KEY_PATH="src/config/your-firebase-service-account-key.json"
GOOGLE_APPLICATION_CREDENTIALS="src/config/your-firebase-service-account-key.json" # Often the same for server-side Google API auth

# Email Accounts Configuration
SECRETARY_EMAIL_ADDRESS=karensecretaryai@gmail.com  # Account Karen sends FROM
SECRETARY_TOKEN_PATH=gmail_token_karen.json       # Token for SECRETARY_EMAIL_ADDRESS
MONITORED_EMAIL_ACCOUNT=hello@757handy.com        # Account Karen monitors FOR
MONITORED_EMAIL_TOKEN_PATH=gmail_token_monitor.json # Token for MONITORED_EMAIL_ACCOUNT
ADMIN_EMAIL_ADDRESS=your_admin_email@example.com  # Where admin notifications are sent

# Google Calendar Configuration (uses the same OAuth token as MONITORED_EMAIL_ACCOUNT by default)
GOOGLE_CALENDAR_TOKEN_PATH=gmail_token_monitor.json # Token for calendar access (usually same as monitored email)
CALENDAR_ID=primary                                 # Calendar ID to use (e.g., 'primary' or a specific calendar ID)

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Gemini API Key
GEMINI_API_KEY=your_gemini_api_key # Get this from Google AI Studio or GCP

# Django Settings for Celery Beat
DJANGO_SETTINGS_MODULE="src.django_settings"

# Mock Email Client Setting (False for live operation)
USE_MOCK_EMAIL_CLIENT=False

# Timezone for datetime parsing and calendar events (IANA format)
DEFAULT_TIMEZONE=America/New_York
```
**Ensure `.env`, `credentials.json`, and `*.json` token files (like `gmail_token_karen.json`, `gmail_token_monitor.json`) are added to `.gitignore` to prevent committing secrets.**

### 7. Generate OAuth Tokens for Email & Calendar Accounts

You need to authorize Karen to access the two Gmail accounts and the Google Calendar associated with the monitoring account. Run the following scripts from the project root. These scripts will open a web browser for you to log in and grant permissions. The necessary scopes for Gmail (read, send, modify) and Calendar (read, write) are included in the scripts.

#### a. For the Sending Account (`karensecretaryai@gmail.com` - for sending emails):
```bash
python setup_karen_oauth.py
```
- Log in as `karensecretaryai@gmail.com` when prompted in the browser.
- This will create/update `gmail_token_karen.json` in the project root.

#### b. For the Monitoring Account (`hello@757handy.com` - for monitoring emails AND calendar access):
```bash
python setup_monitor_oauth.py
```
- Log in as `hello@757handy.com` when prompted in the browser.
- This will create/update `gmail_token_monitor.json` in the project root. This token will be used for both reading emails from this account and accessing its Google Calendar.

**Important OAuth Consent Screen Note:**
For these OAuth flows to work, especially when initially setting up or if tokens expire (approx. 7 days for apps in "Testing" mode), your Google Cloud Project's OAuth consent screen should be configured as follows:
- **Publishing Status:** Testing
- **User Type:** External
- Add the email addresses `karensecretaryai@gmail.com` and `hello@757handy.com` (and any other accounts you might test with) as **Test users** under the OAuth consent screen configuration in your GCP project. This allows these specific accounts to grant permissions even though the app is not fully published/verified by Google.
- Ensure the following scopes are enabled for your OAuth Client ID in GCP:
    - `https://www.googleapis.com/auth/gmail.readonly`
    - `https://www.googleapis.com/auth/gmail.send`
    - `https://www.googleapis.com/auth/gmail.modify`
    - `https://www.googleapis.com/auth/calendar` (or `https://www.googleapis.com/auth/calendar.events` if only event access is needed)

### 8. Database Setup (for Celery Beat)
Django Celery Beat uses a database to store its schedule. A SQLite database (`celerybeat-schedule.sqlite3`) will be created automatically in the project root when Celery Beat starts. If you prefer a different database, you'll need to configure Django settings in `src/django_settings.py` and install the appropriate database drivers. For SQLite, no further action is usually needed.

## Running the Application

1.  **Ensure Redis is running.**
    If using Docker: `docker run -d --name karen-redis -p 6379:6379 redis` (if a container named `karen-redis` doesn't already exist, or ensure your existing Redis container is started).
2.  **Activate your virtual environment:**
    ```bash
    # On Windows
    .venv\\Scripts\\activate
    # On macOS/Linux
    source .venv/bin/activate
    ```
3.  **Start Celery Services (from the project root `karen/`):**
    It's recommended to run Celery Beat and Worker as separate, backgrounded processes with logs redirected.

    **a. Start Celery Beat (Scheduler):**
    ```powershell
    # On Windows (PowerShell)
    Start-Process .venv\\Scripts\\python.exe -ArgumentList "-m celery -A src.celery_app:celery_app beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler" -RedirectStandardOutput celery_beat_logs_new.txt -RedirectStandardError celery_beat_logs_new.txt -NoNewWindow
    # Or, for simpler redirection if Start-Process is complex:
    # .venv/Scripts/python.exe -m celery -A src.celery_app:celery_app beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler >> celery_beat_logs_new.txt 2>&1 &
    ```
    ```bash
    # On macOS/Linux
    .venv/bin/python -m celery -A src.celery_app:celery_app beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler >> celery_beat_logs_new.txt 2>&1 &
    ```
    This will create `celerybeat-schedule.sqlite3` if it doesn't exist. Check `celery_beat_logs_new.txt` for scheduler activity.
    Make sure to delete any old `celerybeat.pid` file if you encounter "Pidfile already exists" errors: `Remove-Item -Path celerybeat.pid -Force -ErrorAction SilentlyContinue` (PowerShell) or `rm -f celerybeat.pid` (Linux/macOS).

    **b. Start Celery Worker:**
    ```powershell
    # On Windows (PowerShell)
    Start-Process .venv\\Scripts\\python.exe -ArgumentList "-m celery -A src.celery_app:celery_app worker -l DEBUG --pool=solo" -RedirectStandardOutput celery_worker_debug_logs_new.txt -RedirectStandardError celery_worker_debug_logs_new.txt -NoNewWindow
    # Or, for simpler redirection:
    # .venv/Scripts/python.exe -m celery -A src.celery_app:celery_app worker -l DEBUG --pool=solo >> celery_worker_debug_logs_new.txt 2>&1 &
    ```
    ```bash
    # On macOS/Linux
    .venv/bin/python -m celery -A src.celery_app:celery_app worker -l DEBUG --pool=solo >> celery_worker_debug_logs_new.txt 2>&1 &
    ```
    Check `celery_worker_debug_logs_new.txt` for task processing. The `--pool=solo` argument is used for simplicity during development and debugging on Windows; for production on Linux/macOS, you might consider other pool options like `prefork` (default) or `gevent`.

4.  **(Optional) Start FastAPI Application:**
    If you need to access any API endpoints defined in `src/main.py`:
    ```bash
    python -m src.main
    ```
    This will typically run the FastAPI server on `http://localhost:8002`. However, the core email processing loop relies on Celery and does not require the FastAPI server to be running explicitly unless specific API endpoints are being used for control or status.

## Stopping the Application

To stop the Celery services:
-   **Find Process IDs (PIDs):**
    ```powershell
    # On Windows (PowerShell) - Find Python processes running Celery
    Get-Process -Name python | Where-Object {$_.Path -like '*celery*'} | Select-Object Id, Path, CommandLine
    ```
    ```bash
    # On macOS/Linux
    ps aux | grep 'celery -A src.celery_app'
    ```
-   **Stop the Processes:**
    Use the PIDs found to stop the Celery Beat and Worker processes.
    ```powershell
    # On Windows (PowerShell)
    Stop-Process -Id <PID_FOR_BEAT> -Force
    Stop-Process -Id <PID_FOR_WORKER> -Force
    # Or a more comprehensive stop:
    Get-Process -Name python | Stop-Process -Force -ErrorAction SilentlyContinue; Get-Process -Name celery | Stop-Process -Force -ErrorAction SilentlyContinue; Remove-Item -Path celerybeat.pid -Force -ErrorAction SilentlyContinue
    ```
    ```bash
    # On macOS/Linux
    kill <PID_FOR_BEAT>
    kill <PID_FOR_WORKER>
    # Or, to kill all celery workers/beat for this app (use with caution):
    # pkill -f 'celery -A src.celery_app'
    # rm -f celerybeat.pid
    ```

## Key Scripts & Utilities

-   **`scripts/temp_send_test_email.py`**: Sends a predefined test email from `SECRETARY_EMAIL_ADDRESS` to `MONITORED_EMAIL_ACCOUNT` to trigger the processing flow. Useful for end-to-end testing.
-   **`scripts/temp_fetch_last_received_email_by_karen.py`**: Fetches and displays the last email received by `SECRETARY_EMAIL_ADDRESS`. Useful for verifying replies sent by Karen. (Note: This script may have limitations in fetching the full email body due to `EmailClient` behavior).
-   **`scripts/test_calendar_client.py`**: Tests the Google Calendar integration.
-   **`scripts/test_datetime_parser.py`**: Tests the datetime parsing utility.

## Known Issues & Limitations
-   **Email Body Fetching in `temp_fetch_last_received_email_by_karen.py`**: The utility script for fetching Karen's replies might not always display the full email body content due to current limitations in how `EmailClient.fetch_emails` parses/retrieves multipart emails. However, the LLM processing and actual email sending work correctly with full content.
-   **`dateutil` relative date parsing ("today", "tomorrow"):** In some environments, `dateutil.parser.parse` might have issues with "today" and "tomorrow" even with a default date. This is a known behavior being monitored.
-   **Firebase/Firestore Integration**: Currently disabled/commented out due to `ModuleNotFoundError`. Requires manual steps to re-enable (see Setup section).

## Future Enhancements / To-Do
-   Robust error handling and retry mechanisms for external API calls.
-   More comprehensive unit and integration tests.
-   Admin dashboard/UI for monitoring and configuration.
-   Full implementation of SMS and Voice Transcription handlers.
-   Re-evaluate and complete Firebase/Firestore integration if needed.
-   CI/CD pipeline for automated testing and deployment.
-   Containerization with Docker for easier deployment of the entire application stack (including Redis, Celery, FastAPI).
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Backend (Python/FastAPI/Celery)

```bash
# Install dependencies
pip install -r src/requirements.txt

# Run Celery Beat (scheduler)
.venv/bin/python -m celery -A src.celery_app:celery_app beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler

# Run Celery Worker
.venv/bin/python -m celery -A src.celery_app:celery_app worker -l DEBUG --pool=solo

# Run FastAPI server (optional, not required for core email processing)
python -m src.main

# Run unit tests
python -m unittest discover -s tests
python -m pytest  # Alternative with pytest

# Run specific test markers
python -m pytest -m interactive  # Run interactive tests
```

### Frontend (React/Webpack)

```bash
# Install dependencies
npm install

# Start development server (runs on port 8082)
npm start

# Build for production
npm run build

# Run ESLint
npx eslint src/

# Format with Prettier
npx prettier --write "src/**/*.{js,jsx}"
```

### OAuth Setup Commands

```bash
# Setup OAuth for sending email account (karensecretaryai@gmail.com)
python setup_karen_oauth.py

# Setup OAuth for monitored email account (hello@757handy.com)
python setup_monitor_oauth.py

# Setup OAuth for calendar access
python setup_calendar_oauth.py
```

### Redis (Required for Celery)

```bash
# Using Docker
docker run -d --name karen-redis -p 6379:6379 redis

# Check Redis connection
redis-cli ping
```

## High-Level Architecture

### Core Components

1. **Email Processing System (Celery-based)**
   - `src/celery_app.py`: Defines Celery tasks and schedules for email monitoring
   - `src/communication_agent/agent.py`: Core logic for processing emails, LLM interaction, and calendar integration
   - `src/email_client.py`: Gmail API integration for sending/fetching emails
   - `src/handyman_response_engine.py`: Email classification and LLM prompt generation
   - `src/llm_client.py`: Google Gemini API integration for generating responses
   - `src/calendar_client.py`: Google Calendar API integration for appointment scheduling

2. **Multi-Agent System**
   - `src/orchestrator_agent.py`: Coordinates between different agents
   - `src/task_manager_agent.py`: Manages tasks and tracks completion
   - `src/scheduler_agent.py`: Handles appointment scheduling
   - `src/knowledge_base_agent.py`: Manages information retrieval
   - `src/communication_agent.py`: Handles email/SMS/voice communications
   - `src/billing_agent.py`: Manages billing and invoicing

3. **API Layer (FastAPI)**
   - `src/main.py`: Main FastAPI application entry point
   - `src/api/`: API route definitions
   - `src/endpoints/`: Individual endpoint implementations
   - `src/routers/`: Router configurations for different modules

4. **Configuration & Authentication**
   - `src/config.py`: Central configuration management
   - `src/auth/`: JWT authentication, OAuth handlers, RBAC
   - Environment-based configuration via `.env` files
   - OAuth tokens stored as JSON files (gmail_token_*.json)

5. **Frontend (React)**
   - `src/App.jsx`: Main React application
   - `src/components/`: React components for UI
   - `src/api/client.js`: Frontend API client
   - Webpack configuration for bundling

### Key Design Patterns

1. **Asynchronous Task Processing**: Uses Celery for background email processing with Redis as message broker
2. **Agent-Based Architecture**: Each agent has specific responsibilities and can operate independently
3. **OAuth 2.0 Authentication**: For Gmail and Google Calendar access
4. **Environment-Based Configuration**: Different `.env` files for different environments
5. **Mock Clients for Testing**: `MockEmailClient` can be enabled via `USE_MOCK_EMAIL_CLIENT` flag

### Email Processing Flow

1. Celery Beat schedules `check_emails_task` every minute
2. Task fetches unread emails from monitored account (hello@757handy.com)
3. CommunicationAgent processes each email:
   - Classifies intent using HandymanResponseEngine
   - Generates response using LLM (Gemini)
   - Checks calendar availability if appointment requested
   - Sends reply from secretary account (karensecretaryai@gmail.com)
   - Notifies admin of processed emails

### Important Environment Variables

- `SECRETARY_EMAIL_ADDRESS`: Email account for sending replies
- `MONITORED_EMAIL_ACCOUNT`: Email account being monitored
- `ADMIN_EMAIL_ADDRESS`: Admin notification recipient
- `GEMINI_API_KEY`: Google Gemini API key
- `GOOGLE_PROJECT_ID`: GCP project ID
- `CELERY_BROKER_URL`: Redis connection URL
- `USE_MOCK_EMAIL_CLIENT`: Enable mock email client for testing
- `DEFAULT_TIMEZONE`: Timezone for datetime parsing (e.g., America/New_York)

### Testing Approach

- Unit tests: `tests/unit_tests.py`
- Integration tests: `tests/test_*.py` files
- Interactive tests marked with `@pytest.mark.interactive`
- Test scripts in `scripts/` for specific functionality testing
- Mock email client available for testing without live Gmail API

### Database & Storage

- SQLite for Celery Beat schedule storage (`celerybeat-schedule.sqlite3`)
- Firebase/Firestore integration (currently disabled due to missing dependencies)
- Future: PostgreSQL or other databases can be configured in Django settings

### Logging

- Comprehensive logging throughout the application
- Celery worker logs: `celery_worker_debug_logs_new.txt`
- Celery beat logs: `celery_beat_logs_new.txt`
- FastAPI logs: `fastapi_logs.txt`
- Email agent activity: `logs/email_agent_activity.log`

### Code Style

- Python: Follow PEP 8
- JavaScript/React: ESLint configuration in `.eslintrc.json`
- Prettier formatting: `{"semi": false, "singleQuote": true}`
- No trailing semicolons in JS, single quotes preferred
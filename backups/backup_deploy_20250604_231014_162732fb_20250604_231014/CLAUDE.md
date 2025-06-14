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
python -m pytest -m unit         # Run only unit tests
python -m pytest -m email        # Run email functionality tests
python -m pytest -m calendar     # Run calendar functionality tests
python -m pytest -m "not slow"   # Skip slow tests
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

### Docker Development Environment

```bash
# Start all services (Redis, PostgreSQL, API, Worker, Beat, Frontend)
docker-compose up -d

# Start only core services (Redis, API, Worker, Beat)
docker-compose up -d redis karen-api karen-worker karen-beat

# View logs
docker-compose logs -f karen-worker
docker-compose logs -f karen-beat

# Stop all services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

### Autonomous Agent System

```bash
# Launch specific agents
python launch_orchestrator.py      # Main orchestrator
python launch_memory_engineer.py   # Memory system agent
python launch_sms_engineer.py      # SMS implementation agent
python launch_test_engineer.py     # Testing automation agent

# Monitor agent status
python check_archaeologist_status.py

# Run autonomous system (all agents)
python orchestrator_active.py
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

# Using Docker Compose (recommended)
docker-compose up -d redis
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

2. **Autonomous Agent Ecosystem**
   - **Orchestrator**: `orchestrator_active.py` - Master coordinator managing workflow phases and agent health
   - **Archaeologist Agent**: `agents/archaeologist/` - System analysis and architectural pattern discovery
   - **SMS Engineer Agent**: `agents/sms/` - SMS functionality implementation via Twilio
   - **Phone Engineer Agent**: `agents/phone/` - Voice call processing and integration
   - **Memory Engineer Agent**: `agents/memory/` - Cross-medium conversation memory and identity linking
   - **Test Engineer Agent**: `agents/test/` - Quality assurance and automated testing
   - **Communication System**: `autonomous-agents/communication/` - File-based messaging and Redis pub/sub
   - **Task Management**: `agent_task_system.py` - Advanced task queuing with priorities and dependencies

3. **Multi-Agent System (Legacy)**
   - `src/orchestrator_agent.py`: Coordinates between different agents
   - `src/task_manager_agent.py`: Manages tasks and tracks completion
   - `src/scheduler_agent.py`: Handles appointment scheduling
   - `src/knowledge_base_agent.py`: Manages information retrieval
   - `src/communication_agent.py`: Handles email/SMS/voice communications
   - `src/billing_agent.py`: Manages billing and invoicing

4. **API Layer (FastAPI)**
   - `src/main.py`: Main FastAPI application entry point
   - `src/api/`: API route definitions
   - `src/endpoints/`: Individual endpoint implementations
   - `src/routers/`: Router configurations for different modules

5. **Configuration & Authentication**
   - `src/config.py`: Central configuration management
   - `src/auth/`: JWT authentication, OAuth handlers, RBAC
   - Environment-based configuration via `.env` files
   - OAuth tokens stored as JSON files (gmail_token_*.json)

6. **Frontend (React)**
   - `src/App.jsx`: Main React application
   - `src/components/`: React components for UI
   - `src/api/client.js`: Frontend API client
   - Webpack configuration for bundling

7. **Memory & Knowledge Systems**
   - `src/intelligent_memory_system.py`: Cross-medium conversation tracking
   - `autonomous-agents/communication/knowledge-base/`: Shared agent discoveries and patterns
   - `src/memory_embeddings_manager.py`: Vector-based memory storage with ChromaDB
   - `src/personality/`: Personality engine for consistent voice across mediums

### Key Design Patterns

1. **Asynchronous Task Processing**: Uses Celery for background email processing with Redis as message broker
2. **Autonomous Agent Architecture**: Self-coordinating agents with file-based messaging and Redis pub/sub communication
3. **Phase-Based Workflow**: Analysis → Development → Testing → Integration phases managed by orchestrator
4. **Cross-Medium Memory**: Unified conversation tracking across email, SMS, voice with identity linking
5. **OAuth 2.0 Authentication**: For Gmail and Google Calendar access
6. **Environment-Based Configuration**: Different `.env` files for different environments
7. **Mock Clients for Testing**: `MockEmailClient` can be enabled via `USE_MOCK_EMAIL_CLIENT` flag
8. **Fail-Fast Initialization**: Validate all prerequisites at startup with descriptive error messages
9. **Knowledge Base Sharing**: Agents share discoveries via structured JSON files in shared knowledge base

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

**Core System**
- `SECRETARY_EMAIL_ADDRESS`: Email account for sending replies
- `MONITORED_EMAIL_ACCOUNT`: Email account being monitored
- `ADMIN_EMAIL_ADDRESS`: Admin notification recipient
- `GEMINI_API_KEY`: Google Gemini API key
- `GOOGLE_PROJECT_ID`: GCP project ID
- `CELERY_BROKER_URL`: Redis connection URL
- `USE_MOCK_EMAIL_CLIENT`: Enable mock email client for testing
- `DEFAULT_TIMEZONE`: Timezone for datetime parsing (e.g., America/New_York)

**Autonomous Agent System**
- `AGENT_COMMUNICATION_REDIS_URL`: Redis URL for agent pub/sub communication
- `AGENT_STATUS_CHECK_INTERVAL`: Health check interval in seconds (default: 300)
- `EIGENCODE_MONITORING_ENABLED`: Enable Eigencode pattern analysis (default: true)
- `AGENT_TASK_RETENTION_DAYS`: Days to retain completed tasks (default: 30)

**SMS Integration (Twilio)**
- `TWILIO_ACCOUNT_SID`: Twilio account SID
- `TWILIO_AUTH_TOKEN`: Twilio authentication token
- `TWILIO_PHONE_NUMBER`: Twilio phone number for SMS

**Voice Integration**
- `VOICE_WEBHOOK_BASE_URL`: Base URL for voice webhooks
- `ELEVENLABS_API_KEY`: ElevenLabs API key for voice synthesis (optional)

### Testing Approach

**Test Organization**
- Unit tests: `tests/unit_tests.py` and files with `@pytest.mark.unit`
- Integration tests: `tests/test_*.py` files with `@pytest.mark.integration`
- Interactive tests: `@pytest.mark.interactive` (long-running, requires manual interaction)
- Performance tests: `@pytest.mark.performance` for load testing and benchmarks
- Security tests: `@pytest.mark.security` for security feature validation

**Test Markers (from pytest.ini)**
```bash
pytest -m unit           # Fast, isolated unit tests
pytest -m integration    # Tests requiring live services
pytest -m email          # Email functionality tests
pytest -m calendar       # Calendar functionality tests
pytest -m api            # API endpoint tests
pytest -m "not slow"     # Skip tests taking > 5 seconds
pytest -m performance    # Load testing and benchmarks
```

**Test Scripts**
- `scripts/temp_send_test_email.py`: End-to-end email processing test
- `scripts/test_calendar_client.py`: Google Calendar integration test
- `scripts/test_datetime_parser.py`: Date parsing utility test
- Mock email client available via `USE_MOCK_EMAIL_CLIENT=True`

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

### Autonomous Agent Communication Patterns

**Agent Communication Structure**
```python
# Standard agent message format
{
    "from": "orchestrator",
    "to": "memory_engineer", 
    "type": "high_priority_task_assignment",
    "content": {
        "task_assignment": { /* detailed requirements */ },
        "templates_available": [ /* available templates */ ],
        "integration_points": { /* coordination needs */ }
    },
    "timestamp": "2025-06-04T02:21:55.385911"
}
```

**Implementation Patterns (from autonomous-agents/shared-knowledge/karen-implementation-patterns.md)**
- **OAuth Pattern**: Always use PROJECT_ROOT-relative paths, implement refresh with proper error handling
- **Celery Task Pattern**: Use `bind=True`, update status at start/completion, handle errors with admin notification
- **Error Handling**: Specific handling for HttpError, RefreshError, and general exceptions with exc_info=True
- **LLM Integration**: Async context with `asyncio.to_thread()`, fallback responses on failure
- **Agent Communication**: File-based messaging in `autonomous-agents/communication/inbox/` plus Redis pub/sub

**Critical File Patterns**
- Agent inboxes: `autonomous-agents/communication/inbox/{agent_name}/`
- Knowledge sharing: `autonomous-agents/communication/knowledge-base/`
- Status tracking: Agent status files with timestamp validation
- DO NOT MODIFY: Files listed in `autonomous-agents/shared-knowledge/DO-NOT-MODIFY-LIST.md`

### Code Style

- Python: Follow PEP 8
- JavaScript/React: ESLint configuration in `.eslintrc.json`
- Prettier formatting: `{"semi": false, "singleQuote": true}`
- No trailing semicolons in JS, single quotes preferred
- **Autonomous Agents**: Follow patterns in `karen-implementation-patterns.md`
- **Error Handling**: Always use `exc_info=True` for error logs
- **Logging**: Module-level loggers with context (IDs, email addresses)
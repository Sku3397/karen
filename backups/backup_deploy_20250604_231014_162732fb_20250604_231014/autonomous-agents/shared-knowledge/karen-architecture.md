# Karen AI Architecture - Code Archaeology Report

## Email Processing Flow - Complete Journey

### 1. Entry Point: Celery Task Scheduler
```python
# src/celery_app.py:177
@celery_app.task(name='check_emails_task', ignore_result=True)
def check_secretary_emails_task():
    agent = get_communication_agent_instance()
    asyncio.run(agent.check_and_process_incoming_tasks(process_last_n_days=1))
```

**Schedule**: Every 2 minutes via Celery Beat
```python
# src/celery_app.py:347
'check-secretary-emails-every-2-minutes': {
    'task': 'check_emails_task',
    'schedule': crontab(minute='*/2'),
}
```

### 2. Email Fetching: Gmail API Integration
```python
# src/email_client.py:267
def fetch_emails(self, search_criteria: str = 'UNREAD', 
                 last_n_days: Optional[int] = None, 
                 newer_than: Optional[str] = None,
                 max_results: int = 10) -> List[Dict[str, Any]]:
```

**Key Operations**:
- Builds Gmail query: `"UNREAD after:2024/01/01"`
- Uses Gmail API v1 with OAuth2 credentials
- Fetches full message content including multipart MIME
- Returns structured email data with extracted headers and body

### 3. Email Processing: CommunicationAgent
```python
# src/communication_agent/agent.py:167
async def check_and_process_incoming_tasks(self, process_last_n_days: int = 7):
    # Fetches unread emails from monitored account
    emails = self.monitoring_email_client.fetch_emails(
        search_criteria='is:unread',
        last_n_days=process_last_n_days,
        max_results=10
    )
```

**Processing Pipeline**:
1. Filter out self-emails and test emails
2. Generate response using HandymanResponseEngine
3. Extract tasks if present (TASK: prefix)
4. Send reply via secretary account
5. Mark email as processed with label

### 4. Response Generation: HandymanResponseEngine
```python
# src/handyman_response_engine.py:44
def classify_email_type(self, subject: str, body: str) -> Dict[str, Any]:
    # Classifications:
    # - is_emergency (flood, burst pipe, etc.)
    # - services_mentioned (plumbing, electrical, etc.)
    # - is_quote_request
    # - is_appointment_request
```

**LLM Integration**:
```python
# src/handyman_response_engine.py:152
async def generate_response_async(self, email_from: str, email_subject: str, 
                                 email_body: str) -> Tuple[str, Dict[str, Any]]:
    classification = self.classify_email_type(email_subject, email_body)
    enhanced_prompt = self.generate_enhanced_prompt(...)
    response_text = await asyncio.to_thread(
        self.llm_client.generate_text,
        enhanced_prompt
    )
```

### 5. Calendar Integration for Appointments
```python
# src/communication_agent/agent.py:573
if intent == "schedule_appointment":
    extracted_details = await self.response_engine.extract_appointment_details(...)
    requested_start_dt_utc = parse_datetime_from_details(...)
    busy_slots = await self.get_calendar_availability(...)
    if is_slot_free:
        created_event = await self.create_calendar_event(...)
```

### 6. Email Sending: Gmail API
```python
# src/email_client.py:229
def send_email(self, to: str, subject: str, body: str) -> bool:
    msg = MIMEText(body)
    msg['To'] = to
    msg['From'] = self.email_address
    msg['Subject'] = subject
    
    encoded_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    message_body = {'raw': encoded_message}
    
    service.users().messages().send(userId='me', body=message_body).execute()
```

## Critical Integration Points

### 1. Gmail OAuth Flow
**Files**:
- `gmail_token_monitor.json` - OAuth token for hello@757handy.com (monitored inbox)
- `gmail_token_karen.json` - OAuth token for karensecretaryai@gmail.com (sending account)
- `credentials.json` - OAuth client ID and secret

**Token Management**:
```python
# src/email_client.py:80
def _load_and_refresh_credentials(self) -> Optional[Credentials]:
    # Load token from JSON file
    # Check expiry and refresh if needed
    # Save refreshed token back to file
```

**OAuth Scopes Required**:
```python
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
]
```

### 2. Gemini API Integration
**Location**: `src/llm_client.py`
```python
class LLMClient:
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
    
    def generate_text(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)
        return response.text
```

**System Prompt**: Loaded from `src/llm_system_prompt.txt`
- Contains Karen's personality and business context
- Instructs professional, helpful responses
- Business hours, phone number, service area

### 3. Calendar Integration
**Location**: `src/calendar_client.py`
```python
class CalendarClient:
    def __init__(self, token_file_path: str, calendar_id: str = 'primary'):
        # Uses same OAuth mechanism as Gmail
        # Shares token with monitored email account
```

**Key Methods**:
- `get_availability()` - Returns busy slots for time range
- `create_event()` - Creates calendar event with attendees
- Uses Google Calendar API v3

### 4. Celery Task Scheduling
**Configuration**:
- Broker: Redis (`redis://localhost:6379/0`)
- Result Backend: Redis
- Beat Scheduler: Django-Celery-Beat with SQLite

**Task Definitions**:
```python
# Current active tasks:
- check_emails_task (every 2 min)
- check_instruction_emails_task (every 5 min)
- monitor_celery_logs_task (every 15 min)
- monitor_redis_queues_task (every 10 min)
```

### 5. Environment Variables
**Critical Variables from .env**:
```bash
# Email Accounts
SECRETARY_EMAIL_ADDRESS=karensecretaryai@gmail.com
MONITORED_EMAIL_ACCOUNT=hello@757handy.com
ADMIN_EMAIL_ADDRESS=sku3397@icloud.com

# API Keys
GEMINI_API_KEY=<your_key>
GOOGLE_PROJECT_ID=<your_project>

# Tokens
SECRETARY_TOKEN_PATH=gmail_token_karen.json
MONITORED_EMAIL_TOKEN_PATH=gmail_token_monitor.json
GOOGLE_CALENDAR_TOKEN_PATH=gmail_token_monitor.json

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Timezone
DEFAULT_TIMEZONE=America/New_York
```

## Karen's Coding Patterns

### 1. Error Handling Style
```python
# Pattern: Try-except with detailed logging and admin notification
try:
    # Main operation
    result = risky_operation()
except HttpError as error:
    error_content = error.content.decode() if isinstance(error.content, bytes) else error.content
    logger.error(f"Gmail API error: {error}. Details: {error_content}", exc_info=True)
    if error.resp.status == 401:
        logger.error("Authentication error (401). Token may be invalid.")
    return False
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    self.send_admin_email(
        subject=f"[URGENT] Error in {operation_name}",
        body=f"Error details:\n\n{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
    )
    return False
```

### 2. Logging Approach
```python
# Consistent logging pattern with levels
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Entry/exit logging for major operations
logger.info(f"Starting operation X for {identifier}")
logger.debug(f"Operation details: {details}")
# ... operation ...
logger.info(f"Completed operation X. Result: {result}")

# Special markers for important events
logger.info("Celery task: योगFINISHED check_emails_task योग")
```

### 3. Configuration Management
```python
# Pattern: Early .env loading for Celery
# src/celery_app.py:11
PROJECT_ROOT_FOR_CELERY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN_ENV_PATH_FOR_CELERY = os.path.join(PROJECT_ROOT_FOR_CELERY, '.env')
load_dotenv(dotenv_path=MAIN_ENV_PATH_FOR_CELERY, override=True)

# Pattern: Config module with defaults
# src/config.py
SECRETARY_EMAIL_ADDRESS = os.getenv('SECRETARY_EMAIL_ADDRESS', 'default@example.com')
```

### 4. Async/Sync Bridge Pattern
```python
# Pattern: Using asyncio.to_thread for sync methods in async context
response_text = await asyncio.to_thread(
    self.llm_client.generate_text,  # Synchronous method
    enhanced_prompt
)

# Pattern: asyncio.run in Celery tasks
def check_secretary_emails_task():
    agent = get_communication_agent_instance()
    asyncio.run(agent.check_and_process_incoming_tasks())
```

### 5. Schema Validation with Pydantic
```python
# src/schemas/task.py pattern
from pydantic import BaseModel, Field

class TaskDetailsSchema(BaseModel):
    description: str = Field(..., min_length=1, max_length=500)
    
class TaskCreateSchema(BaseModel):
    details: TaskDetailsSchema
    created_by: str = Field(..., regex=r'^[\w\.-]+@[\w\.-]+$')
```

## Flow Diagram
```
┌─────────────────┐
│  Celery Beat    │
│ (Every 2 mins)  │
└────────┬────────┘
         │
         v
┌─────────────────┐     ┌──────────────────┐
│ check_emails_   │────>│ Gmail API        │
│ task()          │     │ (Fetch UNREAD)   │
└────────┬────────┘     └──────────────────┘
         │
         v
┌─────────────────────────────────────┐
│ CommunicationAgent.                 │
│ check_and_process_incoming_tasks()  │
└────────┬────────────────────────────┘
         │
         ├──────────────────┐
         │                  v
         │         ┌────────────────┐
         │         │ Classify Email │
         │         │ (emergency,    │
         │         │  quote, etc.)  │
         │         └────────┬───────┘
         │                  │
         │                  v
         │         ┌────────────────┐     ┌─────────────┐
         │         │ Generate LLM   │────>│ Gemini API  │
         │         │ Response       │     └─────────────┘
         │         └────────┬───────┘
         │                  │
         │                  v
         │         ┌────────────────┐
         │         │ Calendar Check │──┐
         │         │ (if appointment)│ │
         │         └────────┬───────┘ │
         │                  │         │
         │                  v         v
         │         ┌──────────────────────┐
         │         │ Gmail API            │
         │         │ (Send Reply)         │
         │         └──────────────────────┘
         │
         v
┌─────────────────┐
│ Mark Processed  │
│ (Add Label)     │
└─────────────────┘
```

## System Dependencies
1. **Redis** - Message broker for Celery
2. **SQLite** - Celery Beat schedule storage
3. **Google APIs** - Gmail, Calendar, Gemini
4. **Python 3.9+** - Async support required
5. **OAuth 2.0** - Token management infrastructure

## DO NOT MODIFY List - Critical Files

### 1. Core Task Definitions
**File**: `src/celery_app.py`
- Contains all Celery task definitions
- Critical task scheduling configuration
- Agent instance management
- Modification could break entire email processing pipeline

### 2. Environment Configuration
**File**: `.env`
- Contains working API keys and credentials
- Email account configurations
- Modification could break authentication

### 3. OAuth Token Files
**Files**:
- `gmail_token_monitor.json` - Token for hello@757handy.com
- `gmail_token_karen.json` - Token for karensecretaryai@gmail.com
- These tokens are active and working
- Regeneration requires manual OAuth flow

### 4. LLM System Prompt
**File**: `src/llm_system_prompt.txt`
- Currently contains edge case test (may need investigation)
- Tuned for current business functionality
- Changes affect all AI responses

### 5. OAuth Credentials
**File**: `credentials.json`
- Google OAuth client ID and secret
- Required for all Google API interactions
- Modification breaks authentication flow

### 6. Email Client Core
**File**: `src/email_client.py`
- Gmail API integration logic
- Token refresh mechanism
- Critical error handling for API failures

### 7. Communication Agent Core
**File**: `src/communication_agent/agent.py`
- Main email processing logic
- Integration between all components
- Task extraction and admin notifications

## Critical System Dependencies & External Services

### 1. Google Cloud Services
**Required APIs**:
- Gmail API (quotas: 1 billion requests/day, 250 quota units/user/second)
- Calendar API (quotas: 1 million requests/day)
- Gemini API (rate limits vary by tier)

**OAuth Scopes in Production**:
```python
GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose', 
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
]

CALENDAR_SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events'
]
```

### 2. Redis Infrastructure
**Usage**:
- Celery message broker (queue: `celery`)
- Task result backend storage
- Connection monitoring via `monitor_redis_queues_task`

**Configuration**:
```python
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
```

### 3. File System Dependencies
**Critical Files**:
- `gmail_token_monitor.json` - hello@757handy.com OAuth token
- `gmail_token_karen.json` - karensecretaryai@gmail.com OAuth token  
- `gmail_token_hello_calendar.json` - Calendar access token
- `credentials.json` - Google OAuth client credentials
- `src/llm_system_prompt.txt` - AI personality and context
- `celerybeat-schedule.sqlite3` - Celery Beat scheduler database

## Agent Communication Framework Implementation

### AgentCommunication Class (Missing Implementation)
**Referenced in Celery Tasks**:
```python
# src/celery_app.py:219, 269, 348, etc.
comm = AgentCommunication('agent_name')
comm.update_status('processing', 50, {'phase': 'working'})
comm.share_knowledge('pattern_type', discovery_data)
comm.send_message('target_agent', 'message_type', content)
```

**Required Methods**:
- `update_status(status, progress, metadata)`
- `share_knowledge(knowledge_type, data)`
- `send_message(recipient, message_type, content)`
- `read_messages()`

### Agent Registry (Active Agents)
**Current Celery Task Agents**:
1. **archaeologist** - Code analysis and system mapping
2. **sms_engineer** - SMS processing via Twilio
3. **phone_engineer** - Voice call handling and transcription
4. **memory_engineer** - Conversation history consolidation
5. **test_engineer** - QA automation and testing

## Data Flow Architecture

### Email Processing State Machine
```
UNREAD EMAIL → FETCHED → CLASSIFIED → LLM_PROCESSED → CALENDAR_CHECKED → REPLY_SENT → LABELED_PROCESSED
```

### Task Creation Pipeline
```
EMAIL_WITH_TASK → EXTRACTED → VALIDATED → CREATED → LLM_SUGGESTION → ADMIN_NOTIFIED
```

### Calendar Integration Flow
```
APPOINTMENT_REQUEST → DETAILS_EXTRACTED → AVAILABILITY_CHECKED → EVENT_CREATED → CONFIRMATION_SENT
```

## Performance & Monitoring

### Current Monitoring Tasks
```python
# Every 15 minutes - Log file analysis
'monitor-celery-logs-every-15-mins'

# Every 10 minutes - Redis queue monitoring  
'monitor-redis-queues-every-10-mins'

# Every 12 hours - Gmail API quota check
'monitor-gmail-api-quota-every-12-hours'
```

### Rate Limiting Considerations
- Gmail API: 250 quota units/user/second
- Gemini API: Model-specific rate limits
- Calendar API: 100 requests/second/user
- Email check frequency: Every 2 minutes (safe for quotas)

## Karen's Detailed Coding Patterns

### 1. Comprehensive Error Handling
```python
# Pattern: Multi-level exception handling with admin notification
try:
    # Primary operation
    result = await operation()
except HttpError as error:
    # Specific API error handling
    error_content = error.content.decode() if isinstance(error.content, bytes) else error.content
    logger.error(f"API error: {error}. Details: {error_content}", exc_info=True)
    
    # Status-specific handling
    if error.resp.status == 401:
        logger.error("Authentication error. Token may be invalid.")
    elif error.resp.status == 403:
        logger.error("Permission error. Check API scopes.")
    
    # Admin notification for critical errors
    self.send_admin_email(
        subject=f"[URGENT] API Error in {operation_name}",
        body=f"Error: {error}\nDetails: {error_content}"
    )
    return False
except Exception as e:
    # Generic exception with full traceback
    logger.error(f"Unexpected error: {e}", exc_info=True)
    import traceback
    tb_str = traceback.format_exc()
    self.send_admin_email(
        subject=f"[URGENT] Unexpected Error in {operation_name}",
        body=f"Error: {str(e)}\n\nTraceback:\n{tb_str}"
    )
    return False
```

### 2. Structured Logging Pattern
```python
# Pattern: Hierarchical logging with operation tracking
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Operation entry
logger.info(f"Starting {operation_name} for {identifier}")
logger.debug(f"Operation parameters: {params}")

# Progress tracking
logger.debug(f"Step 1: {description}")
logger.info(f"Milestone reached: {milestone}")

# Result logging
logger.info(f"Successfully completed {operation_name}. Result: {result_summary}")

# Special markers for visibility
logger.info("Celery task: योगFINISHED task_name योग")
logger.debug("PRINT_DEBUG: Critical checkpoint reached")
```

### 3. Configuration Management Patterns
```python
# Pattern 1: Early .env loading for Celery
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, '.env'), override=True)

# Pattern 2: Environment-specific configuration
APP_ENV = os.getenv("APP_ENV")
if APP_ENV == "interactive_test":
    dotenv_path = os.path.join(PROJECT_ROOT, '.env.interactive_test')
    load_dotenv(dotenv_path=dotenv_path, override=True)

# Pattern 3: Config with defaults and type conversion
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
USE_MOCK = os.getenv('USE_MOCK_EMAIL_CLIENT', 'False').lower() == 'true'
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS', 'default@example.com')
```

### 4. Async Integration Patterns
```python
# Pattern 1: Sync-to-async bridge
async def async_operation(self):
    # Run synchronous method in thread pool
    result = await asyncio.to_thread(
        self.sync_client.blocking_method,
        param1, param2
    )
    return result

# Pattern 2: Celery task with async
@celery_app.task(name='async_task')
def celery_async_task():
    # Run async coroutine in sync context
    asyncio.run(async_main_operation())

# Pattern 3: Async context manager
async with self.async_client as client:
    result = await client.operation()
```

### 5. Data Validation Patterns
```python
# Pattern 1: Pydantic models for request/response
class EmailData(BaseModel):
    sender: EmailStr
    subject: str = Field(..., min_length=1, max_length=200)
    body: str
    received_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Pattern 2: Manual validation with logging
if not email_from or '@' not in email_from:
    logger.warning(f"Invalid email address: {email_from}")
    return None

# Pattern 3: Regex extraction with fallback
parsed_email = re.search(r'[\w\.-]+@[\w\.-]+', email_string)
email = parsed_email.group(0) if parsed_email else email_string
```

### 6. Service Integration Patterns
```python
# Pattern 1: Service client initialization
class ServiceClient:
    def __init__(self, config: Dict[str, Any]):
        self.token_path = config.get('token_path')
        self.creds = self._load_and_refresh_credentials()
        if not self.creds:
            raise ValueError(f"Failed to load credentials from {self.token_path}")
        self.service = build('service', 'v1', credentials=self.creds)

# Pattern 2: Retry with backoff
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def api_call_with_retry(self):
    return self.service.operation().execute()

# Pattern 3: Caching for expensive operations
def _get_cached_or_fetch(self, key: str) -> Any:
    if key in self._cache:
        return self._cache[key]
    value = self._fetch_from_api(key)
    self._cache[key] = value
    return value
```

### 7. Task Processing Patterns
```python
# Pattern 1: Task extraction from email
task_match = re.search(r"TASK:(.*?)(?=\n\n|$)", email_body, re.IGNORECASE | re.DOTALL)
if task_match:
    task_description = task_match.group(1).strip()
    task_schema = TaskCreateSchema(
        details=TaskDetailsSchema(description=task_description),
        created_by=email_from
    )
    self.task_manager.create_task(task_schema)

# Pattern 2: Intent classification
classification = {
    'is_emergency': any(kw in content.lower() for kw in emergency_keywords),
    'services_mentioned': detected_services,
    'is_appointment_request': 'schedule' in content.lower()
}

# Pattern 3: Conditional processing
if intent == "schedule_appointment" and self.calendar_client:
    # Calendar-specific logic
elif intent == "emergency":
    # Emergency response logic
else:
    # Default handling
```
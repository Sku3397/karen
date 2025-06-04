# Karen Project Implementation Patterns

This document outlines the key architectural patterns, authentication handling, error handling, and service initialization patterns found in the Karen project codebase. These patterns should be followed by all agents when implementing new features.

## Table of Contents
1. [OAuth and Authentication Patterns](#oauth-and-authentication-patterns)
2. [Service Client Initialization](#service-client-initialization)
3. [Celery Task Patterns](#celery-task-patterns)
4. [Email Processing Flow](#email-processing-flow)
5. [Error Handling and Retry Logic](#error-handling-and-retry-logic)
6. [LLM Integration Patterns](#llm-integration-patterns)
7. [Calendar Integration](#calendar-integration)
8. [Logging Standards](#logging-standards)
9. [Configuration Management](#configuration-management)
10. [Agent Communication](#agent-communication)

## OAuth and Authentication Patterns

### Token Management
```python
# Pattern: OAuth token storage and refresh
class EmailClient:
    def __init__(self, email_address: str, token_file_path: str):
        self.token_file_path = os.path.join(PROJECT_ROOT, token_file_path)
        self.creds = self._load_and_refresh_credentials()
        
    def _load_and_refresh_credentials(self) -> Optional[Credentials]:
        # 1. Try to load existing token
        if os.path.exists(self.token_file_path):
            creds = Credentials.from_authorized_user_info(token_data, SCOPES)
        
        # 2. Check if refresh is needed
        if creds and (not creds.valid or creds.expired):
            try:
                creds.refresh(GoogleAuthRequest())
                self._save_token_from_creds(creds)
            except google.auth.exceptions.RefreshError:
                # Handle refresh failure - token may be revoked
                creds = None
                
        return creds
```

### Key Principles:
- Always store tokens relative to PROJECT_ROOT
- Implement automatic refresh with proper error handling
- Save refreshed tokens immediately after refresh
- Handle RefreshError separately (indicates revoked/invalid refresh token)
- Log all authentication attempts and failures

## Service Client Initialization

### Pattern: Fail-Fast with Detailed Error Messages
```python
class CalendarClient:
    def __init__(self, email_address: str, token_path: str, credentials_path: str):
        # 1. Load client configuration first
        self.client_config = self._load_client_config()
        if not self.client_config:
            raise ValueError(f"Failed to load client configuration from {self.credentials_path}")
        
        # 2. Load and validate credentials
        self.creds = self._load_and_refresh_credentials()
        if not self.creds:
            raise ValueError(f"Failed to load/refresh OAuth credentials from {self.token_path}")
        
        # 3. Build service
        try:
            self.service = build('calendar', 'v3', credentials=self.creds)
        except Exception as e:
            logger.error(f"Failed to build service: {e}", exc_info=True)
            raise
```

### Key Principles:
- Validate all prerequisites before proceeding
- Raise ValueError with descriptive messages for setup failures
- Use try/except with exc_info=True for unexpected errors
- Initialize services in constructor to fail early

## Celery Task Patterns

### Task Definition Pattern
```python
@celery_app.task(name='task_name', bind=True, ignore_result=True)
def task_function(self, payload: dict = None):
    """Task description"""
    task_logger = self.get_logger()
    comm = AgentCommunication('agent_name')
    
    try:
        # Update status at start
        comm.update_status('processing', 10, {'phase': 'starting', 'task_id': self.request.id})
        
        # Read any messages for this agent
        messages = comm.read_messages()
        for msg in messages:
            task_logger.info(f"Received: {msg}")
        
        # Perform task work
        # ...
        
        # Share results
        comm.share_knowledge('category', {'data': 'value'})
        
        # Update completion
        comm.update_status('completed', 100, {'phase': 'done', 'task_id': self.request.id})
        
    except Exception as e:
        task_logger.error(f"Error in task: {e}", exc_info=True)
        comm.update_status('error', 0, {'error': str(e), 'task_id': self.request.id})
```

### Async Task Pattern
```python
@celery_app.task(name='async_task', ignore_result=True)
def async_task_runner():
    try:
        agent = get_agent_instance()
        # Run async method in sync context
        asyncio.run(agent.async_method())
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise
```

## Email Processing Flow

### Email Checking Pattern
```python
async def check_and_process_incoming_tasks(self, process_last_n_days: Optional[int] = None):
    KAREN_PROCESSED_LABEL = "Karen_Processed"
    
    # 1. Build search criteria
    search_criteria = f'-label:{KAREN_PROCESSED_LABEL}'
    if process_last_n_days:
        date_n_days_ago = (datetime.now() - timedelta(days=process_last_n_days)).strftime('%Y/%m/%d')
        search_criteria = f'after:{date_n_days_ago} -label:{KAREN_PROCESSED_LABEL}'
    
    # 2. Fetch emails
    emails = self.monitoring_email_client.fetch_emails(search_criteria=search_criteria)
    
    # 3. Process each email
    for email_data in emails:
        try:
            # Process email
            # ...
            
            # Mark as processed
            if email_uid:
                self.monitoring_email_client.mark_email_as_processed(
                    uid=email_uid, 
                    label_to_add=KAREN_PROCESSED_LABEL
                )
        except Exception as e:
            logger.error(f"Error processing email {email_uid}: {e}", exc_info=True)
            # Continue processing other emails
```

### Key Principles:
- Use labels to track processed emails (avoid reprocessing)
- Handle each email independently (continue on error)
- Always mark emails as processed, even if processing fails
- Use specific search criteria to limit scope

## Error Handling and Retry Logic

### Comprehensive Error Handling Pattern
```python
def api_operation(self):
    try:
        # Attempt operation
        result = self.service.operation().execute()
        return result
        
    except HttpError as e:
        # Handle specific API errors
        if e.resp.status == 401:
            logger.error("Authentication error - token may be invalid")
        elif e.resp.status == 403:
            logger.error("Permission error - check API scopes")
        elif e.resp.status == 404:
            logger.error("Resource not found")
        return None
        
    except google.auth.exceptions.RefreshError as e:
        # Handle refresh failures specifically
        logger.error(f"Token refresh failed: {e}", exc_info=True)
        return None
        
    except Exception as e:
        # Catch-all for unexpected errors
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return None
```

### Admin Notification Pattern
```python
def critical_operation(self):
    try:
        # Operation
        pass
    except Exception as e:
        # Log the error
        logger.error(f"Critical error: {e}", exc_info=True)
        
        # Notify admin
        import traceback
        tb_str = traceback.format_exc()
        self.send_admin_email(
            subject=f"[URGENT] Critical Error in {self.__class__.__name__}",
            body=f"Error: {str(e)}\n\nTraceback:\n{tb_str}"
        )
```

## LLM Integration Patterns

### LLM Client Usage
```python
class ServiceWithLLM:
    def __init__(self):
        try:
            self.llm_client = LLMClient()
        except ValueError as e:
            logger.error(f"Failed to initialize LLMClient: {e}")
            self.llm_client = None
    
    async def generate_response(self, prompt: str) -> str:
        if not self.llm_client:
            return "AI service unavailable"
        
        try:
            # For async context, use asyncio.to_thread
            response = await asyncio.to_thread(
                self.llm_client.generate_text,
                prompt
            )
            return response
        except Exception as e:
            logger.error(f"LLM generation failed: {e}", exc_info=True)
            return self._generate_fallback_response()
```

### System Prompt Management
- Store system prompts in `llm_system_prompt.txt`
- Support dynamic variables like `{{current_date}}`
- Reload prompts on each request to support hot updates
- Provide fallback prompts if file is missing

## Calendar Integration

### Availability Checking Pattern
```python
async def check_appointment_availability(self, requested_time: datetime, duration_hours: float):
    # 1. Convert to UTC if needed
    requested_start_utc = requested_time.astimezone(pytz.utc)
    requested_end_utc = requested_start_utc + timedelta(hours=duration_hours)
    
    # 2. Get full day availability to provide context
    business_tz = pytz.timezone("America/New_York")
    local_day = requested_start_utc.astimezone(business_tz).date()
    day_start_utc = datetime.combine(local_day, datetime.min.time(), business_tz).astimezone(pytz.utc)
    day_end_utc = day_start_utc + timedelta(days=1)
    
    # 3. Check for conflicts
    busy_slots = await self.calendar_client.get_availability(
        day_start_utc.isoformat() + 'Z',
        day_end_utc.isoformat() + 'Z'
    )
    
    # 4. Determine if requested slot is free
    is_free = True
    if busy_slots:
        for busy in busy_slots:
            if overlaps(requested_start_utc, requested_end_utc, busy['start'], busy['end']):
                is_free = False
                break
    
    return is_free
```

## Logging Standards

### Logging Levels and Patterns
```python
# Module-level logger
logger = logging.getLogger(__name__)

# In classes/functions:
logger.debug(f"Detailed info for debugging: {variable}")
logger.info(f"Normal operation: Successfully processed {item}")
logger.warning(f"Warning but not error: {condition}")
logger.error(f"Error occurred: {error}", exc_info=True)  # Always use exc_info=True for errors

# For Celery tasks
task_logger = self.get_logger()  # Use task-specific logger
```

### Key Principles:
- Use module-level loggers (`__name__`)
- Include context in log messages (IDs, email addresses, etc.)
- Use exc_info=True for all error logs
- Log at appropriate levels (debug for details, info for operations, error for failures)

## Configuration Management

### Environment Variable Pattern
```python
# In config.py
import os
from dotenv import load_dotenv

# Load environment-specific .env file
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(PROJECT_ROOT, '.env')
load_dotenv(env_path)

# Export configuration with defaults
SECRETARY_EMAIL_ADDRESS = os.getenv('SECRETARY_EMAIL_ADDRESS', 'karensecretaryai@gmail.com')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')  # No default for sensitive data

# Validate required configuration
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY must be set in environment")
```

## Agent Communication

### Inter-Agent Messaging Pattern
```python
from src.agent_communication import AgentCommunication

class MyAgent:
    def __init__(self, agent_name: str):
        self.comm = AgentCommunication(agent_name)
    
    def process(self):
        # Read messages
        messages = self.comm.read_messages()
        for msg in messages:
            if msg['type'] == 'request':
                self.handle_request(msg)
        
        # Send messages
        self.comm.send_message('target_agent', 'response', {
            'status': 'completed',
            'data': result
        })
        
        # Share knowledge
        self.comm.share_knowledge('category', {
            'discovered': 'pattern',
            'timestamp': datetime.now().isoformat()
        })
        
        # Update status
        self.comm.update_status('processing', 50, {'current_task': 'analyzing'})
```

## Critical Dependencies and Constraints

1. **Redis**: Required for Celery message broker
   - Default URL: `redis://localhost:6379/0`
   - Must be running for task execution

2. **Google APIs**: 
   - Gmail API for email operations
   - Calendar API for scheduling
   - Gemini API for LLM responses
   - All require valid OAuth tokens or API keys

3. **Token Files**:
   - `gmail_token_karen.json`: Secretary email sending
   - `gmail_token_monitor.json`: Monitored inbox
   - `calendar_token.json`: Calendar access
   - Must have appropriate scopes

4. **Environment Variables**:
   - Must be set in `.env` file
   - Critical ones: `GEMINI_API_KEY`, email addresses, token paths
   - Validated on startup

5. **File Paths**:
   - Always use absolute paths relative to PROJECT_ROOT
   - Use `os.path.join()` for cross-platform compatibility
   - Verify file existence before operations

## Best Practices Summary

1. **Always fail fast**: Validate configuration and credentials at initialization
2. **Log everything**: Use appropriate log levels with context
3. **Handle errors gracefully**: Specific handling for different error types
4. **Notify on critical failures**: Send admin emails for urgent issues
5. **Use labels/flags**: Prevent reprocessing of emails/tasks
6. **Async when needed**: Use `asyncio.run()` or `asyncio.to_thread()` appropriately
7. **Test with mocks**: Support mock clients for testing (USE_MOCK_EMAIL_CLIENT)
8. **Document patterns**: Keep this document updated with new patterns
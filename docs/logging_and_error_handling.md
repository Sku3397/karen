# Logging, Error Handling, and Retry Mechanisms

## Logging Strategy
- **Framework:** Utilizes Python's standard `logging` module for centralized and consistent logging across the application.
- **Log Levels:** Standard levels are used: DEBUG (for detailed development/diagnostic information), INFO (for operational messages, task lifecycle), WARNING (for recoverable issues or unexpected but non-critical situations), ERROR (for failures that prevent a specific operation from completing), CRITICAL (for systemic outages - less common in this application type).
- **Loggers:** Module-level loggers are obtained via `logging.getLogger(__name__)` to provide context.
- **Log Format:** Logs typically include a timestamp, log level, logger name (module), and the message. Celery tasks have specific formatters defined in `src/celery_app.py` that also include process and task IDs.
- **Output:**
    - **Celery Logs:** Celery Worker and Beat logs are configured to output to specific files (e.g., `celery_worker_debug_logs_new.txt`, `celery_beat_logs_new.txt`) when started with redirection as shown in `README.md`.
    - **General Logs:** Other parts of the application (if run outside Celery, e.g., utility scripts) may log to stdout/stderr or specific files if configured.
- **Celery Logger Configuration:** `src/celery_app.py` contains signal handlers (`after_setup_logger`, `after_setup_task_logger`) to customize Celery's logging format and levels.

## Error Handling
- **Standard Exceptions:** Python's built-in exceptions are used extensively.
- **API Client Exceptions:** Specific exceptions raised by third-party API clients (e.g., `googleapiclient.errors.HttpError` for Google APIs, `requests.exceptions.RequestException`) are caught where appropriate.
- **Custom Exceptions (Aspirational/Partial):** While the system aims for domain-specific error clarity (e.g., `EmailClientError`), comprehensive custom exceptions for all scenarios (e.g., `TransientError`, `PermanentError`, `GracefulDegradationError`) are more of a target state. Some specific custom exceptions may be present in modules like `EmailClient`.
- **Try/Except Blocks:** Critical integration points (API calls, file operations) are generally wrapped in try/except blocks.
- **Logging Exceptions:** Exceptions are logged, often with `exc_info=True` to include stack traces for unexpected failures, facilitating debugging.

## Retry Policies
- **Celery Task Retries:** Celery tasks leverage Celery's built-in retry mechanisms (e.g., `self.retry(exc=e, countdown=...)`). This is used for potentially transient issues encountered during task execution. Max attempts and backoff periods can be configured per task retry call.
- **Generic Retry Decorators (Aspirational):** A general-purpose decorator-based retry mechanism with exponential backoff for non-Celery external API calls is a good practice and may be partially implemented or a target for future enhancement.
- **Scope of Retries:** Retries are generally intended for errors that are likely transient (e.g., temporary network issues, rate limits that might pass after a delay).

## Graceful Degradation (Conceptual/Partial)
- **Current State:** If a critical operation (like LLM call or email sending) fails after retries (if applicable), the system typically logs the error and may fail the current task or operation. An admin notification might be sent.
- **Aspirational:** A more formal graceful degradation strategy (e.g., informing users of reduced functionality, using cached data, or providing specific fallback responses) is a target for more complex failure scenarios.

## Integration Example (Conceptual)
Each external API integration (Gmail, Gemini, Calendar) aims to follow these patterns. Specific error parsing and retry logic are implemented within the respective client modules (`EmailClient`, `LLMClient`, `CalendarClient`) and the Celery tasks that use them.
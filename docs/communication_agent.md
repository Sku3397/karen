# Communication Agent

**Note:** This document provides a brief overview. For detailed, up-to-date information on the `CommunicationAgent`'s functionality, configuration, and API, please refer to:
- The main project **`README.md`** (sections on Core Functionality, Project Structure, and How it Works).
- The source code: **`src/communication_agent/agent.py`**.

The `CommunicationAgent` module is a central component in the Karen AI Assistant. Its primary responsibilities include:

-   **Orchestrating Email Processing:**
    -   Monitoring a designated Gmail account (e.g., `hello@757handy.com`) for new customer inquiries using the `EmailClient`.
    -   Processing these emails by leveraging the `HandymanResponseEngine` and `LLMClient` to:
        -   Understand email content and intent (e.g., quote request, service query, appointment request).
        -   Interact with Google Calendar via `CalendarClient` for availability and scheduling.
        -   Generate appropriate, context-aware replies.
    -   Sending generated replies to customers via a separate designated Gmail account (e.g., `karensecretaryai@gmail.com`) using the `EmailClient`.
    -   Marking processed emails in the monitored inbox.
-   **Handling Instruction Emails:**
    -   Monitoring a designated Gmail account (typically the secretary/sending account, e.g., `karensecretaryai@gmail.com`) for special instruction emails, such as "UPDATE PROMPT".
    -   Updating system configurations (like the `llm_system_prompt.txt`) based on these instructions.
-   **Admin Notifications:**
    -   Sending notification emails to a designated admin email address about processed customer inquiries, successful instruction updates, or errors encountered during operation.
-   **Asynchronous Operations:**
    -   Its core email processing logic (`check_and_process_incoming_tasks`) is designed to be `async` and is typically run as a Celery task.

## Key Interactions

The `CommunicationAgent` interacts with several other key modules:

-   `src/email_client.py`: For all Gmail API interactions (fetching, sending, labeling emails).
-   `src/llm_client.py`: For generating text responses using the configured LLM (e.g., Google Gemini).
-   `src/handyman_response_engine.py`: For interpreting email content, determining intent, crafting LLM prompts, and managing calendar-related logic.
-   `src/calendar_client.py`: For interacting with Google Calendar (checking availability, creating events).
-   `src/config.py`: For sourcing configuration details like email addresses, token paths, and API keys.
-   `src/celery_app.py`: Defines the Celery tasks that trigger the agent's processing methods.

Placeholders for `SMSHandler` and `VoiceTranscriptionHandler` exist but are not currently core to the primary email and calendar processing loop.

## Components
- `EmailHandler`: Handles SMTP email sending.
- `SMSHandler`: Interfaces with Twilio for SMS.
- `VoiceTranscriptionHandler`: Leverages Google Cloud Speech-to-Text for transcription.
- `CommunicationAgent`: Facade class orchestrating all handlers for unified processing.

## Usage Example
```python
from communication_agent.agent import CommunicationAgent

email_cfg = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 465,
    'username': 'your@email.com',
    'password': 'app_password',
}
sms_cfg = {
    'account_sid': 'TWILIO_SID',
    'auth_token': 'TWILIO_TOKEN',
    'from_number': '+1234567890',
}
transcription_cfg = {
    'language_code': 'en-US'
}
agent = CommunicationAgent(email_cfg, sms_cfg, transcription_cfg)

# Send an email
agent.process_email('client@email.com', 'Subject', 'Message body')

# Send SMS
agent.process_sms('+10987654321', 'Your handyman is confirmed!')

# Transcribe voice (audio_bytes: bytes)
# transcript = agent.process_voice_transcription(audio_bytes)
```

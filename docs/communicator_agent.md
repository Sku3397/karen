# Communicator Agent

## Overview
The Communicator Agent provides unified APIs for managing Gmail email, Twilio SMS/calls, transcription (Google Cloud), and multi-language response generation (Google Translate).

### Features
- Send and receive emails (Gmail API)
- Send and receive SMS (Twilio)
- Initiate and handle calls (Twilio)
- Transcribe voicemails (Google Speech-to-Text)
- Generate responses in multiple languages (Google Translate)

### Usage
1. Instantiate CommunicatorAgent with required credentials.
2. Use `send_email`, `send_sms`, `initiate_call`, and `handle_incoming_call` APIs.
3. Multi-language responses via `lang` parameter.

### Example
```python
agent = CommunicatorAgent(gmail_creds, twilio_creds, gcloud_creds)
agent.send_email('user@example.com', 'Subject', 'Hello!', lang='es')
```

See source code for more details and test cases in `tests/test_communicator_agent.py`.

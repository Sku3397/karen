# Communication Agent

The Communication Agent module manages client communications via:
- **Email**: Sending transactional and informational emails.
- **SMS (Twilio)**: Sending and receiving SMS for confirmations and notifications.
- **Voice Transcription (GCP Speech-to-Text)**: Transcribing client audio (calls/voicemails) to text.

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

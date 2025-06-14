# SMS Production Configuration

## Environment Variables Required

```bash
# Twilio Configuration
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
KAREN_PHONE_NUMBER=+17575551234

# SMS Processing
SMS_PROCESSING_INTERVAL=60
ADMIN_PHONE_NUMBER=+17575559999

# Webhook Configuration
SMS_WEBHOOK_URL=https://your-domain.com/webhooks/sms/incoming
```

## Twilio Setup

1. Purchase a phone number in Twilio Console
2. Configure webhook URL in Twilio Console:
   - Phone Numbers → Manage → Active numbers
   - Click your number → Configure webhook URL
   - Set to: https://your-domain.com/webhooks/sms/incoming

## Celery Configuration

Add to celery_app.py:

```python
from .celery_sms_schedule import SMS_BEAT_SCHEDULE
celery_app.conf.beat_schedule.update(SMS_BEAT_SCHEDULE)
```

## Testing Commands

```bash
# Test SMS client
python -m src.sms_client

# Run comprehensive tests  
python scripts/test_sms_system.py

# Test webhook locally with ngrok
ngrok http 8000
# Then update Twilio webhook to ngrok URL
```

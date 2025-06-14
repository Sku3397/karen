"""
SMS Celery Beat Schedule Configuration
Add these entries to celery_app.py beat_schedule to enable SMS processing
"""

from celery.schedules import crontab

# SMS task schedule entries to add to celery_app.conf.beat_schedule
SMS_BEAT_SCHEDULE = {
    # Check for new SMS messages every minute (similar to email)
    'check-sms-every-minute': {
        'task': 'check_sms_task',
        'schedule': crontab(minute='*'),  # Every minute
    },
    
    # Test SMS system daily at 8 AM
    'test-sms-system-daily': {
        'task': 'test_sms_system',
        'schedule': crontab(hour=8, minute=0),  # Daily at 8:00 AM
    },
    
    # Optional: Less frequent SMS check (every 5 minutes) if every minute is too frequent
    'check-sms-every-5-minutes': {
        'task': 'check_sms_task', 
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
        # Note: Only use this OR the every-minute check, not both
    },
}

# To integrate with existing celery_app.py, add these lines:
"""
# In celery_app.py, add to the existing beat_schedule:

# Import SMS schedule
from .celery_sms_schedule import SMS_BEAT_SCHEDULE

# Add to existing beat_schedule
celery_app.conf.beat_schedule.update(SMS_BEAT_SCHEDULE)

# Or manually add entries:
celery_app.conf.beat_schedule.update({
    'check-sms-every-minute': {
        'task': 'check_sms_task',
        'schedule': crontab(minute='*'),
    },
    'test-sms-system-daily': {
        'task': 'test_sms_system',
        'schedule': crontab(hour=8, minute=0),
    },
})
"""

# Instructions for .env file additions
ENV_ADDITIONS = """
# Add these to your .env file for SMS functionality:

# Twilio Configuration (required)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
KAREN_PHONE_NUMBER=+17575551234

# Optional SMS Configuration
MONITORED_SMS_PHONE=+17575551234  # Defaults to KAREN_PHONE_NUMBER
SMS_PROCESSING_INTERVAL=60  # Seconds between SMS checks
ADMIN_PHONE_NUMBER=+17575559999  # For emergency SMS notifications
TEST_PHONE_NUMBER=+15551234567  # For testing (optional)

# Business Information (if not already set)
BUSINESS_NAME=Beach Handyman
BUSINESS_PHONE=757-354-4577
SERVICE_AREA=Virginia Beach area
"""

if __name__ == '__main__':
    print("SMS Celery Schedule Configuration")
    print("=" * 40)
    print("\n1. Beat Schedule Entries:")
    for name, config in SMS_BEAT_SCHEDULE.items():
        print(f"   {name}: {config['task']} - {config['schedule']}")
    
    print("\n2. Environment Variables Needed:")
    print(ENV_ADDITIONS)
    
    print("\n3. Integration Steps:")
    print("   - Add SMS_BEAT_SCHEDULE to celery_app.py")
    print("   - Add environment variables to .env")
    print("   - Import celery_sms_tasks in celery_app.py")
    print("   - Restart Celery Beat and Worker")
    
    print("\n4. Test Command:")
    print("   python scripts/test_sms_system.py")
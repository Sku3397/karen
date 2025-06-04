# KAREN AI SYSTEM - DO NOT MODIFY LIST
## Critical Files That Must Remain Untouched

> **WARNING**: Modifying any files in this list could break the entire Karen AI system. These files contain production configurations, working authentication tokens, and battle-tested code with complex edge case handling.

## 🔒 CRITICAL - NEVER MODIFY

### 1. OAuth Token Files
```
- gmail_token_monitor.json          # hello@757handy.com OAuth token
- gmail_token_karen.json            # karensecretaryai@gmail.com OAuth token  
- gmail_token_hello_calendar.json   # Calendar access token
- credentials.json                  # Google OAuth client credentials
```
**Reason**: These contain active OAuth tokens. Modification requires manual re-authentication flow. Breaking these stops all email processing.

### 2. Environment Configuration
```
- .env                             # Production environment variables
- .env.interactive_test            # Test environment overrides
```
**Reason**: Contains working API keys, email configurations, and critical system settings. Changes can break authentication.

### 3. Core Celery Task Definitions
```
- src/celery_app.py
```
**Reason**: Contains all Celery task definitions, scheduling configuration, and agent instance management. Modification breaks the entire email processing pipeline.

### 4. Email Processing Core
```
- src/email_client.py              # Gmail API integration & OAuth refresh
- src/communication_agent/agent.py # Main email processing logic
```
**Reason**: Battle-tested Gmail API integration with complex OAuth refresh logic and email processing state machine.

## ⚠️ MODIFY WITH EXTREME CAUTION

### 5. LLM System Integration
```
- src/llm_system_prompt.txt        # AI personality and business context
- src/llm_client.py                # Gemini API integration
- src/handyman_response_engine.py  # Email classification engine
```
**Reason**: Tuned for current business requirements. Changes affect all AI responses and email classification.

### 6. Configuration Management
```
- src/config.py                    # Environment loading and validation
```
**Reason**: Handles complex environment loading for different contexts (production, testing). Has early loading logic for Celery.

### 7. Calendar Integration
```
- src/calendar_client.py           # Google Calendar API integration
```
**Reason**: Complex OAuth handling and appointment scheduling logic. Shares authentication with email system.

### 8. Task Management System
```
- src/task_manager_agent.py        # Task creation and management
- src/schemas/task.py              # Task data structures
```
**Reason**: Integrated with email processing for task extraction. Schema changes could break API contracts.

## 📁 DATABASE FILES - BACKUP BEFORE TOUCHING
```
- celerybeat-schedule.sqlite3      # Celery Beat scheduler database
```
**Reason**: Contains task scheduling state. Corruption stops all automated email checking.

## 🔧 SAFE TO MODIFY (With Testing)

### Templates and Documentation
```
- autonomous-agents/shared-knowledge/*.md
- autonomous-agents/shared-knowledge/templates/*
- docs/*
```

### Test Scripts
```
- scripts/*.py
- tests/*.py
```

### Frontend Components (If Applicable)
```
- src/components/*
- public/*
```

## 🚨 EMERGENCY RECOVERY PROCEDURES

### If OAuth Tokens Are Broken:
```bash
# Re-run OAuth setup scripts
python setup_karen_oauth.py      # For karensecretaryai@gmail.com
python setup_monitor_oauth.py    # For hello@757handy.com  
python setup_calendar_oauth.py   # For calendar access
```

### If Environment Variables Are Lost:
1. Check `src/config.py` for required variable names
2. Refer to deployment documentation for correct values
3. Never commit real credentials to version control

### If Celery Tasks Break:
1. Check Redis connection: `redis-cli ping`
2. Verify `.env` has correct `CELERY_BROKER_URL`
3. Restart Celery worker and beat processes

### If Email Processing Stops:
1. Check Gmail API quotas in Google Cloud Console
2. Verify OAuth tokens haven't expired
3. Check admin email for error notifications

## 📋 MODIFICATION CHECKLIST

Before modifying ANY file:

- [ ] Is it in the DO NOT MODIFY list?
- [ ] Have you backed up the current version?
- [ ] Do you understand all dependencies?
- [ ] Is there a test environment to verify changes?
- [ ] Have you documented the change reason?
- [ ] Can you quickly rollback if something breaks?

## 🔍 PATTERN RECOGNITION

**If you see these patterns, STOP:**
- OAuth token refresh logic (`_load_and_refresh_credentials`)
- Celery task decorators (`@celery_app.task`)
- Gmail API error handling with admin notifications
- Environment variable loading with early `.env` processing
- Email label tracking (`Karen_Processed`)

**These patterns are battle-tested and handle complex edge cases.**

---

**Remember**: Karen is a production system handling real customer emails. Breaking it means breaking customer service. When in doubt, document the change need but don't implement until you fully understand the impact.
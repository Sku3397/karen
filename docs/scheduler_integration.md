# Scheduler and Calendar Integration

This module provides:
- Bidirectional syncing between Google Calendar and Microsoft Outlook Calendar
- Appointment and reminder management
- Conflict resolution for overlapping events
- Real-time updates via webhooks

## Main files
- `agent.py`: SchedulerAgent orchestrates sync and event management
- `google_calendar.py`: Interface to Google Calendar API
- `outlook_calendar.py`: Interface to Outlook Calendar API
- `webhooks.py`: Webhook endpoints for real-time sync
- `models.py`: Event normalization and mapping
- `utils.py`: Sync and conflict logic

## Notes
- OAuth2 credentials must be supplied for both calendar providers
- Event mappings are stored in Firestore for reliability
- Test coverage and mocking required for API calls in real deployments

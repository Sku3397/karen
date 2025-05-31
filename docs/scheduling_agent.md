# Scheduling Agent with Calendar Integration

## Features
- Schedule events with Google Calendar and Outlook
- List calendar events for a user
- Store scheduled events and reminders in Firestore
- API endpoints for schedule and event retrieval
- Reminder scheduling logic for event notifications

## Endpoints
- `POST /schedule` — Schedule a new event (requires `user_id`, `provider`, `event_data`)
- `GET /events` — List events for a user within a date range

## Integration Notes
- Google and Outlook OAuth2 tokens required per user (see `src/utils/oauth.py`)
- Reminders currently stored in Firestore (can be extended for push notifications)
- Firestore collections used: `scheduled_events`, `reminders`

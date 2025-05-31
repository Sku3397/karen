# Scheduler Agent & Google Calendar Integration

## Features
- Appointment creation, update, deletion
- Conflict detection (overlapping events)
- Google Calendar API integration (OAuth2)
- Reminder scheduling (SMS/email; pluggable)
- Route optimization between appointments

## Components
- `SchedulerAgent`: Main orchestrator
- `GoogleCalendarService`: Handles API calls
- `ReminderService`: Abstract reminder scheduling (e.g., Twilio, SendGrid)
- `RouteOptimizer`: Route logic (stub; replace with Google Maps API)

## Usage
- Ensure user OAuth2 credentials are available per Google Calendar API
- Use `SchedulerAgent.create_appointment(details)` to add appointments
- Conflict detection returns overlapping appointments
- Reminder logic is pluggable

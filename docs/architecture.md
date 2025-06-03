# System Architecture

**Note:** This document primarily describes a **target/future-state serverless architecture**. For details on the **current operational architecture** (Celery/Redis-based), please refer to the main project `README.md`.

## Target Architecture Overview (Serverless, Event-Driven)
The envisioned AI Handyman Secretary Assistant utilizes a serverless, event-driven architecture. Agents would communicate via Pub/Sub, persist data in Firestore, and connect to external APIs for scheduling, payments, and messaging.

### Target Components
- **Serverless Agent Functions**: Each agent would be a Google Cloud Function triggered by HTTP or Pub/Sub events.
- **Pub/Sub**: Would facilitate multi-agent message exchange.
- **Firestore (NoSQL)**: Intended for client history, handyman procedures, pricing, FAQs, and agent states. (Currently not actively used in the primary application flow).
- **Third-party APIs**:
  - *Google Calendar*: Scheduling (Currently integrated in the Celery-based system)
  - *Stripe*: Payments (Future)
  - *Twilio*: Messaging/voice (Placeholders exist in the current system)
- **GCP Speech-to-Text**: Voice processing (Future)
- **CI/CD**: GitHub Actions or Google Cloud Build for automated testing and deployment (Partially present with `cloudbuild.yaml`).
- **Backups**: Automated Firestore and config backups (Future, tied to Firestore usage).

### Target Data Flow
1. User request triggers an agent function via HTTP or Pub/Sub.
2. Agent processes input, accesses Firestore, and may invoke third-party APIs.
3. Results routed back to the user or further agents as needed.

### Target Security & Compliance
- Service Account IAM roles scoped to least privilege.
- Secure management of API keys and secrets (e.g., GCP Secret Manager).
- Logging and monitoring via GCP Cloud Logging.

---

## Current Implemented Architecture (Celery/Redis-based)

For a detailed understanding of the system as it currently operates, please consult the main **`README.md`**. The key aspects are:
- **Core Framework:** Python, Celery for task queuing and scheduling, Redis as a message broker.
- **Email Processing:** `CommunicationAgent` uses `EmailClient` (Gmail API) and `LLMClient` (Gemini API).
- **Calendar Integration:** `CalendarClient` interacts with Google Calendar.
- **Data Storage:** `celerybeat-schedule.sqlite3` for Celery Beat schedule; primary data is within emails and LLM context, not a persistent database for user/task history yet.
- **Execution:** Runs as Python processes (Celery worker, Celery beat) typically on a local machine or VM, not serverless functions.
- **Logging:** To local files (`celery_worker_debug_logs_new.txt`, `celery_beat_logs_new.txt`).

---
**See `iac/main.tf` for initial resource provisioning.**

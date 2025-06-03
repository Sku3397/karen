# AI Handyman Secretary Assistant: System Architecture Overview

**Note:** This document primarily describes a **target/future-state cloud-native, microservices-oriented architecture**. For details on the **current operational architecture** (Celery/Redis-based, monolithic Python application), please refer to the main project `README.md`.

## 1. Target Architecture Introduction (Cloud-Native, Microservices)
The envisioned AI Handyman Secretary Assistant is a cloud-native service that assists users in managing tasks, appointments, communications, and payments. It would leverage Google Cloud Platform (GCP), integrate with external APIs (Google Workspace, Twilio, Stripe, SendGrid), and support multi-language interactions using a microservices approach.

## 2. Target High-Level Components
- **API Gateway / REST API**: Entry point for client applications (mobile/web/voice) to interact with backend services.
- **Authentication & Authorization**: OAuth2 (Google Identity Platform) for user and agent authentication; role-based access control.
- **Agent Orchestration Layer**: Manages specialized AI agents (e.g., Scheduling Agent, Communication Agent, Task Management Agent) as microservices, routing tasks between them (potentially via Pub/Sub).
- **Business Logic Layer**: Implements core logic for scheduling, reminders, notifications, and payment workflows, likely within specific microservices.
- **Database (Firestore)**: Stores user profiles, tasks, appointments, communications, and audit logs. (Currently not actively used in the primary application flow of the Celery-based system).
- **Integration Services**: Handles communication with external APIs:
  - Google Workspace (Calendar, Contacts, Drive)
  - Twilio (SMS/Voice)
  - Stripe (Payments)
  - SendGrid (Email) (Current system uses Gmail API directly)
- **NLP/NLU Module**: Processes and understands multi-language user input, routes intent to appropriate agent.
- **Monitoring & Logging**: Centralized logging, error tracking, and metrics (e.g., Google Cloud Logging/Stackdriver).

## 3. Target Data Flow Overview
1. User request received via API Gateway.
2. Authenticated and passed to NLP/NLU for intent identification.
3. Agent Orchestration Layer routes request to appropriate agent microservice.
4. Agents interact with business logic, database (Firestore), and external APIs as needed.
5. Responses consolidated and returned to user.

## 4. Key Architectural Considerations (for Target Architecture)
- **Eventual Consistency**: Firestore's consistency model requires conflict resolution strategies for concurrent updates.
- **External API Latency/Availability**: Implement retries, circuit breakers, and graceful degradation for API failures.
- **Security & Compliance**: Strict permission boundaries, encrypted data-at-rest/in-transit, audit logging, and secure API credential management (e.g., GCP Secret Manager).
- **Scalability**: Designed for horizontal scaling via GCP Cloud Functions or Cloud Run microservices.
- **Multi-language Support**: NLP/NLU models must support target languages.

---

## Current Implemented Architecture (Celery/Redis-based)

For a detailed understanding of the system as it currently operates, please consult the main **`README.md`**. The key aspects are:
- **Core Framework:** Python, with Celery for task queuing and scheduling, and Redis as a message broker. The application structure is more monolithic compared to the microservices vision above.
- **Email Processing:** The `CommunicationAgent` (within the `src` directory) handles email fetching, LLM interaction (via `LLMClient` for Gemini), and sending replies, using the `EmailClient` (Gmail API).
- **Calendar Integration:** `CalendarClient` is used by `HandymanResponseEngine` (invoked by `CommunicationAgent`) to interact with Google Calendar.
- **Data Storage:** Primarily `celerybeat-schedule.sqlite3` for Celery Beat's schedule. User/task data is transient within email content and LLM processing, not in a persistent database like Firestore for general application data.
- **Execution Model:** Runs as standard Python processes (Celery worker, Celery beat) that can be hosted on a local machine, VM, or a container, but not as individual serverless functions or orchestrated microservices.
- **Logging:** Currently to local files (e.g., `celery_worker_debug_logs_new.txt`).
- **API:** FastAPI (`src/main.py`) is present but primarily for potential future REST endpoints; the core email processing loop is Celery-driven, not API Gateway-driven.

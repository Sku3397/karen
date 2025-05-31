# Multi-Agent System Architecture: AI Handyman Secretary Assistant

## Overview
This architecture document defines the multi-agent setup for the AI Handyman Secretary Assistant, leveraging GCP serverless technologies and Pub/Sub for inter-agent communication.

## Agent Roles and Responsibilities

### 1. Voice Interface Agent
- **Role**: Ingests user voice input (calls, recordings), invokes GCP Speech-to-Text, and transcribes input.
- **Communicates via**: Publishes transcribed text to `user-input` Pub/Sub topic.

### 2. NLU Agent
- **Role**: Interprets user intent and entities (optionally via Dialogflow or custom NLU).
- **Communicates via**: Subscribes to `user-input`, publishes parsed intents to `nlu-output`.

### 3. Scheduling Agent
- **Role**: Handles appointment creation, modification, and cancellation; interfaces with Google Calendar API.
- **Communicates via**: Subscribes to `nlu-output`, interacts with Firestore for persistent storage, uses `events` topic for downstream notifications.

### 4. Billing Agent
- **Role**: Handles pricing queries, invoicing, and payment processing via Stripe API.
- **Communicates via**: Subscribes to `nlu-output`, publishes to `billing-events`.

### 5. Notification Agent
- **Role**: Manages outgoing notifications (SMS/email) via Twilio or similar.
- **Communicates via**: Subscribes to `events` and `billing-events`, triggers outbound communication.

### 6. Knowledge Base Agent
- **Role**: Answers FAQs, retrieves handyman procedures, and surfaces relevant operational info from Firestore.
- **Communicates via**: Subscribes to `nlu-output`, publishes answers to `response-output`.

### 7. Orchestrator Agent (optional, for complex flows)
- **Role**: Coordinates multi-step workflows, tracks agent state, and manages conversation context.
- **Communicates via**: Subscribes/multicasts as needed to coordinate agents.

---

## Agent Communication Patterns (via GCP Pub/Sub)

- Agents are deployed as independent serverless Cloud Functions, each subscribing to one or more Pub/Sub topics.
- All inter-agent communication occurs via Pub/Sub messages: decoupling compute, improving reliability, and scaling effortlessly.
- Message payloads must not exceed Pub/Sub limits (~10MB/message, recommend <256KB for latency).

### Example Topics
- `user-input`: Transcribed text from Voice Interface Agent
- `nlu-output`: Parsed intents/entities from NLU Agent
- `events`: Scheduling and operational notifications
- `billing-events`: Payment/invoice-related events
- `response-output`: Final responses to return to the user (for speech synthesis or text reply)

---

## Message Routing and Processing

- Each agent subscribes to relevant topics and publishes results downstream.
- Pub/Sub topics can be filtered for event-type or user-session, reducing unnecessary invocations.
- Dead-letter topics can be configured for failed message processing.

---

## Data Persistence

- All agents use Firestore for storing operational state, knowledge base documents, history, and agent metadata.
- Firestore is schema-flexible and serverless, supporting high availability and scalability.

---

## High-Level Data Flow Example
1. User calls: Voice Interface Agent transcribes and publishes to `user-input`.
2. NLU Agent reads `user-input`, extracts intent (e.g., schedule appointment), and publishes to `nlu-output`.
3. Scheduling Agent reads `nlu-output`, updates Firestore and Google Calendar, then publishes confirmation to `events`.
4. Notification Agent reads `events`, sends SMS/email via Twilio.
5. Knowledge Base Agent responds to FAQ intents (from `nlu-output`) by publishing to `response-output`.

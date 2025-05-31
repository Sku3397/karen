# High-Level System Architecture

## Overview
The AI Handyman Secretary Assistant utilizes a serverless, event-driven architecture. Agents communicate via Pub/Sub, persist data in Firestore, and connect to external APIs for scheduling, payments, and messaging.

## Components
- **Serverless Agent Functions**: Each agent is a Google Cloud Function triggered by HTTP or Pub/Sub events.
- **Pub/Sub**: Facilitates multi-agent message exchange within size/latency limits.
- **Firestore (NoSQL)**: Stores client history, handyman procedures, pricing, FAQs, and agent states. Designed for high availability and scalability.
- **Third-party APIs**:
  - *Google Calendar*: Scheduling
  - *Stripe*: Payments
  - *Twilio*: Messaging/voice
- **GCP Speech-to-Text**: Voice processing for user interactions
- **CI/CD**: GitHub Actions for automated testing and deployment
- **Backups**: Automated Firestore and config backups

## Data Flow
1. User request triggers an agent via HTTP or Pub/Sub.
2. Agent processes input, accesses Firestore, and may invoke third-party APIs.
3. Results routed back to the user or further agents as needed.

## Security & Compliance
- Service Account IAM roles scoped to least privilege
- Secure management of API keys and secrets (GCP Secret Manager)
- Logging and monitoring via GCP Cloud Logging

---
**See `iac/main.tf` for initial resource provisioning.**

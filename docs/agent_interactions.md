# Agent Interactions

## Primary Agents and Responsibilities

- **Secretary Agent**
  - Entry point for user requests
  - Validates input, determines task type
  - Publishes task messages to Pub/Sub topics
  - Handles scheduling/conflict resolution

- **Handyman Agent(s)**
  - Subscribes to relevant task topics
  - Simulates task assignment/execution
  - Publishes status updates and completion events

- **Billing Agent**
  - Listens for completed tasks
  - Initiates billing workflow (Stripe/PayPal API calls)
  - Publishes payment status

- **Notification Agent**
  - Subscribes to notification events (e.g., task assigned, completed, payment received)
  - Sends SMS/voice notifications via Twilio

- **Knowledge Base Agent**
  - Handles FAQ/KB requests
  - Fetches data from Firestore

## Interaction Patterns

1. **Task Initiation**
   - User submits request (UI → API Gateway → Secretary Agent)
   - Secretary Agent publishes a `task.create` event to Pub/Sub

2. **Task Assignment**
   - Handyman Agent listens for `task.create`
   - Accepts/declines based on simulated availability, updates state

3. **State Updates**
   - Agents publish status (`task.in_progress`, `task.completed`, `task.failed`) to Pub/Sub
   - Other agents (Secretary, Billing, Notification) subscribe to relevant topics

4. **Billing & Notification**
   - Billing Agent triggers on `task.completed`
   - After billing, Notification Agent notifies user

5. **Conflict/Concurrency Handling**
   - Secretary Agent checks Firestore for conflicts before assigning tasks
   - Pub/Sub ensures parallel execution and event-driven updates

6. **External API Rate Limits**
   - Agents implement retry/backoff for API calls
   - Throttling logic to respect third-party limits

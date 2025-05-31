# Agent Communication Flow (Pub/Sub)

## Pub/Sub Topics Design
- `task.create` – New task requests
- `task.status` – Updates on task state (in progress, completed, failed)
- `task.billing` – Billing events
- `notification.events` – Notification triggers
- `faq.request` / `faq.response` – Knowledge base queries

## Message Flow Example

1. **User creates a new handyman request**
   - Secretary Agent validates and publishes to `task.create`
2. **Handyman Agent picks up task**
   - Updates status via `task.status`
3. **Secretary Agent monitors status, handles rescheduling/conflicts**
4. **Upon completion, Billing Agent triggered by `task.status:completed`**
   - Initiates billing, updates via `task.billing`
5. **Notification Agent monitors `notification.events` for user updates**

## Concurrency & Conflict Resolution
- Secretary Agent maintains assignment table in Firestore
- Before assigning, checks for conflicts (overlaps, unavailability)
- Pub/Sub ensures agents operate asynchronously, avoiding deadlocks
- Firestore used for distributed locks/state where necessary

## Security Considerations
- All Pub/Sub topics secured with IAM
- Agent authentication/authorization enforced via service accounts
- Sensitive data (billing, user info) encrypted at rest and in transit

# Task Manager & Dependency Tracker - Firestore Schema

**Note:** The Task Manager system and its associated Firestore integration are **currently not active or fully implemented** in the main application flow. The necessary `firestore_models` dependency and related code have been temporarily commented out. This document describes the **intended/planned Firestore schema** for this functionality.

## Planned Collection: `tasks`

Each task document in this planned collection would contain fields such as:
- **id**: (str) Firestore document ID (auto-generated by Firestore).
- **title**: (str) A concise name or summary for the task.
- **description**: (str) A more detailed description of the work to be done.
- **status**: (str) The current state of the task, e.g., one of: `pending`, `in_progress`, `blocked`, `completed`, `failed`, `cancelled`.
- **assigned_to**: (str | null) Identifier for the handyman, resource, or agent assigned to the task (e.g., user ID, simulated agent ID).
- **priority**: (str | int) Task priority, e.g., `high`, `medium`, `low`, or a numeric value.
- **dependencies**: (array of str) A list of other task IDs that this task depends on (i.e., must be completed before this task can start or be completed).
- **parent_task_id**: (str | null) If this is a sub-task, the ID of its parent task.
- **sub_tasks**: (array of str) If this is a parent task, a list of its sub-task IDs.
- **due_date**: (timestamp | null) The target completion date for the task.
- **estimated_effort**: (str | float | null) Estimated time or effort required (e.g., "2 hours", 4.5).
- **actual_effort**: (str | float | null) Actual time or effort spent.
- **created_at**: (timestamp) Timestamp of when the task was created.
- **updated_at**: (timestamp) Timestamp of the last modification to the task.
- **completed_at**: (timestamp | null) Timestamp of when the task was completed.
- **metadata**: (object) An optional field for any other relevant information, such as client details, location, specific requirements, or custom fields.
  - Example: `{"client_name": "John Doe", "address": "123 Main St", "contact_phone": "555-1212"}`
- **history_log**: (array of objects) An audit trail of changes to the task.
  - Example entry: `{"timestamp": <timestamp>, "user_id": "system", "action": "status_changed", "from": "pending", "to": "in_progress"}`

## Example Planned Document
```json
{
  "title": "Install New Kitchen Faucet",
  "description": "Client requested replacement and installation of a new Moen kitchen faucet (model #XYZ). Old faucet to be removed and disposed of.",
  "status": "pending",
  "assigned_to": "handyman_agent_123",
  "priority": "high",
  "dependencies": ["task_abc_acquire_faucet"],
  "parent_task_id": null,
  "sub_tasks": [],
  "due_date": "2025-07-15T17:00:00Z",
  "estimated_effort": "2 hours",
  "created_at": "2025-07-10T10:00:00Z",
  "updated_at": "2025-07-10T10:00:00Z",
  "completed_at": null,
  "metadata": {
    "client_id": "client_789",
    "property_address": "456 Oak Avenue, Anytown, USA",
    "faucet_model_supplied_by_client": true
  },
  "history_log": [
    {"timestamp": "2025-07-10T10:00:00Z", "user_id": "system_generated", "action": "created"}
  ]
}
```

## Notes on Planned Schema
- Tasks could represent both parent-level work orders and granular sub-tasks.
- Dependency management would be handled by referencing other task IDs within the `dependencies` array.
- Status transitions would need to account for dependencies to avoid logical deadlocks (e.g., a task cannot start if its dependencies are not met).
- Firestore security rules would be crucial for implementing role-based access control (RBAC) to ensure that only authorized users/agents can create, read, update, or delete tasks.
- The schema is designed to be flexible using the `metadata` field for custom attributes and `history_log` for auditing.

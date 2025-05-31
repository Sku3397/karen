# Task Manager & Dependency Tracker - Firestore Schema

## Collection: tasks

Each task document contains:
- **id**: (str) Firestore document ID
- **title**: (str) Task name
- **description**: (str)
- **status**: (str) One of: pending, in_progress, blocked, completed, failed
- **assigned_agent_id**: (str|null) Simulated handyman agent assigned
- **dependencies**: (array of str) Task IDs this task depends on
- **created_at**: (timestamp)
- **updated_at**: (timestamp)
- **metadata**: (object) Optional extra info

## Example Document
```
{
  "title": "Install New Faucet",
  "description": "Replace and install new kitchen faucet",
  "status": "pending",
  "assigned_agent_id": "agent_123",
  "dependencies": ["task_abc", "task_xyz"],
  "created_at": <timestamp>,
  "updated_at": <timestamp>,
  "metadata": {
    "priority": "high"
  }
}
```

## Notes
- Tasks can represent both parent (project) and subtasks.
- Dependency management is handled by referencing other task IDs.
- Status transitions must account for dependencies to avoid deadlocks.
- Use Firestore security rules for role-based access control.

# Task Manager Agent Documentation

**Note:** The Task Manager Agent and its associated Firestore integration are **currently not active or fully implemented** in the main application flow. The necessary `firestore_models` dependency and related code in `src/task_manager_agent.py` (or `src/task_manager.py`) have been temporarily commented out to resolve startup issues. This document describes the **intended/planned functionality** for this agent.

## Overview
The Task Manager Agent is designed to handle work order lifecycle operations including creation, assignment, priority/status management, resource allocation, and evidence verification. It would integrate with Firestore for persistence and is envisioned for Google Cloud deployment.

See the [API Design](api_design.md) for a full list of planned endpoints and security requirements.

## Planned Endpoints (Illustrative)

- `POST /tasks/create`: Create a new work order
- `POST /tasks/assign`: Assign a user to a task
- `POST /tasks/status`: Update task status/priority
- `POST /tasks/resource`: Allocate resources to a task
- `POST /tasks/evidence`: Verify and attach evidence to a task

## Planned Firestore Data Model (`tasks` collection)
- `details`: dict (task details/description)
- `priority`: str (e.g., "high", "medium", "low")
- `status`: str (e.g., "todo", "in_progress", "completed")
- `assignments`: list of assignment objects (e.g., user ID, role)
- `resources`: list of resource objects (e.g., materials, equipment)
- `evidence`: list of evidence records (e.g., photo URLs, notes)
- `history`: list of change events (audit trail)
- `created_at`, `updated_at`: ISO8601 timestamps

## Planned Authentication & Security
- All endpoints would require JWT authentication and RBAC (see [Authentication](authentication.md) and [Security](security.md)).
- Input validation would be enforced via Pydantic schemas.
- See [Security and Validation](security_and_validation.md) for error handling and best practices.

## Notes on Planned Functionality
- Firestore eventual consistency would need to be considered for real-time reads immediately after writes.
- All planned endpoints would expect JSON payloads and return status information.

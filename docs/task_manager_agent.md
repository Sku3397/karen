# Task Manager Agent Documentation

## Overview
The Task Manager Agent handles work order lifecycle operations including creation, assignment, priority/status management, resource allocation, and evidence verification. It integrates with Firestore for persistence and is designed for Google Cloud deployment.

See the [API Design](api_design.md) for a full list of endpoints and security requirements.

## Endpoints

- `POST /tasks/create`: Create a new work order
- `POST /tasks/assign`: Assign a user to a task
- `POST /tasks/status`: Update task status/priority
- `POST /tasks/resource`: Allocate resources to a task
- `POST /tasks/evidence`: Verify and attach evidence to a task

## Firestore Data Model (`tasks` collection)
- `details`: dict (task details/description)
- `priority`: str (e.g., "high", "medium", "low")
- `status`: str
- `assignments`: list of assignment objects
- `resources`: list of resource objects
- `evidence`: list of evidence records
- `history`: list of change events
- `created_at`, `updated_at`: ISO8601 timestamps

## Authentication & Security
- All endpoints require JWT authentication and RBAC (see [Authentication](authentication.md) and [Security](security.md)).
- Input validation is enforced via Pydantic schemas.
- See [Security and Validation](security_and_validation.md) for error handling and best practices.

## Notes
- Firestore eventual consistency may affect real-time reads immediately after writes.
- All endpoints expect JSON payloads and return status info.

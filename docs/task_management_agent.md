# Task Management Agent

**Note:** The Task Management Agent and its associated Firestore integration are **currently not active or fully implemented** in the main application flow. The necessary `firestore_models` dependency and related code in `src/task_manager_agent.py` (or `src/task_manager.py`) have been temporarily commented out to resolve startup issues. This document describes the **intended/planned functionality** for this agent.

## Planned Overview
The Task Management Agent is envisioned to be responsible for:
- Breaking down client requests into actionable steps.
- Assigning tasks/subtasks to handyman resources (simulated or real).
- Tracking progress and status of all tasks.

## Planned Main Components
- **FirestoreTaskInterface**: An abstraction layer for Firestore task storage operations.
- **TaskManagementAgent**: Core agent logic for task creation, breakdown, assignment, and progress tracking.
- **REST API**: FastAPI endpoints for agent communication, intended for use by other agents or an orchestrator.

## Planned API Endpoints (Illustrative)
- `POST /tasks/` : Create and potentially break down a task.
- `POST /tasks/{task_id}/assign/` : Assign a task to a handyman resource.
- `POST /tasks/{task_id}/status/` : Update the status of a task.
- `GET /tasks/{parent_task_id}/progress/` : Get progress of a parent task and its sub-tasks/steps.

## Planned Firestore Document Structure
Each task would be a document in Firestore. Parent tasks might have a `steps` array with subtask IDs, and subtasks would have a `parent_task_id` to link them.

## Notes on Planned Functionality
- Assignments to handyman resources would initially be simulated or placeholder.
- Pub/Sub hooks might be implemented for multi-agent notifications if this architecture is pursued.

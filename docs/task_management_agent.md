# Task Management Agent

## Overview
The Task Management Agent is responsible for:
- Breaking down client requests into actionable steps
- Assigning tasks/subtasks to handyman resources (simulated)
- Tracking progress and status of all tasks

## Main Components
- **FirestoreTaskInterface**: Abstraction for Firestore task storage operations
- **TaskManagementAgent**: Core agent logic for creation, breakdown, assignment, progress tracking
- **REST API**: FastAPI endpoints for agent communication, usable by other agents or orchestrators

## API Endpoints
- `POST /tasks/` : Create and breakdown task
- `POST /tasks/{task_id}/assign/` : Assign a task to a handyman resource
- `POST /tasks/{task_id}/status/` : Update the status of a task
- `GET /tasks/{parent_task_id}/progress/` : Get progress of a parent task & its steps

## Firestore Document Structure
Each task is a document. Parent task has `steps` array with subtask IDs; subtasks have `parent_task_id`.

## Notes
- All assignments are simulated
- Pub/Sub hooks to be implemented for multi-agent notifications if needed

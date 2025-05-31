# AI Handyman Secretary Assistant API Design

## Overview
This document outlines the RESTful API design for the AI Handyman Secretary Assistant backend, supporting the web app and automation agents. It includes endpoint descriptions, authentication/security requirements, and references to agent-specific documentation.

---

## API Endpoints

### Users
- `POST /users` — Create a new user
- `GET /users/{userId}` — Retrieve a user's profile
- `PUT /users/{userId}` — Update a user's profile
- `DELETE /users/{userId}` — Delete a user

### Tasks
- `POST /tasks` — Create a new task
- `GET /tasks/{taskId}` — Retrieve task details
- `PUT /tasks/{taskId}` — Update a task
- `DELETE /tasks/{taskId}` — Delete a task
- `POST /tasks/create` — Create a new work order (see [Task Manager Agent](task_manager_agent.md))
- `POST /tasks/assign` — Assign a user to a task
- `POST /tasks/status` — Update task status/priority
- `POST /tasks/resource` — Allocate resources to a task
- `POST /tasks/evidence` — Attach evidence to a task

### Appointments
- `POST /appointments` — Schedule a new appointment
- `GET /appointments` — List all appointments
- `PUT /appointments/{appointmentId}` — Update an appointment
- `DELETE /appointments/{appointmentId}` — Cancel an appointment
- `POST /schedule` — Schedule an event (see [Scheduling Agent](api/scheduling_routes.py))
- `GET /events` — List calendar events

### Communications
- `POST /communications` — Record a new communication log
- `GET /communications` — List all communication logs

### Knowledge Base
- `POST /knowledge` — Add a new knowledge entry
- `GET /knowledge` — List all knowledge entries
- `/knowledge-base/repair-knowledge` — Query technical repair articles (see [Knowledge Base Agent](knowledge_base_agent.md))
- `/knowledge-base/recommend-tools-materials` — Get tool/material recommendations
- `/knowledge-base/estimate-cost` — Estimate cost for a task
- `/knowledge-base/safety-guidelines` — Safety guidelines for a repair task
- `/knowledge-base/learning-resources` — Learning resources for a topic

### Billing
- `POST /billing/invoices` — Create a new invoice
- `GET /billing/invoices/{invoiceId}` — Retrieve an invoice
- `PUT /billing/invoices/{invoiceId}` — Update an invoice
- `DELETE /billing/invoices/{invoiceId}` — Delete an invoice
- `POST /invoices` — Create a Stripe invoice (see [Billing Agent](billing_agent.md))
- `GET /invoices/<invoice_id>` — Retrieve invoice details
- `GET /payments` — List recent payments
- `POST /expenses` — Add a new expense
- `POST /quotes` — Create a new quote
- `GET /reports/financial` — Generate a financial summary

### Inventory
- `POST /inventory/items` — Add a new inventory item
- `GET /inventory/items` — List all inventory items
- `PUT /inventory/items/{itemId}` — Update an item's details
- `DELETE /inventory/items/{itemId}` — Remove an item from inventory

### Other
- `POST /email/process` — Process an email (requires role: admin/agent)
- `POST /voice/process` — Process a voice transcript (requires role: admin/agent)
- `POST /calendar/event` — Create a calendar event (requires role: admin/agent)

---

## Authentication & Security
- All sensitive endpoints require JWT authentication (see [Authentication](authentication.md)).
- OAuth 2.0 login via Google Identity; JWTs issued for session management (see [Security Framework](security.md)).
- Role-Based Access Control (RBAC) enforced via FastAPI middleware; see [Security and Validation](security_and_validation.md).
- Use HTTPS/TLS for all external communication.

## Input Validation & Error Handling
- All inputs validated using Pydantic schemas.
- Common errors: 400 (bad request), 401 (unauthorized), 403 (forbidden), 404 (not found), 500 (server error).
- See [Security and Validation](security_and_validation.md) for details.

## Agent-Specific Documentation
- [Task Manager Agent](task_manager_agent.md)
- [Knowledge Base Agent](knowledge_base_agent.md)
- [Billing Agent](billing_agent.md)

---

## Notes
- Endpoints may be extended or versioned as the platform evolves.
- For full data models and request/response schemas, see agent docs and backend codebase.
- Endpoints requiring role-based access are marked accordingly.
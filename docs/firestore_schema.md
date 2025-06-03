# Firestore Schema Design for AI Handyman Secretary Assistant Project

**Note:** The Firestore database integration is **currently not active or fully implemented** in the main application flow. The necessary `firestore_models` dependency and related code have been temporarily commented out. This document describes a **conceptual/planned Firestore schema** that would support a more comprehensive version of the application. The current application primarily uses a SQLite database (`celerybeat-schedule.sqlite3`) for Celery Beat scheduling and does not use Firestore for general application data storage.

## Planned Collections

This section outlines the collections and their intended fields if Firestore were to be fully integrated.

### Users
Represents users of the system (e.g., admin, handyman staff, potentially clients if they have accounts).
- Document ID: Firestore auto-generated ID or custom ID (e.g., email address).
- Fields:
  - `email`: String (Unique identifier, could be the document ID)
  - `name`: String (User's full name)
  - `role`: String (e.g., `admin`, `handyman`, `client_contact`)
  - `phone_number`: String (Optional)
  - `preferences`: Map (User-specific settings, e.g., notification preferences)
  - `createdAt`: Timestamp
  - `updatedAt`: Timestamp

### Tasks
(Corresponds to the schema detailed in `task_manager_schema.md`)
- Document ID: Firestore auto-generated ID.
- Fields:
  - `title`: String
  - `description`: String
  - `status`: String (e.g., `pending`, `in_progress`, `completed`, `blocked`)
  - `priority`: String (e.g., `high`, `medium`, `low`)
  - `assignedTo_user_id`: Reference -> `Users` collection (ID of the assigned handyman/user)
  - `client_id`: String (Could be a reference to a `Clients` collection or a simple ID/email)
  - `related_communication_id`: Reference -> `Communications` collection (Link to the initiating email/communication)
  - `due_date`: Timestamp
  - `estimated_effort`: String (e.g., "2 hours")
  - `actual_effort`: String
  - `location_address`: String
  - `location_coordinates`: GeoPoint (For mapping)
  - `attachments`: Array of Maps (e.g., `[{name: "photo.jpg", url: "..."}]`)
  - `notes`: Array of Strings or Maps (e.g., `[{timestamp: <ts>, note: "...", user: "..."}]`)
  - `createdAt`: Timestamp
  - `updatedAt`: Timestamp

### Appointments
(Could also be managed primarily via Google Calendar, with a sync to Firestore if needed for offline access or additional metadata).
- Document ID: Firestore auto-generated ID or Google Calendar Event ID.
- Fields:
  - `google_calendar_event_id`: String (If synced from Google Calendar)
  - `title`: String (e.g., "Estimate for fence repair at 123 Main St")
  - `description`: String (Details of the appointment)
  - `attendees_user_ids`: Array of References -> `Users` collection (e.g., assigned handyman, client contact if they are a user)
  - `client_contact_info`: Map (If client is not a system user, e.g., `{"name": "Jane Doe", "email": "jane@example.com", "phone": "555-1234"}`)
  - `start_time`: Timestamp
  - `end_time`: Timestamp
  - `location`: String (Address)
  - `status`: String (e.g., `scheduled`, `confirmed`, `completed`, `cancelled`)
  - `related_task_id`: Reference -> `Tasks` collection (If this appointment is for a specific task)
  - `createdAt`: Timestamp
  - `updatedAt`: Timestamp

### Communications
Records of communications (emails, SMS, etc.) if a persistent log beyond the email server is desired.
- Document ID: Firestore auto-generated ID or original email Message-ID.
- Fields:
  - `type`: String (e.g., `email_inbound`, `email_outbound`, `sms_outbound`)
  - `subject`: String (For emails)
  - `body_snippet`: String (Truncated content for quick view)
  - `full_content_ref`: String (Potentially a reference to a larger text object in Cloud Storage if bodies are very large)
  - `from_address`: String
  - `to_address`: String (or array of strings for multiple recipients)
  - `status`: String (e.g., `received`, `processed`, `replied`, `failed_to_send`)
  - `llm_conversation_history`: Array of Maps (If tracking multi-turn LLM interactions for this communication thread)
  - `related_task_id`: Reference -> `Tasks` (If this communication resulted in or relates to a task)
  - `timestamp`: Timestamp (Time of original communication)
  - `createdAt`: Timestamp (Time record created in Firestore)
  - `updatedAt`: Timestamp

### KnowledgeBase
(For storing structured information, FAQs, troubleshooting guides, pricing info accessible by the LLM or agents).
- Document ID: Firestore auto-generated ID or custom slug.
- Fields:
  - `title`: String
  - `content`: String (Markdown or structured text)
  - `category`: String (e.g., `pricing`, `service_details`, `troubleshooting`)
  - `keywords`: Array of Strings (For searching)
  - `last_validated_by`: String (User ID)
  - `last_validated_at`: Timestamp
  - `createdAt`: Timestamp
  - `updatedAt`: Timestamp

### Billing (Future Scope)
- Document ID: Firestore auto-generated ID.
- Fields:
  - `task_id` or `appointment_id`: Reference -> `Tasks` or `Appointments`
  - `client_id`: Reference -> `Users` (or client identifier)
  - `invoice_details`: Map (Line items, quantities, rates, total)
  - `amount_due`: Number
  - `amount_paid`: Number
  - `status`: String (e.g., `pending`, `paid`, `overdue`, `void`)
  - `payment_method`: String
  - `transaction_id`: String (From payment gateway like Stripe)
  - `invoice_sent_at`: Timestamp
  - `paid_at`: Timestamp
  - `createdAt`: Timestamp
  - `updatedAt`: Timestamp

### Inventory (Future Scope)
- Document ID: Firestore auto-generated ID or SKU.
- Fields:
  - `item_name`: String
  - `description`: String
  - `sku`: String (Stock Keeping Unit)
  - `category`: String
  - `quantity_on_hand`: Number
  - `unit_price`: Number
  - `supplier_info`: Map
  - `last_stock_update`: Timestamp
  - `createdAt`: Timestamp
  - `updatedAt`: Timestamp

## General Notes on Planned Schema
- **References:** Firestore references (`db.collection('collection_name').doc('document_id')`) would be used to link documents across collections (e.g., linking a task to an assigned user).
- **Timestamps:** `createdAt` and `updatedAt` fields would be managed by the application or Firestore server timestamps to track document lifecycle.
- **Security Rules:** Firestore security rules would be essential to control access to these collections and documents based on user roles and ownership.
- **Scalability & Queries:** Schema design would need to consider Firestore's query capabilities and limitations for efficient data retrieval at scale.
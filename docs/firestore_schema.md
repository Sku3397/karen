# Firestore Schema Design for AI Handyman Secretary Assistant Project

## Collections

### Users
- Document ID: Firestore auto-generated ID
- Fields:
  - `email`: String
  - `name`: String
  - `role`: String
  - `createdAt`: Timestamp
  - `updatedAt`: Timestamp

### Tasks
- Document ID: Firestore auto-generated ID
- Fields:
  - `title`: String
  - `description`: String
  - `status`: String
  - `assignedTo`: Reference -> Users
  - `dueDate`: Timestamp
  - `createdAt`: Timestamp
  - `updatedAt`: Timestamp

### Appointments
- Document ID: Firestore auto-generated ID
- Fields:
  - `title`: String
  - `description`: String
  - `with`: Reference -> Users
  - `dateTime`: Timestamp
  - `createdAt`: Timestamp
  - `updatedAt`: Timestamp

### Communications
- Document ID: Firestore auto-generated ID
- Fields:
  - `type`: String
  - `content`: String
  - `from`: Reference -> Users
  - `to`: Reference -> Users
  - `createdAt`: Timestamp
  - `updatedAt`: Timestamp

### Knowledge
- Document ID: Firestore auto-generated ID
- Fields:
  - `title`: String
  - `content`: String
  - `category`: String
  - `createdAt`: Timestamp
  - `updatedAt`: Timestamp

### Billing
- Document ID: Firestore auto-generated ID
- Fields:
  - `userId`: Reference -> Users
  - `details`: Map
  - `amount`: Number
  - `status`: String
  - `createdAt`: Timestamp
  - `updatedAt`: Timestamp

### Inventory
- Document ID: Firestore auto-generated ID
- Fields:
  - `itemName`: String
  - `quantity`: Number
  - `status`: String
  - `createdAt`: Timestamp
  - `updatedAt`: Timestamp

## Notes
- References are used to link documents across collections.
- Timestamp fields are automatically managed by the application to track creation and update times.
# Billing Agent with Stripe Integration

## Overview
The Billing Agent provides:
- Invoice generation via Stripe
- Payment tracking via Stripe
- Expense management
- Quote creation
- Financial reporting (combining Stripe and internal data)

See the [API Design](api_design.md) for a full list of endpoints and security requirements.

## API Endpoints
- `POST /invoices`: Create a Stripe invoice
- `GET /invoices/<invoice_id>`: Retrieve invoice details
- `GET /payments`: List recent payments
- `POST /expenses`: Add a new expense
- `POST /quotes`: Create a new quote
- `GET /reports/financial`: Generate a financial summary

## Authentication & Security
- All endpoints require JWT authentication and RBAC (see [Authentication](authentication.md) and [Security](security.md)).
- Input validation is enforced via Pydantic schemas.
- See [Security and Validation](security_and_validation.md) for error handling and best practices.

## Implementation Notes
- Stripe API key required in environment (`STRIPE_API_KEY`)
- Replace in-memory stores with Firestore for production.
- See `src/billing_agent.py` for endpoint details.

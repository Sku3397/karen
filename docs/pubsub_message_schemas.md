# Pub/Sub Message Schemas

Define standard message schemas for robust inter-agent communication and error handling. All messages are JSON objects with required and optional fields.

## 1. user-input
```json
{
  "session_id": "string",
  "user_id": "string",
  "timestamp": "ISO8601 string",
  "transcript": "string",
  "source": "voice|sms|web"
}
```

## 2. nlu-output
```json
{
  "session_id": "string",
  "user_id": "string",
  "timestamp": "ISO8601 string",
  "intent": "string",
  "entities": { "key": "value", ... },
  "original_text": "string"
}
```

## 3. events
```json
{
  "session_id": "string",
  "event_type": "schedule_created|schedule_updated|cancelled|reminder|custom",
  "details": { ... },
  "timestamp": "ISO8601 string"
}
```

## 4. billing-events
```json
{
  "session_id": "string",
  "user_id": "string",
  "event_type": "invoice_created|payment_received|payment_failed",
  "amount": "number",
  "details": { ... },
  "timestamp": "ISO8601 string"
}
```

## 5. response-output
```json
{
  "session_id": "string",
  "response_text": "string",
  "response_type": "text|audio|card|error",
  "timestamp": "ISO8601 string"
}
```

## Notes
- All messages must fit within GCP Pub/Sub size and field limits.
- Use `session_id` for correlating multi-agent workflows.
- All timestamps should be in ISO8601 format.

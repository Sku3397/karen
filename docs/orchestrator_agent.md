# Orchestrator Agent

The Orchestrator Agent is the central workflow coordinator for the AI Handyman Secretary Assistant project.

## Responsibilities
- Subscribes to a dedicated Pub/Sub topic to receive workflow and agent messages.
- Persists workflow and agent state to Google Cloud Firestore.
- Routes commands to appropriate agent topics via Pub/Sub.
- Handles multi-agent workflow coordination and message passing.

## Configuration
- Pub/Sub topics are defined in `src/config.py`.
- Firestore collections used for workflow and agent state.

## Running
- Ensure GCP credentials are configured.
- Install dependencies: `pip install google-cloud-pubsub google-cloud-firestore`
- Start the orchestrator: `python src/orchestrator_agent.py`

## Message Envelope Example
```json
{
  "workflow_id": "abc123",
  "agent": "scheduling",
  "command": "create_appointment",
  "payload": { "client_id": "xyz", "datetime": "2024-06-01T10:00:00Z" }
}
```

## Extending
- Add new agent topics to `AGENT_TOPICS` in `src/config.py`.
- Enhance orchestration logic in `_process_message` for more complex workflows.

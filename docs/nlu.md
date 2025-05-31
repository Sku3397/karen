# Natural Language Understanding (NLU)

## Overview
This module provides basic and advanced NLU capabilities for client communications:
- **Basic NLU:** Rule-based extraction of intents and entities from client text.
- **Dialogflow Integration (optional):** Uses Google Dialogflow for advanced intent/parameter parsing (requires GCP setup).

## Usage

### Basic NLU
```
from nlu import NLU
nlu = NLU()
result = nlu.parse("I want to book an appointment for plumbing on Monday at 10am")
# result: {'intent': 'book_appointment', 'entities': {'service': ['plumbing'], 'date': ['on Monday'], 'time': ['at 10am']}}
```

### Dialogflow NLU (optional)
1. Install dependencies: `pip install google-cloud-dialogflow`
2. Set up GCP and obtain credentials and project ID.
3. Set environment variable `USE_DIALOGFLOW=true` and configure `dialogflow_project_id` in `config/nlu_config.yaml`.
4. Usage:
```
from nlu import NLU
nlu = NLU(dialogflow_project_id="your-project-id", session_id="unique-session-id")
result = nlu.parse("Cancel my booking for Friday")
# Uses Dialogflow for intent/entity extraction
```

## Configuration
- See `config/nlu_config.yaml` for toggling Dialogflow and setting project info.

## Notes
- All inputs are assumed to be in English (configure language code if needed).
- Dialogflow usage may incur costs and API limits.

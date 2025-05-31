# Dialogflow NLU integration (optional, requires setup)
import os
from typing import Dict

try:
    from google.cloud import dialogflow_v2 as dialogflow
except ImportError:
    dialogflow = None

class DialogflowNLU:
    def __init__(self, project_id: str, session_id: str, language_code: str = 'en'):
        if not dialogflow:
            raise ImportError('google-cloud-dialogflow not installed.')
        self.project_id = project_id
        self.session_id = session_id
        self.language_code = language_code
        self.session_client = dialogflow.SessionsClient()
        self.session = self.session_client.session_path(project_id, session_id)

    def parse(self, text: str) -> Dict:
        text_input = dialogflow.TextInput(text=text, language_code=self.language_code)
        query_input = dialogflow.QueryInput(text=text_input)
        response = self.session_client.detect_intent(request={
            "session": self.session,
            "query_input": query_input
        })
        intent = response.query_result.intent.display_name
        entities = {ent.name: ent.value for ent in response.query_result.parameters.fields.values() if ent}
        return {
            'intent': intent,
            'entities': entities
        }

# NLU module loader and unified interface
import os
from .basic_nlu import parse as basic_parse

try:
    from .dialogflow_nlu import DialogflowNLU
except ImportError:
    DialogflowNLU = None

USE_DIALOGFLOW = os.environ.get('USE_DIALOGFLOW', 'false').lower() == 'true'

class NLU:
    def __init__(self, dialogflow_project_id=None, session_id=None, language_code='en'):
        self.use_dialogflow = USE_DIALOGFLOW and DialogflowNLU is not None and dialogflow_project_id
        if self.use_dialogflow:
            self.df_nlu = DialogflowNLU(dialogflow_project_id, session_id, language_code)
        else:
            self.df_nlu = None

    def parse(self, text: str):
        if self.use_dialogflow and self.df_nlu:
            return self.df_nlu.parse(text)
        return basic_parse(text)

# Basic NLU module: Rule-based intent & entity extraction
import re
from typing import Dict, List

# Intent patterns (expandable)
INTENT_PATTERNS = {
    'book_appointment': [r'book.*appointment', r'schedule.*repair', r'need.*handyman'],
    'cancel_appointment': [r'cancel.*appointment', r'delete.*booking'],
    'inquire_price': [r'(what.*price|how much|cost).*'],
    'faq': [r'(hours|location|open.*time|service.*offer)']
}

ENTITY_PATTERNS = {
    'date': r'(on\s+\w+\s+\d{1,2})',
    'time': r'(at\s+\d{1,2}(:\d{2})?\s*(am|pm)?)',
    'service': r'(plumbing|electrical|painting|cleaning|hvac|repair|install)'
}

def extract_intent(text: str) -> str:
    text = text.lower()
    for intent, patterns in INTENT_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, text):
                return intent
    return 'unknown'

def extract_entities(text: str) -> Dict[str, List[str]]:
    entities = {}
    for ent, pat in ENTITY_PATTERNS.items():
        matches = re.findall(pat, text, re.IGNORECASE)
        if matches:
            entities[ent] = [m[0] if isinstance(m, tuple) else m for m in matches]
    return entities

def parse(text: str) -> Dict:
    return {
        'intent': extract_intent(text),
        'entities': extract_entities(text)
    }

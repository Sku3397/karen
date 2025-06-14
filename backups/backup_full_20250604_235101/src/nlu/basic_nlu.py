# Enhanced NLU module with NLP engine integration
import re
import asyncio
from typing import Dict, List, Optional, Union

# Backward compatibility imports
from ..nlp_engine import get_nlp_engine, Intent, NLPResult

# Legacy intent patterns for fallback compatibility
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

# Legacy functions for backward compatibility
def extract_intent(text: str) -> str:
    """Legacy intent extraction - use parse_async for enhanced NLP"""
    text = text.lower()
    for intent, patterns in INTENT_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, text):
                return intent
    return 'unknown'

def extract_entities(text: str) -> Dict[str, List[str]]:
    """Legacy entity extraction - use parse_async for enhanced NLP"""
    entities = {}
    for ent, pat in ENTITY_PATTERNS.items():
        matches = re.findall(pat, text, re.IGNORECASE)
        if matches:
            entities[ent] = [m[0] if isinstance(m, tuple) else m for m in matches]
    return entities

def parse(text: str) -> Dict:
    """Legacy parsing function - use parse_async for enhanced NLP"""
    return {
        'intent': extract_intent(text),
        'entities': extract_entities(text)
    }

# Enhanced NLP functions
async def parse_async(text: str, context: Optional[Dict] = None, llm_client=None) -> Dict:
    """
    Enhanced async parsing using NLP engine
    
    Args:
        text: Input text to analyze
        context: Optional context for analysis
        llm_client: Optional LLM client for enhanced analysis
        
    Returns:
        Dictionary with enhanced NLP results
    """
    try:
        nlp_engine = get_nlp_engine(llm_client)
        result = await nlp_engine.analyze_text(text, context)
        
        # Convert to legacy format for backward compatibility
        legacy_entities = {}
        for entity in result.entities:
            if entity.type not in legacy_entities:
                legacy_entities[entity.type] = []
            legacy_entities[entity.type].append(entity.value)
        
        return {
            'intent': result.intent.value,
            'entities': legacy_entities,
            'sentiment': result.sentiment.value,
            'priority': result.priority.value,
            'confidence': result.confidence,
            'topics': result.topics,
            'keywords': result.keywords,
            'is_question': result.is_question,
            'is_urgent': result.is_urgent,
            'full_analysis': result.to_dict()
        }
        
    except Exception as e:
        # Fallback to legacy parsing
        return parse(text)

def parse_sync(text: str, context: Optional[Dict] = None, llm_client=None) -> Dict:
    """
    Synchronous wrapper for async parsing
    
    Args:
        text: Input text to analyze
        context: Optional context for analysis
        llm_client: Optional LLM client for enhanced analysis
        
    Returns:
        Dictionary with enhanced NLP results
    """
    try:
        # Try to run async version
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running, create a task instead
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, parse_async(text, context, llm_client))
                    return future.result()
            else:
                return loop.run_until_complete(parse_async(text, context, llm_client))
        except RuntimeError:
            # No event loop available, create new one
            return asyncio.run(parse_async(text, context, llm_client))
    except Exception:
        # Fallback to legacy sync parsing
        return parse(text)

# Intent mapping for backward compatibility
INTENT_MAPPING = {
    'book_appointment': Intent.APPOINTMENT_SCHEDULE.value,
    'cancel_appointment': Intent.APPOINTMENT_CANCEL.value,
    'inquire_price': Intent.QUOTE_REQUEST.value,
    'faq': Intent.GENERAL_INQUIRY.value,
    'unknown': Intent.UNKNOWN.value
}

def map_legacy_intent(legacy_intent: str) -> str:
    """Map legacy intent to new intent system"""
    return INTENT_MAPPING.get(legacy_intent, Intent.GENERAL_INQUIRY.value)

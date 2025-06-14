"""
Enhanced NLP Engine for Karen AI
Provides intelligent natural language processing for SMS/communication features

Combines Gemini LLM capabilities with enhanced rule-based fallbacks
for robust intent classification, entity extraction, and sentiment analysis.
"""

import logging
import re
import json
import asyncio
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class Intent(Enum):
    """Standardized intent types for the handyman business"""
    EMERGENCY = "emergency"
    APPOINTMENT_SCHEDULE = "appointment_schedule"
    APPOINTMENT_CANCEL = "appointment_cancel"
    APPOINTMENT_RESCHEDULE = "appointment_reschedule"
    QUOTE_REQUEST = "quote_request"
    SERVICE_INQUIRY = "service_inquiry"
    GENERAL_INQUIRY = "general_inquiry"
    COMPLAINT = "complaint"
    COMPLIMENT = "compliment"
    PAYMENT_INQUIRY = "payment_inquiry"
    STATUS_CHECK = "status_check"
    GREETING = "greeting"
    GOODBYE = "goodbye"
    UNKNOWN = "unknown"

class Sentiment(Enum):
    """Sentiment classification"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    URGENT = "urgent"

class Priority(Enum):
    """Message priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class Entity:
    """Extracted entity with metadata"""
    type: str
    value: str
    confidence: float
    start_pos: int = 0
    end_pos: int = 0
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class NLPResult:
    """Complete NLP analysis result"""
    text: str
    intent: Intent
    entities: List[Entity]
    sentiment: Sentiment
    priority: Priority
    confidence: float
    topics: List[str]
    keywords: List[str]
    is_question: bool
    is_urgent: bool
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result['intent'] = self.intent.value
        result['sentiment'] = self.sentiment.value
        result['priority'] = self.priority.value
        result['timestamp'] = self.timestamp.isoformat()
        return result

class EnhancedNLPEngine:
    """Enhanced NLP engine with Gemini integration and rule-based fallbacks"""
    
    def __init__(self, llm_client=None):
        """Initialize NLP engine with optional LLM client"""
        self.llm_client = llm_client
        
        # Enhanced keyword patterns for handyman business
        self.intent_patterns = {
            Intent.EMERGENCY: [
                r'\b(emergency|urgent|asap|immediately|right now|help)\b',
                r'\b(flood|flooding|burst pipe|gas leak|electrical fire)\b',
                r'\b(no (power|heat|water))\b',
                r'\b(ceiling (leak|falling))\b',
                r'\b(can\'t (get in|turn off|shut off))\b'
            ],
            Intent.APPOINTMENT_SCHEDULE: [
                r'\b(schedule|book|appointment|when.*available)\b',
                r'\b(come (out|over)|visit|see you)\b',
                r'\b(what time|when can|tomorrow|next week)\b',
                r'\b(free time|available|open)\b'
            ],
            Intent.APPOINTMENT_CANCEL: [
                r'\b(cancel|delete|remove).*appointment\b',
                r'\b(can\'t make it|won\'t be here)\b',
                r'\bneed to cancel\b'
            ],
            Intent.APPOINTMENT_RESCHEDULE: [
                r'\b(reschedule|change.*time|move.*appointment)\b',
                r'\b(different (day|time)|another time)\b'
            ],
            Intent.QUOTE_REQUEST: [
                r'\b(quote|estimate|cost|price|how much)\b',
                r'\b(what.*charge|what.*cost)\b',
                r'\b(budget|pricing|rates)\b'
            ],
            Intent.SERVICE_INQUIRY: [
                r'\b(fix|repair|install|replace|service)\b',
                r'\b(plumb|electric|hvac|paint|carpet|floor)\b',
                r'\b(handyman|maintenance|work)\b'
            ],
            Intent.COMPLAINT: [
                r'\b(unhappy|dissatisfied|problem with|complaint)\b',
                r'\b(not (working|fixed|done right))\b',
                r'\b(terrible|awful|worst)\b'
            ],
            Intent.COMPLIMENT: [
                r'\b(great|excellent|wonderful|amazing|perfect)\b',
                r'\b(thank you|thanks|appreciate)\b',
                r'\b(good (job|work)|well done)\b',
                r'\bthank.*work\b'
            ],
            Intent.PAYMENT_INQUIRY: [
                r'\b(payment|invoice|bill|charge|owe)\b',
                r'\b(credit card|check|cash|venmo|paypal)\b'
            ],
            Intent.STATUS_CHECK: [
                r'\b(status|update|where.*at|how.*going)\b',
                r'\b(still coming|on schedule|finished)\b'
            ],
            Intent.GREETING: [
                r'\b(hello|hi|hey|good (morning|afternoon|evening))\b',
                r'^(hi|hello|hey)[\s,!]*$'
            ],
            Intent.GOODBYE: [
                r'\b(goodbye|bye|see you|have a good)\b',
                r'\b(talk (later|soon))\b'
            ]
        }
        
        # Entity extraction patterns
        self.entity_patterns = {
            'phone_number': r'(\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'address': r'\d+\s+[\w\s]+(?:street|st|avenue|ave|road|rd|drive|dr|lane|ln|court|ct|circle|cir|boulevard|blvd)',
            'time': r'\b(1[0-2]|[1-9])(?::[0-5][0-9])?\s*(?:am|pm|AM|PM)\b',
            'date': r'\b(?:today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday|next week|this week)\b',
            'money': r'\$\d+(?:\.\d{2})?|\b\d+\s*(?:dollars?|bucks?)\b',
            'service_type': r'\b(plumb|electric|hvac|paint|carpet|floor|roof|gutter|fence|deck|door|window|cabinet)\w*\b'
        }
        
        # Urgency indicators
        self.urgency_patterns = [
            r'\b(emergency|urgent|asap|immediately|right now)\b',
            r'\b(flood|leak|no (power|heat|water))\b',
            r'[!]{2,}|\bhelp[!]*\b'
        ]
        
        # Sentiment patterns
        self.positive_patterns = [
            r'\b(great|excellent|wonderful|amazing|perfect|good|nice|thank)\b',
            r'\b(love|like|happy|satisfied|pleased)\b'
        ]
        
        self.negative_patterns = [
            r'\b(terrible|awful|horrible|bad|worst|hate|angry|mad)\b',
            r'\b(unhappy|dissatisfied|disappointed|frustrated)\b'
        ]
        
    async def analyze_text(self, text: str, context: Optional[Dict] = None) -> NLPResult:
        """
        Perform comprehensive NLP analysis on input text
        
        Args:
            text: Input text to analyze
            context: Optional context (conversation history, customer profile, etc.)
            
        Returns:
            NLPResult with complete analysis
        """
        try:
            # Primary analysis using LLM if available
            if self.llm_client:
                llm_result = await self._analyze_with_llm(text, context)
                if llm_result:
                    # Enhance LLM result with rule-based extraction
                    enhanced_result = self._enhance_with_rules(text, llm_result)
                    return enhanced_result
            
            # Fallback to rule-based analysis
            logger.info("Using rule-based NLP analysis as fallback")
            return self._analyze_with_rules(text, context)
            
        except Exception as e:
            logger.error(f"NLP analysis failed: {e}", exc_info=True)
            return self._create_fallback_result(text)
    
    async def _analyze_with_llm(self, text: str, context: Optional[Dict] = None) -> Optional[NLPResult]:
        """Analyze text using Gemini LLM"""
        try:
            prompt = self._build_llm_prompt(text, context)
            
            # Use asyncio.to_thread for synchronous LLM call
            response = await asyncio.to_thread(self.llm_client.generate_text, prompt)
            
            # Parse LLM response
            return self._parse_llm_response(text, response)
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}", exc_info=True)
            return None
    
    def _build_llm_prompt(self, text: str, context: Optional[Dict] = None) -> str:
        """Build prompt for LLM analysis"""
        
        conversation_history = ""
        if context and context.get('conversation_history'):
            history = context['conversation_history'][-3:]  # Last 3 messages
            conversation_history = f"\nConversation History: {history}"
        
        prompt = f"""
Analyze the following customer message for a handyman service business. Provide a JSON response with the following structure:

{{
  "intent": "one of: emergency, appointment_schedule, appointment_cancel, appointment_reschedule, quote_request, service_inquiry, general_inquiry, complaint, compliment, payment_inquiry, status_check, greeting, goodbye, unknown",
  "entities": [
    {{"type": "entity_type", "value": "extracted_value", "confidence": 0.0-1.0}}
  ],
  "sentiment": "positive, negative, neutral, or urgent",
  "priority": "critical, high, medium, or low",
  "confidence": 0.0-1.0,
  "topics": ["main_topic1", "main_topic2"],
  "keywords": ["key1", "key2", "key3"],
  "is_question": true/false,
  "is_urgent": true/false
}}

Customer Message: "{text}"{conversation_history}

Context: This is for a handyman business that handles plumbing, electrical, HVAC, carpentry, painting, and general repairs. Emergency situations should be prioritized.

Analyze the message and respond with ONLY the JSON object:
"""
        return prompt
    
    def _parse_llm_response(self, text: str, response: str) -> Optional[NLPResult]:
        """Parse LLM JSON response into NLPResult"""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                logger.warning(f"No JSON found in LLM response: {response}")
                return None
            
            data = json.loads(json_match.group())
            
            # Convert to NLPResult
            return NLPResult(
                text=text,
                intent=Intent(data.get('intent', 'unknown')),
                entities=[Entity(**e) for e in data.get('entities', [])],
                sentiment=Sentiment(data.get('sentiment', 'neutral')),
                priority=Priority(data.get('priority', 'medium')),
                confidence=float(data.get('confidence', 0.8)),
                topics=data.get('topics', []),
                keywords=data.get('keywords', []),
                is_question=bool(data.get('is_question', False)),
                is_urgent=bool(data.get('is_urgent', False)),
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}. Response: {response}")
            return None
    
    def _analyze_with_rules(self, text: str, context: Optional[Dict] = None) -> NLPResult:
        """Rule-based analysis as fallback"""
        text_lower = text.lower()
        
        # Intent classification
        intent = self._classify_intent_rules(text_lower)
        
        # Entity extraction
        entities = self._extract_entities_rules(text)
        
        # Sentiment analysis
        sentiment = self._classify_sentiment_rules(text_lower)
        
        # Priority assessment
        priority = self._assess_priority_rules(intent, sentiment, text_lower)
        
        # Urgency detection
        is_urgent = self._detect_urgency_rules(text_lower)
        
        # Question detection
        is_question = self._detect_question_rules(text)
        
        # Keywords extraction
        keywords = self._extract_keywords_rules(text_lower)
        
        # Topics (simplified)
        topics = self._extract_topics_rules(text_lower, intent)
        
        return NLPResult(
            text=text,
            intent=intent,
            entities=entities,
            sentiment=sentiment,
            priority=priority,
            confidence=0.7,  # Lower confidence for rule-based
            topics=topics,
            keywords=keywords,
            is_question=is_question,
            is_urgent=is_urgent,
            timestamp=datetime.now(timezone.utc)
        )
    
    def _classify_intent_rules(self, text: str) -> Intent:
        """Rule-based intent classification"""
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return intent
        return Intent.GENERAL_INQUIRY
    
    def _extract_entities_rules(self, text: str) -> List[Entity]:
        """Rule-based entity extraction"""
        entities = []
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append(Entity(
                    type=entity_type,
                    value=match.group().strip(),
                    confidence=0.8,
                    start_pos=match.start(),
                    end_pos=match.end()
                ))
        
        return entities
    
    def _classify_sentiment_rules(self, text: str) -> Sentiment:
        """Rule-based sentiment classification"""
        # Check for urgency first
        for pattern in self.urgency_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return Sentiment.URGENT
        
        positive_score = sum(1 for pattern in self.positive_patterns 
                           if re.search(pattern, text, re.IGNORECASE))
        negative_score = sum(1 for pattern in self.negative_patterns 
                           if re.search(pattern, text, re.IGNORECASE))
        
        if positive_score > negative_score:
            return Sentiment.POSITIVE
        elif negative_score > positive_score:
            return Sentiment.NEGATIVE
        else:
            return Sentiment.NEUTRAL
    
    def _assess_priority_rules(self, intent: Intent, sentiment: Sentiment, text: str) -> Priority:
        """Assess message priority based on intent and sentiment"""
        if intent == Intent.EMERGENCY or sentiment == Sentiment.URGENT:
            return Priority.CRITICAL
        elif intent in [Intent.APPOINTMENT_SCHEDULE, Intent.QUOTE_REQUEST, Intent.COMPLAINT]:
            return Priority.HIGH
        elif intent in [Intent.SERVICE_INQUIRY, Intent.PAYMENT_INQUIRY, Intent.STATUS_CHECK]:
            return Priority.MEDIUM
        else:
            return Priority.LOW
    
    def _detect_urgency_rules(self, text: str) -> bool:
        """Detect urgency indicators"""
        return any(re.search(pattern, text, re.IGNORECASE) 
                  for pattern in self.urgency_patterns)
    
    def _detect_question_rules(self, text: str) -> bool:
        """Detect if text is a question"""
        question_patterns = [
            r'\?',
            r'\b(what|when|where|why|how|who|can|could|would|will|do|does|did|is|are|was|were)\b.*\?',
            r'\b(what|when|where|why|how|who)\b.*(?<!\?)$'
        ]
        return any(re.search(pattern, text, re.IGNORECASE) 
                  for pattern in question_patterns)
    
    def _extract_keywords_rules(self, text: str) -> List[str]:
        """Extract important keywords"""
        # Simple keyword extraction - remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [word for word in words if len(word) > 3 and word not in stop_words]
        return keywords[:10]  # Top 10 keywords
    
    def _extract_topics_rules(self, text: str, intent: Intent) -> List[str]:
        """Extract main topics from text"""
        topics = []
        
        # Service-related topics
        service_types = ['plumbing', 'electrical', 'hvac', 'painting', 'carpentry', 'flooring']
        for service in service_types:
            if service in text:
                topics.append(service)
        
        # Add intent as topic
        topics.append(intent.value)
        
        return list(set(topics))  # Remove duplicates
    
    def _enhance_with_rules(self, text: str, llm_result: NLPResult) -> NLPResult:
        """Enhance LLM result with rule-based extractions"""
        # Add any missed entities from rule-based extraction
        rule_entities = self._extract_entities_rules(text)
        
        # Merge entities (avoid duplicates)
        existing_values = {e.value for e in llm_result.entities}
        for entity in rule_entities:
            if entity.value not in existing_values:
                llm_result.entities.append(entity)
        
        return llm_result
    
    def _create_fallback_result(self, text: str) -> NLPResult:
        """Create minimal fallback result"""
        return NLPResult(
            text=text,
            intent=Intent.UNKNOWN,
            entities=[],
            sentiment=Sentiment.NEUTRAL,
            priority=Priority.MEDIUM,
            confidence=0.1,
            topics=[],
            keywords=[],
            is_question=False,
            is_urgent=False,
            timestamp=datetime.now(timezone.utc)
        )
    
    async def batch_analyze(self, texts: List[str], context: Optional[Dict] = None) -> List[NLPResult]:
        """Analyze multiple texts in batch"""
        tasks = [self.analyze_text(text, context) for text in texts]
        return await asyncio.gather(*tasks)
    
    def get_confidence_threshold(self) -> float:
        """Get minimum confidence threshold for reliable results"""
        return 0.6 if self.llm_client else 0.5

# Global NLP engine instance
nlp_engine = None

def get_nlp_engine(llm_client=None) -> EnhancedNLPEngine:
    """Get or create NLP engine instance"""
    global nlp_engine
    if nlp_engine is None:
        nlp_engine = EnhancedNLPEngine(llm_client)
    return nlp_engine
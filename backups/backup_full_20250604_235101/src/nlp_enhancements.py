"""
Enhanced NLP Processing for Handyman Services

This module provides advanced NLP capabilities including:
1. Custom entity extraction for handyman services
2. Price extraction and quote generation
3. Multi-language support (Spanish for service areas)
4. Conversation context memory
5. Customer preference learning
"""

import re
import json
import spacy
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
import logging
import pickle
import os
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class ServiceEntity:
    """Represents an extracted service entity"""
    service_type: str
    urgency: str
    location: str
    description: str
    estimated_duration: Optional[str] = None
    materials_needed: List[str] = field(default_factory=list)
    confidence_score: float = 0.8
    extracted_keywords: List[str] = field(default_factory=list)
    room_type: Optional[str] = None
    complexity_level: str = "medium"

@dataclass
class PriceEntity:
    """Represents extracted pricing information"""
    amount: float
    currency: str = "USD"
    service_type: str = ""
    is_estimate: bool = True
    factors: List[str] = field(default_factory=list)
    price_range: Optional[Tuple[float, float]] = None
    context: str = ""
    confidence: float = 0.8

@dataclass
class CustomerPreference:
    """Customer preference data"""
    customer_id: str
    preferred_times: List[str] = field(default_factory=list)
    service_history: List[str] = field(default_factory=list)
    communication_style: str = "formal"
    language_preference: str = "en"
    price_sensitivity: str = "medium"
    preferred_contractors: List[str] = field(default_factory=list)
    budget_range: Optional[Tuple[float, float]] = None
    response_time_preference: str = "standard"  # fast, standard, flexible
    contact_method_preference: str = "email"  # email, sms, phone
    last_interaction: Optional[datetime] = None
    satisfaction_history: List[int] = field(default_factory=list)  # 1-5 rating
    emergency_contact_info: Optional[str] = None

class HandymanNLPEnhancer:
    """Enhanced NLP processor for handyman services"""
    
    def __init__(self):
        self.nlp = None
        self.service_patterns = self._load_service_patterns()
        self.price_patterns = self._load_price_patterns()
        self.spanish_translations = self._load_spanish_translations()
        self.customer_preferences = {}
        self.conversation_context = defaultdict(list)
        
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None
    
    def _load_service_patterns(self) -> Dict[str, List[str]]:
        """Load handyman service patterns and keywords"""
        return {
            "plumbing": [
                r"\b(leak|drip|pipe|faucet|toilet|drain|water|clog|unclog)\b",
                r"\b(plumber|plumbing|sink|shower|bathroom)\b",
                r"\b(water damage|flooding|burst pipe)\b"
            ],
            "electrical": [
                r"\b(electric|electrical|wire|wiring|outlet|switch|light|fixture)\b",
                r"\b(breaker|fuse|panel|voltage|electrician)\b",
                r"\b(power out|no power|electrical issue)\b"
            ],
            "carpentry": [
                r"\b(wood|wooden|door|window|cabinet|shelf|frame)\b",
                r"\b(carpenter|carpentry|install|mount|hang)\b",
                r"\b(trim|molding|drywall|flooring)\b"
            ],
            "hvac": [
                r"\b(heat|heating|cool|cooling|air|hvac|furnace|ac)\b",
                r"\b(thermostat|vent|duct|filter|temperature)\b",
                r"\b(hot|cold|not working|broken)\b"
            ],
            "painting": [
                r"\b(paint|painting|wall|ceiling|color|brush|roller)\b",
                r"\b(primer|finish|touch up|repaint)\b"
            ],
            "general_repair": [
                r"\b(fix|repair|broken|replace|install|maintenance)\b",
                r"\b(handyman|general|misc|various)\b"
            ]
        }
    
    def _load_price_patterns(self) -> List[str]:
        """Load price extraction patterns"""
        return [
            r"\$(\d+(?:,\d{3})*(?:\.\d{2})?)",  # $1,234.56
            r"(\d+(?:,\d{3})*(?:\.\d{2})?) dollars?",  # 1234.56 dollars
            r"(\d+(?:,\d{3})*(?:\.\d{2})?) USD",  # 1234.56 USD
            r"around \$?(\d+(?:,\d{3})*(?:\.\d{2})?)",  # around $1000
            r"approximately \$?(\d+(?:,\d{3})*(?:\.\d{2})?)",  # approximately $500
            r"between \$?(\d+(?:,\d{3})*(?:\.\d{2})?) and \$?(\d+(?:,\d{3})*(?:\.\d{2})?)",  # between $100 and $200
        ]
    
    def _load_spanish_translations(self) -> Dict[str, str]:
        """Load Spanish translations for common handyman terms"""
        return {
            # Services
            "plumbing": "plomería",
            "electrical": "eléctrico",
            "carpentry": "carpintería",
            "painting": "pintura",
            "repair": "reparación",
            "installation": "instalación",
            
            # Common phrases
            "emergency": "emergencia",
            "urgent": "urgente",
            "schedule": "programar",
            "appointment": "cita",
            "estimate": "estimación",
            "quote": "cotización",
            "available": "disponible",
            "today": "hoy",
            "tomorrow": "mañana",
            "this_week": "esta semana",
            
            # Responses
            "hello": "Hola",
            "thank_you": "Gracias",
            "yes": "Sí",
            "no": "No",
            "please": "Por favor",
            "when": "cuándo",
            "where": "dónde",
            "how_much": "cuánto cuesta",
            
            # Standard responses
            "will_contact": "Nos pondremos en contacto contigo pronto",
            "estimate_ready": "Tu estimación está lista",
            "scheduled": "Tu cita está programada"
        }
    
    def extract_service_entities(self, text: str) -> List[ServiceEntity]:
        """Extract handyman service entities from text"""
        entities = []
        text_lower = text.lower()
        
        for service_type, patterns in self.service_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    # Extract urgency
                    urgency = self._extract_urgency(text_lower)
                    
                    # Extract location
                    location = self._extract_location(text)
                    
                    # Extract description (use original text)
                    description = self._extract_description(text, service_type)
                    
                    # Estimate duration
                    duration = self._estimate_duration(service_type, text_lower)
                    
                    # Extract materials
                    materials = self._extract_materials(text_lower, service_type)
                    
                    entities.append(ServiceEntity(
                        service_type=service_type,
                        urgency=urgency,
                        location=location,
                        description=description,
                        estimated_duration=duration,
                        materials_needed=materials
                    ))
                    break  # Avoid duplicate service types
        
        return entities
    
    def _extract_urgency(self, text: str) -> str:
        """Extract urgency level from text"""
        emergency_patterns = [
            r"\b(emergency|urgent|asap|immediately|right now|today)\b",
            r"\b(flooding|burst|no power|dangerous)\b"
        ]
        
        for pattern in emergency_patterns:
            if re.search(pattern, text):
                return "high"
        
        soon_patterns = [
            r"\b(soon|this week|few days|when possible)\b"
        ]
        
        for pattern in soon_patterns:
            if re.search(pattern, text):
                return "medium"
        
        return "low"
    
    def _extract_location(self, text: str) -> str:
        """Extract location information from text"""
        if not self.nlp:
            # Fallback pattern matching
            location_patterns = [
                r"\b(kitchen|bathroom|bedroom|living room|basement|attic|garage)\b",
                r"\b(upstairs|downstairs|main floor|second floor)\b",
                r"\b(front|back|side) (door|yard|wall)\b"
            ]
            
            for pattern in location_patterns:
                match = re.search(pattern, text.lower())
                if match:
                    return match.group(0)
            
            return "not specified"
        
        # Use spaCy for better location extraction
        doc = self.nlp(text)
        locations = []
        
        for ent in doc.ents:
            if ent.label_ in ["GPE", "LOC", "FAC"]:  # Geopolitical, Location, Facility
                locations.append(ent.text)
        
        # Also check for room/area mentions
        room_keywords = ["kitchen", "bathroom", "bedroom", "living room", "basement", "attic", "garage"]
        for token in doc:
            if token.text.lower() in room_keywords:
                locations.append(token.text.lower())
        
        return ", ".join(locations) if locations else "not specified"
    
    def _extract_description(self, text: str, service_type: str) -> str:
        """Extract relevant description for the service"""
        # Simple extraction - could be enhanced with more sophisticated NLP
        sentences = text.split('.')
        relevant_sentences = []
        
        service_keywords = self.service_patterns.get(service_type, [])
        
        for sentence in sentences:
            for pattern in service_keywords:
                if re.search(pattern, sentence.lower()):
                    relevant_sentences.append(sentence.strip())
                    break
        
        return ". ".join(relevant_sentences) if relevant_sentences else text[:200]
    
    def _estimate_duration(self, service_type: str, text: str) -> str:
        """Estimate service duration based on type and description"""
        duration_map = {
            "plumbing": {
                "default": "1-2 hours",
                "patterns": {
                    r"\b(install|replacement)\b": "2-4 hours",
                    r"\b(leak|drip)\b": "30 minutes - 1 hour",
                    r"\b(clog|unclog)\b": "30 minutes - 1 hour"
                }
            },
            "electrical": {
                "default": "1-3 hours",
                "patterns": {
                    r"\b(install|new outlet)\b": "1-2 hours",
                    r"\b(replace|fixture)\b": "30 minutes - 1 hour"
                }
            },
            "carpentry": {
                "default": "2-4 hours",
                "patterns": {
                    r"\b(install|mount)\b": "1-2 hours",
                    r"\b(build|construct)\b": "4-8 hours"
                }
            },
            "hvac": {
                "default": "1-3 hours",
                "patterns": {
                    r"\b(filter|maintenance)\b": "30 minutes",
                    r"\b(install|replace)\b": "2-4 hours"
                }
            },
            "painting": {
                "default": "2-6 hours",
                "patterns": {
                    r"\b(touch up)\b": "1 hour",
                    r"\b(room|wall)\b": "4-8 hours"
                }
            },
            "general_repair": {
                "default": "1-2 hours",
                "patterns": {}
            }
        }
        
        service_info = duration_map.get(service_type, {"default": "1-2 hours", "patterns": {}})
        
        for pattern, duration in service_info["patterns"].items():
            if re.search(pattern, text):
                return duration
        
        return service_info["default"]
    
    def _extract_materials(self, text: str, service_type: str) -> List[str]:
        """Extract materials that might be needed"""
        material_patterns = {
            "plumbing": [
                r"\b(pipe|pipes|fitting|fittings|valve|valves)\b",
                r"\b(gasket|seal|washer|o-ring)\b"
            ],
            "electrical": [
                r"\b(wire|wires|outlet|switch|breaker)\b",
                r"\b(bulb|fixture|conduit)\b"
            ],
            "carpentry": [
                r"\b(wood|lumber|nail|nails|screw|screws)\b",
                r"\b(bracket|brackets|hinge|hinges)\b"
            ],
            "painting": [
                r"\b(paint|primer|brush|roller)\b",
                r"\b(drop cloth|tape|sandpaper)\b"
            ]
        }
        
        materials = []
        patterns = material_patterns.get(service_type, [])
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            materials.extend(matches)
        
        return list(set(materials))  # Remove duplicates
    
    def extract_prices(self, text: str) -> List[PriceEntity]:
        """Extract price information from text"""
        prices = []
        
        for pattern in self.price_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                # Handle different pattern types
                if "between" in pattern:
                    # Range pattern
                    min_price = float(match.group(1).replace(",", ""))
                    max_price = float(match.group(2).replace(",", ""))
                    avg_price = (min_price + max_price) / 2
                    
                    prices.append(PriceEntity(
                        amount=avg_price,
                        is_estimate=True,
                        factors=[f"Range: ${min_price:.2f} - ${max_price:.2f}"]
                    ))
                else:
                    # Single price
                    amount_str = match.group(1).replace(",", "")
                    amount = float(amount_str)
                    
                    is_estimate = any(word in text.lower() for word in 
                                    ["estimate", "approximately", "around", "about"])
                    
                    prices.append(PriceEntity(
                        amount=amount,
                        is_estimate=is_estimate
                    ))
        
        return prices
    
    def generate_quote(self, service_entities: List[ServiceEntity], 
                      customer_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate a quote based on extracted service entities"""
        
        # Base pricing (could be loaded from database)
        base_prices = {
            "plumbing": {"min": 75, "max": 150, "hourly": 85},
            "electrical": {"min": 100, "max": 200, "hourly": 95},
            "carpentry": {"min": 80, "max": 160, "hourly": 75},
            "hvac": {"min": 120, "max": 250, "hourly": 110},
            "painting": {"min": 60, "max": 120, "hourly": 45},
            "general_repair": {"min": 65, "max": 130, "hourly": 70}
        }
        
        total_estimate = 0
        service_quotes = []
        
        for entity in service_entities:
            service_pricing = base_prices.get(entity.service_type, base_prices["general_repair"])
            
            # Calculate base estimate
            base_estimate = service_pricing["min"]
            
            # Adjust for urgency
            if entity.urgency == "high":
                base_estimate *= 1.5  # Emergency surcharge
            elif entity.urgency == "medium":
                base_estimate *= 1.2
            
            # Adjust for materials
            if entity.materials_needed:
                material_cost = len(entity.materials_needed) * 20  # Rough estimate
                base_estimate += material_cost
            
            # Adjust for customer preferences
            if customer_id and customer_id in self.customer_preferences:
                pref = self.customer_preferences[customer_id]
                if pref.price_sensitivity == "high":
                    base_estimate *= 0.9  # Small discount for price-sensitive customers
            
            service_quotes.append({
                "service_type": entity.service_type,
                "description": entity.description,
                "estimated_cost": round(base_estimate, 2),
                "estimated_duration": entity.estimated_duration,
                "urgency": entity.urgency,
                "materials_included": bool(entity.materials_needed)
            })
            
            total_estimate += base_estimate
        
        return {
            "total_estimate": round(total_estimate, 2),
            "service_breakdown": service_quotes,
            "valid_until": (datetime.now() + timedelta(days=7)).isoformat(),
            "notes": [
                "Final pricing may vary based on actual conditions",
                "Emergency services include additional surcharge",
                "Material costs estimated and subject to change"
            ]
        }
    
    def detect_language(self, text: str) -> str:
        """Detect language of input text"""
        # Simple Spanish detection
        spanish_indicators = [
            r"\b(hola|gracias|por favor|sí|no|cuándo|dónde|cómo|qué)\b",
            r"\b(necesito|quiero|tengo|problema|reparación|emergencia)\b",
            r"\b(plomería|eléctrico|pintura|carpintería)\b"
        ]
        
        for pattern in spanish_indicators:
            if re.search(pattern, text.lower()):
                return "es"
        
        return "en"
    
    def translate_response(self, text: str, target_language: str) -> str:
        """Translate response to target language (basic implementation)"""
        if target_language != "es":
            return text
        
        # Simple word replacement (in production, use proper translation service)
        translated = text
        for english, spanish in self.spanish_translations.items():
            translated = re.sub(r'\b' + english + r'\b', spanish, translated, flags=re.IGNORECASE)
        
        return translated
    
    def update_conversation_context(self, customer_id: str, message: str, 
                                  response: str, entities: List[ServiceEntity]):
        """Update conversation context for a customer"""
        context_entry = {
            "timestamp": datetime.now().isoformat(),
            "customer_message": message,
            "response": response,
            "extracted_entities": [
                {
                    "service_type": e.service_type,
                    "urgency": e.urgency,
                    "description": e.description
                } for e in entities
            ]
        }
        
        self.conversation_context[customer_id].append(context_entry)
        
        # Keep only last 10 interactions
        if len(self.conversation_context[customer_id]) > 10:
            self.conversation_context[customer_id] = self.conversation_context[customer_id][-10:]
    
    def learn_customer_preferences(self, customer_id: str, interaction_data: Dict[str, Any]):
        """Learn and update customer preferences"""
        if customer_id not in self.customer_preferences:
            self.customer_preferences[customer_id] = CustomerPreference(
                customer_id=customer_id,
                preferred_times=[],
                service_history=[],
                communication_style="formal",
                language_preference="en",
                price_sensitivity="medium"
            )
        
        pref = self.customer_preferences[customer_id]
        
        # Update service history
        if "service_type" in interaction_data:
            if interaction_data["service_type"] not in pref.service_history:
                pref.service_history.append(interaction_data["service_type"])
        
        # Learn preferred times
        if "preferred_time" in interaction_data:
            pref.preferred_times.append(interaction_data["preferred_time"])
            # Keep only recent preferences
            pref.preferred_times = pref.preferred_times[-5:]
        
        # Detect communication style
        if "message_length" in interaction_data:
            if interaction_data["message_length"] < 50:
                pref.communication_style = "casual"
            else:
                pref.communication_style = "detailed"
        
        # Detect language preference
        if "detected_language" in interaction_data:
            pref.language_preference = interaction_data["detected_language"]
        
        # Learn price sensitivity
        if "price_reaction" in interaction_data:
            if interaction_data["price_reaction"] == "concerned":
                pref.price_sensitivity = "high"
            elif interaction_data["price_reaction"] == "accepted":
                pref.price_sensitivity = "low"
    
    def get_contextual_response_suggestions(self, customer_id: str, 
                                         current_entities: List[ServiceEntity]) -> List[str]:
        """Get response suggestions based on customer context"""
        suggestions = []
        
        # Check conversation history
        if customer_id in self.conversation_context:
            recent_context = self.conversation_context[customer_id][-3:]  # Last 3 interactions
            
            # Check for follow-up opportunities
            previous_services = []
            for context in recent_context:
                for entity in context.get("extracted_entities", []):
                    previous_services.append(entity["service_type"])
            
            # Suggest related services
            service_relationships = {
                "plumbing": ["bathroom renovation", "water damage inspection"],
                "electrical": ["smart home installation", "electrical safety inspection"],
                "painting": ["drywall repair", "interior design consultation"],
                "carpentry": ["custom storage solutions", "trim work"]
            }
            
            for entity in current_entities:
                if entity.service_type in service_relationships:
                    related = service_relationships[entity.service_type]
                    suggestions.extend([f"Would you also be interested in {service}?" for service in related])
        
        # Check customer preferences
        if customer_id in self.customer_preferences:
            pref = self.customer_preferences[customer_id]
            
            # Suggest based on service history
            if len(pref.service_history) > 1:
                suggestions.append("Based on your previous services, would you like a maintenance check?")
            
            # Language-specific suggestions
            if pref.language_preference == "es":
                suggestions.append("¿Te gustaría programar una cita de seguimiento?")
        
        return suggestions[:3]  # Return top 3 suggestions
    
    def process_enhanced_message(self, message: str, customer_id: Optional[str] = None) -> Dict[str, Any]:
        """Complete enhanced NLP processing pipeline"""
        
        # Detect language
        detected_language = self.detect_language(message)
        
        # Extract entities
        service_entities = self.extract_service_entities(message)
        price_entities = self.extract_prices(message)
        
        # Generate quote if services detected
        quote = None
        if service_entities:
            quote = self.generate_quote(service_entities, customer_id)
        
        # Get contextual suggestions
        suggestions = []
        if customer_id:
            suggestions = self.get_contextual_response_suggestions(customer_id, service_entities)
        
        # Learn from interaction
        if customer_id:
            interaction_data = {
                "service_type": service_entities[0].service_type if service_entities else None,
                "message_length": len(message),
                "detected_language": detected_language
            }
            self.learn_customer_preferences(customer_id, interaction_data)
        
        return {
            "detected_language": detected_language,
            "service_entities": service_entities,
            "price_entities": price_entities,
            "generated_quote": quote,
            "response_suggestions": suggestions,
            "processing_metadata": {
                "timestamp": datetime.now().isoformat(),
                "customer_id": customer_id,
                "entities_found": len(service_entities),
                "prices_found": len(price_entities)
            }
        }


def create_nlp_enhancer() -> HandymanNLPEnhancer:
    """Factory function to create NLP enhancer instance"""
    return HandymanNLPEnhancer()


# Example usage and testing
if __name__ == "__main__":
    enhancer = HandymanNLPEnhancer()
    
    # Test messages
    test_messages = [
        "I have a leak in my kitchen sink, it's urgent!",
        "Need electrical work done in the living room, around $200 budget",
        "Hola, necesito reparación de plomería en el baño",
        "Can you paint my bedroom? When are you available this week?",
        "Emergency! My toilet is overflowing and there's water everywhere!"
    ]
    
    for i, message in enumerate(test_messages):
        print(f"\n--- Processing Message {i+1} ---")
        print(f"Input: {message}")
        
        result = enhancer.process_enhanced_message(message, f"customer_{i+1}")
        
        print(f"Language: {result['detected_language']}")
        print(f"Services found: {len(result['service_entities'])}")
        if result['service_entities']:
            for entity in result['service_entities']:
                print(f"  - {entity.service_type}: {entity.urgency} urgency")
        
        if result['generated_quote']:
            print(f"Total estimate: ${result['generated_quote']['total_estimate']}")
        
        if result['response_suggestions']:
            print("Suggestions:", result['response_suggestions'])
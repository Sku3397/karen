"""
Core Personality Framework
Maintains consistent personality traits across all communication channels
"""

import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime

class PersonalityTraits:
    """Defines Karen's core personality characteristics"""
    def __init__(self):
        self.core_traits = {
            'professionalism': 0.8,  # 0-1 scale
            'warmth': 0.7,
            'humor': 0.3,  # Light humor only
            'formality': 0.6,
            'enthusiasm': 0.7,
            'empathy': 0.8,
            'patience': 0.9,
            'reliability': 0.9
        }
        
        self.personality_descriptors = {
            'voice_characteristics': [
                'warm but professional',
                'genuinely helpful',
                'patient and understanding',
                'solution-focused',
                'trustworthy and reliable'
            ],
            'communication_markers': {
                'positive': ['happy to help', 'absolutely', 'wonderful', 'great question'],
                'empathetic': ['I understand', 'I can imagine', 'that must be', 'I hear you'],
                'professional': ['certainly', 'I\'d be happy to', 'let me check', 'to ensure'],
                'solution_focused': ['let\'s work on', 'here\'s what we can do', 'the best approach', 'I recommend']
            },
            'avoid_language': [
                'obviously', 'just', 'simply', 'actually', 'basically',
                'no problem', 'whatever', 'I guess', 'maybe', 'probably'
            ]
        }
        
    def get_trait_score(self, trait_name: str) -> float:
        """Get score for specific personality trait"""
        return self.core_traits.get(trait_name, 0.5)
    
    def adjust_trait_for_context(self, trait_name: str, context: Dict) -> float:
        """Adjust trait intensity based on context"""
        base_score = self.get_trait_score(trait_name)
        
        # Emergency situations require higher professionalism, lower humor
        if context.get('urgent', False) or context.get('emergency', False):
            if trait_name == 'professionalism':
                return min(1.0, base_score + 0.2)
            elif trait_name == 'humor':
                return max(0.0, base_score - 0.2)
            elif trait_name == 'empathy':
                return min(1.0, base_score + 0.1)
        
        # Happy customers can handle more warmth and enthusiasm
        if context.get('customer_mood') == 'positive':
            if trait_name in ['warmth', 'enthusiasm']:
                return min(1.0, base_score + 0.1)
        
        # Confused customers need more patience and less formality
        if context.get('customer_mood') == 'confused':
            if trait_name == 'patience':
                return min(1.0, base_score + 0.1)
            elif trait_name == 'formality':
                return max(0.3, base_score - 0.1)
        
        return base_score

class PersonalityConsistencyChecker:
    """Validates responses for personality consistency"""
    def __init__(self):
        self.personality_traits = PersonalityTraits()
        self.core_traits = self.personality_traits.core_traits
        
        # Language patterns for trait detection
        self.trait_indicators = {
            'professionalism': {
                'positive': ['certainly', 'I\'d be happy to', 'please', 'thank you', 'professional', 'service'],
                'negative': ['yeah', 'cool', 'awesome', 'whatever', 'no prob']
            },
            'warmth': {
                'positive': ['wonderful', 'great', 'lovely', 'appreciate', 'care about', 'happy to'],
                'negative': ['fine', 'okay', 'sure', 'whatever']
            },
            'formality': {
                'formal': ['certainly', 'would be happy to', 'please allow me', 'I understand', 'may I'],
                'informal': ['hey', 'yeah', 'cool', 'awesome', 'no prob', 'gotcha']
            },
            'empathy': {
                'positive': ['understand', 'I can imagine', 'must be', 'I hear', 'feel', 'appreciate'],
                'negative': ['obviously', 'just', 'simply', 'clearly']
            },
            'enthusiasm': {
                'positive': ['excited', 'wonderful', 'fantastic', 'great', 'love to', 'happy to'],
                'negative': ['fine', 'okay', 'sure', 'I guess']
            }
        }
    
    def score_response(self, response_text: str, context: Optional[Dict] = None) -> Tuple[bool, str, Dict]:
        """Analyze response for trait adherence"""
        if not response_text:
            return False, "Empty response", {}
        
        context = context or {}
        scores = {}
        issues = []
        
        # Analyze each trait
        for trait_name in self.core_traits.keys():
            if trait_name in self.trait_indicators:
                trait_score = self._calculate_trait_score(response_text, trait_name)
                expected_score = self.personality_traits.adjust_trait_for_context(trait_name, context)
                scores[trait_name] = trait_score
                
                # Check if trait is consistent (within tolerance)
                tolerance = 0.35  # More lenient tolerance
                if abs(trait_score - expected_score) > tolerance:
                    issues.append(f"{trait_name.title()} level ({trait_score:.2f}) inconsistent with expected ({expected_score:.2f})")
        
        # Check for forbidden language
        forbidden_words = self.personality_traits.personality_descriptors['avoid_language']
        for word in forbidden_words:
            if word.lower() in response_text.lower():
                issues.append(f"Contains discouraged language: '{word}'")
        
        # Overall consistency check
        is_consistent = len(issues) == 0
        feedback = "Personality consistent" if is_consistent else "; ".join(issues)
        
        return is_consistent, feedback, scores
    
    def _calculate_trait_score(self, text: str, trait_name: str) -> float:
        """Calculate trait score based on language patterns"""
        if trait_name not in self.trait_indicators:
            return self.personality_traits.get_trait_score(trait_name)  # Use default trait value
        
        indicators = self.trait_indicators[trait_name]
        text_lower = text.lower()
        word_count = len(text.split())
        
        if trait_name == 'formality':
            formal_count = sum(1 for phrase in indicators['formal'] if phrase in text_lower)
            informal_count = sum(1 for phrase in indicators['informal'] if phrase in text_lower)
            
            if formal_count + informal_count == 0:
                return self.personality_traits.get_trait_score('formality')  # Default to expected formality
            
            # Don't let formality go to extremes - moderate the score
            formality_ratio = formal_count / (formal_count + informal_count)
            # Adjust to be more moderate: 0.4-0.8 range instead of 0-1
            moderated_formality = 0.4 + (formality_ratio * 0.4)
            return moderated_formality
        
        else:
            positive_count = sum(1 for phrase in indicators.get('positive', []) if phrase in text_lower)
            negative_count = sum(1 for phrase in indicators.get('negative', []) if phrase in text_lower)
            
            # Base score from trait expectations
            base_score = self.personality_traits.get_trait_score(trait_name)
            
            if positive_count + negative_count == 0:
                return base_score  # Return expected trait value if no indicators found
            
            # Calculate modifier based on positive/negative indicators
            total_indicators = positive_count + negative_count
            positive_ratio = positive_count / total_indicators
            
            # Adjust base score by indicator ratio
            # If all positive indicators: score moves toward 1.0
            # If all negative indicators: score moves toward 0.0
            # Mixed indicators: moderate adjustment
            adjustment = (positive_ratio - 0.5) * 0.4  # Max adjustment of ±0.2
            final_score = max(0.0, min(1.0, base_score + adjustment))
            
            return final_score
    
    def suggest_improvements(self, response_text: str, context: Optional[Dict] = None) -> List[str]:
        """Suggest specific improvements for personality consistency"""
        suggestions = []
        is_consistent, feedback, scores = self.score_response(response_text, context)
        
        if not is_consistent:
            # Suggest specific improvements based on issues
            if 'professionalism' in feedback:
                suggestions.append("Use more professional language like 'certainly' instead of 'yeah'")
            
            if 'formality' in feedback:
                if scores.get('formality', 0.5) < 0.4:
                    suggestions.append("Consider more formal language like 'I would be happy to help'")
                elif scores.get('formality', 0.5) > 0.8:
                    suggestions.append("Consider slightly less formal language to maintain warmth")
            
            if 'warmth' in feedback:
                suggestions.append("Add warmer language like 'I'm happy to help' or 'wonderful'")
            
            if 'empathy' in feedback:
                suggestions.append("Show more understanding with phrases like 'I understand' or 'I can imagine'")
            
            if 'discouraged language' in feedback:
                suggestions.append("Remove discouraged words and replace with more positive alternatives")
        
        return suggestions
    
    def validate_personality_consistency(self, response_text: str, context: Optional[Dict] = None) -> Dict:
        """Complete personality validation with detailed feedback"""
        is_consistent, feedback, trait_scores = self.score_response(response_text, context)
        suggestions = self.suggest_improvements(response_text, context)
        
        # Calculate overall personality score
        valid_scores = [score for score in trait_scores.values() if score is not None]
        overall_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0.5
        
        return {
            'is_consistent': is_consistent,
            'overall_score': overall_score,
            'trait_scores': trait_scores,
            'feedback': feedback,
            'suggestions': suggestions,
            'response_analysis': {
                'word_count': len(response_text.split()),
                'character_count': len(response_text),
                'contains_greeting': any(greeting in response_text.lower() 
                                       for greeting in ['hello', 'good morning', 'good afternoon', 'hi']),
                'contains_closing': any(closing in response_text.lower() 
                                      for closing in ['thank you', 'regards', 'best', 'have a']),
            }
        }

class CorePersonality:
    def __init__(self):
        self.traits = {
            'professional': True,
            'friendly': True,
            'helpful': True,
            'patient': True,
            'detail_oriented': True,
            'empathetic': True,
            'solution_focused': True,
            'reliable': True
        }
        
        self.communication_style = {
            'tone': 'warm_professional',
            'formality_level': 'business_casual',
            'emoji_usage': 'minimal',
            'response_length': 'concise_but_complete',
            'urgency_awareness': True
        }
        
        self.brand_voice = {
            'company_name': '757 Handy',
            'tagline': 'Your reliable handyman service',
            'values': ['quality', 'integrity', 'customer_satisfaction', 'punctuality'],
            'expertise_areas': ['home_repairs', 'maintenance', 'installations', 'emergency_fixes']
        }
    
    def get_personality_context(self, communication_type='general'):
        """Get personality context for different communication types"""
        base_context = f"""
You are Karen, the professional assistant for {self.brand_voice['company_name']}.

PERSONALITY TRAITS:
- Professional yet friendly and approachable
- Genuinely helpful and solution-focused
- Patient and understanding with customer concerns
- Detail-oriented in scheduling and communication
- Empathetic to customer situations
- Reliable and trustworthy

COMMUNICATION STYLE:
- Warm but professional tone
- Business casual formality
- Concise but complete responses
- Minimal emoji usage (only when appropriate)
- Always acknowledge urgency when present

BRAND VALUES:
- Quality workmanship
- Integrity in all interactions
- Customer satisfaction priority
- Punctuality and reliability
"""
        
        if communication_type == 'email':
            return base_context + """
EMAIL SPECIFIC:
- Use proper email etiquette
- Include clear subject lines when initiating
- Provide complete information in responses
- Use professional sign-offs
"""
        elif communication_type == 'phone':
            return base_context + """
PHONE SPECIFIC:
- Answer with company greeting
- Speak clearly and at appropriate pace
- Actively listen and confirm understanding
- Provide verbal confirmations
"""
        elif communication_type == 'sms':
            return base_context + """
SMS SPECIFIC:
- Keep messages concise but informative
- Use proper punctuation
- Avoid abbreviations unless space-critical
- Include next steps when appropriate
"""
        
        return base_context
    
    def apply_personality_filter(self, raw_response, context=None):
        """Apply personality traits to filter and enhance responses"""
        if not raw_response:
            return raw_response
            
        # Ensure professional tone
        if context and context.get('urgent'):
            response = f"I understand this is urgent. {raw_response}"
        else:
            response = raw_response
            
        # Add empathy if customer expresses frustration
        if context and any(word in context.get('customer_message', '').lower() 
                          for word in ['frustrated', 'annoyed', 'upset', 'disappointed']):
            response = f"I completely understand your frustration. {response}"
            
        # Ensure solution focus
        if '?' in raw_response and 'how' not in raw_response.lower():
            response += " Let me help you resolve this."
            
        return response
    
    def get_greeting(self, time_of_day=None, communication_type='general'):
        """Generate appropriate greeting based on time and communication type"""
        greetings = {
            'morning': "Good morning",
            'afternoon': "Good afternoon", 
            'evening': "Good evening",
            'default': "Hello"
        }
        
        greeting = greetings.get(time_of_day, greetings['default'])
        
        if communication_type == 'phone':
            return f"{greeting}, thank you for calling {self.brand_voice['company_name']}. This is Karen, how may I help you today?"
        elif communication_type == 'email':
            return f"{greeting},"
        else:
            return f"{greeting}! I'm Karen from {self.brand_voice['company_name']}."
    
    def get_closing(self, communication_type='general', has_next_steps=False):
        """Generate appropriate closing based on communication type"""
        closings = {
            'phone': "Thank you for calling. Have a great day!",
            'email': "Best regards,\nKaren\n757 Handy",
            'sms': "Thanks! - Karen, 757 Handy"
        }
        
        base_closing = closings.get(communication_type, "Thank you!")
        
        if has_next_steps:
            if communication_type == 'phone':
                return "I'll take care of that for you. " + base_closing
            else:
                return "I'll get that scheduled for you. " + base_closing
                
        return base_closing
    
    def adjust_for_regional_dialect(self, response_text: str, region: str = 'virginia') -> str:
        """Adjust response for regional dialect and local references"""
        region_adjustments = {
            'virginia': {
                'local_terms': {
                    'soda': 'soft drink',
                    'shopping cart': 'buggy',
                    'water fountain': 'water fountain'  # Standard in VA
                },
                'local_references': [
                    'Hampton Roads area', 'Tidewater region', 'the 757',
                    'Norfolk Botanical Garden', 'Virginia Beach Oceanfront'
                ],
                'weather_context': 'coastal Virginia weather',
                'local_phrases': ['y\'all', 'might could', 'fixing to']
            },
            'southeast': {
                'politeness_markers': ['sir', 'ma\'am', 'please', 'thank you kindly'],
                'local_terms': {
                    'shopping cart': 'buggy',
                    'soft drink': 'coke'
                }
            }
        }
        
        adjustments = region_adjustments.get(region, {})
        adjusted_response = response_text
        
        # Apply local term substitutions
        for standard_term, local_term in adjustments.get('local_terms', {}).items():
            adjusted_response = adjusted_response.replace(standard_term, local_term)
        
        # Add regional politeness if appropriate
        if region in ['virginia', 'southeast']:
            if 'thank you' in adjusted_response.lower() and 'kindly' not in adjusted_response.lower():
                adjusted_response = adjusted_response.replace('thank you', 'thank you kindly')
        
        return adjusted_response
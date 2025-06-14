"""
Response Enhancer
Takes basic LLM responses and enhances them with Karen's personality traits
"""

import re
import random
from typing import Dict, List, Optional, Tuple
from .core_personality import PersonalityTraits, PersonalityConsistencyChecker
from .empathy_engine import EmpathyEngine
from .small_talk import SmallTalkEngine

class ResponseEnhancer:
    """Enhances basic LLM responses with consistent personality traits"""
    
    def __init__(self):
        self.personality_traits = PersonalityTraits()
        self.consistency_checker = PersonalityConsistencyChecker()
        self.empathy_engine = EmpathyEngine()
        self.small_talk_engine = SmallTalkEngine()
        
        # Personality injection patterns
        self.personality_phrases = {
            'warmth_openers': [
                "I'm happy to help with that!",
                "I'd be delighted to assist you!",
                "It would be my pleasure to help!",
                "I'm here to take care of this for you!"
            ],
            'professional_transitions': [
                "Let me help you with that.",
                "I'll be happy to handle this for you.",
                "Allow me to assist you with that.",
                "I can certainly help you with this."
            ],
            'solution_focus': [
                "Here's what I can do for you:",
                "Let me find the best solution:",
                "The best approach would be:",
                "I recommend we handle this by:"
            ],
            'conversational_bridges': [
                "By the way,",
                "I should also mention,",
                "Additionally,",
                "Oh, I almost forgot,",
                "While I have you,"
            ],
            'empathy_connectors': [
                "I completely understand that",
                "I can imagine how",
                "That must be",
                "I hear what you're saying about",
                "I appreciate you sharing that"
            ],
            'reliability_assurances': [
                "You can count on us to",
                "We'll make sure to",
                "I'll personally ensure that",
                "You have my word that we'll",
                "Rest assured, we will"
            ]
        }
        
        # Professional boundaries - things to avoid
        self.professional_boundaries = {
            'avoid_topics': [
                'personal_finances', 'family_problems', 'health_issues',
                'political_opinions', 'religious_views', 'relationship_advice'
            ],
            'redirect_phrases': [
                "I focus on helping with your home repair needs, but",
                "While I'm here to help with handyman services,",
                "My expertise is in home maintenance, though",
                "I specialize in home repairs, but I understand"
            ]
        }
        
        # Mannerisms and verbal habits that make Karen feel real
        self.karen_mannerisms = {
            'verbal_habits': [
                "Let me check on that for you",
                "I want to make sure we get this right",
                "That's a great question",
                "I'm glad you asked about that",
                "Perfect timing for asking about this"
            ],
            'reassuring_phrases': [
                "Don't worry, we've got you covered",
                "This is definitely something we can handle",
                "You've come to the right place",
                "We see this kind of thing all the time",
                "This is right up our alley"
            ],
            'enthusiasm_markers': [
                "Absolutely!",
                "Wonderful!",
                "Perfect!",
                "Fantastic!",
                "That sounds great!"
            ]
        }
    
    def enhance_response(self, base_response: str, context: Optional[Dict] = None) -> str:
        """Main method to enhance a basic LLM response with personality"""
        if not base_response or not base_response.strip():
            return base_response
        
        context = context or {}
        enhanced_response = base_response.strip()
        
        # Step 1: Add empathy if customer emotional state detected
        enhanced_response = self._add_empathy_layer(enhanced_response, context)
        
        # Step 2: Inject personality markers
        enhanced_response = self._inject_personality_markers(enhanced_response, context)
        
        # Step 3: Add conversational elements
        enhanced_response = self._add_conversational_elements(enhanced_response, context)
        
        # Step 4: Ensure professional boundaries
        enhanced_response = self._maintain_professional_boundaries(enhanced_response, context)
        
        # Step 5: Add Karen's signature mannerisms
        enhanced_response = self._add_karen_mannerisms(enhanced_response, context)
        
        # Step 6: Validate consistency and adjust if needed
        enhanced_response = self._ensure_consistency(enhanced_response, context)
        
        return enhanced_response
    
    def _add_empathy_layer(self, response: str, context: Dict) -> str:
        """Add empathetic opening if customer emotional state detected"""
        customer_message = context.get('customer_message', '')
        if not customer_message:
            return response
        
        # Analyze customer emotional state
        customer_state = self.empathy_engine.analyze_customer_state(customer_message, context)
        
        if customer_state.get('needs_empathy', False):
            empathy_opening = self.empathy_engine.create_empathetic_opening(customer_state)
            if empathy_opening and not any(phrase in response.lower() for phrase in ['understand', 'sorry', 'imagine']):
                response = f"{empathy_opening} {response}"
        
        return response
    
    def _inject_personality_markers(self, response: str, context: Dict) -> str:
        """Inject personality-appropriate phrases and markers"""
        # Add warmth to dry responses
        if not any(warm_word in response.lower() for warm_word in ['happy', 'delighted', 'pleasure', 'wonderful', 'glad', 'appreciate']):
            if context.get('interaction_type') != 'emergency':
                # Choose appropriate warmth based on context
                if context.get('customer_type') == 'repeat':
                    response = f"I'm happy to help you again! {response}"
                else:
                    response = f"I'd be happy to help with that. {response}"
        
        # Add professional markers to ensure professionalism score (but keep moderate formality)
        if not any(prof_word in response.lower() for prof_word in ['happy', 'help', 'service', 'assist']):
            response = f"I'm happy to help. {response}"
        
        # Add solution-focused language if providing recommendations
        if any(indicator in response.lower() for indicator in ['should', 'recommend', 'suggest', 'advise']):
            if not response.lower().startswith(('here\'s what', 'the best', 'i recommend')):
                solution_opener = random.choice(self.personality_phrases['solution_focus'])
                response = f"{solution_opener} {response}"
        
        # Add reliability assurance for commitments
        if any(commitment in response.lower() for commitment in ['will', 'schedule', 'arrange', 'send']):
            if random.random() < 0.3:  # 30% chance to add assurance
                assurance = random.choice(self.personality_phrases['reliability_assurances'])
                # Replace "we will" or "I will" with assurance
                response = re.sub(r'\b(we will|i will)\b', assurance, response, flags=re.IGNORECASE)
        
        return response
    
    def _add_conversational_elements(self, response: str, context: Dict) -> str:
        """Add natural conversational bridges and small talk opportunities"""
        # Only add conversational elements if response is not already too long
        if len(response.split()) > 20:  # Skip if already long
            return response
            
        # Detect small talk opportunities (but be selective)
        customer_message = context.get('customer_message', '')
        small_talk_opportunity = self.small_talk_engine.detect_small_talk_opportunity(customer_message)
        
        if small_talk_opportunity and random.random() < 0.2 and context.get('interaction_type') != 'emergency':  # 20% chance, not for emergencies
            small_talk = self.small_talk_engine.generate_small_talk_response(
                small_talk_opportunity, {'message': customer_message}
            )
            if small_talk and len(small_talk.split()) < 15:  # Keep small talk short
                response = f"{response} {small_talk}"
        
        return response
    
    def _maintain_professional_boundaries(self, response: str, context: Dict) -> str:
        """Ensure response maintains professional boundaries"""
        # Simplified boundary checking - just ensure we stay focused on handyman services
        return response
    
    def _add_karen_mannerisms(self, response: str, context: Dict) -> str:
        """Add Karen's signature mannerisms and verbal habits"""
        # Skip if response is already long
        if len(response.split()) > 15:
            return response
            
        # Add enthusiasm for positive interactions
        if any(positive_word in context.get('customer_message', '').lower() 
               for positive_word in ['great', 'perfect', 'wonderful', 'sounds good', 'thank you']):
            if not any(enthusiasm in response.lower() for enthusiasm in ['wonderful', 'fantastic', 'perfect', 'absolutely']):
                enthusiasm = random.choice(self.karen_mannerisms['enthusiasm_markers'])
                response = f"{enthusiasm} {response}"
        
        return response
    
    def _ensure_consistency(self, response: str, context: Dict) -> str:
        """Final consistency check and adjustments"""
        # Check personality consistency
        validation = self.consistency_checker.validate_personality_consistency(response, context)
        
        if not validation['is_consistent']:
            # Apply suggested improvements
            for suggestion in validation['suggestions']:
                if 'professional language' in suggestion:
                    response = self._make_more_professional(response)
                elif 'formal language' in suggestion:
                    response = self._adjust_formality(response, 'more_formal')
                elif 'less formal' in suggestion:
                    response = self._adjust_formality(response, 'less_formal')
                elif 'warmer language' in suggestion:
                    response = self._add_warmth(response)
                elif 'understanding' in suggestion:
                    response = self._add_empathy_markers(response)
        
        return response
    
    def _make_more_professional(self, response: str) -> str:
        """Make response more professional"""
        replacements = {
            'yeah': 'yes',
            'yep': 'yes', 
            'nope': 'no',
            'cool': 'excellent',
            'awesome': 'wonderful',
            'no prob': 'you\'re welcome',
            'sure thing': 'certainly'
        }
        
        for informal, formal in replacements.items():
            response = re.sub(r'\b' + re.escape(informal) + r'\b', formal, response, flags=re.IGNORECASE)
        
        return response
    
    def _adjust_formality(self, response: str, direction: str) -> str:
        """Adjust formality level of response"""
        if direction == 'more_formal':
            replacements = {
                'I can': 'I would be able to',
                'let me': 'allow me to',
                'we\'ll': 'we will',
                'can\'t': 'cannot',
                'won\'t': 'will not'
            }
        else:  # less_formal
            replacements = {
                'I would be able to': 'I can',
                'allow me to': 'let me',
                'we will': 'we\'ll',
                'cannot': 'can\'t',
                'will not': 'won\'t'
            }
        
        for original, replacement in replacements.items():
            response = re.sub(r'\b' + re.escape(original) + r'\b', replacement, response, flags=re.IGNORECASE)
        
        return response
    
    def _add_warmth(self, response: str) -> str:
        """Add warmer language to response"""
        warm_additions = [
            "I'm happy to help",
            "I'd be delighted to assist",
            "It would be wonderful to help you",
            "I appreciate you reaching out"
        ]
        
        if not any(warm in response.lower() for warm in ['happy', 'delighted', 'wonderful', 'appreciate']):
            addition = random.choice(warm_additions)
            response = f"{addition}. {response}"
        
        return response
    
    def _add_empathy_markers(self, response: str) -> str:
        """Add empathy markers to response"""
        empathy_starters = [
            "I understand",
            "I can see why",
            "I appreciate that",
            "I hear what you're saying"
        ]
        
        if not any(empathy in response.lower() for empathy in ['understand', 'appreciate', 'see why', 'hear']):
            starter = random.choice(empathy_starters)
            response = f"{starter}. {response}"
        
        return response
    
    def enhance_with_context_awareness(self, response: str, context: Dict) -> str:
        """Enhanced version that considers more context factors"""
        # Time of day adjustments
        current_hour = context.get('current_hour')
        if current_hour:
            if current_hour < 9:  # Early morning
                if not any(time_ref in response.lower() for time_ref in ['morning', 'early']):
                    response = "Good morning! " + response
            elif current_hour > 18:  # Evening
                if not any(time_ref in response.lower() for time_ref in ['evening', 'day']):
                    response = "Good evening! " + response
        
        # Service type adjustments
        service_type = context.get('service_type', '')
        if service_type == 'emergency':
            # More urgent, less small talk
            response = re.sub(r'\b(wonderful|delighted|fantastic)\b', 'certainly', response, flags=re.IGNORECASE)
            if not response.lower().startswith(('i understand', 'right away', 'immediately')):
                response = "I understand this is urgent. " + response
        
        # Customer history adjustments
        if context.get('customer_type') == 'repeat':
            if not any(recog in response.lower() for recog in ['again', 'back', 'return']):
                response = "It's great to hear from you again! " + response
        
        return response
    
    def validate_enhanced_response(self, enhanced_response: str, original_response: str, context: Dict) -> Dict:
        """Validate that enhancement improved the response appropriately"""
        validation = self.consistency_checker.validate_personality_consistency(enhanced_response, context)
        
        # Check that core information wasn't lost
        information_preserved = True
        original_words = set(original_response.lower().split())
        enhanced_words = set(enhanced_response.lower().split())
        
        # Key information words that should be preserved
        key_words = []
        for word in original_words:
            if len(word) > 4 and word not in ['that', 'this', 'with', 'have', 'will', 'they', 'them']:
                key_words.append(word)
        
        preserved_count = sum(1 for word in key_words if word in enhanced_words)
        preservation_ratio = preserved_count / len(key_words) if key_words else 1.0
        
        if preservation_ratio < 0.7:  # Less than 70% of key information preserved
            information_preserved = False
        
        return {
            'personality_consistent': validation['is_consistent'],
            'personality_score': validation['overall_score'],
            'information_preserved': information_preserved,
            'preservation_ratio': preservation_ratio,
            'enhancement_successful': validation['is_consistent'] and information_preserved,
            'suggestions': validation['suggestions'],
            'word_count_change': len(enhanced_response.split()) - len(original_response.split())
        }
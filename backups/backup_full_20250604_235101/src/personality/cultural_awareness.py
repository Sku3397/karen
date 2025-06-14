"""
Cultural Awareness Module
Provides culturally sensitive communication for diverse customer base
"""

from typing import Dict, List, Optional
from datetime import datetime

class CulturalAwareness:
    def __init__(self):
        self.cultural_considerations = {
            'communication_styles': {
                'direct': ['german', 'dutch', 'scandinavian'],
                'indirect': ['east_asian', 'middle_eastern', 'latin_american'],
                'formal': ['german', 'korean', 'japanese'],
                'informal': ['australian', 'american', 'canadian']
            },
            
            'religious_holidays': {
                'christmas': {'dates': ['12-25'], 'greeting': 'Merry Christmas'},
                'hanukkah': {'dates': ['12-varies'], 'greeting': 'Happy Hanukkah'},
                'ramadan': {'dates': ['lunar-varies'], 'greeting': 'Ramadan Mubarak'},
                'diwali': {'dates': ['10-varies'], 'greeting': 'Happy Diwali'},
                'chinese_new_year': {'dates': ['lunar-varies'], 'greeting': 'Happy New Year'},
                'easter': {'dates': ['spring-varies'], 'greeting': 'Happy Easter'}
            },
            
            'cultural_sensitivities': {
                'time_orientation': {
                    'punctual': ['german', 'swiss', 'japanese', 'american'],
                    'flexible': ['latin_american', 'middle_eastern', 'african']
                },
                'family_importance': {
                    'high': ['hispanic', 'asian', 'middle_eastern', 'african'],
                    'moderate': ['american', 'european']
                },
                'decision_making': {
                    'individual': ['american', 'western_european'],
                    'family_based': ['asian', 'hispanic', 'middle_eastern']
                }
            },
            
            'language_preferences': {
                'formal_address': ['korean', 'japanese', 'german', 'russian'],
                'relationship_building': ['hispanic', 'middle_eastern', 'african'],
                'efficiency_focused': ['german', 'dutch', 'american']
            }
        }
        
        self.inclusive_language = {
            'greetings': [
                "Good morning/afternoon/evening",
                "Hello", 
                "Thank you for calling",
                "Welcome"
            ],
            'avoid_assumptions': [
                "What would work best for your schedule?",
                "How would you prefer to handle this?",
                "What's most important to you in this situation?",
                "Is there anything specific I should know?"
            ],
            'respectful_closings': [
                "Thank you for your time",
                "Have a wonderful day",
                "Take care",
                "We appreciate your business"
            ]
        }
        
        self.accessibility_considerations = {
            'hearing_impaired': {
                'email_preference': True,
                'text_preference': True,
                'clear_speech': True,
                'written_confirmation': True
            },
            'vision_impaired': {
                'verbal_descriptions': True,
                'audio_confirmation': True,
                'clear_directions': True
            },
            'mobility_limited': {
                'scheduling_flexibility': True,
                'access_considerations': True,
                'equipment_accommodation': True
            },
            'elderly': {
                'patience_required': True,
                'clear_explanation': True,
                'repeated_confirmation': True,
                'respect_for_experience': True
            }
        }
        
        self.family_dynamics = {
            'decision_makers': {
                'both_spouses': "I'd like to make sure both of you are comfortable with this arrangement.",
                'adult_children': "Would you like to include any family members in this discussion?",
                'elderly_parent': "Is there someone else who helps you with home decisions?",
                'single_parent': "I understand how busy you must be. Let's find a time that works with your schedule."
            }
        }
    
    def detect_cultural_indicators(self, customer_info: Dict) -> Dict:
        """Detect cultural indicators from customer information"""
        indicators = {
            'name_origin': None,
            'accent_detected': None,
            'time_preferences': None,
            'communication_style': None,
            'family_involvement': None
        }
        
        # This would be enhanced with actual name analysis libraries
        # For now, providing framework for cultural sensitivity
        
        return indicators
    
    def adapt_communication_style(self, cultural_indicators: Dict, base_message: str) -> str:
        """Adapt communication style based on cultural indicators"""
        adapted_message = base_message
        
        # Make language more formal if indicated
        if cultural_indicators.get('communication_style') == 'formal':
            adapted_message = self._make_more_formal(adapted_message)
        
        # Add relationship-building elements if appropriate
        if cultural_indicators.get('relationship_focus'):
            adapted_message = self._add_relationship_building(adapted_message)
        
        # Adjust for time orientation
        if cultural_indicators.get('time_orientation') == 'flexible':
            adapted_message = self._add_flexibility_language(adapted_message)
        
        return adapted_message
    
    def _make_more_formal(self, message: str) -> str:
        """Make message more formal"""
        # Replace casual language with formal equivalents
        replacements = {
            "hi": "hello",
            "hey": "hello", 
            "sure": "certainly",
            "ok": "very well",
            "yep": "yes",
            "nope": "no",
            "can't": "cannot",
            "won't": "will not"
        }
        
        for casual, formal in replacements.items():
            message = message.replace(casual, formal)
        
        return message
    
    def _add_relationship_building(self, message: str) -> str:
        """Add relationship-building elements to message"""
        if not any(phrase in message.lower() for phrase in ['hope', 'appreciate', 'understand']):
            message = f"I hope this finds you well. {message}"
        
        return message
    
    def _add_flexibility_language(self, message: str) -> str:
        """Add flexibility-oriented language"""
        if 'schedule' in message.lower() or 'time' in message.lower():
            message += " We're happy to work with whatever timing is most convenient for you and your family."
        
        return message
    
    def get_holiday_appropriate_greeting(self, date_context: Optional[datetime] = None) -> str:
        """Get holiday-appropriate greeting if applicable"""
        if not date_context:
            date_context = datetime.now()
        
        month = date_context.month
        day = date_context.day
        
        # General seasonal greetings that are inclusive
        if month == 12:
            return "Wishing you and your family a wonderful holiday season!"
        elif month == 1:
            return "Wishing you a happy and prosperous new year!"
        elif month in [3, 4, 5]:
            return "Hope you're enjoying the spring season!"
        elif month in [6, 7, 8]:
            return "Hope you're having a great summer!"
        elif month in [9, 10, 11]:
            return "Hope you're enjoying the fall season!"
        
        return ""
    
    def handle_accessibility_needs(self, customer_needs: Dict) -> Dict:
        """Provide accommodations for accessibility needs"""
        accommodations = {}
        
        if customer_needs.get('hearing_impaired'):
            accommodations.update({
                'communication_method': 'email_or_text',
                'confirmation_required': 'written',
                'special_instructions': 'Speak clearly and confirm understanding'
            })
        
        if customer_needs.get('vision_impaired'):
            accommodations.update({
                'verbal_descriptions': True,
                'audio_confirmation': True,
                'clear_directions': True
            })
        
        if customer_needs.get('mobility_limited'):
            accommodations.update({
                'scheduling_note': 'Allow extra time for access',
                'equipment_note': 'Consider mobility limitations',
                'entry_note': 'Confirm accessible entry points'
            })
        
        if customer_needs.get('elderly'):
            accommodations.update({
                'patience_level': 'high',
                'explanation_detail': 'thorough',
                'confirmation_frequency': 'multiple',
                'respect_emphasis': True
            })
        
        return accommodations
    
    def suggest_family_inclusive_language(self, situation: str) -> str:
        """Suggest family-inclusive language for different situations"""
        suggestions = {
            'scheduling': "What time works best for your family's schedule?",
            'decision_making': "Please feel free to discuss this with anyone who helps with home decisions.",
            'pricing': "I want to make sure this fits comfortably within your family's budget.",
            'emergency': "I understand this affects your whole household. Let's get this resolved quickly.",
            'follow_up': "Is this still a good number to reach you, or would another family member prefer to be contacted?"
        }
        
        return suggestions.get(situation, "")
    
    def create_inclusive_service_description(self, service_type: str) -> str:
        """Create inclusive service descriptions"""
        descriptions = {
            'general': "We provide reliable home repair services for all families and households in our community.",
            'emergency': "We understand that home emergencies affect everyone in the household, and we're here to help restore your family's comfort and safety.",
            'maintenance': "Regular home maintenance helps keep your living space comfortable and safe for everyone who calls it home.",
            'installation': "We'll work carefully to minimize disruption to your daily routine and ensure the installation meets your household's specific needs."
        }
        
        return descriptions.get(service_type, descriptions['general'])
    
    def validate_cultural_sensitivity(self, message: str) -> Dict:
        """Validate message for cultural sensitivity"""
        issues = []
        suggestions = []
        
        # Check for potentially insensitive language
        sensitive_terms = ['guys', 'ladies', 'normal', 'weird', 'foreign']
        for term in sensitive_terms:
            if term in message.lower():
                issues.append(f"Consider replacing '{term}' with more inclusive language")
        
        # Check for assumptions
        assumption_indicators = ['obviously', 'everyone knows', 'of course', 'naturally']
        for indicator in assumption_indicators:
            if indicator in message.lower():
                issues.append(f"Phrase '{indicator}' may make assumptions about customer knowledge")
        
        # Suggest improvements
        if not any(inclusive in message.lower() for inclusive in ['please', 'thank you', 'appreciate']):
            suggestions.append("Consider adding polite language like 'please' or 'thank you'")
        
        return {
            'issues': issues,
            'suggestions': suggestions,
            'score': max(0, 10 - len(issues))  # 10 = perfect, deduct for issues
        }
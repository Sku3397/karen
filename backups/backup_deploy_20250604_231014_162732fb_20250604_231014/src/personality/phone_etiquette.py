"""
Professional Phone Etiquette Templates
Handles phone-specific communication patterns for handyman business
"""

from datetime import datetime
from .core_personality import CorePersonality

class PhoneEtiquette:
    def __init__(self):
        self.personality = CorePersonality()
        
        self.standard_responses = {
            'greeting': "Good {time_of_day}, thank you for calling 757 Handy. This is Karen, how may I help you today?",
            'hold': "I'll be happy to help you with that. May I place you on a brief hold while I check that information?",
            'return_from_hold': "Thank you for holding. I have that information for you now.",
            'transfer': "I'm going to transfer you to our {department} who can better assist you with that. Please hold while I connect you.",
            'appointment_confirm': "Perfect! I have you scheduled for {date} at {time}. You should receive a confirmation text shortly.",
            'emergency': "I understand this is urgent. Let me see what we can do to help you as quickly as possible.",
            'pricing_inquiry': "I'd be happy to provide you with pricing information. To give you the most accurate estimate, I'll need a few details about your project.",
            'callback': "I'll have someone call you back within {timeframe}. Is {phone_number} the best number to reach you?",
            'closing': "Thank you for calling 757 Handy. Have a wonderful day!"
        }
        
        self.emergency_keywords = [
            'emergency', 'urgent', 'flooding', 'leak', 'electrical', 'gas',
            'safety', 'dangerous', 'broken', 'not working', 'asap', 'immediate'
        ]
        
        self.service_categories = {
            'plumbing': ['plumber', 'leak', 'toilet', 'sink', 'drain', 'pipe', 'water'],
            'electrical': ['electrical', 'electrician', 'outlet', 'switch', 'light', 'power', 'wiring'],
            'hvac': ['heating', 'cooling', 'air conditioning', 'furnace', 'thermostat', 'hvac'],
            'general': ['repair', 'fix', 'install', 'maintenance', 'handyman', 'general']
        }
    
    def get_greeting(self):
        """Get appropriate phone greeting based on time of day"""
        current_hour = datetime.now().hour
        
        if 5 <= current_hour < 12:
            time_of_day = "morning"
        elif 12 <= current_hour < 17:
            time_of_day = "afternoon"
        elif 17 <= current_hour < 21:
            time_of_day = "evening"
        else:
            time_of_day = "evening"  # Late night/early morning default
            
        return self.standard_responses['greeting'].format(time_of_day=time_of_day)
    
    def analyze_call_intent(self, customer_message):
        """Analyze customer message to determine intent and urgency"""
        message_lower = customer_message.lower()
        
        # Check for emergency
        is_emergency = any(keyword in message_lower for keyword in self.emergency_keywords)
        
        # Determine service category
        service_type = 'general'
        for category, keywords in self.service_categories.items():
            if any(keyword in message_lower for keyword in keywords):
                service_type = category
                break
        
        # Determine intent
        intent = 'general_inquiry'
        if any(word in message_lower for word in ['schedule', 'appointment', 'when', 'available']):
            intent = 'scheduling'
        elif any(word in message_lower for word in ['cost', 'price', 'quote', 'estimate', 'how much']):
            intent = 'pricing'
        elif any(word in message_lower for word in ['cancel', 'reschedule', 'change', 'move']):
            intent = 'appointment_change'
        elif is_emergency:
            intent = 'emergency'
            
        return {
            'intent': intent,
            'service_type': service_type,
            'is_emergency': is_emergency,
            'requires_callback': 'call back' in message_lower or 'call me' in message_lower
        }
    
    def generate_response(self, customer_message, context=None):
        """Generate appropriate phone response based on customer message"""
        analysis = self.analyze_call_intent(customer_message)
        
        if analysis['is_emergency']:
            response = self.standard_responses['emergency']
            
        elif analysis['intent'] == 'scheduling':
            response = "I'd be happy to schedule that for you. Let me check our availability. What type of work do you need done?"
            
        elif analysis['intent'] == 'pricing':
            response = self.standard_responses['pricing_inquiry']
            
        elif analysis['intent'] == 'appointment_change':
            response = "I can help you with that. Let me pull up your appointment. Can you give me your name and phone number?"
            
        else:
            response = "I'd be happy to help you with that. Can you tell me a bit more about what you need?"
        
        # Apply personality filter
        response = self.personality.apply_personality_filter(response, {
            'urgent': analysis['is_emergency'],
            'customer_message': customer_message
        })
        
        return response
    
    def handle_hold_procedure(self):
        """Handle putting customer on hold"""
        return {
            'hold_request': self.standard_responses['hold'],
            'return_message': self.standard_responses['return_from_hold']
        }
    
    def confirm_appointment(self, date, time, service_type=None):
        """Generate appointment confirmation response"""
        confirmation = self.standard_responses['appointment_confirm'].format(
            date=date, time=time
        )
        
        if service_type:
            confirmation += f" Our technician will be there to help with your {service_type} needs."
            
        return confirmation
    
    def handle_callback_request(self, phone_number, timeframe="2 hours"):
        """Handle callback scheduling"""
        return self.standard_responses['callback'].format(
            timeframe=timeframe, phone_number=phone_number
        )
    
    def get_professional_closing(self, has_appointment=False):
        """Get appropriate call closing"""
        if has_appointment:
            return "Thank you for choosing 757 Handy. We'll see you soon! Have a great day."
        else:
            return self.standard_responses['closing']
    
    def handle_difficult_situation(self, situation_type):
        """Handle difficult customer situations professionally"""
        responses = {
            'pricing_concern': "I understand your concern about pricing. Let me see what options we have available and speak with my manager about the best solution for you.",
            'scheduling_conflict': "I apologize for the scheduling conflict. Let me check what other options we have and find a time that works better for you.",
            'service_complaint': "I sincerely apologize for that experience. That's not the level of service we strive for. Let me escalate this to our service manager immediately.",
            'general_frustration': "I completely understand your frustration, and I want to make this right for you. Let me see how we can resolve this issue today."
        }
        
        return responses.get(situation_type, responses['general_frustration'])
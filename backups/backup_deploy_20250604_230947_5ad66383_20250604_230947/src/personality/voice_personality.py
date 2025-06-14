"""
Karen's voice personality for phone calls
"""
from typing import Dict, List
import random
from datetime import datetime
import requests
import logging

logger = logging.getLogger(__name__)

class VoicePersonality:
    def __init__(self):
        self.voice_config = {
            'voice': 'Polly.Joanna',  # Or 'Polly.Matthew' for male
            'speaking_rate': '95%',   # Slightly slower for clarity
            'pitch': '+5%',           # Slightly higher for friendliness
            'volume': 'medium',
            'tone': 'conversational'
        }
        
        self.greetings = {
            'morning': [
                "Good morning! This is Karen from 757 Handy. How can I brighten your day?",
                "Good morning! Karen here from 757 Handy. What can we fix for you today?",
                "Morning! This is Karen with 757 Handy. Ready to tackle your home projects?"
            ],
            'afternoon': [
                "Good afternoon! This is Karen from 757 Handy. How can I help you?",
                "Hi there! Karen from 757 Handy. What brings you to us today?",
                "Afternoon! Karen here from 757 Handy. What's on your to-do list?"
            ],
            'evening': [
                "Good evening! This is Karen from 757 Handy. How can I assist you?",
                "Hello! Karen here from 757 Handy. What can we help you with?",
                "Evening! This is Karen with 757 Handy. How can I help make your home better?"
            ]
        }
        
        self.hold_music_messages = [
            "Thank you for holding. Did you know we offer a 10% discount for regular maintenance plans?",
            "Thanks for your patience. We typically respond to emergency calls within 2 hours!",
            "While you wait, remember we're available 24/7 for emergencies.",
            "Thank you for waiting. All our work comes with a satisfaction guarantee!",
            "Just a moment more - we appreciate your business and want to give you our full attention."
        ]
        
        self.appointment_confirmations = [
            "Perfect! I've got you scheduled for {time} on {date}. We'll send a confirmation text shortly.",
            "Wonderful! Your appointment is set for {time} on {date}. Looking forward to helping you!",
            "Great! We'll see you {time} on {date}. Our technician will call 30 minutes before arriving."
        ]
        
        self.empathy_responses = {
            'urgent': [
                "I understand this is urgent for you. Let me see what we can do right away.",
                "I hear how important this is - let's get this handled as quickly as possible.",
                "That sounds really stressful. I'm here to help make this easier for you."
            ],
            'frustrated': [
                "I completely understand your frustration, and I'm here to help make this right.",
                "I can hear this has been challenging. Let's work together to solve this.",
                "That sounds really frustrating. I want to help turn this around for you."
            ],
            'concerned': [
                "I hear your concern, and I want to help resolve this for you.",
                "That's definitely something we should address. Let me help you with that.",
                "I understand why you'd be worried about that. Let's get it taken care of."
            ]
        }
        
    def get_greeting(self) -> str:
        """Get appropriate greeting based on time of day"""
        hour = datetime.now().hour
        if hour < 12:
            period = 'morning'
        elif hour < 17:
            period = 'afternoon'
        else:
            period = 'evening'
            
        return random.choice(self.greetings[period])
    
    def handle_difficult_customer(self, sentiment_score: float) -> str:
        """Adjust response for upset customers"""
        if sentiment_score < -0.7:  # Very upset
            return random.choice(self.empathy_responses['frustrated'])
        elif sentiment_score < -0.3:   # Mildly upset or concerned
            return random.choice(self.empathy_responses['concerned'])
        else:
            return "I'd be happy to help you with that!"
    
    def get_hold_message(self) -> str:
        """Get a random hold message"""
        return random.choice(self.hold_music_messages)
    
    def confirm_appointment(self, appointment_time: str, appointment_date: str) -> str:
        """Generate appointment confirmation message"""
        template = random.choice(self.appointment_confirmations)
        return template.format(time=appointment_time, date=appointment_date)
    
    def add_vocal_emphasis(self, message: str, emotion: str = 'friendly') -> Dict:
        """Add SSML markup for vocal emphasis"""
        ssml_config = {
            'message': message,
            'rate': self.voice_config['speaking_rate'],
            'pitch': self.voice_config['pitch'],
            'volume': self.voice_config['volume']
        }
        
        if emotion == 'excited':
            ssml_config['pitch'] = '+10%'
            ssml_config['rate'] = '105%'
        elif emotion == 'calm':
            ssml_config['pitch'] = '0%'
            ssml_config['rate'] = '90%'
        elif emotion == 'empathetic':
            ssml_config['pitch'] = '-5%'
            ssml_config['rate'] = '85%'
            
        return ssml_config
    
    def handle_callback_request(self, customer_name: str, phone_number: str, best_time: str = None) -> str:
        """Generate callback confirmation message"""
        base_message = f"Absolutely, {customer_name}. I'll have one of our team members call you back at {phone_number}"
        
        if best_time:
            base_message += f" around {best_time}"
        else:
            base_message += " within the next few hours"
            
        base_message += ". Is there anything specific you'd like them to know about your project?"
        
        return base_message
    
    def handle_emergency_call(self) -> str:
        """Special handling for emergency situations"""
        return ("I understand this is an emergency. Let me connect you with our emergency dispatch right away. "
                "Please stay on the line - help is on the way.")
    
    def end_call_pleasantly(self, outcome: str) -> str:
        """Generate appropriate call ending"""
        endings = {
            'appointment_scheduled': [
                "Perfect! We'll see you soon. Have a wonderful day!",
                "Great talking with you! We're looking forward to helping you out.",
                "All set! Thanks for choosing 757 Handy. Take care!"
            ],
            'callback_requested': [
                "Someone will be calling you back shortly. Thanks for reaching out!",
                "We'll get back to you soon. Have a great day!",
                "Perfect! Expect a call back soon. Thanks for choosing 757 Handy!"
            ],
            'information_provided': [
                "I hope that information was helpful! Feel free to call us anytime.",
                "Thanks for calling 757 Handy. We're always here when you need us!",
                "Glad I could help! Don't hesitate to reach out if you have more questions."
            ],
            'general': [
                "Thanks for calling 757 Handy! Have a wonderful day!",
                "It was great talking with you. Take care!",
                "Thanks for choosing 757 Handy. We appreciate your business!"
            ]
        }
        
        return random.choice(endings.get(outcome, endings['general']))
    
    def adapt_for_repeat_customer(self, customer_name: str, last_service: str = None) -> str:
        """Personalized greeting for returning customers"""
        base_greeting = f"Hi {customer_name}! It's Karen from 757 Handy. Great to hear from you again!"
        
        if last_service:
            base_greeting += f" How did that {last_service} work out for you?"
            
        return base_greeting
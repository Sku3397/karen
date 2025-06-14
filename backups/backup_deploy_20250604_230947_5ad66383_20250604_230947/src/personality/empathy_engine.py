"""
Empathy Response System
Detects emotional states and generates appropriate empathetic responses
"""

import re
from typing import Dict, List, Optional

class EmpathyEngine:
    def __init__(self):
        self.emotion_keywords = {
            'frustrated': [
                'frustrated', 'annoyed', 'irritated', 'fed up', 'angry',
                'upset', 'mad', 'furious', 'livid', 'bothered'
            ],
            'worried': [
                'worried', 'concerned', 'anxious', 'nervous', 'stressed',
                'panicked', 'scared', 'afraid', 'fearful'
            ],
            'disappointed': [
                'disappointed', 'let down', 'upset', 'sad', 'discouraged',
                'bummed', 'down', 'unhappy'
            ],
            'urgent': [
                'urgent', 'emergency', 'asap', 'immediately', 'right away',
                'can\'t wait', 'need now', 'critical', 'serious'
            ],
            'confused': [
                'confused', 'don\'t understand', 'unclear', 'lost',
                'not sure', 'puzzled', 'bewildered'
            ],
            'grateful': [
                'thank you', 'thanks', 'appreciate', 'grateful',
                'helpful', 'wonderful', 'great', 'amazing'
            ]
        }
        
        self.empathy_responses = {
            'frustrated': [
                "I completely understand your frustration, and I'm here to help resolve this.",
                "I can hear that this has been really frustrating for you. Let's work together to fix this.",
                "Your frustration is completely valid. I want to make this right for you.",
                "I'm sorry this has been such a hassle. Let me see what I can do to help."
            ],
            'worried': [
                "I understand this is concerning for you. Let me help put your mind at ease.",
                "I can sense your worry about this situation. We'll take good care of you.",
                "Your concerns are completely understandable. I'm here to help you through this.",
                "I know this can be stressful. Let me walk you through what we can do."
            ],
            'disappointed': [
                "I'm truly sorry to hear about your disappointment. That's not the experience we want for you.",
                "I can understand why you'd feel disappointed. Let's see how we can improve this situation.",
                "Your disappointment is completely justified. I want to make this better for you.",
                "I'm sorry we've let you down. Let me see what we can do to turn this around."
            ],
            'urgent': [
                "I understand this is urgent for you. Let me see what we can do to help you as quickly as possible.",
                "I can hear the urgency in your situation. Let me prioritize this for you.",
                "Time is important here, I get that. Let me find the fastest solution for you.",
                "I understand you need this resolved quickly. Let me see our earliest availability."
            ],
            'confused': [
                "I can see why this might be confusing. Let me clarify that for you.",
                "No worries about the confusion. I'm here to help explain everything clearly.",
                "That's a great question, and I'm happy to walk you through it step by step.",
                "Let me break this down for you so it's easier to understand."
            ],
            'grateful': [
                "You're very welcome! I'm happy I could help.",
                "It's my pleasure to help. That's what we're here for!",
                "Thank you for saying that! I'm glad we could take care of you.",
                "I appreciate your kind words. It means a lot to know we're helping."
            ]
        }
        
        self.situation_empathy = {
            'home_damage': "Dealing with home repairs can be really stressful. We understand how important your home is to you.",
            'emergency_repair': "Emergency situations are never convenient. We're here to help you get through this.",
            'repeat_customer': "Thank you for continuing to trust us with your home repair needs.",
            'first_time_customer': "Welcome! We understand that finding a reliable handyman service can be challenging.",
            'elderly_customer': "We take extra care to ensure our senior customers feel comfortable and well-informed.",
            'busy_schedule': "I know how hard it can be to find time in a busy schedule. We'll work around your availability."
        }
    
    def detect_emotions(self, message: str) -> Dict[str, float]:
        """Detect emotional content in customer message"""
        message_lower = message.lower()
        detected_emotions = {}
        
        for emotion, keywords in self.emotion_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in message_lower:
                    score += 1
            
            if score > 0:
                # Normalize score based on message length
                normalized_score = min(score / len(message.split()) * 10, 1.0)
                detected_emotions[emotion] = normalized_score
        
        return detected_emotions
    
    def generate_empathy_response(self, emotions: Dict[str, float], context: Optional[Dict] = None) -> str:
        """Generate appropriate empathetic response based on detected emotions"""
        if not emotions:
            return ""
        
        # Get the strongest emotion
        primary_emotion = max(emotions.items(), key=lambda x: x[1])
        emotion_type = primary_emotion[0]
        
        # Select response from appropriate category
        responses = self.empathy_responses.get(emotion_type, [])
        if responses:
            # Use first response for consistency, but could randomize
            return responses[0]
        
        return ""
    
    def add_situational_empathy(self, base_response: str, situation: str) -> str:
        """Add situational empathy to base response"""
        empathy_addition = self.situation_empathy.get(situation, "")
        
        if empathy_addition:
            return f"{empathy_addition} {base_response}"
        
        return base_response
    
    def analyze_customer_state(self, message: str, context: Optional[Dict] = None) -> Dict:
        """Comprehensive analysis of customer emotional state"""
        emotions = self.detect_emotions(message)
        
        # Determine overall sentiment
        negative_emotions = ['frustrated', 'worried', 'disappointed']
        positive_emotions = ['grateful']
        neutral_emotions = ['confused', 'urgent']
        
        sentiment = 'neutral'
        if any(emotion in emotions for emotion in negative_emotions):
            sentiment = 'negative'
        elif any(emotion in emotions for emotion in positive_emotions):
            sentiment = 'positive'
        
        # Determine urgency level
        urgency_level = 'normal'
        if 'urgent' in emotions:
            urgency_level = 'high'
        elif sentiment == 'negative':
            urgency_level = 'elevated'
        
        # Determine communication style needed
        communication_style = 'standard'
        if sentiment == 'negative':
            communication_style = 'extra_supportive'
        elif 'confused' in emotions:
            communication_style = 'explanatory'
        elif sentiment == 'positive':
            communication_style = 'appreciative'
        
        return {
            'emotions': emotions,
            'sentiment': sentiment,
            'urgency_level': urgency_level,
            'communication_style': communication_style,
            'needs_empathy': sentiment == 'negative' or 'worried' in emotions
        }
    
    def create_empathetic_opening(self, customer_state: Dict) -> str:
        """Create an empathetic opening based on customer state"""
        if not customer_state.get('needs_empathy'):
            return ""
        
        emotions = customer_state.get('emotions', {})
        primary_emotion = max(emotions.items(), key=lambda x: x[1])[0] if emotions else None
        
        return self.generate_empathy_response({primary_emotion: 1.0} if primary_emotion else {})
    
    def adjust_tone_for_empathy(self, response: str, customer_state: Dict) -> str:
        """Adjust response tone based on customer emotional state"""
        style = customer_state.get('communication_style', 'standard')
        
        if style == 'extra_supportive':
            # Add supportive language
            if not any(word in response.lower() for word in ['understand', 'sorry', 'help']):
                response = f"I want to help you with this. {response}"
        
        elif style == 'explanatory':
            # Make response more detailed and clear
            if '.' in response and not response.endswith('?'):
                response += " Please let me know if you need me to clarify anything."
        
        elif style == 'appreciative':
            # Add positive reinforcement
            if not any(word in response.lower() for word in ['thank', 'appreciate', 'glad']):
                response += " Thank you for choosing our services!"
        
        return response
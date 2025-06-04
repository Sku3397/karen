"""
Small Talk Engine
Provides natural conversation capabilities for building rapport with customers
"""

from datetime import datetime, date
import random
from typing import List, Dict, Optional

class SmallTalkEngine:
    def __init__(self):
        self.weather_responses = {
            'good': [
                "It's such a beautiful day today! Perfect weather for getting some projects done around the house.",
                "Lovely weather we're having! I hope you're able to enjoy it.",
                "What a nice day! Great weather for any outdoor work you might need done."
            ],
            'bad': [
                "I hope you're staying warm and dry with this weather!",
                "This weather definitely makes you appreciate being indoors! Is your heating system working well?",
                "Weather like this can really put a strain on homes. I hope everything is holding up well for you."
            ],
            'seasonal': {
                'spring': "Spring is such a great time for home maintenance! Are you planning any spring cleaning projects?",
                'summer': "Summer weather is perfect for those outdoor projects. Anything on your home improvement list?",
                'fall': "Fall is the perfect time to prepare your home for winter. Any winterizing projects on your mind?",
                'winter': "Winter weather can be tough on homes. How is your heating system treating you?"
            }
        }
        
        self.time_based_comments = {
            'morning': [
                "Good morning! I hope you're having a great start to your day.",
                "Early bird! I love that you're getting an early start on taking care of your home.",
                "Morning is such a productive time. What can we help you accomplish today?"
            ],
            'afternoon': [
                "Good afternoon! I hope your day is going well so far.",
                "Perfect timing for an afternoon call! How can we help brighten your day?",
                "Afternoon is a great time to tackle those home projects. What's on your list?"
            ],
            'evening': [
                "Good evening! I hope you've had a productive day.",
                "Evening calls often mean something needs attention. We're here to help!",
                "End of the day is a good time to plan ahead. What can we help you with?"
            ]
        }
        
        self.local_references = {
            'virginia_beach': [
                "The oceanfront keeps homes busy with maintenance, doesn't it?",
                "Salt air can be tough on homes. Regular maintenance is so important here.",
                "Living near the beach has its perks, but it does keep us handymen busy!"
            ],
            'norfolk': [
                "Historic homes in Norfolk have such character, but they need good care.",
                "The Norfolk area has such beautiful neighborhoods. We love working in this area.",
                "Norfolk homeowners really take pride in their properties. We appreciate that!"
            ],
            'chesapeake': [
                "Chesapeake has such lovely residential areas. We enjoy working out that way.",
                "The Chesapeake area has grown so much! Lots of homes needing good maintenance.",
                "Rural areas like parts of Chesapeake have unique home maintenance needs."
            ]
        }
        
        self.rapport_builders = {
            'homeowner_pride': [
                "I can tell you really take care of your home. That's wonderful to see.",
                "It's clear your home means a lot to you. We appreciate homeowners like you.",
                "You're being so proactive about maintenance. Your home is lucky to have you!"
            ],
            'repeat_customer': [
                "It's always great to hear from you again!",
                "Thanks for thinking of us again. We really appreciate your continued trust.",
                "So nice to work with you again. How has everything been since our last visit?"
            ],
            'referral': [
                "We're so grateful for referrals! Word of mouth means everything to small businesses like ours.",
                "Thank you for the referral! Your friend has great taste in recommendations.",
                "Referrals are the best compliment we can receive. Thank you so much!"
            ]
        }
        
        self.conversation_bridges = [
            "Speaking of that, how can we help you today?",
            "That reminds me, what brings you to call us today?",
            "On that note, what can we take care of for you?",
            "That's great! Now, what project can we help you with?",
            "I'm glad to hear that! What can we do for you today?"
        ]
    
    def get_time_appropriate_comment(self) -> str:
        """Get a comment appropriate for the current time of day"""
        current_hour = datetime.now().hour
        
        if 5 <= current_hour < 12:
            time_period = 'morning'
        elif 12 <= current_hour < 17:
            time_period = 'afternoon'
        else:
            time_period = 'evening'
        
        comments = self.time_based_comments.get(time_period, [])
        return random.choice(comments) if comments else ""
    
    def get_seasonal_comment(self) -> str:
        """Get a seasonal comment based on current date"""
        current_month = datetime.now().month
        
        if 3 <= current_month <= 5:
            season = 'spring'
        elif 6 <= current_month <= 8:
            season = 'summer'
        elif 9 <= current_month <= 11:
            season = 'fall'
        else:
            season = 'winter'
        
        return self.weather_responses['seasonal'].get(season, "")
    
    def detect_small_talk_opportunity(self, customer_message: str) -> Optional[str]:
        """Detect opportunities for appropriate small talk in customer message"""
        message_lower = customer_message.lower()
        
        # Weather mentions
        weather_keywords = ['weather', 'rain', 'snow', 'hot', 'cold', 'sunny', 'cloudy', 'storm', 'beautiful day', 'nice day', 'lovely day', 'perfect day', 'gorgeous day']
        if any(keyword in message_lower for keyword in weather_keywords):
            return 'weather'
        
        # Location mentions
        location_keywords = ['virginia beach', 'norfolk', 'chesapeake', 'hampton roads', 'beach', 'oceanfront']
        if any(keyword in message_lower for keyword in location_keywords):
            return 'location'
        
        # Time references
        time_keywords = ['morning', 'afternoon', 'evening', 'early', 'late', 'busy day', 'long day']
        if any(keyword in message_lower for keyword in time_keywords):
            return 'time'
        
        # Home pride indicators
        pride_keywords = ['love my home', 'proud of', 'take care of', 'maintain', 'keep up']
        if any(keyword in message_lower for keyword in pride_keywords):
            return 'home_pride'
        
        return None
    
    def generate_small_talk_response(self, opportunity_type: str, context: Optional[Dict] = None) -> str:
        """Generate appropriate small talk response"""
        if opportunity_type == 'weather':
            return random.choice(self.weather_responses['good'])
        
        elif opportunity_type == 'location':
            # Try to detect specific location
            if context and 'message' in context:
                message_lower = context['message'].lower()
                for location, responses in self.local_references.items():
                    if location.replace('_', ' ') in message_lower:
                        return random.choice(responses)
            return "We love working in the Hampton Roads area! Great community here."
        
        elif opportunity_type == 'time':
            return self.get_time_appropriate_comment()
        
        elif opportunity_type == 'home_pride':
            return random.choice(self.rapport_builders['homeowner_pride'])
        
        return ""
    
    def add_conversation_bridge(self, small_talk: str) -> str:
        """Add a natural bridge from small talk to business"""
        if small_talk:
            bridge = random.choice(self.conversation_bridges)
            return f"{small_talk} {bridge}"
        return ""
    
    def create_rapport_building_opener(self, customer_type: str = 'new') -> str:
        """Create an opening that builds rapport based on customer type"""
        if customer_type == 'repeat':
            return random.choice(self.rapport_builders['repeat_customer'])
        elif customer_type == 'referral':
            return random.choice(self.rapport_builders['referral'])
        else:
            return self.get_time_appropriate_comment()
    
    def suggest_follow_up_small_talk(self, service_type: str) -> str:
        """Suggest relevant small talk based on service type"""
        follow_ups = {
            'plumbing': "Plumbing issues always seem to happen at the most inconvenient times, don't they?",
            'electrical': "Electrical work is so important for safety and peace of mind.",
            'hvac': "A comfortable home temperature makes such a difference in daily life.",
            'general': "Home maintenance never really ends, but that's what keeps your house a home!"
        }
        
        return follow_ups.get(service_type, follow_ups['general'])
    
    def handle_customer_small_talk(self, customer_message: str) -> str:
        """Respond appropriately to customer-initiated small talk"""
        message_lower = customer_message.lower()
        
        # Positive responses
        if any(word in message_lower for word in ['great', 'good', 'wonderful', 'excellent', 'fantastic']):
            return "That's wonderful to hear! "
        
        # Negative responses  
        elif any(word in message_lower for word in ['terrible', 'awful', 'bad', 'horrible', 'rough']):
            return "I'm sorry to hear that. I hope we can help make your day a little better! "
        
        # Neutral acknowledgment
        elif any(word in message_lower for word in ['busy', 'okay', 'alright', 'fine']):
            return "I understand. "
        
        return "I appreciate you sharing that. "
    
    def get_closing_small_talk(self, appointment_scheduled: bool = False) -> str:
        """Get appropriate closing small talk"""
        if appointment_scheduled:
            closings = [
                "We look forward to seeing you soon!",
                "Thanks again for choosing us. Have a great rest of your day!",
                "We'll take good care of you. Enjoy the rest of your day!"
            ]
        else:
            closings = [
                "Feel free to call us anytime. Have a wonderful day!",
                "Thanks for thinking of us. Enjoy your day!",
                "We're here whenever you need us. Take care!"
            ]
        
        return random.choice(closings)
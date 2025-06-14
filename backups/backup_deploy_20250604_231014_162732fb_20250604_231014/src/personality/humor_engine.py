"""
Karen's humor engine - safe, appropriate humor for customer interactions
"""
from typing import Dict, List, Optional
import random
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class HumorEngine:
    def __init__(self):
        # Light, safe humor that builds rapport without being unprofessional
        self.situational_humor = {
            'scheduling': [
                "I'll pencil you in... well, actually it's digital, but you get the idea!",
                "Let me check our calendar - it's busier than a bee in a flower garden!",
                "Time management is like home repair - it's all about having the right tools!"
            ],
            'weather': [
                "At least your plumbing problems are indoors where it's dry!",
                "Good thing we're fixing things inside - much more comfortable than this weather!",
                "Home repairs wait for no weather - rain or shine, we're on it!"
            ],
            'technology': [
                "Technology is great when it works... kind of like that leaky faucet, right?",
                "Sometimes I think smart homes are smarter than their owners - myself included!",
                "The good news is, a hammer never needs a software update!"
            ],
            'home_ownership': [
                "Home ownership: where every weekend project becomes a week-long adventure!",
                "They say home is where the heart is... and apparently where all the repairs are too!",
                "Houses are like teenagers - right when you think everything's fine, something breaks!"
            ]
        }
        
        self.gentle_observations = {
            'diy_attempts': [
                "DIY videos make it look so easy, don't they? We're here when reality kicks in!",
                "YouTube University is great, but sometimes you need the professionals!",
                "We've all been there - started a simple project and suddenly it's... not so simple!",
                "Pinterest had such high hopes for that project, didn't it?"
            ],
            'timing': [
                "Things always seem to break at the most interesting times, don't they?",
                "It's like appliances have a sixth sense for the worst possible timing!",
                "Murphy's Law of home repair: everything breaks right before company comes over!"
            ],
            'tools': [
                "The most dangerous tool in any house? The confidence of someone who just watched a YouTube video!",
                "We have all the tools, including the one that matters most - experience!",
                "Sometimes the best tool is knowing when to call the professionals!"
            ]
        }
        
        # Safe, family-friendly puns and wordplay
        self.light_puns = {
            'plumbing': [
                "We're really good at going with the flow!",
                "Don't worry, we'll get everything flowing smoothly again!",
                "We're not just good plumbers - we're drain-right fantastic!"
            ],
            'electrical': [
                "We're positively charged about fixing your electrical issues!",
                "Current situation got you amped up? We'll help you stay grounded!",
                "We're here to brighten your day... literally!"
            ],
            'carpentry': [
                "We nail it every time!",
                "Wood you believe how good we are at this?",
                "We're board-certified in making things right!"
            ],
            'general': [
                "We're screwing around... but only with the actual screws!",
                "We're pretty handy at being handy!",
                "We're level-headed about getting everything level!"
            ]
        }
        
        # Warm, encouraging humor for stressed customers
        self.stress_relief_humor = [
            "Don't worry - we've seen worse, and we fixed that too!",
            "Every home has its quirks. Think of it as... character building!",
            "On the bright side, at least you'll have a great story to tell afterward!",
            "We like to think of home repairs as adventures... just adventures that end with everything working!",
            "The good news is, once we fix this, it'll probably outlast everything else in the house!"
        ]
        
        # Holiday and seasonal humor
        self.seasonal_humor = {
            'spring': [
                "Spring cleaning revealed some surprises, did it?",
                "Ah, spring - when we discover what winter did to our homes!",
                "Spring: the season of renewal... and home repair revelations!"
            ],
            'summer': [
                "Summer heat bringing out the best in your AC system, I see!",
                "Nothing says summer like... indoor plumbing problems!",
                "Hot weather means we appreciate working in air conditioning even more!"
            ],
            'fall': [
                "Fall means leaves are falling... hopefully nothing else is!",
                "Autumn: when we prep for winter and hope everything holds together!",
                "Fall maintenance is like raking leaves - better to stay on top of it!"
            ],
            'winter': [
                "Winter: when you really appreciate indoor heating!",
                "Cold weather finds every little crack and leak, doesn't it?",
                "Winter is nature's way of testing all our home systems at once!"
            ]
        }
        
    def add_appropriate_humor(self, message: str, context: Dict) -> str:
        """Add light, appropriate humor when suitable"""
        # Only add humor if the situation is appropriate
        if context.get('emergency') or context.get('upset_customer'):
            return message  # No humor in serious situations
            
        humor_chance = context.get('humor_level', 0.3)  # Default 30% chance
        
        if random.random() > humor_chance:
            return message  # Skip humor this time
            
        situation = context.get('situation', 'general')
        humor_type = context.get('humor_type', 'situational')
        
        if humor_type == 'pun' and situation in self.light_puns:
            humor = random.choice(self.light_puns[situation])
        elif situation in self.situational_humor:
            humor = random.choice(self.situational_humor[situation])
        else:
            # Default to gentle stress relief
            humor = random.choice(self.stress_relief_humor)
            
        return f"{message} {humor}"
    
    def get_seasonal_humor(self) -> Optional[str]:
        """Get seasonal humor based on current time"""
        month = datetime.now().month
        
        if month in [3, 4, 5]:  # Spring
            return random.choice(self.seasonal_humor['spring'])
        elif month in [6, 7, 8]:  # Summer
            return random.choice(self.seasonal_humor['summer'])
        elif month in [9, 10, 11]:  # Fall
            return random.choice(self.seasonal_humor['fall'])
        elif month in [12, 1, 2]:  # Winter
            return random.choice(self.seasonal_humor['winter'])
            
        return None
    
    def respond_to_diy_mention(self) -> str:
        """Special humor for DIY situations"""
        return random.choice(self.gentle_observations['diy_attempts'])
    
    def lighten_bad_timing_situation(self) -> str:
        """Humor for when things break at bad times"""
        return random.choice(self.gentle_observations['timing'])
    
    def add_tool_humor(self, message: str) -> str:
        """Add tool-related humor"""
        tool_joke = random.choice(self.gentle_observations['tools'])
        return f"{message} {tool_joke}"
    
    def get_callback_humor(self) -> str:
        """Light humor for callback situations"""
        callback_humor = [
            "We'll call you back faster than you can say 'honey-do list'!",
            "Consider it done - well, the calling back part is done. The fixing part comes next!",
            "We'll get back to you quicker than that leaky faucet started dripping!"
        ]
        return random.choice(callback_humor)
    
    def defuse_pricing_tension(self) -> str:
        """Light humor to ease pricing discussions"""
        pricing_humor = [
            "Good news - our prices won't require a home equity loan!",
            "We keep our prices as level as our work - fair and square!",
            "Our rates are like our repairs - honest and straightforward!"
        ]
        return random.choice(pricing_humor)
    
    def should_use_humor(self, context: Dict) -> bool:
        """Determine if humor is appropriate for the situation"""
        # Never use humor in these situations
        no_humor_situations = [
            'emergency',
            'safety_issue',
            'upset_customer',
            'complaint',
            'urgent_repair',
            'water_damage',
            'electrical_danger'
        ]
        
        situation = context.get('situation', '')
        customer_mood = context.get('customer_mood', 'neutral')
        
        # Check for situations where humor is inappropriate
        if any(situation in str(context) for situation in no_humor_situations):
            return False
            
        # Check customer mood
        if customer_mood in ['angry', 'frustrated', 'worried', 'stressed']:
            return False
            
        # Time of day considerations
        hour = datetime.now().hour
        if hour < 7 or hour > 21:  # Early morning or late evening calls
            return False
            
        return True
    
    def get_ice_breaker_humor(self) -> str:
        """Safe humor to start conversations on a positive note"""
        ice_breakers = [
            "How's your day going? Besides the whole 'things need fixing' part!",
            "Beautiful day for indoor repairs, right?",
            "What can we tackle for you today? We promise to use our powers for good!",
            "Ready to turn this repair into a success story?"
        ]
        return random.choice(ice_breakers)
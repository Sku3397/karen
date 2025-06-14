"""
Adapt Karen's personality to regional preferences
"""
from typing import Dict, List, Optional
import random
from datetime import datetime
import requests
import logging

logger = logging.getLogger(__name__)

class RegionalAdaptation:
    def __init__(self, region='virginia'):
        self.region = region
        self.adaptations = {
            'virginia': {
                'pace': 'moderate',  # Not too fast, not too slow
                'formality': 'friendly_professional',
                'local_references': [
                    'Norfolk area', 'Hampton Roads', 'the Peninsula',
                    'Virginia Beach', 'the Navy base', 'Chesapeake',
                    'Portsmouth', 'Newport News', 'Suffolk'
                ],
                'weather_talk': True,  # Southerners appreciate weather chat
                'sports_teams': ['Virginia Tech Hokies', 'UVA Cavaliers', 'Washington Nationals', 'Norfolk Admirals'],
                'local_phrases': [
                    "down here in Hampton Roads",
                    "here in the 757",
                    "in our neck of the woods",
                    "around these parts"
                ],
                'seasonal_references': {
                    'spring': 'hurricane season prep',
                    'summer': 'keeping cool in this humidity',
                    'fall': 'getting ready for winter',
                    'winter': 'staying warm during the cold snaps'
                }
            }
        }
        
        self.weather_responses = {
            'sunny': [
                "Beautiful day today!",
                "Perfect weather for some home projects!",
                "Gorgeous day out there!"
            ],
            'rainy': [
                "Good day to tackle those indoor projects!",
                "Perfect weather to be inside working on your home!",
                "Great time to address those interior items!"
            ],
            'hot': [
                "Staying cool in this heat I hope!",
                "Hot one today - good thing we work in air conditioning!",
                "Hope you're staying comfortable in this weather!"
            ],
            'cold': [
                "Staying warm I hope!",
                "Chilly day - perfect time to check that heating system!",
                "Bundle up out there!"
            ]
        }
        
        self.local_knowledge = {
            'traffic_patterns': {
                'hampton_roads_bridge_tunnel': "I know the HRBT can be a pain - we'll plan around traffic!",
                'monitor_merrimac': "Traffic on the Monitor-Merrimac can be tricky - we factor that in!",
                'i64': "I-64 can get backed up - we always plan extra time for travel.",
                'military_traffic': "With all the bases around here, we know traffic can be unpredictable!"
            },
            'local_challenges': {
                'humidity': "This Hampton Roads humidity can be tough on homes - we see it all the time!",
                'salt_air': "Living near the water is beautiful, but that salt air can be hard on fixtures.",
                'flooding': "We know about the flooding issues around here - happy to help with water damage prevention!",
                'military_schedule': "We work around deployment schedules - we know how important that is for military families."
            },
            'local_pride': [
                "We love serving the Hampton Roads community!",
                "Proud to be your local 757 team!",
                "Born and raised here in Hampton Roads - we know this area!",
                "Local business serving local families - that's what we're all about!"
            ]
        }
        
    def adapt_message(self, base_message: str, context: Dict) -> str:
        """Add regional flavor to messages"""
        adapted_message = base_message
        region_config = self.adaptations.get(self.region, {})
        
        # Add weather reference if appropriate
        if region_config.get('weather_talk') and context.get('include_weather'):
            weather_comment = self._get_weather_comment()
            if weather_comment:
                adapted_message = f"{weather_comment} {adapted_message}"
        
        # Add local reference if context suggests it
        if context.get('mention_location'):
            local_phrase = random.choice(region_config.get('local_phrases', []))
            if local_phrase:
                adapted_message = adapted_message.replace(
                    'in the area', f'{local_phrase}'
                ).replace(
                    'locally', f'{local_phrase}'
                )
        
        # Add military-friendly language if indicated
        if context.get('military_customer'):
            adapted_message = self._add_military_sensitivity(adapted_message)
            
        return adapted_message
    
    def _get_weather_comment(self) -> Optional[str]:
        """Get appropriate weather comment based on current conditions"""
        try:
            # In a real implementation, you'd call a weather API
            # For now, we'll simulate based on season
            month = datetime.now().month
            
            if month in [6, 7, 8]:  # Summer
                return random.choice(self.weather_responses['hot'])
            elif month in [12, 1, 2]:  # Winter
                return random.choice(self.weather_responses['cold'])
            elif month in [3, 4, 5, 9, 10, 11]:  # Spring/Fall
                return random.choice(self.weather_responses['sunny'])
                
        except Exception as e:
            logger.warning(f"Could not get weather comment: {e}")
            return None
    
    def _add_military_sensitivity(self, message: str) -> str:
        """Add military-friendly touches to messages"""
        military_adaptations = [
            ("schedule", "schedule around deployments"),
            ("timing", "timing that works with your military schedule"),
            ("emergency", "emergency - we support our service members"),
            ("family", "military family")
        ]
        
        for original, military_version in military_adaptations:
            if original in message.lower():
                message = message.replace(original, military_version)
                
        return message
    
    def get_local_reference(self, context_type: str) -> Optional[str]:
        """Get specific local reference for context"""
        if context_type == 'traffic':
            return random.choice(list(self.local_knowledge['traffic_patterns'].values()))
        elif context_type == 'weather_challenge':
            return random.choice(list(self.local_knowledge['local_challenges'].values()))
        elif context_type == 'pride':
            return random.choice(self.local_knowledge['local_pride'])
        
        return None
    
    def adapt_for_seasonal_context(self, base_message: str) -> str:
        """Add seasonal awareness to messages"""
        month = datetime.now().month
        region_config = self.adaptations.get(self.region, {})
        seasonal_refs = region_config.get('seasonal_references', {})
        
        if month in [3, 4, 5]:  # Spring
            if 'maintenance' in base_message.lower():
                return f"{base_message} Spring is perfect for {seasonal_refs.get('spring', 'seasonal maintenance')}!"
        elif month in [6, 7, 8]:  # Summer
            if 'cooling' in base_message.lower() or 'ac' in base_message.lower():
                return f"{base_message} Especially important for {seasonal_refs.get('summer', 'summer comfort')}!"
        elif month in [9, 10, 11]:  # Fall
            if 'preparation' in base_message.lower():
                return f"{base_message} Great time for {seasonal_refs.get('fall', 'winter preparation')}!"
        elif month in [12, 1, 2]:  # Winter
            if 'heating' in base_message.lower():
                return f"{base_message} Essential for {seasonal_refs.get('winter', 'winter comfort')}!"
                
        return base_message
    
    def get_neighborhood_specific_advice(self, neighborhood: str) -> Optional[str]:
        """Provide neighborhood-specific insights"""
        neighborhood_advice = {
            'norfolk': "Norfolk's historic homes often need special care - we love working on those classic properties!",
            'virginia_beach': "Beach proximity means we see a lot of salt air corrosion - we know how to handle it!",
            'chesapeake': "Chesapeake's newer developments often have modern systems we work with daily!",
            'portsmouth': "Portsmouth's mix of historic and modern homes keeps us on our toes - we love the variety!",
            'newport_news': "Newport News has such diverse housing - from shipyard communities to historic districts!",
            'hampton': "Hampton's waterfront properties need special attention - we're experienced with coastal challenges!",
            'suffolk': "Suffolk's growing so fast - we're keeping up with all the new construction and older home needs!"
        }
        
        return neighborhood_advice.get(neighborhood.lower().replace(' ', '_'))
    
    def adapt_pricing_discussion(self, base_pricing_message: str) -> str:
        """Adapt pricing discussion for local market"""
        local_pricing_context = [
            "We know how important it is to get good value here in Hampton Roads.",
            "As a local business, we keep our prices fair for our neighbors.",
            "We're competitive with the local market and proud of our quality.",
            "Local business, local prices, local quality - that's our promise!"
        ]
        
        pricing_addition = random.choice(local_pricing_context)
        return f"{base_pricing_message} {pricing_addition}"
    
    def handle_competitor_mention(self, competitor_name: str) -> str:
        """Gracefully handle competitor mentions"""
        responses = [
            f"I respect the other local businesses like {competitor_name}. What we focus on is our personal service and local commitment.",
            f"There are good contractors around Hampton Roads. What sets us apart is our 24/7 availability and local roots.",
            f"We work alongside other professionals in the area. Our strength is really listening to what you need.",
            f"The Hampton Roads market has options, which is great! We focus on being the most responsive and reliable choice."
        ]
        
        return random.choice(responses)
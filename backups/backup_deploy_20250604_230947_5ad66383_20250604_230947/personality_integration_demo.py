#!/usr/bin/env python3
"""
Personality System Integration Demo
Demonstrates Karen's personality system with real-world scenarios
"""

import sys
import os
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from personality import ResponseEnhancer, PersonalityConsistencyChecker, CorePersonality

def demonstrate_personality_system():
    """Demonstrate the personality system with various customer scenarios"""
    
    print("🤖 Karen's Personality System - Integration Demo")
    print("=" * 60)
    
    # Initialize components
    enhancer = ResponseEnhancer()
    checker = PersonalityConsistencyChecker()
    core_personality = CorePersonality()
    
    # Real-world customer scenarios
    scenarios = [
        {
            "name": "Emergency Plumbing",
            "customer_message": "HELP! My basement is flooding from a burst pipe! I need someone RIGHT NOW!",
            "basic_response": "We can send someone out for emergency plumbing. Emergency rate is $150/hour.",
            "context": {
                "urgent": True,
                "emergency": True,
                "interaction_type": "emergency",
                "customer_mood": "panicked"
            }
        },
        {
            "name": "Happy Repeat Customer",
            "customer_message": "Hi Karen! You guys did such amazing work on my kitchen last month. Can we schedule something for the bathroom?",
            "basic_response": "We can schedule a bathroom consultation for next week.",
            "context": {
                "customer_type": "repeat",
                "customer_mood": "positive",
                "interaction_type": "service_request"
            }
        },
        {
            "name": "Confused New Customer",
            "customer_message": "I'm not really sure what's wrong... there's this weird noise coming from somewhere in the walls when I turn on the water.",
            "basic_response": "We'll need to investigate to identify the source of the noise.",
            "context": {
                "customer_type": "new",
                "customer_mood": "confused",
                "interaction_type": "diagnostic"
            }
        },
        {
            "name": "Budget-Conscious Customer",
            "customer_message": "I really need this fixed but I'm worried about the cost. Money is tight right now.",
            "basic_response": "Our estimate for the repair is $300-400.",
            "context": {
                "customer_mood": "worried",
                "interaction_type": "estimate"
            }
        },
        {
            "name": "Weather Small Talk",
            "customer_message": "What a beautiful day today! Perfect weather for getting some outdoor projects done.",
            "basic_response": "We can schedule your deck repair for this week.",
            "context": {
                "interaction_type": "scheduling",
                "customer_mood": "positive"
            }
        },
        {
            "name": "Frustrated Customer",
            "customer_message": "This is the third time I'm calling about this! The last two guys you sent couldn't figure out what's wrong!",
            "basic_response": "We'll send our most experienced technician to resolve this issue.",
            "context": {
                "customer_mood": "frustrated",
                "interaction_type": "complaint",
                "customer_type": "repeat"
            }
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n📞 Scenario {i}: {scenario['name']}")
        print("-" * 40)
        print(f"Customer: \"{scenario['customer_message']}\"")
        print(f"Basic Response: \"{scenario['basic_response']}\"")
        
        # Enhance the response
        enhanced_response = enhancer.enhance_response(
            scenario['basic_response'], 
            {
                'customer_message': scenario['customer_message'],
                **scenario['context']
            }
        )
        
        print(f"Karen's Response: \"{enhanced_response}\"")
        
        # Validate personality consistency
        validation = checker.validate_personality_consistency(
            enhanced_response, scenario['context']
        )
        
        print(f"✅ Personality Score: {validation['overall_score']:.2f}/1.0")
        print(f"✅ Consistency: {'PASS' if validation['is_consistent'] else 'FAIL'}")
        
        if not validation['is_consistent']:
            print(f"⚠️  Issues: {validation['feedback']}")
        
        # Show trait breakdown
        traits = validation['trait_scores']
        trait_display = []
        for trait, score in traits.items():
            if score is not None:
                trait_display.append(f"{trait}: {score:.2f}")
        
        if trait_display:
            print(f"📊 Traits: {' | '.join(trait_display)}")
    
    print("\n" + "=" * 60)
    print("🎯 Integration Demo Complete!")
    print("Karen's personality system is ready for production use.")

def test_greeting_variations():
    """Test different greeting styles"""
    print("\n🌅 Testing Greeting Variations")
    print("-" * 30)
    
    core = CorePersonality()
    
    times = ['morning', 'afternoon', 'evening']
    channels = ['phone', 'email', 'sms']
    
    for time_of_day in times:
        for channel in channels:
            greeting = core.get_greeting(time_of_day, channel)
            print(f"{time_of_day.title()} {channel.title()}: {greeting}")

def test_regional_adjustments():
    """Test regional dialect adjustments"""
    print("\n🌍 Testing Regional Adjustments")
    print("-" * 30)
    
    core = CorePersonality()
    
    test_responses = [
        "Thank you for choosing our service.",
        "We'll have that shopping cart moved for you.",
        "Please grab a soft drink from the fridge."
    ]
    
    for response in test_responses:
        adjusted = core.adjust_for_regional_dialect(response, 'virginia')
        if adjusted != response:
            print(f"Original: {response}")
            print(f"Virginia: {adjusted}")
        else:
            print(f"No change: {response}")

if __name__ == "__main__":
    demonstrate_personality_system()
    test_greeting_variations()
    test_regional_adjustments()
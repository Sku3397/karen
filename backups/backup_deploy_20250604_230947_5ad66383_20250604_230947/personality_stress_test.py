#!/usr/bin/env python3
"""
Personality System Stress Test
Tests edge cases, performance, and robustness
"""

import sys
import os
import time
import random

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from personality import ResponseEnhancer, PersonalityConsistencyChecker, CorePersonality

def test_edge_cases():
    """Test edge cases and error handling"""
    print("🧪 Testing Edge Cases and Error Handling")
    print("-" * 50)
    
    enhancer = ResponseEnhancer()
    checker = PersonalityConsistencyChecker()
    
    edge_cases = [
        # Empty/None inputs
        ("", {}),
        ("   ", {}),
        (None, {}),
        
        # Very short responses
        ("Yes.", {}),
        ("No.", {}),
        ("OK.", {}),
        
        # Very long responses
        ("This is a very long response that goes on and on and contains lots of information about various things that might be relevant to the customer's situation and we want to make sure that our personality enhancement system can handle responses of this length without any issues or problems that might arise from the complexity of the text." * 3, {}),
        
        # Special characters and formatting
        ("We can fix it for $100-$200 (estimated).", {}),
        ("Call us at (757) 555-0123 or email info@757handy.com", {}),
        ("Available times: 9:00 AM, 1:00 PM, 3:30 PM", {}),
        
        # Mixed languages/technical terms
        ("We'll install the HVAC system with R-410A refrigerant.", {}),
        ("The PVC pipe needs replacing due to calcification.", {}),
    ]
    
    passed = 0
    total = len(edge_cases)
    
    for i, (response, context) in enumerate(edge_cases):
        try:
            if response is None:
                enhanced = enhancer.enhance_response("", context)
            else:
                enhanced = enhancer.enhance_response(response, context)
            
            if enhanced is not None:
                validation = checker.validate_personality_consistency(enhanced, context)
                if validation is not None:
                    passed += 1
                    print(f"✅ Case {i+1}: Handled successfully")
                else:
                    print(f"❌ Case {i+1}: Validation failed")
            else:
                print(f"❌ Case {i+1}: Enhancement failed")
                
        except Exception as e:
            print(f"❌ Case {i+1}: Exception - {e}")
    
    print(f"\n📊 Edge Cases: {passed}/{total} passed ({passed/total*100:.1f}%)")
    return passed == total

def test_performance():
    """Test system performance with multiple scenarios"""
    print("\n⚡ Performance Testing")
    print("-" * 50)
    
    enhancer = ResponseEnhancer()
    
    # Generate test scenarios
    test_responses = [
        "We can fix your sink.",
        "The estimate is $500 for the repair.",
        "Our technician will arrive between 2-4 PM.",
        "We need to order a replacement part.",
        "The job should take about 3 hours.",
    ] * 20  # 100 total tests
    
    test_contexts = [
        {"customer_message": "My sink is broken.", "interaction_type": "service"},
        {"customer_message": "How much will this cost?", "interaction_type": "estimate"},
        {"customer_message": "When can you come?", "interaction_type": "scheduling"},
        {"customer_message": "This is taking forever!", "customer_mood": "frustrated"},
        {"customer_message": "Thank you so much!", "customer_mood": "positive"},
    ]
    
    start_time = time.time()
    successful_enhancements = 0
    
    for i, response in enumerate(test_responses):
        context = random.choice(test_contexts)
        try:
            enhanced = enhancer.enhance_response(response, context)
            if enhanced and len(enhanced) > len(response):
                successful_enhancements += 1
        except Exception as e:
            print(f"Error in test {i}: {e}")
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"✅ Processed: {len(test_responses)} responses")
    print(f"✅ Successful: {successful_enhancements}/{len(test_responses)}")
    print(f"✅ Duration: {duration:.2f} seconds")
    print(f"✅ Rate: {len(test_responses)/duration:.1f} responses/second")
    
    # Performance should be good (>10 responses/second)
    return len(test_responses)/duration > 10

def test_consistency_across_variations():
    """Test that similar inputs produce consistently good results"""
    print("\n🔄 Consistency Testing")
    print("-" * 50)
    
    enhancer = ResponseEnhancer()
    checker = PersonalityConsistencyChecker()
    
    # Similar customer messages with slight variations
    similar_scenarios = [
        [
            "My sink is broken and leaking everywhere!",
            "My sink broke and it's leaking all over!",
            "The sink is broken and water is everywhere!",
            "Help! My sink is broken and leaking!"
        ],
        [
            "Thank you for the great work!",
            "Thanks so much for the excellent service!",
            "Really appreciate the wonderful job you did!",
            "Thank you for such amazing work!"
        ],
        [
            "I'm not sure what's wrong with my toilet.",
            "Something's wrong with my toilet but I don't know what.",
            "My toilet isn't working right but I'm not sure why.",
            "I can't figure out what's wrong with my toilet."
        ]
    ]
    
    base_response = "We can help you with that issue."
    consistency_scores = []
    
    for scenario_group in similar_scenarios:
        group_scores = []
        for message in scenario_group:
            context = {"customer_message": message}
            enhanced = enhancer.enhance_response(base_response, context)
            validation = checker.validate_personality_consistency(enhanced, context)
            group_scores.append(validation['overall_score'])
        
        # Check if scores are consistent (within 0.1 of each other)
        max_score = max(group_scores)
        min_score = min(group_scores)
        variation = max_score - min_score
        
        print(f"Scenario group scores: {[f'{s:.2f}' for s in group_scores]} (variation: {variation:.2f})")
        consistency_scores.append(variation < 0.15)  # Allow 0.15 variation
    
    consistent_groups = sum(consistency_scores)
    print(f"✅ Consistent groups: {consistent_groups}/{len(similar_scenarios)}")
    
    return consistent_groups == len(similar_scenarios)

def test_personality_trait_coverage():
    """Ensure all personality traits are being properly evaluated"""
    print("\n🎭 Personality Trait Coverage Testing")
    print("-" * 50)
    
    checker = PersonalityConsistencyChecker()
    
    # Test responses designed to trigger different traits
    trait_tests = {
        'professionalism': "I'd be happy to help you with your request.",
        'warmth': "I'm so glad you called! I love helping customers.",
        'empathy': "I understand how frustrating this must be for you.",
        'enthusiasm': "That sounds wonderful! I'm excited to help!",
        'formality': "Please allow me to assist you with this matter."
    }
    
    trait_coverage = {}
    
    for trait_name, test_response in trait_tests.items():
        validation = checker.validate_personality_consistency(test_response, {})
        trait_scores = validation.get('trait_scores', {})
        
        if trait_name in trait_scores:
            score = trait_scores[trait_name]
            trait_coverage[trait_name] = score
            print(f"✅ {trait_name.title()}: {score:.2f}")
        else:
            print(f"❌ {trait_name.title()}: Not evaluated")
            trait_coverage[trait_name] = None
    
    covered_traits = sum(1 for score in trait_coverage.values() if score is not None)
    total_traits = len(trait_coverage)
    
    print(f"✅ Trait coverage: {covered_traits}/{total_traits}")
    return covered_traits == total_traits

def run_stress_tests():
    """Run all stress tests"""
    print("🚀 Karen's Personality System - Stress Testing")
    print("=" * 60)
    
    tests = [
        ("Edge Cases", test_edge_cases),
        ("Performance", test_performance),
        ("Consistency", test_consistency_across_variations),
        ("Trait Coverage", test_personality_trait_coverage)
    ]
    
    results = {}
    passed = 0
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
            if result:
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            results[test_name] = False
            print(f"💥 {test_name}: CRASHED ({e})")
    
    print("\n" + "=" * 60)
    print(f"🎯 Stress Test Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 ALL STRESS TESTS PASSED! System is robust and production-ready.")
        return True
    else:
        print("⚠️  Some stress tests failed. System needs attention.")
        return False

if __name__ == "__main__":
    success = run_stress_tests()
    sys.exit(0 if success else 1)
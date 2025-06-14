#!/usr/bin/env python3
"""
Test 2: NLP Integration Verification
Comprehensive test of all 13 NLP intents and system functionality
"""

import sys
import asyncio
import json
from datetime import datetime

# Add src to path for imports
sys.path.append('src')

from nlp_engine import EnhancedNLPEngine, Intent, get_nlp_engine

async def test_nlp_intents():
    """Test all 13 NLP intents with comprehensive message examples"""
    print("🧠 NLP INTEGRATION VERIFICATION")
    print("=" * 50)
    print(f"Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialize NLP engine
    nlp = get_nlp_engine()
    
    # Comprehensive test messages covering all 13 intents
    test_messages = [
        # 1. EMERGENCY
        ("My toilet is overflowing! Help!", "emergency"),
        ("Emergency! Gas leak in the basement!", "emergency"),
        ("Water pipe burst! Need help ASAP!", "emergency"),
        ("Electrical fire in the kitchen! Urgent!", "emergency"),
        
        # 2. APPOINTMENT_SCHEDULE  
        ("Can I schedule an appointment for Tuesday?", "appointment_schedule"),
        ("When are you available to come out?", "appointment_schedule"),
        ("I need to book a handyman for next week", "appointment_schedule"),
        ("What time slots do you have open tomorrow?", "appointment_schedule"),
        
        # 3. APPOINTMENT_CANCEL
        ("I need to cancel my appointment", "appointment_cancel"),
        ("Can you delete my booking for Friday?", "appointment_cancel"),
        ("Won't be home, please cancel", "appointment_cancel"),
        
        # 4. APPOINTMENT_RESCHEDULE
        ("Can we reschedule for a different time?", "appointment_reschedule"),
        ("Need to move my appointment to Thursday", "appointment_reschedule"),
        ("Change the time to 3pm instead", "appointment_reschedule"),
        
        # 5. QUOTE_REQUEST
        ("How much to fix a leaky faucet?", "quote_request"),
        ("What would you charge for painting a room?", "quote_request"),
        ("I need an estimate for electrical work", "quote_request"),
        ("What are your rates for plumbing?", "quote_request"),
        
        # 6. SERVICE_INQUIRY
        ("Do you install ceiling fans?", "service_inquiry"),
        ("Can you fix broken cabinets?", "service_inquiry"),
        ("I need plumbing repair", "service_inquiry"),
        ("Do you do HVAC maintenance?", "service_inquiry"),
        
        # 7. GENERAL_INQUIRY
        ("What services do you offer?", "general_inquiry"),
        ("Are you licensed and insured?", "general_inquiry"),
        ("How long have you been in business?", "general_inquiry"),
        
        # 8. COMPLAINT
        ("The work wasn't done correctly", "complaint"),
        ("I'm not satisfied with the repair", "complaint"),
        ("This is terrible service", "complaint"),
        ("The job was done wrong", "complaint"),
        
        # 9. COMPLIMENT
        ("Thanks for the great service!", "compliment"),
        ("Excellent work on the plumbing!", "compliment"),
        ("You guys are amazing!", "compliment"),
        ("Perfect job, very professional", "compliment"),
        
        # 10. PAYMENT_INQUIRY
        ("How much do I owe for the work?", "payment_inquiry"),
        ("Can I pay with credit card?", "payment_inquiry"),
        ("When is payment due?", "payment_inquiry"),
        ("Do you take Venmo?", "payment_inquiry"),
        
        # 11. STATUS_CHECK
        ("What's the status on my repair?", "status_check"),
        ("Are you still coming today?", "status_check"),
        ("How's the work going?", "status_check"),
        ("Is the job finished yet?", "status_check"),
        
        # 12. GREETING
        ("Hello, how are you?", "greeting"),
        ("Good morning!", "greeting"),
        ("Hi there", "greeting"),
        ("Hey", "greeting"),
        
        # 13. GOODBYE
        ("Thanks, goodbye!", "goodbye"),
        ("Have a good day", "goodbye"),
        ("Talk to you later", "goodbye"),
        ("Bye for now", "goodbye")
    ]
    
    print(f"Testing {len(test_messages)} messages across all 13 intents...")
    print()
    
    # Track results
    results = {
        'total_tests': len(test_messages),
        'passed': 0,
        'failed': 0,
        'intent_accuracy': {},
        'failed_tests': [],
        'confidence_scores': []
    }
    
    # Test each message
    for i, (message, expected_intent) in enumerate(test_messages, 1):
        try:
            # Analyze the message
            result = await nlp.analyze_text(message)
            
            # Check if intent matches
            actual_intent = result.intent.value if hasattr(result.intent, 'value') else str(result.intent)
            is_correct = actual_intent == expected_intent
            
            # Track results
            if is_correct:
                results['passed'] += 1
                status = "✅ PASS"
            else:
                results['failed'] += 1
                results['failed_tests'].append({
                    'message': message,
                    'expected': expected_intent,
                    'actual': actual_intent,
                    'confidence': result.confidence
                })
                status = "❌ FAIL"
            
            # Track intent-specific accuracy
            if expected_intent not in results['intent_accuracy']:
                results['intent_accuracy'][expected_intent] = {'correct': 0, 'total': 0}
            
            results['intent_accuracy'][expected_intent]['total'] += 1
            if is_correct:
                results['intent_accuracy'][expected_intent]['correct'] += 1
            
            # Track confidence scores
            results['confidence_scores'].append(result.confidence)
            
            # Print result
            print(f"{i:2d}. {status} | Intent: {expected_intent:20} | Confidence: {result.confidence:.2f}")
            print(f"    Message: \"{message}\"")
            print(f"    Expected: {expected_intent}, Got: {actual_intent}")
            
            # Show additional details for interesting cases
            if result.is_urgent or result.priority.value == 'critical':
                print(f"    🚨 Urgent: {result.is_urgent}, Priority: {result.priority.value}")
            
            if result.entities:
                entities_str = ", ".join([f"{e.type}:{e.value}" for e in result.entities])
                print(f"    📋 Entities: {entities_str}")
            
            print()
            
        except Exception as e:
            print(f"{i:2d}. ❌ ERROR | Intent: {expected_intent}")
            print(f"    Message: \"{message}\"")
            print(f"    Error: {str(e)}")
            print()
            results['failed'] += 1
            results['failed_tests'].append({
                'message': message,
                'expected': expected_intent,
                'actual': 'ERROR',
                'error': str(e)
            })
    
    # Print summary
    print("=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    accuracy = (results['passed'] / results['total_tests']) * 100
    avg_confidence = sum(results['confidence_scores']) / len(results['confidence_scores']) if results['confidence_scores'] else 0
    
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Overall Accuracy: {accuracy:.1f}%")
    print(f"Average Confidence: {avg_confidence:.2f}")
    print()
    
    # Intent-specific accuracy
    print("📈 INTENT-SPECIFIC ACCURACY:")
    for intent, stats in results['intent_accuracy'].items():
        intent_accuracy = (stats['correct'] / stats['total']) * 100 if stats['total'] > 0 else 0
        status_emoji = "✅" if intent_accuracy >= 75 else "⚠️" if intent_accuracy >= 50 else "❌"
        print(f"  {status_emoji} {intent:20}: {stats['correct']}/{stats['total']} ({intent_accuracy:.1f}%)")
    
    print()
    
    # Failed tests details
    if results['failed_tests']:
        print("❌ FAILED TESTS DETAILS:")
        for fail in results['failed_tests']:
            print(f"  • \"{fail['message']}\"")
            print(f"    Expected: {fail['expected']}, Got: {fail['actual']}")
            if 'confidence' in fail:
                print(f"    Confidence: {fail['confidence']:.2f}")
            if 'error' in fail:
                print(f"    Error: {fail['error']}")
            print()
    
    # Overall assessment
    print("🎯 OVERALL ASSESSMENT:")
    if accuracy >= 90:
        print("  🟢 EXCELLENT: NLP system is production-ready")
    elif accuracy >= 80:
        print("  🟡 GOOD: NLP system is mostly reliable, minor tuning needed")
    elif accuracy >= 70:
        print("  🟠 ACCEPTABLE: NLP system needs improvement before production")
    else:
        print("  🔴 POOR: NLP system requires significant improvements")
    
    print()
    
    # Save detailed results
    detailed_results = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_tests': results['total_tests'],
            'passed': results['passed'],
            'failed': results['failed'],
            'accuracy_percent': accuracy,
            'average_confidence': avg_confidence
        },
        'intent_accuracy': results['intent_accuracy'],
        'failed_tests': results['failed_tests']
    }
    
    with open('nlp_test_results.json', 'w') as f:
        json.dump(detailed_results, f, indent=2)
    
    print(f"💾 Detailed results saved to: nlp_test_results.json")
    print("=" * 50)
    
    return accuracy >= 80  # Return True if acceptable performance

async def test_entity_extraction():
    """Test entity extraction capabilities"""
    print("\n🔍 ENTITY EXTRACTION TEST")
    print("-" * 30)
    
    nlp = get_nlp_engine()
    
    test_cases = [
        ("Call me at 555-123-4567 tomorrow", ["phone_number"]),
        ("My email is john@example.com", ["email"]),
        ("The address is 123 Main Street", ["address"]),
        ("Schedule for 2:30 PM please", ["time"]),
        ("Come on Monday morning", ["date"]),
        ("The quote was $150 for plumbing work", ["money", "service_type"]),
    ]
    
    entity_score = 0
    total_entities = 0
    
    for message, expected_entity_types in test_cases:
        result = await nlp.analyze_text(message)
        found_types = [e.type for e in result.entities]
        
        print(f"Message: \"{message}\"")
        print(f"Expected entities: {expected_entity_types}")
        print(f"Found entities: {[(e.type, e.value) for e in result.entities]}")
        
        for expected_type in expected_entity_types:
            total_entities += 1
            if expected_type in found_types:
                entity_score += 1
                print(f"  ✅ Found {expected_type}")
            else:
                print(f"  ❌ Missing {expected_type}")
        print()
    
    entity_accuracy = (entity_score / total_entities) * 100 if total_entities > 0 else 0
    print(f"Entity Extraction Accuracy: {entity_accuracy:.1f}% ({entity_score}/{total_entities})")
    
    return entity_accuracy >= 70

async def test_sentiment_analysis():
    """Test sentiment analysis"""
    print("\n😊 SENTIMENT ANALYSIS TEST")
    print("-" * 30)
    
    nlp = get_nlp_engine()
    
    sentiment_tests = [
        ("Thank you so much! Great work!", "positive"),
        ("This is terrible service", "negative"), 
        ("When will you be here?", "neutral"),
        ("EMERGENCY! Water everywhere!", "urgent"),
    ]
    
    sentiment_score = 0
    
    for message, expected_sentiment in sentiment_tests:
        result = await nlp.analyze_text(message)
        actual_sentiment = result.sentiment.value if hasattr(result.sentiment, 'value') else str(result.sentiment)
        
        is_correct = actual_sentiment == expected_sentiment
        status = "✅" if is_correct else "❌"
        
        if is_correct:
            sentiment_score += 1
        
        print(f"{status} \"{message}\"")
        print(f"    Expected: {expected_sentiment}, Got: {actual_sentiment}")
        print(f"    Urgency: {result.is_urgent}, Priority: {result.priority.value}")
        print()
    
    sentiment_accuracy = (sentiment_score / len(sentiment_tests)) * 100
    print(f"Sentiment Analysis Accuracy: {sentiment_accuracy:.1f}% ({sentiment_score}/{len(sentiment_tests)})")
    
    return sentiment_accuracy >= 75

async def main():
    """Run all NLP integration tests"""
    print("🚀 STARTING NLP INTEGRATION VERIFICATION")
    print("=" * 60)
    
    try:
        # Test intent classification (main test)
        intent_success = await test_nlp_intents()
        
        # Test entity extraction
        entity_success = await test_entity_extraction()
        
        # Test sentiment analysis
        sentiment_success = await test_sentiment_analysis()
        
        # Overall results
        print("\n" + "=" * 60)
        print("🏆 FINAL RESULTS")
        print("=" * 60)
        
        tests_results = [
            ("Intent Classification", intent_success),
            ("Entity Extraction", entity_success),
            ("Sentiment Analysis", sentiment_success)
        ]
        
        passed_tests = sum(1 for _, success in tests_results if success)
        total_tests = len(tests_results)
        
        for test_name, success in tests_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}")
        
        print()
        overall_success = passed_tests == total_tests
        
        if overall_success:
            print("🎉 ALL TESTS PASSED! NLP system is ready for production.")
        else:
            print(f"⚠️ {total_tests - passed_tests} test(s) failed. Review and improve before production.")
        
        print(f"Success Rate: {passed_tests}/{total_tests} ({(passed_tests/total_tests)*100:.1f}%)")
        
        return overall_success
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR during NLP testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 
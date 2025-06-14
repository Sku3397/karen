#!/usr/bin/env python3
"""
Test script for NLP integration with SMS/communication features
Validates the enhanced NLP engine and SMS integration
"""

import asyncio
import sys
import os
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.nlp_engine import get_nlp_engine, Intent, Sentiment, Priority
from src.nlu.basic_nlu import parse_async, parse_sync, parse
from src.llm_client import LLMClient

# Test messages covering different intents and scenarios
TEST_MESSAGES = [
    # Emergency messages
    "EMERGENCY! My pipe burst and water is flooding my basement! Help ASAP!",
    "Urgent - no power in my house, electrical issue, need immediate help",
    "Gas leak smell in kitchen - come now please",
    
    # Appointment scheduling
    "Can you schedule an appointment to fix my faucet tomorrow morning?",
    "I need a handyman to come look at my deck this weekend",
    "When are you available to install new outlets?",
    "Book appointment for plumbing repair next Tuesday",
    
    # Quote requests
    "How much would it cost to paint my living room?",
    "Can you give me an estimate for roof repair?",
    "What do you charge for electrical work?",
    "Need a quote for bathroom renovation",
    
    # Service inquiries
    "Do you handle HVAC repairs?",
    "Can you fix ceiling fans?",
    "I need help with drywall repair",
    "My garage door won't open",
    
    # Complaints
    "The work you did last week is terrible, the faucet is still leaking",
    "Very unhappy with the painting job, looks awful",
    "This is the worst service I've ever received",
    
    # Compliments
    "Thank you so much! The electrical work is perfect!",
    "Excellent job on the deck repair, looks amazing",
    "Great service, very professional team",
    
    # General inquiries
    "What are your business hours?",
    "Do you service Virginia Beach?",
    "Hello, I have some questions about your services",
    
    # Payment inquiries
    "How do I pay my invoice?",
    "Can I pay with credit card?",
    "What's my outstanding balance?",
    
    # Status checks
    "What's the status of my repair request?",
    "Are you still coming today?",
    "When will the work be finished?",
    
    # Complex messages with entities
    "Hi Karen, can you schedule me at 2pm tomorrow at 123 Main St for plumbing repair? My phone is 757-555-1234",
    "Need urgent electrical work at my office on Oak Avenue, budget is around $500",
    "Good morning! Please call me at (757) 555-9999 about the kitchen renovation estimate"
]

async def test_nlp_engine_basic():
    """Test basic NLP engine functionality"""
    print("\n=== Testing Basic NLP Engine ===")
    
    # Test without LLM client (rule-based only)
    nlp_engine = get_nlp_engine()
    
    test_message = "Emergency! My pipe burst and I need help immediately!"
    result = await nlp_engine.analyze_text(test_message)
    
    print(f"Text: {test_message}")
    print(f"Intent: {result.intent.value}")
    print(f"Sentiment: {result.sentiment.value}")
    print(f"Priority: {result.priority.value}")
    print(f"Is Urgent: {result.is_urgent}")
    print(f"Keywords: {result.keywords[:5]}")
    print(f"Confidence: {result.confidence}")

async def test_nlp_engine_with_llm():
    """Test NLP engine with LLM integration"""
    print("\n=== Testing NLP Engine with LLM ===")
    
    try:
        # Initialize LLM client
        llm_client = LLMClient()
        nlp_engine = get_nlp_engine(llm_client)
        
        test_message = "Can you give me a quote for fixing my kitchen faucet tomorrow at 2pm?"
        result = await nlp_engine.analyze_text(test_message)
        
        print(f"Text: {test_message}")
        print(f"Intent: {result.intent.value}")
        print(f"Entities: {[f'{e.type}:{e.value}' for e in result.entities]}")
        print(f"Sentiment: {result.sentiment.value}")
        print(f"Priority: {result.priority.value}")
        print(f"Topics: {result.topics}")
        print(f"Is Question: {result.is_question}")
        print(f"Confidence: {result.confidence}")
        
    except Exception as e:
        print(f"LLM test failed (expected if no API key): {e}")
        print("Continuing with rule-based tests...")

async def test_legacy_compatibility():
    """Test backward compatibility with legacy NLU"""
    print("\n=== Testing Legacy Compatibility ===")
    
    test_message = "I need to book an appointment for plumbing repair"
    
    # Legacy sync method
    legacy_result = parse(test_message)
    print(f"Legacy parse: {legacy_result}")
    
    # Enhanced sync method
    enhanced_sync = parse_sync(test_message)
    print(f"Enhanced sync: Intent={enhanced_sync['intent']}, Confidence={enhanced_sync.get('confidence', 'N/A')}")
    
    # Enhanced async method
    enhanced_async = await parse_async(test_message)
    print(f"Enhanced async: Intent={enhanced_async['intent']}, Sentiment={enhanced_async.get('sentiment', 'N/A')}")

async def test_comprehensive_analysis():
    """Test comprehensive analysis on multiple message types"""
    print("\n=== Testing Comprehensive Analysis ===")
    
    nlp_engine = get_nlp_engine()
    
    print("Intent Classification Results:")
    print("-" * 80)
    
    for i, message in enumerate(TEST_MESSAGES[:15], 1):  # Test first 15 messages
        try:
            result = await nlp_engine.analyze_text(message)
            truncated_msg = message[:50] + "..." if len(message) > 50 else message
            
            print(f"{i:2d}. {truncated_msg}")
            print(f"    Intent: {result.intent.value:20} Priority: {result.priority.value:8} "
                  f"Sentiment: {result.sentiment.value:8} Urgent: {result.is_urgent}")
            
            # Show entities if any found
            if result.entities:
                entities_str = ", ".join([f"{e.type}:{e.value}" for e in result.entities[:3]])
                print(f"    Entities: {entities_str}")
            
            print()
            
        except Exception as e:
            print(f"Error processing message {i}: {e}")

async def test_batch_processing():
    """Test batch processing capabilities"""
    print("\n=== Testing Batch Processing ===")
    
    nlp_engine = get_nlp_engine()
    batch_messages = TEST_MESSAGES[:5]
    
    start_time = datetime.now()
    results = await nlp_engine.batch_analyze(batch_messages)
    end_time = datetime.now()
    
    processing_time = (end_time - start_time).total_seconds()
    print(f"Processed {len(batch_messages)} messages in {processing_time:.2f} seconds")
    print(f"Average: {processing_time/len(batch_messages):.3f} seconds per message")
    
    for i, (msg, result) in enumerate(zip(batch_messages, results), 1):
        truncated_msg = msg[:40] + "..." if len(msg) > 40 else msg
        print(f"{i}. {truncated_msg} -> {result.intent.value}")

def test_entity_extraction():
    """Test entity extraction capabilities"""
    print("\n=== Testing Entity Extraction ===")
    
    nlp_engine = get_nlp_engine()
    
    # Test messages with specific entities
    entity_test_messages = [
        "Call me at 757-555-1234 tomorrow at 2:30 PM",
        "My address is 123 Oak Street, Virginia Beach",
        "The repair will cost about $500 dollars",
        "Schedule for next Monday morning around 9am",
        "Email me at john@example.com with the quote"
    ]
    
    async def run_entity_tests():
        for msg in entity_test_messages:
            result = await nlp_engine.analyze_text(msg)
            print(f"Text: {msg}")
            if result.entities:
                for entity in result.entities:
                    print(f"  {entity.type}: {entity.value} (confidence: {entity.confidence:.2f})")
            else:
                print("  No entities found")
            print()
    
    # Run in event loop
    asyncio.run(run_entity_tests())

async def main():
    """Main test runner"""
    print("🔍 NLP Integration Test Suite")
    print("=" * 50)
    
    # Run all tests
    await test_nlp_engine_basic()
    await test_nlp_engine_with_llm()
    await test_legacy_compatibility()
    await test_comprehensive_analysis()
    await test_batch_processing()
    
    # Run synchronous entity test
    test_entity_extraction()
    
    print("\n✅ NLP Integration Tests Complete!")
    print("\nKey Features Tested:")
    print("- Intent classification (rule-based and LLM-enhanced)")
    print("- Entity extraction (phone, email, address, time, money)")
    print("- Sentiment analysis")
    print("- Priority assessment")
    print("- Urgency detection")
    print("- Batch processing")
    print("- Legacy compatibility")
    
    print("\nRecommendations:")
    print("1. Configure GEMINI_API_KEY for enhanced LLM-based analysis")
    print("2. Test with real SMS integration using test_sms_integration.py")
    print("3. Monitor confidence scores and adjust thresholds as needed")
    print("4. Consider training custom models for domain-specific entities")

if __name__ == "__main__":
    # Run the test suite
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n❌ Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
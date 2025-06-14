#!/usr/bin/env python3
"""
NLP Integration Example
Demonstrates how to use the enhanced NLP features in Karen AI

This example shows:
1. Basic NLP analysis 
2. SMS integration with NLP
3. Legacy compatibility
4. Advanced features like batch processing and entity extraction
"""

import asyncio
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.nlp_engine import get_nlp_engine, Intent, Sentiment, Priority
from src.nlu.basic_nlu import parse_async, parse_sync
from src.llm_client import LLMClient

async def basic_nlp_example():
    """Example 1: Basic NLP analysis"""
    print("=== Example 1: Basic NLP Analysis ===\n")
    
    # Initialize NLP engine (rule-based)
    nlp_engine = get_nlp_engine()
    
    # Analyze a customer message
    message = "Emergency! My kitchen sink is overflowing and flooding the floor!"
    result = await nlp_engine.analyze_text(message)
    
    print(f"Customer Message: {message}")
    print(f"Intent: {result.intent.value}")
    print(f"Sentiment: {result.sentiment.value}")
    print(f"Priority: {result.priority.value}")
    print(f"Is Urgent: {result.is_urgent}")
    print(f"Keywords: {result.keywords[:5]}")
    print(f"Confidence: {result.confidence}")
    
    # Use the analysis for business logic
    if result.intent == Intent.EMERGENCY:
        print("\n🚨 EMERGENCY DETECTED - Triggering immediate response protocol")
    elif result.priority == Priority.HIGH:
        print("\n⚡ HIGH PRIORITY - Scheduling within 24 hours")
    else:
        print("\n📝 STANDARD REQUEST - Adding to regular queue")

async def enhanced_nlp_with_llm_example():
    """Example 2: Enhanced NLP with LLM integration"""
    print("\n\n=== Example 2: Enhanced NLP with LLM ===\n")
    
    try:
        # Initialize with LLM client for enhanced analysis
        llm_client = LLMClient()
        nlp_engine = get_nlp_engine(llm_client)
        
        message = "Can you give me a quote for installing new outlets in my home office? I need 4 outlets and my budget is around $300. Best time to call is after 5pm."
        
        # Add conversation context
        context = {
            'conversation_history': [
                "Hi, I need some electrical work done",
                "It's for my home office"
            ],
            'customer_profile': {
                'previous_services': ['plumbing'],
                'preferred_contact_time': 'evening'
            }
        }
        
        result = await nlp_engine.analyze_text(message, context)
        
        print(f"Customer Message: {message}")
        print(f"Intent: {result.intent.value}")
        print(f"Entities Found:")
        for entity in result.entities:
            print(f"  - {entity.type}: {entity.value} (confidence: {entity.confidence:.2f})")
        print(f"Topics: {result.topics}")
        print(f"Is Question: {result.is_question}")
        print(f"Priority: {result.priority.value}")
        
    except Exception as e:
        print(f"LLM integration not available: {e}")
        print("Falling back to rule-based analysis...")
        
        nlp_engine = get_nlp_engine()
        result = await nlp_engine.analyze_text(message)
        print(f"Rule-based analysis - Intent: {result.intent.value}, Priority: {result.priority.value}")

async def sms_integration_example():
    """Example 3: SMS integration with NLP"""
    print("\n\n=== Example 3: SMS Integration with NLP ===\n")
    
    # Simulate SMS webhook data
    sms_webhook_data = {
        'From': '+17575551234',
        'To': '+17573544577',
        'Body': 'Hi Karen, I need to reschedule my appointment for tomorrow. Can we do Wednesday instead?',
        'MessageSid': 'SM123456789'
    }
    
    # This would normally be called by the SMS webhook handler
    nlp_engine = get_nlp_engine()
    
    # Analyze the SMS message
    result = await nlp_engine.analyze_text(sms_webhook_data['Body'])
    
    print(f"SMS from: {sms_webhook_data['From']}")
    print(f"Message: {sms_webhook_data['Body']}")
    print(f"Detected Intent: {result.intent.value}")
    print(f"Sentiment: {result.sentiment.value}")
    print(f"Priority: {result.priority.value}")
    
    # Generate response based on intent
    if result.intent == Intent.APPOINTMENT_RESCHEDULE:
        response = "I can help you reschedule. What day and time works better for you? You can also call us at 757-354-4577 for faster scheduling."
    elif result.intent == Intent.EMERGENCY:
        response = "🚨 Emergency received! We're contacting you immediately at 757-354-4577"
    else:
        response = f"Thank you for your message. We'll respond to your {result.intent.value.replace('_', ' ')} shortly. For immediate assistance, call 757-354-4577."
    
    print(f"Generated Response: {response}")

def legacy_compatibility_example():
    """Example 4: Legacy compatibility"""
    print("\n\n=== Example 4: Legacy Compatibility ===\n")
    
    message = "I need to book an appointment for plumbing repair"
    
    # Legacy synchronous parsing (still works)
    from src.nlu.basic_nlu import parse
    legacy_result = parse(message)
    print(f"Legacy parse result: {legacy_result}")
    
    # Enhanced synchronous parsing
    enhanced_result = parse_sync(message)
    print(f"Enhanced sync result: Intent={enhanced_result['intent']}, Confidence={enhanced_result.get('confidence', 'N/A')}")
    
    print("\nBoth methods work, but enhanced parsing provides more insights!")

async def batch_processing_example():
    """Example 5: Batch processing for analytics"""
    print("\n\n=== Example 5: Batch Processing ===\n")
    
    # Simulate multiple customer messages for analysis
    messages = [
        "Emergency plumbing issue!",
        "Can you schedule an appointment?", 
        "Thank you for the great service!",
        "How much for electrical work?",
        "What are your business hours?"
    ]
    
    nlp_engine = get_nlp_engine()
    
    # Process all messages at once
    results = await nlp_engine.batch_analyze(messages)
    
    print("Batch Analysis Results:")
    print("-" * 40)
    
    intent_counts = {}
    priority_counts = {}
    
    for i, (msg, result) in enumerate(zip(messages, results), 1):
        print(f"{i}. {msg}")
        print(f"   Intent: {result.intent.value}, Priority: {result.priority.value}")
        
        # Count for analytics
        intent_counts[result.intent.value] = intent_counts.get(result.intent.value, 0) + 1
        priority_counts[result.priority.value] = priority_counts.get(result.priority.value, 0) + 1
    
    print(f"\nAnalytics Summary:")
    print(f"Intent distribution: {intent_counts}")
    print(f"Priority distribution: {priority_counts}")

async def customer_profile_example():
    """Example 6: Customer profile enhancement"""
    print("\n\n=== Example 6: Customer Profile Enhancement ===\n")
    
    # Simulate customer conversation history
    customer_messages = [
        "Hi, I need a plumber",
        "It's my kitchen faucet leaking",
        "How much will it cost?",
        "Can you come tomorrow?",
        "Thank you, that was excellent work!"
    ]
    
    nlp_engine = get_nlp_engine()
    customer_profile = {
        'message_count': 0,
        'intents': [],
        'sentiment_history': [],
        'topics': set()
    }
    
    print("Building customer profile from conversation:")
    
    for i, message in enumerate(customer_messages, 1):
        result = await nlp_engine.analyze_text(message)
        
        # Update profile
        customer_profile['message_count'] += 1
        customer_profile['intents'].append(result.intent.value)
        customer_profile['sentiment_history'].append(result.sentiment.value)
        customer_profile['topics'].update(result.topics)
        
        print(f"{i}. {message}")
        print(f"   Intent: {result.intent.value}, Sentiment: {result.sentiment.value}")
    
    print(f"\nFinal Customer Profile:")
    print(f"Total messages: {customer_profile['message_count']}")
    print(f"Intent journey: {' → '.join(customer_profile['intents'])}")
    print(f"Sentiment pattern: {customer_profile['sentiment_history']}")
    print(f"Topics discussed: {list(customer_profile['topics'])}")
    
    # Business insights
    if Intent.COMPLIMENT.value in customer_profile['intents']:
        print("🎉 Happy customer - good candidate for referrals!")
    if customer_profile['sentiment_history'].count('positive') > len(customer_profile['sentiment_history']) // 2:
        print("😊 Overall positive experience")

async def main():
    """Run all examples"""
    print("🤖 Karen AI - NLP Integration Examples")
    print("=" * 50)
    
    # Run all examples
    await basic_nlp_example()
    await enhanced_nlp_with_llm_example()
    await sms_integration_example()
    legacy_compatibility_example()  # Synchronous
    await batch_processing_example()
    await customer_profile_example()
    
    print("\n\n🎯 Integration Complete!")
    print("\nKey Takeaways:")
    print("1. NLP engine provides comprehensive text analysis")
    print("2. SMS integration uses NLP for intelligent responses")
    print("3. Legacy code continues to work with enhanced features")
    print("4. Batch processing enables analytics and insights")
    print("5. Customer profiles are enriched with NLP data")
    print("\nNext Steps:")
    print("- Configure GEMINI_API_KEY for enhanced LLM analysis")
    print("- Test with real SMS messages using Twilio webhooks")
    print("- Customize intent patterns for your specific business needs")
    print("- Set up monitoring and analytics dashboards")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n❌ Examples interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Examples failed: {e}")
        import traceback
        traceback.print_exc()
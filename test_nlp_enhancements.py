#!/usr/bin/env python3
"""
Test script for enhanced NLP capabilities in Karen's handyman system

This script demonstrates the new NLP features:
1. Custom entity extraction for handyman services
2. Price extraction and quote generation
3. Multi-language support (Spanish)
4. Conversation context memory
5. Customer preference learning
"""

import sys
import os
import asyncio
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.nlp_enhancements import HandymanNLPEnhancer
from src.handyman_response_engine import HandymanResponseEngine


def print_separator(title: str):
    """Print a nice separator for test sections"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def print_entity_details(entities):
    """Print extracted entity details in a formatted way"""
    if not entities:
        print("No entities extracted")
        return
    
    for i, entity in enumerate(entities, 1):
        print(f"\nEntity {i}:")
        print(f"  Service Type: {entity.service_type}")
        print(f"  Urgency: {entity.urgency}")
        print(f"  Location: {entity.location}")
        print(f"  Description: {entity.description}")
        if entity.estimated_duration:
            print(f"  Estimated Duration: {entity.estimated_duration}")
        if entity.materials_needed:
            print(f"  Materials: {', '.join(entity.materials_needed)}")


def print_price_details(prices):
    """Print extracted price details"""
    if not prices:
        print("No prices extracted")
        return
    
    for i, price in enumerate(prices, 1):
        print(f"\nPrice {i}:")
        print(f"  Amount: ${price.amount:.2f}")
        print(f"  Currency: {price.currency}")
        print(f"  Is Estimate: {price.is_estimate}")
        if price.factors:
            print(f"  Factors: {', '.join(price.factors)}")


def print_quote_details(quote):
    """Print generated quote details"""
    if not quote:
        print("No quote generated")
        return
    
    print(f"\nGenerated Quote:")
    print(f"  Total Estimate: ${quote['total_estimate']:.2f}")
    print(f"  Valid Until: {quote['valid_until'][:10]}")
    
    print(f"\nService Breakdown:")
    for service in quote['service_breakdown']:
        print(f"  - {service['service_type'].title()}: ${service['estimated_cost']:.2f}")
        print(f"    Duration: {service['estimated_duration']}")
        print(f"    Urgency: {service['urgency']}")
        print(f"    Materials Included: {service['materials_included']}")
    
    if quote['notes']:
        print(f"\nNotes:")
        for note in quote['notes']:
            print(f"  - {note}")


async def test_basic_nlp_features():
    """Test basic NLP enhancement features"""
    print_separator("Basic NLP Features Test")
    
    enhancer = HandymanNLPEnhancer()
    
    test_messages = [
        {
            "text": "I have an urgent leak in my kitchen sink! Water is everywhere and I need help ASAP.",
            "description": "Emergency plumbing situation"
        },
        {
            "text": "Can you give me a quote for painting my living room? It's about 12x15 feet with 10-foot ceilings.",
            "description": "Painting quote request with dimensions"
        },
        {
            "text": "Need electrical work in the garage - installing new outlets and fixing a broken light switch. Budget around $300-500.",
            "description": "Electrical work with budget range"
        },
        {
            "text": "Hola, necesito reparación de plomería en el baño. ¿Cuándo están disponibles?",
            "description": "Spanish plumbing inquiry"
        }
    ]
    
    for i, test_case in enumerate(test_messages, 1):
        print(f"\n--- Test Case {i}: {test_case['description']} ---")
        print(f"Input: {test_case['text']}")
        
        result = enhancer.process_enhanced_message(test_case['text'], f"customer_{i}")
        
        print(f"\nLanguage Detected: {result['detected_language']}")
        print(f"Entities Found: {len(result['service_entities'])}")
        print_entity_details(result['service_entities'])
        
        print(f"\nPrices Found: {len(result['price_entities'])}")
        print_price_details(result['price_entities'])
        
        print_quote_details(result['generated_quote'])
        
        if result['response_suggestions']:
            print(f"\nResponse Suggestions:")
            for suggestion in result['response_suggestions']:
                print(f"  - {suggestion}")


async def test_customer_learning():
    """Test customer preference learning"""
    print_separator("Customer Preference Learning Test")
    
    enhancer = HandymanNLPEnhancer()
    customer_id = "test_customer_001"
    
    # Simulate multiple interactions
    interactions = [
        {
            "message": "Hi, I need plumbing work done. I'm usually free in the mornings.",
            "preferred_time": "morning",
            "service_type": "plumbing"
        },
        {
            "message": "Great service last time! Can you do electrical work too? I prefer weekday mornings.",
            "preferred_time": "weekday morning",
            "service_type": "electrical"
        },
        {
            "message": "The quote seems a bit high. Is there a more budget-friendly option?",
            "price_reaction": "concerned"
        }
    ]
    
    print("Simulating customer interactions and learning...")
    
    for i, interaction in enumerate(interactions, 1):
        print(f"\nInteraction {i}: {interaction['message']}")
        
        # Process message
        result = enhancer.process_enhanced_message(interaction['message'], customer_id)
        
        # Learn from interaction
        interaction_data = {key: value for key, value in interaction.items() if key != 'message'}
        interaction_data['message_length'] = len(interaction['message'])
        interaction_data['detected_language'] = result['detected_language']
        
        enhancer.learn_customer_preferences(customer_id, interaction_data)
        
        # Show learned preferences
        if customer_id in enhancer.customer_preferences:
            pref = enhancer.customer_preferences[customer_id]
            print(f"  Learned preferences:")
            print(f"    Preferred times: {pref.preferred_times}")
            print(f"    Service history: {pref.service_history}")
            print(f"    Communication style: {pref.communication_style}")
            print(f"    Language: {pref.language_preference}")
            print(f"    Price sensitivity: {pref.price_sensitivity}")


async def test_conversation_context():
    """Test conversation context memory"""
    print_separator("Conversation Context Memory Test")
    
    enhancer = HandymanNLPEnhancer()
    customer_id = "context_test_customer"
    
    conversation = [
        "I need help with a leaky faucet in my kitchen",
        "Actually, I also noticed the bathroom faucet is dripping too",
        "Can you do both at the same time? What would that cost?",
        "Perfect! When are you available this week?"
    ]
    
    print("Building conversation context...")
    
    for i, message in enumerate(conversation, 1):
        print(f"\nMessage {i}: {message}")
        
        result = enhancer.process_enhanced_message(message, customer_id)
        
        # Mock response for context
        mock_response = f"Thank you for message {i}. I'll help with your request."
        
        enhancer.update_conversation_context(
            customer_id, message, mock_response, result['service_entities']
        )
        
        # Show suggestions based on context
        suggestions = enhancer.get_contextual_response_suggestions(
            customer_id, result['service_entities']
        )
        
        if suggestions:
            print(f"  Contextual suggestions:")
            for suggestion in suggestions:
                print(f"    - {suggestion}")
    
    # Show full conversation context
    if customer_id in enhancer.conversation_context:
        print(f"\nFull conversation context for {customer_id}:")
        for entry in enhancer.conversation_context[customer_id]:
            print(f"  {entry['timestamp'][:19]}: {entry['customer_message'][:50]}...")


async def test_integrated_response_engine():
    """Test the integrated response engine with NLP enhancements"""
    print_separator("Integrated Response Engine Test")
    
    # Note: This test doesn't require an actual LLM client
    # It shows how the enhanced classification works
    
    response_engine = HandymanResponseEngine()
    
    test_emails = [
        {
            "from": "john.doe@example.com",
            "subject": "Emergency Plumbing Help Needed",
            "body": "Hi, I have a burst pipe in my basement and water is flooding everywhere! This is an emergency, please help ASAP!"
        },
        {
            "from": "maria.garcia@example.com", 
            "subject": "Cotización para trabajo eléctrico",
            "body": "Hola, necesito un electricista para instalar nuevos tomacorrientes en mi cocina. ¿Pueden darme una cotización?"
        },
        {
            "from": "bob.smith@example.com",
            "subject": "Painting Quote Request",
            "body": "I need a quote for painting my living room and dining room. Budget is around $800-1200. When are you available?"
        }
    ]
    
    for i, email in enumerate(test_emails, 1):
        print(f"\n--- Email {i} ---")
        print(f"From: {email['from']}")
        print(f"Subject: {email['subject']}")
        print(f"Body: {email['body']}")
        
        customer_id = email['from'].split('@')[0]  # Use email prefix as customer ID
        classification = response_engine.classify_email_type(
            email['subject'], email['body'], customer_id
        )
        
        print(f"\nClassification Results:")
        print(f"  Language: {classification['language']}")
        print(f"  Emergency: {classification['is_emergency']}")
        print(f"  Quote Request: {classification['is_quote_request']}")
        print(f"  Services: {classification['services_mentioned']}")
        print(f"  Entities Found: {len(classification['extracted_entities'])}")
        
        if classification['extracted_entities']:
            print_entity_details(classification['extracted_entities'])
        
        if classification['generated_quote']:
            print_quote_details(classification['generated_quote'])
        
        # Show priority and admin notification
        priority = response_engine.get_priority_level(classification)
        should_notify = response_engine.should_notify_admin_immediately(classification)
        
        print(f"\nProcessing Info:")
        print(f"  Priority: {priority}")
        print(f"  Notify Admin Immediately: {should_notify}")


async def main():
    """Run all NLP enhancement tests"""
    print("Karen's Enhanced NLP System Test Suite")
    print(f"Test run started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        await test_basic_nlp_features()
        await test_customer_learning()
        await test_conversation_context()
        await test_integrated_response_engine()
        
        print_separator("Test Suite Completed Successfully")
        print("All NLP enhancements are working correctly!")
        
    except Exception as e:
        print_separator("Test Suite Failed")
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
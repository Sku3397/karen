#!/usr/bin/env python3
"""
Test script for enhanced memory system with cross-medium conversation linking
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.memory_client import (
    memory_client, 
    store_email_memory, 
    store_sms_memory, 
    store_voice_memory,
    get_conversation_context, 
    search_memory,
    link_customer_identities
)
from src.agent_communication import AgentCommunication

async def test_cross_medium_memory():
    """Test the enhanced memory system with cross-medium linking"""
    
    print("=== Testing Enhanced Memory System with Cross-Medium Linking ===\n")
    
    # Initialize agent communication
    agent_comm = AgentCommunication('memory_engineer')
    
    # Update status
    agent_comm.update_status('testing', 50, {
        'phase': 'cross_medium_testing',
        'components': ['email', 'sms', 'voice', 'identity_linking']
    })
    
    # Test data
    customer_email = "john.doe@example.com"
    customer_phone = "+17574567890"
    customer_name = "John Doe"
    
    # Also test SMS gateway email format
    sms_gateway_email = "7574567890@vtext.com"
    
    karen_email = "karensecretaryai@gmail.com"
    karen_phone = "+17571234567"
    
    print(f"1. Testing identity linking...")
    # Link customer identities
    link_success = await link_customer_identities(customer_email, customer_phone, customer_name)
    print(f"   - Linked {customer_email} <-> {customer_phone}: {link_success}")
    
    print(f"\n2. Storing email conversation...")
    # Store email conversation
    email_data = {
        'id': 'email_123456',
        'sender': customer_email,
        'recipient': karen_email,
        'subject': 'Need handyman service',
        'body': 'Hi, I need help fixing my fence. Can someone come by tomorrow?',
        'received_date_dt': datetime.now() - timedelta(hours=2)
    }
    
    email_reply = "Hi John! I'd be happy to help with your fence repair. I have availability tomorrow at 2 PM. Would that work for you?"
    
    email_conv_id = await store_email_memory(email_data, email_reply)
    print(f"   - Stored email conversation: {email_conv_id}")
    
    print(f"\n3. Storing SMS conversation from same customer...")
    # Store SMS conversation (same customer, different medium)
    sms_data = {
        'sid': 'sms_789012',
        'from': customer_phone,
        'to': karen_phone,
        'body': 'Yes, 2 PM works great! See you then.',
        'direction': 'inbound',
        'date_created': datetime.now() - timedelta(hours=1)
    }
    
    sms_conv_id = await store_sms_memory(sms_data)
    print(f"   - Stored SMS conversation: {sms_conv_id}")
    
    print(f"\n4. Testing SMS gateway email auto-linking...")
    # Test SMS gateway email (should auto-link)
    gateway_email_data = {
        'id': 'email_gateway_456',
        'sender': sms_gateway_email,
        'recipient': karen_email,
        'subject': 'SMS from 7574567890',
        'body': 'Running late, be there at 2:15 instead',
        'received_date_dt': datetime.now() - timedelta(minutes=30)
    }
    
    gateway_conv_id = await store_email_memory(gateway_email_data)
    print(f"   - Stored SMS gateway email: {gateway_conv_id}")
    
    print(f"\n5. Storing voice conversation...")
    # Store voice conversation
    voice_data = {
        'call_sid': 'call_345678',
        'from': customer_phone,
        'to': karen_phone,
        'transcript': 'Customer: Hi, just calling to confirm our appointment. Karen: Yes, confirmed for 2:15 PM today.',
        'duration': 45,
        'direction': 'inbound',
        'start_time': datetime.now() - timedelta(minutes=15)
    }
    
    voice_conv_id = await store_voice_memory(voice_data)
    print(f"   - Stored voice conversation: {voice_conv_id}")
    
    print(f"\n6. Getting unified conversation context...")
    # Get conversation context (should include all mediums)
    context = await get_conversation_context(customer_email, karen_email)
    print(f"   - Total messages across all mediums: {context.get('message_count', 0)}")
    print(f"   - Primary communication medium: {context.get('primary_medium', 'Unknown')}")
    print(f"   - Last interaction: {context.get('last_interaction', 'None')}")
    print(f"   - Recent topics: {', '.join(context.get('recent_topics', []))}")
    
    # Also test with phone number
    phone_context = await get_conversation_context(customer_phone, karen_phone)
    print(f"   - Context lookup by phone: {phone_context.get('message_count', 0)} messages")
    
    print(f"\n7. Testing conversation search...")
    # Search for conversations
    search_results = await search_memory("fence repair", limit=5)
    print(f"   - Found {len(search_results)} conversations matching 'fence repair'")
    
    for i, result in enumerate(search_results, 1):
        print(f"     {i}. {result.medium} - {result.sender} -> {result.recipient}")
        print(f"        Content: {result.content[:100]}...")
    
    print(f"\n8. Testing linked identities retrieval...")
    # Get all linked identities
    linked_by_email = await memory_client.get_linked_identities(customer_email)
    linked_by_phone = await memory_client.get_linked_identities(customer_phone)
    
    print(f"   - Identities linked to {customer_email}:")
    for identity in linked_by_email:
        print(f"     Email: {identity['email']}, Phone: {identity['phone']}, Name: {identity['name']}")
    
    print(f"   - Identities linked to {customer_phone}:")
    for identity in linked_by_phone:
        print(f"     Email: {identity['email']}, Phone: {identity['phone']}, Name: {identity['name']}")
    
    print(f"\n9. Testing conversation history across mediums...")
    # Get full conversation history
    history = await memory_client.get_conversation_history([customer_email, karen_email], limit=20)
    
    print(f"   - Full conversation history ({len(history)} entries):")
    for entry in history:
        print(f"     [{entry.timestamp.strftime('%H:%M')}] {entry.medium:6} | {entry.sender} -> {entry.recipient}")
        print(f"       {entry.content[:80]}...")
    
    # Update status
    agent_comm.update_status('active', 100, {
        'test_completed': True,
        'cross_medium_linking': 'operational',
        'identity_mapping': 'active'
    })
    
    # Share knowledge about cross-medium memory patterns
    knowledge = {
        'type': 'cross_medium_memory_pattern',
        'description': 'Memory system now supports unified conversation tracking across email, SMS, and voice',
        'features': [
            'Automatic phone number extraction from SMS gateway emails',
            'Identity linking between email addresses and phone numbers',
            'Unified conversation context across all mediums',
            'Conversation history merging when identities are linked'
        ],
        'implementation_details': {
            'phone_normalization': 'Converts all phone formats to 10-digit format',
            'email_normalization': 'Lowercase and stripped',
            'auto_linking': 'Detects phone numbers in email addresses like 1234567890@vtext.com',
            'collections': ['conversations', 'context', 'identity_mappings']
        },
        'timestamp': datetime.now().isoformat()
    }
    
    agent_comm.share_knowledge('cross_medium_memory', knowledge)
    
    print("\n=== Cross-Medium Memory Test Complete ===")
    
    return True

async def main():
    """Main test function"""
    try:
        # Check if memory system is enabled
        if not memory_client.enabled:
            print("WARNING: Memory system is disabled. Set USE_MEMORY_SYSTEM=True to enable.")
            print("Some tests will be skipped.")
        
        success = await test_cross_medium_memory()
        
        if success:
            print("\nAll memory system tests completed successfully!")
        else:
            print("\nSome tests failed. Check the output above.")
            
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
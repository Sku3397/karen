"""
Migration 003: Conversation History Schema
DATABASE-003 Implementation

Creates comprehensive conversation history structure supporting cross-medium
tracking (email, SMS, voice) with NLP analysis and response tracking.
"""

from datetime import datetime
from google.cloud import firestore
import logging

logger = logging.getLogger(__name__)

def up(db: firestore.Client):
    """Apply migration - create conversation history schema"""
    print("🔄 Running migration 003: Conversation History Schema")
    
    # Create sample conversation documents
    conversations = [
        {
            'id': 'conv_20250604_230015_001',
            'customer_id': 'customer_sample_001',
            'conversation_thread_id': 'thread_email_001',
            'external_id': 'gmail_message_id_456',
            
            # Message Details
            'medium': 'email',
            'direction': 'inbound',
            'subject': 'Need help with leaky faucet',
            'content': 'Hi, I have a leaky faucet in my kitchen. It\'s been dripping for a few days and I\'m worried about water damage. Can someone come take a look this week?',
            'content_type': 'text/plain',
            'raw_content': {
                'headers': {
                    'message-id': 'gmail_message_id_456',
                    'from': 'john.doe@example.com',
                    'to': 'hello@757handy.com',
                    'subject': 'Need help with leaky faucet',
                    'date': '2025-06-04T23:00:15Z'
                },
                'body': 'Hi, I have a leaky faucet in my kitchen...',
                'attachments': []
            },
            
            # Contact Info
            'from_address': 'john.doe@example.com',
            'to_address': 'hello@757handy.com',
            'cc_addresses': [],
            'phone_number': None,
            
            # Processing
            'status': 'processed',
            'processing_stage': 'completed',
            
            # NLP Analysis
            'nlp_analysis': {
                'intent': 'service_request',
                'sentiment': 'concerned',
                'priority': 'normal',
                'confidence_score': 0.92,
                'entities': [
                    {'type': 'location', 'value': 'kitchen'},
                    {'type': 'issue', 'value': 'leaky faucet'},
                    {'type': 'timeframe', 'value': 'this week'}
                ],
                'keywords': ['faucet', 'leak', 'kitchen', 'repair', 'water damage'],
                'topics': ['plumbing', 'maintenance', 'repair'],
                'urgency_indicators': ['water damage', 'worried'],
                'action_items': [
                    'Schedule plumbing service call',
                    'Assess faucet leak severity',
                    'Provide repair estimate'
                ]
            },
            
            # Response Info
            'response_id': 'conv_20250604_230020_002',
            'response_template_used': 'service_inquiry_response',
            'response_generated_at': firestore.SERVER_TIMESTAMP,
            'response_method': 'template',
            
            # Timing
            'message_timestamp': firestore.SERVER_TIMESTAMP,
            'received_at': firestore.SERVER_TIMESTAMP,
            'processed_at': firestore.SERVER_TIMESTAMP,
            
            # Metadata
            'metadata': {
                'ip_address': '192.168.1.1',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                'processing_time_ms': 2500,
                'auto_response_triggered': True,
                'customer_timezone': 'America/New_York'
            },
            'agent_id': 'communication_agent',
            'session_id': 'session_20250604_001',
            
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP
        },
        {
            'id': 'conv_20250604_230020_002',
            'customer_id': 'customer_sample_001',
            'conversation_thread_id': 'thread_email_001',
            'external_id': 'sent_response_456',
            
            # Message Details
            'medium': 'email',
            'direction': 'outbound',
            'subject': 'Re: Need help with leaky faucet',
            'content': 'Hi John,\n\nThank you for contacting 757 Handy! I understand you have a leaky faucet in your kitchen and are concerned about potential water damage.\n\nI can schedule one of our licensed plumbers to come assess the situation this week. We have availability:\n- Wednesday afternoon (2-5 PM)\n- Thursday morning (9 AM-12 PM)\n- Friday afternoon (1-4 PM)\n\nOur standard faucet repair starts at $85, which includes diagnosis and minor repairs. If replacement is needed, we\'ll provide a detailed estimate before proceeding.\n\nWould any of these times work for you? Please reply with your preference and I\'ll confirm the appointment.\n\nBest regards,\nKaren\n757 Handy Secretary',
            'content_type': 'text/plain',
            'raw_content': {
                'headers': {
                    'message-id': 'sent_response_456',
                    'from': 'karensecretaryai@gmail.com',
                    'to': 'john.doe@example.com',
                    'subject': 'Re: Need help with leaky faucet',
                    'in-reply-to': 'gmail_message_id_456'
                },
                'body': 'Hi John,\n\nThank you for contacting 757 Handy!...',
                'template_used': 'service_inquiry_response'
            },
            
            # Contact Info
            'from_address': 'karensecretaryai@gmail.com',
            'to_address': 'john.doe@example.com',
            'cc_addresses': [],
            'phone_number': None,
            
            # Processing
            'status': 'sent',
            'processing_stage': 'completed',
            
            # NLP Analysis (for outbound messages, this tracks response quality)
            'nlp_analysis': {
                'response_type': 'service_scheduling',
                'sentiment': 'professional_helpful',
                'includes_pricing': True,
                'includes_availability': True,
                'next_action_clear': True,
                'personalization_score': 0.8,
                'professional_tone_score': 0.95
            },
            
            # Response Info (this IS the response to previous message)
            'response_to_id': 'conv_20250604_230015_001',
            'response_template_used': 'service_inquiry_response',
            'response_generated_at': firestore.SERVER_TIMESTAMP,
            'response_method': 'template',
            
            # Timing
            'message_timestamp': firestore.SERVER_TIMESTAMP,
            'received_at': firestore.SERVER_TIMESTAMP,
            'processed_at': firestore.SERVER_TIMESTAMP,
            
            # Metadata
            'metadata': {
                'generated_response': True,
                'template_version': '1.2',
                'personalization_applied': True,
                'calendar_check_performed': True,
                'pricing_included': True
            },
            'agent_id': 'communication_agent',
            'session_id': 'session_20250604_001',
            
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP
        },
        {
            'id': 'conv_20250604_145030_003',
            'customer_id': 'customer_sample_001',
            'conversation_thread_id': 'thread_sms_001',
            'external_id': 'twilio_msg_789',
            
            # Message Details
            'medium': 'sms',
            'direction': 'inbound',
            'subject': None,
            'content': 'Hey, can you guys come today? The leak got worse overnight 😰',
            'content_type': 'text/plain',
            'raw_content': {
                'twilio_data': {
                    'MessageSid': 'twilio_msg_789',
                    'From': '+12345551234',
                    'To': '+17575551234',
                    'Body': 'Hey, can you guys come today? The leak got worse overnight 😰',
                    'MediaUrl': None
                }
            },
            
            # Contact Info
            'from_address': '+12345551234',
            'to_address': '+17575551234',
            'cc_addresses': [],
            'phone_number': '+12345551234',
            
            # Processing
            'status': 'processed',
            'processing_stage': 'completed',
            
            # NLP Analysis
            'nlp_analysis': {
                'intent': 'urgent_service_request',
                'sentiment': 'worried',
                'priority': 'high',
                'confidence_score': 0.88,
                'entities': [
                    {'type': 'timeframe', 'value': 'today'},
                    {'type': 'issue_escalation', 'value': 'leak got worse'},
                    {'type': 'emotion', 'value': 'worried_emoji'}
                ],
                'keywords': ['today', 'leak', 'worse', 'overnight'],
                'topics': ['plumbing', 'emergency', 'escalation'],
                'urgency_indicators': ['today', 'got worse', 'overnight', '😰'],
                'escalation_detected': True,
                'linked_to_previous_conversation': 'conv_20250604_230015_001'
            },
            
            # Response Info
            'response_id': 'conv_20250604_145035_004',
            'response_template_used': 'urgent_sms_response',
            'response_generated_at': firestore.SERVER_TIMESTAMP,
            'response_method': 'template',
            
            # Timing
            'message_timestamp': firestore.SERVER_TIMESTAMP,
            'received_at': firestore.SERVER_TIMESTAMP,
            'processed_at': firestore.SERVER_TIMESTAMP,
            
            # Metadata
            'metadata': {
                'character_count': 52,
                'contains_emoji': True,
                'escalation_from_email': True,
                'cross_medium_conversation': True,
                'auto_priority_elevated': True
            },
            'agent_id': 'sms_agent',
            'session_id': 'session_20250604_002',
            
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP
        }
    ]
    
    # Create conversation documents
    for conv in conversations:
        conv_ref = db.collection('conversations').document(conv['id'])
        conv_ref.set(conv)
    
    print(f"✅ Created {len(conversations)} conversation documents")
    
    # Create sample attachment
    attachment = {
        'id': 'attach_001',
        'conversation_id': 'conv_20250604_230015_001',
        'file_name': 'kitchen_faucet.jpg',
        'file_type': 'image/jpeg',
        'file_size': 1024576,
        'storage_path': 'gs://karen-attachments/2025/06/04/kitchen_faucet.jpg',
        'content_id': 'image001',
        'is_inline': False,
        'checksum': 'sha256:abc123def456',
        'virus_scan_status': 'clean',
        'virus_scan_result': {
            'scanned_at': firestore.SERVER_TIMESTAMP,
            'engine': 'clamav',
            'result': 'clean',
            'scan_duration_ms': 150
        },
        'created_at': firestore.SERVER_TIMESTAMP
    }
    
    # Create attachment document
    attach_ref = db.collection('conversations').document('conv_20250604_230015_001').collection('attachments').document('attach_001')
    attach_ref.set(attachment)
    print("✅ Created sample attachment document")
    
    # Create conversation analytics summary
    analytics = {
        'customer_id': 'customer_sample_001',
        'type': 'conversation_analytics',
        'period': '30_days',
        'data': {
            'total_conversations': 3,
            'by_medium': {
                'email': 2,
                'sms': 1,
                'voice': 0
            },
            'by_direction': {
                'inbound': 2,
                'outbound': 1
            },
            'response_metrics': {
                'average_response_time_minutes': 5,
                'auto_response_rate': 1.0,
                'customer_satisfaction_score': None
            },
            'intent_distribution': {
                'service_request': 2,
                'urgent_service_request': 1
            },
            'sentiment_distribution': {
                'concerned': 1,
                'worried': 1,
                'professional_helpful': 1
            },
            'cross_medium_conversations': 1,
            'escalations_detected': 1
        },
        'calculated_at': firestore.SERVER_TIMESTAMP,
        'metadata': {
            'migration': '003_conversation_history_schema',
            'sample_data': True
        }
    }
    
    analytics_ref = db.collection('conversation_analytics').document('customer_sample_001_conversations')
    analytics_ref.set(analytics)
    print("✅ Created conversation analytics document")
    
    # Create conversation thread tracking
    thread_tracking = {
        'thread_id': 'thread_email_001',
        'customer_id': 'customer_sample_001',
        'primary_medium': 'email',
        'conversation_ids': ['conv_20250604_230015_001', 'conv_20250604_230020_002'],
        'status': 'active',
        'last_message_at': firestore.SERVER_TIMESTAMP,
        'total_messages': 2,
        'awaiting_response': False,
        'escalated_to_sms': True,
        'escalation_thread_id': 'thread_sms_001',
        'metadata': {
            'original_subject': 'Need help with leaky faucet',
            'service_category': 'plumbing',
            'priority_level': 'normal_escalated_to_high'
        },
        'created_at': firestore.SERVER_TIMESTAMP,
        'updated_at': firestore.SERVER_TIMESTAMP
    }
    
    thread_ref = db.collection('conversation_threads').document('thread_email_001')
    thread_ref.set(thread_tracking)
    print("✅ Created conversation thread tracking document")
    
    # Create cross-medium conversation linking
    cross_medium_link = {
        'customer_id': 'customer_sample_001',
        'linked_conversations': [
            {
                'conversation_id': 'conv_20250604_230015_001',
                'medium': 'email',
                'thread_id': 'thread_email_001',
                'timestamp': firestore.SERVER_TIMESTAMP,
                'role': 'primary'
            },
            {
                'conversation_id': 'conv_20250604_145030_003',
                'medium': 'sms',
                'thread_id': 'thread_sms_001',
                'timestamp': firestore.SERVER_TIMESTAMP,
                'role': 'escalation'
            }
        ],
        'link_type': 'escalation',
        'link_reason': 'customer_urgency_increase',
        'confidence_score': 0.95,
        'detected_by': 'nlp_analysis',
        'context': {
            'original_issue': 'leaky faucet',
            'escalation_trigger': 'leak got worse overnight',
            'time_between_messages_hours': 14.5
        },
        'created_at': firestore.SERVER_TIMESTAMP,
        'updated_at': firestore.SERVER_TIMESTAMP
    }
    
    link_ref = db.collection('cross_medium_links').document('link_email_sms_001')
    link_ref.set(cross_medium_link)
    print("✅ Created cross-medium conversation link")
    
    # Create migration tracking document
    migration_ref = db.collection('_migrations').document('003_conversation_history_schema')
    migration_ref.set({
        'migration_id': '003_conversation_history_schema',
        'applied_at': firestore.SERVER_TIMESTAMP,
        'status': 'completed',
        'description': 'Conversation history schema with cross-medium tracking',
        'collections_created': [
            'conversations',
            'conversations/{id}/attachments',
            'conversation_analytics',
            'conversation_threads',
            'cross_medium_links'
        ],
        'documents_created': len(conversations) + 4  # conversations + attachment + analytics + thread + link
    })
    
    print("✅ Migration 003 completed successfully")

def down(db: firestore.Client):
    """Rollback migration - remove conversation history schema"""
    print("🔄 Rolling back migration 003: Conversation History Schema")
    
    # Remove conversation documents
    conversations_to_remove = [
        'conv_20250604_230015_001',
        'conv_20250604_230020_002', 
        'conv_20250604_145030_003'
    ]
    
    for conv_id in conversations_to_remove:
        # Remove attachments first
        conv_ref = db.collection('conversations').document(conv_id)
        attachments = conv_ref.collection('attachments').get()
        for attach in attachments:
            attach.reference.delete()
            print(f"✅ Removed attachment: {attach.id}")
        
        # Remove conversation
        if conv_ref.get().exists:
            conv_ref.delete()
            print(f"✅ Removed conversation: {conv_id}")
    
    # Remove analytics
    analytics_ref = db.collection('conversation_analytics').document('customer_sample_001_conversations')
    if analytics_ref.get().exists:
        analytics_ref.delete()
        print("✅ Removed conversation analytics document")
    
    # Remove thread tracking
    thread_ref = db.collection('conversation_threads').document('thread_email_001')
    if thread_ref.get().exists:
        thread_ref.delete()
        print("✅ Removed conversation thread document")
    
    # Remove cross-medium link
    link_ref = db.collection('cross_medium_links').document('link_email_sms_001')
    if link_ref.get().exists:
        link_ref.delete()
        print("✅ Removed cross-medium link document")
    
    # Remove migration tracking document
    migration_ref = db.collection('_migrations').document('003_conversation_history_schema')
    if migration_ref.get().exists:
        migration_ref.delete()
        print("✅ Removed migration tracking document")
    
    print("✅ Migration 003 rollback completed")

if __name__ == "__main__":
    from src.firebase_setup import setup_firebase
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python migrations/003_conversation_history_schema.py [up|down]")
        sys.exit(1)
    
    action = sys.argv[1].lower()
    
    try:
        db = setup_firebase()
        
        if action == 'up':
            up(db)
        elif action == 'down':
            down(db)
        else:
            print("Invalid action. Use 'up' or 'down'")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        print(f"Migration failed: {e}")
        sys.exit(1)
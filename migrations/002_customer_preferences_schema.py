"""
Migration 002: Customer Preferences Schema
DATABASE-002 Implementation

Creates comprehensive customer preferences tables with support for
learned preferences, confidence scoring, and multi-medium preferences.
"""

from datetime import datetime
from google.cloud import firestore
import logging

logger = logging.getLogger(__name__)

def up(db: firestore.Client):
    """Apply migration - create customer preferences schema"""
    print("🔄 Running migration 002: Customer Preferences Schema")
    
    # Create sample customer first
    customer_ref = db.collection('customers').document('customer_sample_001')
    customer_data = {
        'id': 'customer_sample_001',
        'external_id': 'ext_001',
        'first_name': 'John',
        'last_name': 'Doe',
        'company_name': None,
        'customer_type': 'individual',
        'primary_email': 'john.doe@example.com',
        'primary_phone': '+1234567890',
        'secondary_email': None,
        'secondary_phone': None,
        'billing_address': {
            'street': '123 Main St',
            'city': 'Virginia Beach',
            'state': 'VA',
            'zip_code': '23451',
            'country': 'USA'
        },
        'service_address': {
            'street': '123 Main St',
            'city': 'Virginia Beach', 
            'state': 'VA',
            'zip_code': '23451',
            'country': 'USA'
        },
        'status': 'active',
        'customer_tier': 'standard',
        'preferred_contact_method': 'email',
        'preferred_contact_time': 'business_hours',
        'communication_style': 'professional',
        'referral_source': 'google_search',
        'customer_since': '2025-01-15',
        'lifetime_value': 1250.00,
        'total_jobs': 5,
        'notes': 'Prefers email communication, has pets',
        'tags': ['pet_owner', 'repeat_customer'],
        'metadata': {
            'property_type': 'single_family',
            'pets': ['dog'],
            'special_instructions': 'Call before arriving'
        },
        'created_at': firestore.SERVER_TIMESTAMP,
        'updated_at': firestore.SERVER_TIMESTAMP,
        'last_contact_at': firestore.SERVER_TIMESTAMP
    }
    customer_ref.set(customer_data)
    print("✅ Created sample customer document")
    
    # Create communication method preferences
    comm_prefs = [
        {
            'id': 'pref_comm_001',
            'customer_id': 'customer_sample_001',
            'preference_type': 'communication_method',
            'preference_key': 'preferred_channel',
            'preference_value': {
                'value': 'email',
                'metadata': {
                    'fallback': 'sms',
                    'business_hours_only': True,
                    'response_time_expectation': 'within_2_hours'
                }
            },
            'confidence_score': 0.92,
            'source': 'learned',
            'medium': 'general',
            'context': {
                'learned_from_pattern': 'always responds to email within 2 hours',
                'interaction_count': 15,
                'success_rate': 0.93,
                'last_email_response_time_minutes': 45
            },
            'learned_from_interaction_id': 'conv_sample_001',
            'learned_at': firestore.SERVER_TIMESTAMP,
            'expires_at': None,
            'is_active': True,
            'priority': 1,
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP,
            'created_by': 'system',
            'updated_by': 'system'
        },
        {
            'id': 'pref_comm_002',
            'customer_id': 'customer_sample_001',
            'preference_type': 'communication_method',
            'preference_key': 'avoid_channels',
            'preference_value': {
                'value': ['voice'],
                'metadata': {
                    'reason': 'customer_stated_preference',
                    'exception_circumstances': ['emergency_only']
                }
            },
            'confidence_score': 0.95,
            'source': 'explicit',
            'medium': 'general',
            'context': {
                'stated_in_conversation': 'Please don\'t call unless emergency',
                'date_stated': '2025-01-20'
            },
            'learned_from_interaction_id': 'conv_sample_003',
            'learned_at': firestore.SERVER_TIMESTAMP,
            'expires_at': None,
            'is_active': True,
            'priority': 1,
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP,
            'created_by': 'system',
            'updated_by': 'system'
        }
    ]
    
    # Create scheduling preferences
    schedule_prefs = [
        {
            'id': 'pref_sched_001',
            'customer_id': 'customer_sample_001',
            'preference_type': 'scheduling',
            'preference_key': 'preferred_days',
            'preference_value': {
                'value': ['tuesday', 'wednesday', 'thursday'],
                'metadata': {
                    'avoid_mondays': 'work_schedule',
                    'avoid_fridays': 'personal_preference'
                }
            },
            'confidence_score': 0.85,
            'source': 'learned',
            'medium': 'general',
            'context': {
                'pattern_observed': 'always reschedules Monday/Friday appointments',
                'successful_appointments': 8,
                'rescheduled_appointments': 3
            },
            'learned_from_interaction_id': None,
            'learned_at': firestore.SERVER_TIMESTAMP,
            'expires_at': None,
            'is_active': True,
            'priority': 2,
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP,
            'created_by': 'system',
            'updated_by': 'system'
        },
        {
            'id': 'pref_sched_002',
            'customer_id': 'customer_sample_001',
            'preference_type': 'scheduling',
            'preference_key': 'preferred_times',
            'preference_value': {
                'value': {'start': '10:00', 'end': '15:00'},
                'metadata': {
                    'timezone': 'America/New_York',
                    'flexibility': 'moderate'
                }
            },
            'confidence_score': 0.78,
            'source': 'learned',
            'medium': 'general',
            'context': {
                'analysis_period_days': 90,
                'appointments_in_range': 6,
                'total_appointments': 8
            },
            'learned_from_interaction_id': None,
            'learned_at': firestore.SERVER_TIMESTAMP,
            'expires_at': None,
            'is_active': True,
            'priority': 2,
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP,
            'created_by': 'system',
            'updated_by': 'system'
        }
    ]
    
    # Create service preferences
    service_prefs = [
        {
            'id': 'pref_service_001',
            'customer_id': 'customer_sample_001',
            'preference_type': 'service',
            'preference_key': 'special_requirements',
            'preference_value': {
                'value': ['pet_friendly', 'remove_shoes'],
                'metadata': {
                    'pet_details': 'friendly golden retriever',
                    'house_rules': 'shoes off at door'
                }
            },
            'confidence_score': 1.0,
            'source': 'explicit',
            'medium': 'general',
            'context': {
                'customer_notes': 'Please be comfortable with dogs and remove shoes',
                'mentioned_multiple_times': True
            },
            'learned_from_interaction_id': 'conv_sample_001',
            'learned_at': firestore.SERVER_TIMESTAMP,
            'expires_at': None,
            'is_active': True,
            'priority': 1,
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP,
            'created_by': 'system',
            'updated_by': 'system'
        }
    ]
    
    # Create communication style preferences
    style_prefs = [
        {
            'id': 'pref_style_001',
            'customer_id': 'customer_sample_001',
            'preference_type': 'communication_style',
            'preference_key': 'formality_level',
            'preference_value': {
                'value': 'professional',
                'metadata': {
                    'uses_formal_language': True,
                    'prefers_detailed_explanations': True
                }
            },
            'confidence_score': 0.88,
            'source': 'learned',
            'medium': 'email',
            'context': {
                'language_analysis': 'formal tone, technical questions',
                'message_length_avg': 250,
                'uses_salutations': True
            },
            'learned_from_interaction_id': None,
            'learned_at': firestore.SERVER_TIMESTAMP,
            'expires_at': None,
            'is_active': True,
            'priority': 2,
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP,
            'created_by': 'system',
            'updated_by': 'system'
        }
    ]
    
    # Insert all preferences
    all_prefs = comm_prefs + schedule_prefs + service_prefs + style_prefs
    
    for pref in all_prefs:
        pref_ref = db.collection('customers').document('customer_sample_001').collection('preferences').document(pref['id'])
        pref_ref.set(pref)
    
    print(f"✅ Created {len(all_prefs)} customer preference documents")
    
    # Create preference analytics summary
    analytics_ref = db.collection('customer_analytics').document('customer_sample_001_preferences')
    analytics_data = {
        'customer_id': 'customer_sample_001',
        'type': 'preference_summary',
        'data': {
            'total_preferences': len(all_prefs),
            'preference_types': ['communication_method', 'scheduling', 'service', 'communication_style'],
            'confidence_distribution': {
                'high_confidence': len([p for p in all_prefs if p['confidence_score'] >= 0.9]),
                'medium_confidence': len([p for p in all_prefs if 0.7 <= p['confidence_score'] < 0.9]),
                'low_confidence': len([p for p in all_prefs if p['confidence_score'] < 0.7])
            },
            'source_distribution': {
                'learned': len([p for p in all_prefs if p['source'] == 'learned']),
                'explicit': len([p for p in all_prefs if p['source'] == 'explicit'])
            },
            'last_updated': firestore.SERVER_TIMESTAMP
        },
        'calculated_at': firestore.SERVER_TIMESTAMP,
        'metadata': {
            'migration': '002_customer_preferences_schema',
            'sample_data': True
        }
    }
    analytics_ref.set(analytics_data)
    print("✅ Created customer preference analytics document")
    
    # Create migration tracking document
    migration_ref = db.collection('_migrations').document('002_customer_preferences_schema')
    migration_ref.set({
        'migration_id': '002_customer_preferences_schema',
        'applied_at': firestore.SERVER_TIMESTAMP,
        'status': 'completed',
        'description': 'Customer preferences schema with sample data',
        'collections_created': [
            'customers/{customer_id}/preferences',
            'customer_analytics'
        ],
        'documents_created': len(all_prefs) + 2  # prefs + customer + analytics
    })
    
    print("✅ Migration 002 completed successfully")

def down(db: firestore.Client):
    """Rollback migration - remove customer preferences schema"""
    print("🔄 Rolling back migration 002: Customer Preferences Schema")
    
    # Remove all preference documents
    customer_ref = db.collection('customers').document('customer_sample_001')
    preferences_ref = customer_ref.collection('preferences')
    
    # Get all preference documents
    docs = preferences_ref.get()
    for doc in docs:
        doc.reference.delete()
        print(f"✅ Removed preference document: {doc.id}")
    
    # Remove customer document
    if customer_ref.get().exists:
        customer_ref.delete()
        print("✅ Removed sample customer document")
    
    # Remove analytics document
    analytics_ref = db.collection('customer_analytics').document('customer_sample_001_preferences')
    if analytics_ref.get().exists:
        analytics_ref.delete()
        print("✅ Removed customer analytics document")
    
    # Remove migration tracking document
    migration_ref = db.collection('_migrations').document('002_customer_preferences_schema')
    if migration_ref.get().exists:
        migration_ref.delete()
        print("✅ Removed migration tracking document")
    
    print("✅ Migration 002 rollback completed")

if __name__ == "__main__":
    from src.firebase_setup import setup_firebase
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python migrations/002_customer_preferences_schema.py [up|down]")
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
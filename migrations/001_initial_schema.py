"""
Migration 001: Initial Schema Setup
DATABASE-001 Implementation

Creates the initial Firestore collections and documents structure for Karen AI.
"""

from datetime import datetime
from google.cloud import firestore

def up(db: firestore.Client):
    """Apply migration - create initial schema"""
    print("🔄 Running migration 001: Initial Schema Setup")
    
    # Create tasks collection structure
    task_sample = {
        'title': 'Sample Task',
        'description': 'This is a sample task to establish the schema',
        'status': 'completed',  # Mark as completed so it doesn't interfere
        'assigned_agent_id': None,
        'dependencies': [],
        'created_at': firestore.SERVER_TIMESTAMP,
        'updated_at': firestore.SERVER_TIMESTAMP,
        'metadata': {
            'migration': '001_initial_schema',
            'sample_data': True
        }
    }
    
    # Create agents collection structure
    agent_sample = {
        'name': 'Sample Agent',
        'type': 'task_manager',
        'status': 'inactive',
        'capabilities': ['task_management', 'dependency_tracking'],
        'created_at': firestore.SERVER_TIMESTAMP,
        'last_active': firestore.SERVER_TIMESTAMP,
        'metadata': {
            'migration': '001_initial_schema',
            'sample_data': True
        }
    }
    
    # Create customers collection structure
    customer_sample = {
        'name': 'Sample Customer',
        'email': 'sample@example.com',
        'phone': '+1234567890',
        'created_at': firestore.SERVER_TIMESTAMP,
        'last_contact': firestore.SERVER_TIMESTAMP,
        'status': 'active',
        'metadata': {
            'migration': '001_initial_schema',
            'sample_data': True
        }
    }
    
    # Create conversations collection structure
    conversation_sample = {
        'customer_id': 'sample_customer',
        'medium': 'email',
        'content': 'Sample conversation content',
        'direction': 'inbound',
        'timestamp': firestore.SERVER_TIMESTAMP,
        'processed': True,
        'metadata': {
            'migration': '001_initial_schema',
            'sample_data': True
        }
    }
    
    # Create preferences collection structure
    preference_sample = {
        'customer_id': 'sample_customer',
        'type': 'communication_preference',
        'value': 'email',
        'confidence': 1.0,
        'learned_at': firestore.SERVER_TIMESTAMP,
        'metadata': {
            'migration': '001_initial_schema',
            'sample_data': True
        }
    }
    
    # Create analytics collection structure
    analytics_sample = {
        'type': 'customer_analytics',
        'customer_id': 'sample_customer',
        'data': {
            'total_conversations': 0,
            'preferred_medium': 'email',
            'contact_frequency': 0.0,
            'value_score': 0.0
        },
        'calculated_at': firestore.SERVER_TIMESTAMP,
        'metadata': {
            'migration': '001_initial_schema',
            'sample_data': True
        }
    }
    
    # Insert sample documents
    collections_data = {
        'tasks': task_sample,
        'agents': agent_sample,
        'customers': customer_sample,
        'conversations': conversation_sample,
        'preferences': preference_sample,
        'analytics': analytics_sample
    }
    
    for collection_name, sample_data in collections_data.items():
        doc_ref = db.collection(collection_name).document(f'migration_001_sample')
        doc_ref.set(sample_data)
        print(f"✅ Created {collection_name} collection with sample document")
    
    # Create migration tracking document
    migration_ref = db.collection('_migrations').document('001_initial_schema')
    migration_ref.set({
        'migration_id': '001_initial_schema',
        'applied_at': firestore.SERVER_TIMESTAMP,
        'status': 'completed',
        'description': 'Initial schema setup with sample documents'
    })
    
    print("✅ Migration 001 completed successfully")

def down(db: firestore.Client):
    """Rollback migration - remove sample documents"""
    print("🔄 Rolling back migration 001: Initial Schema Setup")
    
    collections = ['tasks', 'agents', 'customers', 'conversations', 'preferences', 'analytics']
    
    for collection_name in collections:
        doc_ref = db.collection(collection_name).document('migration_001_sample')
        if doc_ref.get().exists:
            doc_ref.delete()
            print(f"✅ Removed sample document from {collection_name}")
    
    # Remove migration tracking document
    migration_ref = db.collection('_migrations').document('001_initial_schema')
    if migration_ref.get().exists:
        migration_ref.delete()
        print("✅ Removed migration tracking document")
    
    print("✅ Migration 001 rollback completed")

if __name__ == "__main__":
    from src.firebase_setup import setup_firebase
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python migrations/001_initial_schema.py [up|down]")
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
        print(f"Migration failed: {e}")
        sys.exit(1)
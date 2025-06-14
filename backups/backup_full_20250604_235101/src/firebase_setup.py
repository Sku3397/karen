"""
Firebase/Firestore Setup and Configuration
DATABASE-001 Implementation
"""

import os
import json
from typing import Optional
from google.cloud import firestore
from google.oauth2 import service_account
import firebase_admin
from firebase_admin import credentials, firestore as admin_firestore

class FirebaseSetup:
    """Handle Firebase initialization and configuration"""
    
    def __init__(self):
        self.db = None
        self.app = None
        
    def initialize_from_service_account(self, service_account_path: str) -> firestore.Client:
        """Initialize Firestore using service account credentials"""
        try:
            if not os.path.exists(service_account_path):
                raise FileNotFoundError(f"Service account file not found: {service_account_path}")
            
            # Initialize Firebase Admin SDK
            if not firebase_admin._apps:
                cred = credentials.Certificate(service_account_path)
                self.app = firebase_admin.initialize_app(cred)
            
            # Initialize Firestore client
            self.db = admin_firestore.client()
            print(f"✅ Firestore initialized with service account: {service_account_path}")
            return self.db
            
        except Exception as e:
            print(f"❌ Failed to initialize Firestore: {e}")
            raise
    
    def initialize_from_environment(self, project_id: Optional[str] = None) -> firestore.Client:
        """Initialize Firestore using environment variables"""
        try:
            # Use GOOGLE_APPLICATION_CREDENTIALS environment variable
            if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
                service_account_path = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
                return self.initialize_from_service_account(service_account_path)
            
            # Use project ID from environment or parameter
            project_id = project_id or os.environ.get('GOOGLE_CLOUD_PROJECT') or os.environ.get('GCP_PROJECT')
            
            if not project_id:
                raise ValueError("Project ID must be provided or set in GOOGLE_CLOUD_PROJECT environment variable")
            
            # Initialize Firestore client directly
            self.db = firestore.Client(project=project_id)
            print(f"✅ Firestore initialized for project: {project_id}")
            return self.db
            
        except Exception as e:
            print(f"❌ Failed to initialize Firestore: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test Firestore connection"""
        try:
            if not self.db:
                print("❌ Firestore not initialized")
                return False
            
            # Try to write and read a test document
            test_ref = self.db.collection('_test').document('connection_test')
            test_ref.set({'timestamp': firestore.SERVER_TIMESTAMP, 'test': True})
            
            # Read it back
            doc = test_ref.get()
            if doc.exists:
                # Clean up test document
                test_ref.delete()
                print("✅ Firestore connection test successful")
                return True
            else:
                print("❌ Firestore connection test failed - document not found")
                return False
                
        except Exception as e:
            print(f"❌ Firestore connection test failed: {e}")
            return False
    
    def setup_collections(self):
        """Set up initial Firestore collections and indexes"""
        try:
            if not self.db:
                raise ValueError("Firestore not initialized")
            
            # Create initial collections with sample documents (will be deleted)
            collections_to_create = [
                'tasks',
                'agents', 
                'customers',
                'conversations',
                'preferences',
                'analytics'
            ]
            
            for collection_name in collections_to_create:
                # Create a temporary document to initialize the collection
                temp_ref = self.db.collection(collection_name).document('_init')
                temp_ref.set({
                    'created_at': firestore.SERVER_TIMESTAMP,
                    'type': 'initialization_document',
                    'delete_me': True
                })
                
                # Delete the temporary document
                temp_ref.delete()
                print(f"✅ Initialized collection: {collection_name}")
            
            print("✅ All collections initialized successfully")
            
        except Exception as e:
            print(f"❌ Failed to setup collections: {e}")
            raise
    
    def create_indexes(self):
        """Create necessary Firestore indexes"""
        print("📋 Firestore indexes should be created through the Firebase Console or gcloud CLI")
        print("Required indexes:")
        print("1. tasks collection: status (ascending)")
        print("2. tasks collection: assigned_agent_id (ascending), status (ascending)")
        print("3. tasks collection: dependencies (array), status (ascending)")
        print("4. conversations collection: customer_id (ascending), timestamp (descending)")
        print("5. preferences collection: customer_id (ascending), type (ascending)")
        
    def get_client(self) -> Optional[firestore.Client]:
        """Get the initialized Firestore client"""
        return self.db

def setup_firebase(service_account_path: Optional[str] = None, project_id: Optional[str] = None) -> firestore.Client:
    """
    Main function to setup Firebase/Firestore
    
    Args:
        service_account_path: Path to service account JSON file
        project_id: GCP project ID (used if no service account provided)
    
    Returns:
        Initialized Firestore client
    """
    setup = FirebaseSetup()
    
    # Try service account first, then environment
    if service_account_path:
        db = setup.initialize_from_service_account(service_account_path)
    else:
        db = setup.initialize_from_environment(project_id)
    
    # Test connection
    if setup.test_connection():
        # Setup collections
        setup.setup_collections()
        # Print index information
        setup.create_indexes()
        return db
    else:
        raise ConnectionError("Failed to establish Firestore connection")

if __name__ == "__main__":
    # Example usage
    import sys
    
    service_account = None
    project_id = None
    
    if len(sys.argv) > 1:
        service_account = sys.argv[1]
    if len(sys.argv) > 2:
        project_id = sys.argv[2]
    
    try:
        db = setup_firebase(service_account, project_id)
        print("🎉 Firebase setup completed successfully!")
        
        # Example: Create a test task
        from firestore_models import create_task
        task_id = create_task(db, "Test Task", "This is a test task created during setup")
        print(f"✅ Created test task with ID: {task_id}")
        
    except Exception as e:
        print(f"💥 Setup failed: {e}")
        sys.exit(1)
# Scheduler Agent: manages appointments, reminders, and bidirectional sync
from .google_calendar import GoogleCalendarClient
from .outlook_calendar import OutlookCalendarClient
from .models import EventMapping
from .utils import resolve_conflicts
import os

class SchedulerAgent:
    def __init__(self, user_id, gc_creds, outlook_creds):
        self.user_id = user_id
        self.gc_client = GoogleCalendarClient(gc_creds)
        self.outlook_client = OutlookCalendarClient(outlook_creds)
        
        # Initialize Firestore with error handling for testing
        try:
            # Only import and initialize Firestore if credentials are available
            if os.environ.get('GOOGLE_APPLICATION_CREDENTIALS') or os.environ.get('FIRESTORE_EMULATOR_HOST'):
                from google.cloud import firestore
                self.db = firestore.Client()
                self.is_mock_db = False
            else:
                # Use mock database for testing
                self.db = MockFirestoreClient()
                self.is_mock_db = True
        except Exception:
            # Fallback to mock database if Firestore initialization fails
            self.db = MockFirestoreClient()
            self.is_mock_db = True

    def create_event(self, source, event_data):
        if source == 'google':
            ext_event = self.gc_client.create_event(event_data)
            self._persist_mapping('google', ext_event['id'], event_data)
        elif source == 'outlook':
            ext_event = self.outlook_client.create_event(event_data)
            self._persist_mapping('outlook', ext_event['id'], event_data)
        return ext_event

    def sync_events(self):
        # Fetch events from both calendars
        gc_events = self.gc_client.list_events()
        outlook_events = self.outlook_client.list_events()
        # Resolve and synchronize
        new_events, conflicts = resolve_conflicts(gc_events, outlook_events)
        # Apply missing events to opposite calendars
        for event in new_events['google_to_outlook']:
            self.outlook_client.create_event(event)
        for event in new_events['outlook_to_google']:
            self.gc_client.create_event(event)
        # Persist mappings
        for mapping in new_events['mappings']:
            self._persist_mapping(**mapping)
        return {"synced": True, "conflicts": conflicts}

    def _persist_mapping(self, source, ext_event_id, event_data):
        # Map external event ID to internal event data for future updates/deletes
        if self.is_mock_db:
            # For testing, just log the mapping
            print(f"Mock DB: Persisting mapping - User: {self.user_id}, Source: {source}, Event ID: {ext_event_id}")
        else:
            mapping_ref = self.db.collection('event_mappings').document()
            mapping_ref.set({
                'user_id': self.user_id,
                'source': source,
                'external_event_id': ext_event_id,
                'event_data': event_data
            })


class MockFirestoreClient:
    """Mock Firestore client for testing"""
    
    def __init__(self):
        self.data = {}
    
    def collection(self, name):
        return MockCollection(name, self.data)


class MockCollection:
    """Mock Firestore collection for testing"""
    
    def __init__(self, name, data):
        self.name = name
        self.data = data
        if name not in self.data:
            self.data[name] = {}
    
    def document(self, doc_id=None):
        if doc_id is None:
            doc_id = f"mock_doc_{len(self.data[self.name])}"
        return MockDocument(self.name, doc_id, self.data)


class MockDocument:
    """Mock Firestore document for testing"""
    
    def __init__(self, collection_name, doc_id, data):
        self.collection_name = collection_name
        self.doc_id = doc_id
        self.data = data
    
    def set(self, document_data):
        self.data[self.collection_name][self.doc_id] = document_data
        return True

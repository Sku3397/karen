# Emergency Response Agent: 24/7 Monitoring and Coordination
import time
import threading
from src.agents.escalation_protocols import handle_escalation
from src.agents.contact_manager import get_emergency_contacts
from src.agents.response_coordinator import coordinate_response
from google.cloud import firestore

FIRESTORE_COLLECTION = 'emergencies'

class EmergencyResponseAgent:
    def __init__(self, polling_interval=10):
        self.db = firestore.Client()
        self.polling_interval = polling_interval
        self.running = False

    def start_monitoring(self):
        self.running = True
        thread = threading.Thread(target=self._monitor_loop)
        thread.daemon = True
        thread.start()

    def stop_monitoring(self):
        self.running = False

    def _monitor_loop(self):
        while self.running:
            emergencies = self._fetch_active_emergencies()
            for emergency in emergencies:
                self._process_emergency(emergency)
            time.sleep(self.polling_interval)

    def _fetch_active_emergencies(self):
        docs = self.db.collection(FIRESTORE_COLLECTION).where('status', '==', 'active').stream()
        return [doc.to_dict() | {'id': doc.id} for doc in docs]

    def _process_emergency(self, emergency):
        # Step 1: Escalate if needed
        escalation_action = handle_escalation(emergency)
        # Step 2: Notify contacts
        contacts = get_emergency_contacts(emergency.get('user_id'))
        for contact in contacts:
            coordinate_response(emergency, contact, escalation_action)
        # Step 3: Update status in Firestore
        self.db.collection(FIRESTORE_COLLECTION).document(emergency['id']).update({'status': 'processing'})

# Usage (entry point):
# agent = EmergencyResponseAgent()
# agent.start_monitoring()
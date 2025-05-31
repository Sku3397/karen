# Multi-Agent Context Manager
class MultiAgentContextManager:
    def __init__(self, db):
        self.db = db

    def get_context(self, user_id):
        doc_ref = self.db.collection('users').document(user_id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict().get('context', {})
        else:
            return {}

    def update_context(self, user_id, tasks):
        doc_ref = self.db.collection('users').document(user_id)
        doc_ref.update({'context': {'last_tasks': tasks}})

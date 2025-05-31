# Firestore repository abstraction
import os
from google.cloud import firestore
from typing import Any, Dict, List, Optional

class FirestoreRepository:
    def __init__(self):
        self.db = firestore.Client()

    def get_document(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        doc_ref = self.db.collection(collection).document(doc_id)
        doc = doc_ref.get()
        return doc.to_dict() if doc.exists else None

    def set_document(self, collection: str, doc_id: str, data: Dict[str, Any]):
        self.db.collection(collection).document(doc_id).set(data)

    def update_document(self, collection: str, doc_id: str, updates: Dict[str, Any]):
        self.db.collection(collection).document(doc_id).update(updates)

    def delete_document(self, collection: str, doc_id: str):
        self.db.collection(collection).document(doc_id).delete()

    def list_documents(self, collection: str, filters: Optional[List] = None) -> List[Dict[str, Any]]:
        coll_ref = self.db.collection(collection)
        if filters:
            for f in filters:
                coll_ref = coll_ref.where(*f)
        return [doc.to_dict() for doc in coll_ref.stream()]

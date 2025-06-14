# Emergency Contact Manager
from google.cloud import firestore

USERS_COLLECTION = 'users'

# Retrieve emergency contacts for a given user_id
def get_emergency_contacts(user_id):
    db = firestore.Client()
    user_ref = db.collection(USERS_COLLECTION).document(user_id)
    user_doc = user_ref.get()
    if user_doc.exists:
        profile = user_doc.to_dict().get('profile', {})
        contacts = profile.get('emergency_contacts', [])
        return contacts
    return []
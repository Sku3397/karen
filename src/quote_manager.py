# Quote management module
from datetime import datetime
import uuid

# In-memory store for demonstration; should be replaced with Firestore or persistent DB in prod
QUOTES = {}

class QuoteManager:
    def create_quote(self, data):
        quote_id = str(uuid.uuid4())
        quote = {
            'id': quote_id,
            'customer_id': data['customer_id'],
            'items': data['items'],
            'total': sum(item['price'] * item['quantity'] for item in data['items']),
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat()
        }
        QUOTES[quote_id] = quote
        return quote
    def list_quotes(self):
        return list(QUOTES.values())

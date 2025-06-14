# Payment Model
import uuid
from datetime import datetime

class Payment:
    def __init__(self, id, invoice_id, amount, method, transaction_id, timestamp=None):
        self.id = id
        self.invoice_id = invoice_id
        self.amount = amount
        self.method = method
        self.transaction_id = transaction_id
        self.timestamp = timestamp or datetime.utcnow().isoformat()

    @classmethod
    def create(cls, invoice_id, amount, method, transaction_id):
        return cls(str(uuid.uuid4()), invoice_id, amount, method, transaction_id)

    def to_dict(self):
        return self.__dict__

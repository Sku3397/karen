# Invoice Model
import uuid
from datetime import datetime

class Invoice:
    def __init__(self, id, client_id, items, total_amount, due_date, status='unpaid', created_at=None):
        self.id = id
        self.client_id = client_id
        self.items = items
        self.total_amount = total_amount
        self.due_date = due_date
        self.status = status
        self.created_at = created_at or datetime.utcnow().isoformat()

    @classmethod
    def create(cls, client_id, items, due_date):
        total_amount = sum(item['amount'] for item in items)
        return cls(str(uuid.uuid4()), client_id, items, total_amount, due_date)

    def to_dict(self):
        return self.__dict__

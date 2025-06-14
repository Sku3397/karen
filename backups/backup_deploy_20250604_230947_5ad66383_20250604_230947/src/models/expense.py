# Expense Model
import uuid
from datetime import datetime

class Expense:
    def __init__(self, id, amount, category, note=None, timestamp=None):
        self.id = id
        self.amount = amount
        self.category = category
        self.note = note
        self.timestamp = timestamp or datetime.utcnow().isoformat()

    @classmethod
    def create(cls, amount, category, note=None):
        return cls(str(uuid.uuid4()), amount, category, note)

    def to_dict(self):
        return self.__dict__

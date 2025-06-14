# Expense management module
from datetime import datetime
import uuid

# In-memory store for demonstration; should be replaced with Firestore or persistent DB in prod
EXPENSES = {}

class ExpenseManager:
    def add_expense(self, data):
        expense_id = str(uuid.uuid4())
        expense = {
            'id': expense_id,
            'amount': data['amount'],
            'description': data.get('description', ''),
            'category': data.get('category', 'General'),
            'date': data.get('date', datetime.utcnow().isoformat()),
            'created_at': datetime.utcnow().isoformat()
        }
        EXPENSES[expense_id] = expense
        return expense
    def list_expenses(self):
        return list(EXPENSES.values())

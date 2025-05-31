# Financial reporting module
from src.expense_manager import EXPENSES
from src.quote_manager import QUOTES
from src.stripe_client import StripeClient
from datetime import datetime

class FinancialReports:
    def __init__(self):
        self.stripe_client = StripeClient()

    def generate(self):
        expenses = list(EXPENSES.values())
        quotes = list(QUOTES.values())
        try:
            payments = self.stripe_client.list_payments()
        except Exception:
            payments = []
        total_expenses = sum(float(e['amount']) for e in expenses)
        total_quotes = sum(float(q['total']) for q in quotes)
        total_payments = sum(float(p.amount_received)/100 for p in payments if hasattr(p, 'amount_received'))
        report = {
            'total_expenses': total_expenses,
            'total_quotes': total_quotes,
            'total_payments': total_payments,
            'generated_at': datetime.utcnow().isoformat()
        }
        return report

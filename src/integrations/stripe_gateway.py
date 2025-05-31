# Stripe Integration (PCI DSS compliant)
import os
import stripe
from dotenv import load_dotenv

load_dotenv()
stripe.api_key = os.getenv('STRIPE_API_KEY')

class StripeGateway:
    def charge(self, amount, payment_info):
        try:
            # Do not store card data anywhere, use Stripe tokenization
            charge = stripe.Charge.create(
                amount=int(amount * 100),
                currency='usd',
                source=payment_info['token'], # tokenized card
                description=payment_info.get('description', 'Handyman invoice payment')
            )
            return {'success': True, 'transaction_id': charge.id}
        except Exception as e:
            return {'success': False, 'error': str(e)}

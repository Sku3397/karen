# PayPal Integration (PCI DSS compliant)
import os
from paypalrestsdk import Payment as PayPalPayment, configure
from dotenv import load_dotenv

load_dotenv()
configure({
    "mode": os.getenv('PAYPAL_MODE', 'sandbox'),
    "client_id": os.getenv('PAYPAL_CLIENT_ID'),
    "client_secret": os.getenv('PAYPAL_CLIENT_SECRET')
})

class PayPalGateway:
    def charge(self, amount, payment_info):
        payment = PayPalPayment({
            "intent": "sale",
            "payer": {"payment_method": "paypal"},
            "transactions": [{
                "amount": {"total": f"{amount:.2f}", "currency": "USD"},
                "description": payment_info.get('description', 'Handyman invoice payment')
            }],
            "redirect_urls": {
                "return_url": payment_info['return_url'],
                "cancel_url": payment_info['cancel_url']
            }
        })
        if payment.create():
            return {'success': True, 'transaction_id': payment.id, 'approval_url': payment['links'][1]['href']}
        else:
            return {'success': False, 'error': payment.error}

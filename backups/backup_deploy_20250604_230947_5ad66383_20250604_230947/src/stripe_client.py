# Stripe API interaction module
import stripe
import os

stripe.api_key = os.getenv('STRIPE_API_KEY')

class StripeClient:
    def create_invoice(self, data):
        customer_id = data['customer_id']
        items = data['items'] # List of {price, quantity}
        invoice_item_ids = []
        for item in items:
            invoice_item = stripe.InvoiceItem.create(
                customer=customer_id,
                price=item['price'],
                quantity=item['quantity']
            )
            invoice_item_ids.append(invoice_item.id)
        invoice = stripe.Invoice.create(customer=customer_id, auto_advance=True)
        return invoice

    def get_invoice(self, invoice_id):
        invoice = stripe.Invoice.retrieve(invoice_id)
        return invoice

    def list_payments(self):
        payments = stripe.PaymentIntent.list(limit=20)
        return [p for p in payments.auto_paging_iter()]

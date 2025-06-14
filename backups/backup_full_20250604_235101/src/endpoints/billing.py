"""
Billing API endpoint for the AI Handyman Secretary Assistant.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

router = APIRouter()

class InvoiceCreate(BaseModel):
    client_id: str
    amount: float
    description: str
    due_date: str

class InvoiceResponse(BaseModel):
    id: str
    client_id: str
    amount: float
    description: str
    due_date: str
    status: str
    created_at: str

# In-memory storage
invoices_db = {}

@router.post("/billing/invoices", response_model=InvoiceResponse)
async def create_invoice(invoice: InvoiceCreate):
    """Create a new invoice."""
    invoice_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    invoice_data = {
        "id": invoice_id,
        "client_id": invoice.client_id,
        "amount": invoice.amount,
        "description": invoice.description,
        "due_date": invoice.due_date,
        "status": "pending",
        "created_at": now
    }
    
    invoices_db[invoice_id] = invoice_data
    return InvoiceResponse(**invoice_data)

@router.get("/billing/invoices", response_model=List[InvoiceResponse])
async def list_invoices():
    """List all invoices."""
    return [InvoiceResponse(**inv) for inv in invoices_db.values()]

@router.get("/billing/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: str):
    """Get a specific invoice."""
    if invoice_id not in invoices_db:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return InvoiceResponse(**invoices_db[invoice_id])
"""
Inventory API endpoint for the AI Handyman Secretary Assistant.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

router = APIRouter()

class InventoryItemCreate(BaseModel):
    name: str
    description: str
    quantity: int
    unit_price: float
    category: str

class InventoryItemResponse(BaseModel):
    id: str
    name: str
    description: str
    quantity: int
    unit_price: float
    category: str
    created_at: str

# In-memory storage
inventory_db = {}

@router.post("/inventory/items", response_model=InventoryItemResponse)
async def create_inventory_item(item: InventoryItemCreate):
    """Create a new inventory item."""
    item_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    item_data = {
        "id": item_id,
        "name": item.name,
        "description": item.description,
        "quantity": item.quantity,
        "unit_price": item.unit_price,
        "category": item.category,
        "created_at": now
    }
    
    inventory_db[item_id] = item_data
    return InventoryItemResponse(**item_data)

@router.get("/inventory/items", response_model=List[InventoryItemResponse])
async def list_inventory_items():
    """List all inventory items."""
    return [InventoryItemResponse(**item) for item in inventory_db.values()]

@router.get("/inventory/items/{item_id}", response_model=InventoryItemResponse)
async def get_inventory_item(item_id: str):
    """Get a specific inventory item."""
    if item_id not in inventory_db:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    return InventoryItemResponse(**inventory_db[item_id])
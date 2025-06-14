from fastapi import APIRouter

router = APIRouter()

@router.get('/inventory/')
def list_inventory_items():
    pass
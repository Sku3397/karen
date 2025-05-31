from fastapi import APIRouter

router = APIRouter()

@router.post('/billing/charge')
def charge(charge_details: ChargeDetails):
    pass
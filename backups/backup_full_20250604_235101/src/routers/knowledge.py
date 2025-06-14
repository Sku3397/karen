from fastapi import APIRouter

router = APIRouter()

@router.get('/knowledge/')
def get_knowledge_item(item_id: str):
    pass
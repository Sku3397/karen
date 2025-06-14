# FastAPI endpoints for Scheduling Agent
from fastapi import APIRouter, Request, HTTPException
from src.agents.scheduling_agent import SchedulingAgent

router = APIRouter()
agent = SchedulingAgent()

@router.post('/schedule')
async def schedule_event(request: Request):
    data = await request.json()
    user_id = data.get('user_id')
    provider = data.get('provider')  # 'google' or 'outlook'
    event_data = data.get('event_data')
    if not all([user_id, provider, event_data]):
        raise HTTPException(status_code=400, detail='Missing required fields')
    try:
        event = agent.schedule_event(user_id, provider, event_data)
        return {'status': 'scheduled', 'event': event}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/events')
async def list_events(user_id: str, provider: str, start: str, end: str):
    try:
        events = agent.list_events(user_id, provider, {'start': start, 'end': end})
        return {'events': events}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

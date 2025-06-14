"""
SMS Webhook Handler for real-time SMS processing
Integrates with FastAPI main application
"""
from fastapi import APIRouter, Request, HTTPException, Response
from typing import Dict, Any
import logging
from .celery_sms_tasks import handle_incoming_sms_webhook

logger = logging.getLogger(__name__)
sms_router = APIRouter(prefix="/webhooks/sms", tags=["sms"])

@sms_router.post("/incoming")
async def handle_sms_webhook(request: Request):
    """Handle incoming SMS webhook from Twilio"""
    try:
        # Get webhook data from Twilio
        webhook_data = await request.form()
        webhook_dict = dict(webhook_data)
        
        logger.info(f"Received SMS webhook: {webhook_dict.get('MessageSid')}")
        
        # Queue for processing
        handle_incoming_sms_webhook.delay(webhook_dict)
        
        # Return TwiML response
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
            media_type="application/xml"
        )
        
    except Exception as e:
        logger.error(f"SMS webhook error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

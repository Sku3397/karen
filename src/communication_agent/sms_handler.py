from twilio.rest import Client
from typing import Optional
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SMSHandler:
    def __init__(self, account_sid: str, auth_token: str, from_number: str):
        self.client = Client(account_sid, auth_token)
        self.from_number = from_number

    def send_sms(self, to_number: str, message: str) -> Optional[str]:
        try:
            msg = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to_number
            )
            
            # Store in memory system
            try:
                from ..memory_client import memory_client
                sms_data = {
                    'sid': msg.sid,
                    'from': self.from_number,
                    'to': to_number,
                    'body': message,
                    'direction': 'outbound',
                    'date_created': datetime.now()
                }
                asyncio.create_task(memory_client.store_sms_conversation(sms_data))
                logger.debug(f"Queued SMS memory storage for SID: {msg.sid}")
            except Exception as memory_error:
                logger.warning(f"Failed to store SMS in memory: {memory_error}")
            
            return msg.sid
        except Exception as e:
            logger.error(f"SMSHandler: Failed to send SMS - {e}")
            return None

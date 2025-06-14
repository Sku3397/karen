"""
Template for creating new handlers following CommunicationAgent structure
Replace TODO items with your specific implementation
"""
import logging
import re
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta, timezone
import asyncio
import pytz

from pydantic import BaseModel, Field, EmailStr
from fastapi import HTTPException

# Import existing patterns
from ..config import USE_MOCK_EMAIL_CLIENT, ADMIN_EMAIL_ADDRESS
from ..email_client import EmailClient
from ..mock_email_client import MockEmailClient
from ..llm_client import LLMClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class TODOHandler:
    """Handler for TODO functionality following CommunicationAgent patterns"""
    
    def __init__(self,
                 primary_config: Dict[str, Any],
                 secondary_config: Optional[Dict[str, Any]] = None,
                 admin_email: str = ADMIN_EMAIL_ADDRESS,
                 llm_client: Optional[LLMClient] = None):
        """
        Initialize handler with configuration
        
        Args:
            primary_config: Main configuration dictionary
            secondary_config: Optional secondary configuration
            admin_email: Admin email for notifications
            llm_client: Optional LLM client for AI operations
        """
        logger.debug(f"Initializing TODOHandler. USE_MOCK: {USE_MOCK_EMAIL_CLIENT}")
        
        self.admin_email = admin_email
        self.llm_client = llm_client
        
        # Initialize primary service/client
        if USE_MOCK_EMAIL_CLIENT:
            logger.warning("Using mock client for testing purposes")
            self.primary_client = MockEmailClient(
                email_address=primary_config.get('email_address'),
                # Add other mock params
            )
        else:
            logger.debug("Initializing real client")
            try:
                # TODO: Initialize your actual client
                # self.primary_client = YourClient(**primary_config)
                pass
            except Exception as e:
                logger.error(f"Failed to initialize primary client: {e}", exc_info=True)
                raise
        
        # Initialize cache if needed
        self._cache: Dict[str, Any] = {}
        
        logger.info("TODOHandler initialized successfully")
    
    async def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing method following async pattern
        
        Args:
            request_data: Input data to process
            
        Returns:
            Processing result dictionary
        """
        request_id = request_data.get('id', 'unknown')
        logger.info(f"Processing request {request_id}")
        logger.debug(f"Request data: {request_data}")
        
        try:
            # Step 1: Validate input
            validated_data = self._validate_request(request_data)
            
            # Step 2: Classify/analyze request
            classification = self._classify_request(validated_data)
            logger.info(f"Request classification: {classification}")
            
            # Step 3: Process based on classification
            if classification.get('type') == 'urgent':
                result = await self._handle_urgent_request(validated_data, classification)
            elif classification.get('type') == 'scheduled':
                result = await self._handle_scheduled_request(validated_data, classification)
            else:
                result = await self._handle_standard_request(validated_data, classification)
            
            # Step 4: Post-processing
            if result.get('success'):
                logger.info(f"Successfully processed request {request_id}")
                await self._send_success_notification(request_id, result)
            else:
                logger.warning(f"Request {request_id} completed with warnings: {result.get('warnings')}")
            
            return result
            
        except HTTPException as http_exc:
            logger.error(f"HTTP error processing request {request_id}: {http_exc.detail}", exc_info=True)
            await self._send_admin_notification(
                subject=f"[ERROR] HTTP Error in TODOHandler",
                body=f"Request ID: {request_id}\nError: {http_exc.detail}"
            )
            raise
            
        except Exception as e:
            logger.error(f"Unexpected error processing request {request_id}: {e}", exc_info=True)
            import traceback
            tb_str = traceback.format_exc()
            
            await self._send_admin_notification(
                subject=f"[URGENT] Error in TODOHandler",
                body=f"Request ID: {request_id}\nError: {str(e)}\n\nTraceback:\n{tb_str}"
            )
            
            return {
                'success': False,
                'error': str(e),
                'request_id': request_id
            }
    
    def _validate_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate request data following Karen's validation patterns"""
        # Required field validation
        if not request_data.get('id'):
            raise ValueError("Request ID is required")
        
        # Email validation if present
        if email := request_data.get('email'):
            if not re.match(r'[\w\.-]+@[\w\.-]+', email):
                logger.warning(f"Invalid email format: {email}")
                request_data['email'] = None
        
        # Date parsing if present
        if date_str := request_data.get('date'):
            try:
                # Use Karen's date parsing pattern
                from ..datetime_utils import parse_datetime_from_details
                parsed_date = parse_datetime_from_details(date_str, None, "request")
                request_data['parsed_date'] = parsed_date
            except Exception as e:
                logger.warning(f"Could not parse date '{date_str}': {e}")
        
        return request_data
    
    def _classify_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Classify request following Karen's classification pattern"""
        content = str(request_data).lower()
        
        classification = {
            'type': 'standard',
            'priority': 'normal',
            'tags': [],
            'requires_llm': False
        }
        
        # Check for urgent keywords
        urgent_keywords = ['urgent', 'emergency', 'asap', 'immediately']
        if any(keyword in content for keyword in urgent_keywords):
            classification['type'] = 'urgent'
            classification['priority'] = 'high'
        
        # Check for scheduling keywords
        schedule_keywords = ['schedule', 'appointment', 'calendar', 'book']
        if any(keyword in content for keyword in schedule_keywords):
            classification['type'] = 'scheduled'
            classification['tags'].append('calendar')
        
        # Determine if LLM is needed
        if request_data.get('requires_ai_response'):
            classification['requires_llm'] = True
        
        return classification
    
    async def _handle_standard_request(self, data: Dict[str, Any], 
                                     classification: Dict[str, Any]) -> Dict[str, Any]:
        """Handle standard requests"""
        logger.debug(f"Handling standard request: {data.get('id')}")
        
        result = {
            'success': True,
            'request_id': data.get('id'),
            'type': 'standard',
            'processed_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Generate LLM response if needed
        if classification.get('requires_llm') and self.llm_client:
            try:
                prompt = self._generate_llm_prompt(data, classification)
                response = await asyncio.to_thread(
                    self.llm_client.generate_text,
                    prompt
                )
                result['ai_response'] = response
                logger.info(f"Generated AI response: {len(response)} chars")
            except Exception as e:
                logger.error(f"Failed to generate LLM response: {e}", exc_info=True)
                result['warnings'] = ['AI response unavailable']
        
        return result
    
    async def _handle_urgent_request(self, data: Dict[str, Any],
                                   classification: Dict[str, Any]) -> Dict[str, Any]:
        """Handle urgent requests with immediate notification"""
        logger.warning(f"URGENT request received: {data.get('id')}")
        
        # Send immediate admin notification
        await self._send_admin_notification(
            subject=f"[URGENT] Request {data.get('id')} requires attention",
            body=f"Urgent request received:\n\n{data}"
        )
        
        # Process with priority
        result = await self._handle_standard_request(data, classification)
        result['type'] = 'urgent'
        result['admin_notified'] = True
        
        return result
    
    async def _handle_scheduled_request(self, data: Dict[str, Any],
                                      classification: Dict[str, Any]) -> Dict[str, Any]:
        """Handle scheduled/calendar requests"""
        logger.info(f"Processing scheduled request: {data.get('id')}")
        
        result = {
            'success': True,
            'request_id': data.get('id'),
            'type': 'scheduled',
            'processed_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Extract scheduling details
        if parsed_date := data.get('parsed_date'):
            result['scheduled_for'] = parsed_date.isoformat()
            
            # TODO: Integrate with calendar client
            # if self.calendar_client:
            #     availability = await self.check_availability(parsed_date)
            #     result['availability'] = availability
        
        return result
    
    def _generate_llm_prompt(self, data: Dict[str, Any], 
                           classification: Dict[str, Any]) -> str:
        """Generate LLM prompt following Karen's pattern"""
        base_prompt = f"""You are an AI assistant handling a {classification.get('type')} request.

REQUEST DETAILS:
- ID: {data.get('id')}
- Priority: {classification.get('priority')}
- Tags: {', '.join(classification.get('tags', []))}

REQUEST CONTENT:
{data}

INSTRUCTIONS:
1. Provide a helpful and professional response
2. Be concise but informative
3. Include relevant next steps
4. Maintain a friendly tone

Generate an appropriate response:"""
        
        return base_prompt
    
    async def _send_admin_notification(self, subject: str, body: str):
        """Send admin notification following Karen's pattern"""
        try:
            logger.info(f"Sending admin notification: {subject[:50]}...")
            # TODO: Implement based on your email setup
            # if hasattr(self, 'email_client'):
            #     self.email_client.send_email(
            #         to=self.admin_email,
            #         subject=subject,
            #         body=body
            #     )
        except Exception as e:
            logger.error(f"Failed to send admin notification: {e}", exc_info=True)
    
    async def _send_success_notification(self, request_id: str, result: Dict[str, Any]):
        """Send success notification if configured"""
        if result.get('notify_on_success'):
            await self._send_admin_notification(
                subject=f"Successfully processed request {request_id}",
                body=f"Request completed:\n\n{result}"
            )
    
    def get_cached_value(self, key: str) -> Optional[Any]:
        """Get cached value following Karen's caching pattern"""
        if key in self._cache:
            logger.debug(f"Cache hit for key: {key}")
            return self._cache[key]
        return None
    
    def set_cached_value(self, key: str, value: Any):
        """Set cached value"""
        self._cache[key] = value
        logger.debug(f"Cached value for key: {key}")

# Example Pydantic schemas following Karen's pattern
class TODORequestSchema(BaseModel):
    """Schema for TODO requests"""
    id: str = Field(..., description="Unique request ID")
    email: Optional[EmailStr] = Field(None, description="Contact email")
    content: str = Field(..., min_length=1, max_length=1000)
    urgent: bool = Field(False, description="Is this urgent?")
    scheduled_date: Optional[str] = Field(None, description="Scheduled date if applicable")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "req_123",
                "email": "user@example.com",
                "content": "Process this request",
                "urgent": False
            }
        }

class TODOResponseSchema(BaseModel):
    """Schema for TODO responses"""
    success: bool
    request_id: str
    type: str
    processed_at: str
    ai_response: Optional[str] = None
    warnings: Optional[List[str]] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
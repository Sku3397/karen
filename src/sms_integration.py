"""
Complete SMS Integration for Karen AI Secretary
Communications Agent (COMMS-001)

Handles all SMS communications including:
- Sending SMS messages
- Receiving SMS webhooks
- Message processing and routing
- Error handling and logging
- Integration with LLM for intelligent responses
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from twilio.base.exceptions import TwilioException

from src.llm_client import LLMClient
from src.logging_config import setup_logger

logger = setup_logger(__name__)

@dataclass
class SMSMessage:
    """Data class for SMS message structure"""
    sid: str
    from_number: str
    to_number: str
    body: str
    timestamp: datetime
    status: str
    direction: str  # 'inbound' or 'outbound'
    
    def to_dict(self) -> Dict:
        return {
            'sid': self.sid,
            'from_number': self.from_number,
            'to_number': self.to_number,
            'body': self.body,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status,
            'direction': self.direction
        }

class SMSIntegration:
    """Complete SMS integration handler for Karen AI"""
    
    def __init__(self):
        """Initialize SMS integration with Twilio credentials"""
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = os.getenv('TWILIO_FROM_NUMBER')
        self.webhook_url = os.getenv('TWILIO_WEBHOOK_URL')
        
        # Validate required credentials
        if not all([self.account_sid, self.auth_token, self.from_number]):
            raise ValueError("Missing required Twilio credentials. Check environment variables.")
        
        # Initialize Twilio client
        try:
            self.client = Client(self.account_sid, self.auth_token)
            logger.info("Twilio SMS client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Twilio client: {e}")
            raise
        
        # Initialize LLM client for intelligent responses
        self.llm_client = LLMClient()
        
        # Message history for context
        self.message_history: Dict[str, List[SMSMessage]] = {}
        
        # Known customer numbers and their preferences
        self.customer_profiles: Dict[str, Dict] = {}
        
    def send_sms(self, to_number: str, message: str, priority: str = 'normal') -> SMSMessage:
        """
        Send SMS message with error handling and logging
        
        Args:
            to_number: Recipient phone number
            message: Message content
            priority: Message priority ('urgent', 'normal', 'low')
            
        Returns:
            SMSMessage object with send details
        """
        try:
            # Format phone number
            formatted_number = self._format_phone_number(to_number)
            
            # Add priority indicator for urgent messages
            if priority == 'urgent':
                message = f"🚨 URGENT: {message}"
            
            # Send message via Twilio
            twilio_message = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=formatted_number
            )
            
            # Create SMS message object
            sms_message = SMSMessage(
                sid=twilio_message.sid,
                from_number=self.from_number,
                to_number=formatted_number,
                body=message,
                timestamp=datetime.now(timezone.utc),
                status=twilio_message.status,
                direction='outbound'
            )
            
            # Log successful send
            logger.info(f"SMS sent successfully to {formatted_number} - SID: {twilio_message.sid}")
            
            # Store in message history
            self._add_to_history(formatted_number, sms_message)
            
            return sms_message
            
        except TwilioException as e:
            logger.error(f"Twilio error sending SMS to {to_number}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending SMS to {to_number}: {e}")
            raise
    
    def receive_sms_webhook(self, webhook_data: Dict) -> Tuple[str, SMSMessage]:
        """
        Process incoming SMS webhook from Twilio
        
        Args:
            webhook_data: Webhook data from Twilio
            
        Returns:
            Tuple of (response_message, sms_message_object)
        """
        try:
            # Extract message data from webhook
            from_number = webhook_data.get('From', '')
            to_number = webhook_data.get('To', '')
            message_body = webhook_data.get('Body', '')
            message_sid = webhook_data.get('MessageSid', '')
            
            # Create SMS message object
            sms_message = SMSMessage(
                sid=message_sid,
                from_number=from_number,
                to_number=to_number,
                body=message_body,
                timestamp=datetime.now(timezone.utc),
                status='received',
                direction='inbound'
            )
            
            logger.info(f"Received SMS from {from_number}: {message_body[:100]}...")
            
            # Store in message history
            self._add_to_history(from_number, sms_message)
            
            # Process message and generate response
            response_message = self._process_incoming_message(sms_message)
            
            return response_message, sms_message
            
        except Exception as e:
            logger.error(f"Error processing SMS webhook: {e}")
            return "I'm sorry, I encountered an error processing your message. Please try again.", None
    
    def _process_incoming_message(self, sms_message: SMSMessage) -> str:
        """
        Process incoming SMS and generate intelligent response
        
        Args:
            sms_message: Incoming SMS message
            
        Returns:
            Response message string
        """
        try:
            # Get conversation history for context
            history = self.message_history.get(sms_message.from_number, [])
            
            # Classify message intent
            intent = self._classify_message_intent(sms_message.body)
            
            # Get customer profile if available
            profile = self.customer_profiles.get(sms_message.from_number, {})
            
            # Generate context-aware response using LLM
            context = {
                'message': sms_message.body,
                'intent': intent,
                'customer_profile': profile,
                'conversation_history': [msg.body for msg in history[-5:]],  # Last 5 messages
                'timestamp': sms_message.timestamp.isoformat()
            }
            
            response = self._generate_llm_response(context)
            
            # Log the interaction
            logger.info(f"Generated response for {sms_message.from_number} (intent: {intent})")
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "Thank you for your message. I'll get back to you shortly."
    
    def _classify_message_intent(self, message: str) -> str:
        """
        Classify the intent of incoming message
        
        Args:
            message: Message content
            
        Returns:
            Intent classification string
        """
        message_lower = message.lower()
        
        # Emergency keywords
        if any(word in message_lower for word in ['emergency', 'urgent', 'asap', 'help', 'problem']):
            return 'emergency'
        
        # Appointment keywords
        if any(word in message_lower for word in ['appointment', 'schedule', 'book', 'available', 'time']):
            return 'appointment'
        
        # Quote/pricing keywords
        if any(word in message_lower for word in ['quote', 'price', 'cost', 'estimate', 'how much']):
            return 'quote'
        
        # Service inquiry keywords
        if any(word in message_lower for word in ['service', 'repair', 'fix', 'install', 'maintenance']):
            return 'service_inquiry'
        
        # General inquiry
        return 'general_inquiry'
    
    def _generate_llm_response(self, context: Dict) -> str:
        """
        Generate intelligent response using LLM
        
        Args:
            context: Message context and metadata
            
        Returns:
            Generated response string
        """
        try:
            # Create prompt for LLM
            prompt = f"""
You are Karen, a professional AI secretary for a handyman service. 

Customer message: "{context['message']}"
Message intent: {context['intent']}
Conversation history: {context.get('conversation_history', [])}

Respond professionally and helpfully. Keep responses concise but informative.
For emergencies, prioritize and show urgency.
For appointments, ask for preferred times and details.
For quotes, ask for service details and offer to schedule an assessment.

Response:"""

            response = self.llm_client.generate_response(prompt)
            
            # Ensure response is appropriate length for SMS (max 1600 chars)
            if len(response) > 1500:
                response = response[:1500] + "... (continued in next message)"
            
            return response
            
        except Exception as e:
            logger.error(f"LLM response generation failed: {e}")
            return self._get_fallback_response(context['intent'])
    
    def _get_fallback_response(self, intent: str) -> str:
        """
        Get fallback response if LLM fails
        
        Args:
            intent: Message intent
            
        Returns:
            Fallback response string
        """
        fallback_responses = {
            'emergency': "I understand this is urgent. I'm contacting our team immediately. We'll respond ASAP.",
            'appointment': "I'd be happy to help schedule an appointment. What type of service do you need and when works best?",
            'quote': "I can help with a quote. Please describe the work needed and I'll get you an estimate.",
            'service_inquiry': "Thanks for your inquiry. Can you provide more details about the service you need?",
            'general_inquiry': "Thank you for contacting us. How can I assist you today?"
        }
        
        return fallback_responses.get(intent, "Thank you for your message. I'll get back to you shortly.")
    
    def send_bulk_sms(self, recipients: List[str], message: str) -> List[SMSMessage]:
        """
        Send SMS to multiple recipients
        
        Args:
            recipients: List of phone numbers
            message: Message content
            
        Returns:
            List of SMSMessage objects
        """
        results = []
        for number in recipients:
            try:
                result = self.send_sms(number, message)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to send bulk SMS to {number}: {e}")
                
        logger.info(f"Bulk SMS sent to {len(results)}/{len(recipients)} recipients")
        return results
    
    def get_message_history(self, phone_number: str, limit: int = 50) -> List[SMSMessage]:
        """
        Get message history for a phone number
        
        Args:
            phone_number: Phone number to get history for
            limit: Maximum number of messages to return
            
        Returns:
            List of SMSMessage objects
        """
        formatted_number = self._format_phone_number(phone_number)
        history = self.message_history.get(formatted_number, [])
        return history[-limit:] if limit else history
    
    def _format_phone_number(self, phone_number: str) -> str:
        """
        Format phone number to E.164 format
        
        Args:
            phone_number: Raw phone number
            
        Returns:
            Formatted phone number
        """
        # Remove all non-digit characters
        digits = ''.join(filter(str.isdigit, phone_number))
        
        # Add +1 if US number without country code
        if len(digits) == 10:
            return f"+1{digits}"
        elif len(digits) == 11 and digits.startswith('1'):
            return f"+{digits}"
        else:
            return f"+{digits}"
    
    def _add_to_history(self, phone_number: str, message: SMSMessage):
        """
        Add message to conversation history
        
        Args:
            phone_number: Phone number
            message: SMS message to add
        """
        if phone_number not in self.message_history:
            self.message_history[phone_number] = []
        
        self.message_history[phone_number].append(message)
        
        # Keep only last 100 messages per number
        if len(self.message_history[phone_number]) > 100:
            self.message_history[phone_number] = self.message_history[phone_number][-100:]
    
    def create_twiml_response(self, response_message: str) -> str:
        """
        Create TwiML response for Twilio webhook
        
        Args:
            response_message: Message to send back
            
        Returns:
            TwiML XML string
        """
        resp = MessagingResponse()
        resp.message(response_message)
        return str(resp)
    
    def get_sms_status(self, message_sid: str) -> Dict:
        """
        Get status of sent SMS message
        
        Args:
            message_sid: Twilio message SID
            
        Returns:
            Message status dictionary
        """
        try:
            message = self.client.messages(message_sid).fetch()
            return {
                'sid': message.sid,
                'status': message.status,
                'error_code': message.error_code,
                'error_message': message.error_message,
                'date_sent': message.date_sent,
                'date_updated': message.date_updated
            }
        except Exception as e:
            logger.error(f"Error fetching SMS status for {message_sid}: {e}")
            return {'error': str(e)}
    
    def health_check(self) -> Dict:
        """
        Perform health check on SMS integration
        
        Returns:
            Health status dictionary
        """
        try:
            # Test Twilio connection
            account = self.client.api.account.fetch()
            
            return {
                'status': 'healthy',
                'twilio_connected': True,
                'account_sid': account.sid[:8] + '...',  # Partial SID for security
                'from_number': self.from_number,
                'webhook_configured': bool(self.webhook_url),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"SMS health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

# Global SMS integration instance
sms_integration = None

def get_sms_integration() -> SMSIntegration:
    """Get or create SMS integration instance"""
    global sms_integration
    if sms_integration is None:
        sms_integration = SMSIntegration()
    return sms_integration

# FastAPI webhook endpoint handler
async def handle_sms_webhook(webhook_data: Dict) -> str:
    """
    Async handler for SMS webhooks
    
    Args:
        webhook_data: Webhook data from Twilio
        
    Returns:
        TwiML response string
    """
    try:
        sms = get_sms_integration()
        response_message, sms_message = sms.receive_sms_webhook(webhook_data)
        
        # Create TwiML response
        twiml_response = sms.create_twiml_response(response_message)
        
        # Log the interaction
        if sms_message:
            logger.info(f"SMS webhook processed - From: {sms_message.from_number}, Response sent")
        
        return twiml_response
        
    except Exception as e:
        logger.error(f"Error handling SMS webhook: {e}")
        # Return error response
        resp = MessagingResponse()
        resp.message("I'm sorry, I'm experiencing technical difficulties. Please try again later.")
        return str(resp)
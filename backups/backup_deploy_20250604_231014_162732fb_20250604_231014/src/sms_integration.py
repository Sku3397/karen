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
from src.nlp_engine import get_nlp_engine, Intent, Sentiment, Priority
from src.template_storage import get_template_storage

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
        
        # Initialize NLP engine with LLM client
        self.nlp_engine = get_nlp_engine(self.llm_client)
        
        # Initialize template storage for SMS templates
        self.template_storage = get_template_storage()
        
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
    
    async def receive_sms_webhook(self, webhook_data: Dict) -> Tuple[str, SMSMessage]:
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
            
            # Process message and generate response (async)
            response_message = await self._process_incoming_message(sms_message)
            
            return response_message, sms_message
            
        except Exception as e:
            logger.error(f"Error processing SMS webhook: {e}")
            return "I'm sorry, I encountered an error processing your message. Please try again.", None
    
    async def _process_incoming_message(self, sms_message: SMSMessage) -> str:
        """
        Process incoming SMS and generate intelligent response using NLP engine
        
        Args:
            sms_message: Incoming SMS message
            
        Returns:
            Response message string
        """
        try:
            # Get conversation history for context
            history = self.message_history.get(sms_message.from_number, [])
            
            # Get customer profile if available
            profile = self.customer_profiles.get(sms_message.from_number, {})
            
            # Prepare context for NLP analysis
            context = {
                'customer_profile': profile,
                'conversation_history': [msg.body for msg in history[-5:]],  # Last 5 messages
                'customer_phone': sms_message.from_number
            }
            
            # Perform comprehensive NLP analysis
            nlp_result = await self.nlp_engine.analyze_text(sms_message.body, context)
            
            # Log NLP analysis
            logger.info(f"NLP Analysis for {sms_message.from_number}: Intent={nlp_result.intent.value}, "
                       f"Sentiment={nlp_result.sentiment.value}, Priority={nlp_result.priority.value}, "
                       f"Confidence={nlp_result.confidence}")
            
            # Generate context-aware response
            response = await self._generate_nlp_response(sms_message, nlp_result, context)
            
            # Store NLP analysis in customer profile for future reference
            self._update_customer_profile(sms_message.from_number, nlp_result)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message with NLP: {e}", exc_info=True)
            return "Thank you for your message. I'll get back to you shortly."
    
    async def _generate_nlp_response(self, sms_message: SMSMessage, nlp_result, context: Dict) -> str:
        """
        Generate intelligent response based on NLP analysis
        
        Args:
            sms_message: Original SMS message
            nlp_result: NLP analysis result
            context: Message context
            
        Returns:
            Generated response string
        """
        try:
            # Handle critical priority messages immediately
            if nlp_result.priority == Priority.CRITICAL or nlp_result.intent == Intent.EMERGENCY:
                return await self._handle_emergency_message(sms_message, nlp_result)
            
            # Create enhanced prompt based on NLP analysis
            prompt = self._build_response_prompt(sms_message, nlp_result, context)
            
            # Generate response using LLM
            response = await asyncio.to_thread(self.llm_client.generate_response, prompt)
            
            # Ensure response is appropriate length for SMS
            if len(response) > 1500:
                response = response[:1500] + "... (continued in next message)"
            
            # Add urgency indicator if needed
            if nlp_result.is_urgent and nlp_result.priority in [Priority.CRITICAL, Priority.HIGH]:
                response = f"🚨 {response}"
            
            return response
            
        except Exception as e:
            logger.error(f"NLP response generation failed: {e}", exc_info=True)
            return self._get_fallback_response_by_intent(nlp_result.intent)
    
    def _build_response_prompt(self, sms_message: SMSMessage, nlp_result, context: Dict) -> str:
        """Build enhanced prompt based on NLP analysis"""
        
        entities_text = ""
        if nlp_result.entities:
            entities_list = [f"{e.type}: {e.value}" for e in nlp_result.entities]
            entities_text = f"\nExtracted Information: {', '.join(entities_list)}"
        
        history_text = ""
        if context.get('conversation_history'):
            history_text = f"\nConversation History: {context['conversation_history']}"
        
        current_time = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
        
        prompt = f"""
You are Karen, the professional AI secretary for Beach Handyman service in Virginia Beach.

CUSTOMER MESSAGE ANALYSIS:
- Message: "{sms_message.body}"
- Intent: {nlp_result.intent.value}
- Sentiment: {nlp_result.sentiment.value}
- Priority: {nlp_result.priority.value}
- Is Question: {nlp_result.is_question}
- Is Urgent: {nlp_result.is_urgent}
- Topics: {', '.join(nlp_result.topics)}
- Keywords: {', '.join(nlp_result.keywords[:5])}{entities_text}{history_text}

BUSINESS INFO:
- Business: Beach Handyman
- Service Area: Virginia Beach area  
- Phone: 757-354-4577
- Current Time: {current_time}

RESPONSE GUIDELINES:
1. Respond based on the detected intent and sentiment
2. Keep responses concise for SMS (under 160 chars when possible)
3. Be professional but friendly
4. Reference extracted entities when relevant
5. For emergencies, show urgency and provide immediate help
6. For appointments, ask for details and offer scheduling
7. For quotes, ask for service details
8. Include business phone for complex requests

Generate an appropriate SMS response:"""
        
        return prompt
    
    async def _handle_emergency_message(self, sms_message: SMSMessage, nlp_result) -> str:
        """Handle emergency messages with special urgency"""
        emergency_response = f"""🚨 EMERGENCY RECEIVED 🚨

I understand this is urgent. Our emergency team has been notified immediately.

Call us NOW: 757-354-4577

For life-threatening emergencies, call 911 first.

We're dispatching help to you ASAP."""
        
        # Log emergency for immediate admin notification
        logger.critical(f"EMERGENCY SMS received from {sms_message.from_number}: {sms_message.body}")
        
        # TODO: Trigger immediate admin notification (email, phone, etc.)
        
        return emergency_response
    
    def _get_fallback_response_by_intent(self, intent: Intent) -> str:
        """Get fallback response based on intent"""
        fallback_responses = {
            Intent.EMERGENCY: "🚨 Emergency received. Calling you immediately at 757-354-4577",
            Intent.APPOINTMENT_SCHEDULE: "I'd be happy to schedule an appointment. What service do you need and when works best? Call 757-354-4577 for faster scheduling.",
            Intent.QUOTE_REQUEST: "I can help with a quote. Please describe the work needed or call 757-354-4577 for a free estimate.",
            Intent.SERVICE_INQUIRY: "Thanks for your inquiry. Can you provide more details about the service you need? Call 757-354-4577.",
            Intent.COMPLAINT: "I apologize for any issues. Please call 757-354-4577 so we can address this immediately.",
            Intent.COMPLIMENT: "Thank you so much! We appreciate your kind words. Beach Handyman - 757-354-4577",
            Intent.PAYMENT_INQUIRY: "For billing questions, please call 757-354-4577 or reply with your invoice number.",
            Intent.GREETING: "Hello! This is Karen from Beach Handyman. How can I help you today? 757-354-4577"
        }
        
        return fallback_responses.get(intent, "Thank you for contacting Beach Handyman. Please call 757-354-4577 for immediate assistance.")
    
    def _update_customer_profile(self, phone_number: str, nlp_result):
        """Update customer profile with NLP insights"""
        if phone_number not in self.customer_profiles:
            self.customer_profiles[phone_number] = {
                'first_contact': datetime.now(timezone.utc).isoformat(),
                'message_count': 0,
                'intents': [],
                'sentiment_history': [],
                'priority_contacts': 0,
                'emergency_contacts': 0
            }
        
        profile = self.customer_profiles[phone_number]
        profile['message_count'] += 1
        profile['last_contact'] = datetime.now(timezone.utc).isoformat()
        profile['intents'].append(nlp_result.intent.value)
        profile['sentiment_history'].append(nlp_result.sentiment.value)
        
        if nlp_result.priority in [Priority.CRITICAL, Priority.HIGH]:
            profile['priority_contacts'] += 1
        
        if nlp_result.intent == Intent.EMERGENCY:
            profile['emergency_contacts'] += 1
        
        # Keep only last 10 intents and sentiments
        profile['intents'] = profile['intents'][-10:]
        profile['sentiment_history'] = profile['sentiment_history'][-10:]
    
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
        response_message, sms_message = await sms.receive_sms_webhook(webhook_data)
        
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
"""
Communication Router for Karen AI Secretary
Communications Agent (COMMS-001)

Central routing system that manages communication flow between:
- Email (Gmail API)
- SMS (Twilio)
- Phone (Twilio Voice)
- Internal systems

Routes messages to appropriate handlers and ensures consistent responses
across all communication channels.
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum

from src.sms_integration import get_sms_integration, SMSMessage
from src.phone_integration import get_phone_integration, PhoneCall
from src.email_client import EmailClient
from src.llm_client import LLMClient
from src.logging_config import setup_logger
from templates.sms_templates import SMSTemplates, get_template_by_intent
from templates.email_templates import EmailTemplates, create_custom_email

logger = setup_logger(__name__)

class ChannelType(Enum):
    """Communication channel types"""
    EMAIL = "email"
    SMS = "sms"
    PHONE = "phone"
    INTERNAL = "internal"

class MessageType(Enum):
    """Message type classifications"""
    EMERGENCY = "emergency"
    APPOINTMENT = "appointment"
    QUOTE = "quote"
    SERVICE_INQUIRY = "service_inquiry"
    FOLLOW_UP = "follow_up"
    GENERAL = "general"

class Priority(Enum):
    """Message priority levels"""
    CRITICAL = "critical"  # Emergencies
    HIGH = "high"         # Urgent requests
    NORMAL = "normal"     # Standard requests
    LOW = "low"          # Marketing, follow-ups

@dataclass
class CommunicationMessage:
    """Unified message structure for all channels"""
    id: str
    channel: ChannelType
    direction: str  # 'inbound' or 'outbound'
    from_contact: str
    to_contact: str
    content: str
    message_type: MessageType
    priority: Priority
    timestamp: datetime
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'channel': self.channel.value,
            'direction': self.direction,
            'from_contact': self.from_contact,
            'to_contact': self.to_contact,
            'content': self.content,
            'message_type': self.message_type.value,
            'priority': self.priority.value,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }

class CommunicationRouter:
    """Central communication routing and management system"""
    
    def __init__(self):
        """Initialize communication router with all integrations"""
        # Initialize communication clients
        self.sms_integration = get_sms_integration()
        self.phone_integration = get_phone_integration()
        self.email_client = EmailClient()
        self.llm_client = LLMClient()
        
        # Message tracking
        self.message_history: List[CommunicationMessage] = []
        self.active_conversations: Dict[str, List[CommunicationMessage]] = {}
        
        # Routing rules and preferences
        self.routing_rules = self._load_routing_rules()
        self.customer_preferences = self._load_customer_preferences()
        
        # Channel availability
        self.channel_status = {
            ChannelType.EMAIL: True,
            ChannelType.SMS: True,
            ChannelType.PHONE: True
        }
        
        logger.info("Communication router initialized with all channels")
    
    async def route_inbound_message(self, channel: ChannelType, raw_message: Any) -> Optional[CommunicationMessage]:
        """
        Route incoming message from any channel
        
        Args:
            channel: Source channel type
            raw_message: Raw message data from channel
            
        Returns:
            Processed CommunicationMessage
        """
        try:
            # Convert raw message to unified format
            message = self._convert_to_unified_message(channel, raw_message)
            if not message:
                return None
            
            # Classify message type and priority
            message.message_type = self._classify_message_type(message.content)
            message.priority = self._determine_priority(message.message_type, message.content)
            
            # Store in message history
            self._add_to_history(message)
            
            # Route for processing based on priority and type
            if message.priority == Priority.CRITICAL:
                await self._handle_emergency_message(message)
            else:
                await self._handle_standard_message(message)
            
            logger.info(f"Routed {channel.value} message from {message.from_contact} - Type: {message.message_type.value}")
            return message
            
        except Exception as e:
            logger.error(f"Error routing inbound {channel.value} message: {e}")
            return None
    
    async def send_outbound_message(self, 
                                  to_contact: str, 
                                  content: str, 
                                  channel: ChannelType = None,
                                  message_type: MessageType = MessageType.GENERAL,
                                  priority: Priority = Priority.NORMAL,
                                  template_data: Dict = None) -> bool:
        """
        Send outbound message through best available channel
        
        Args:
            to_contact: Recipient contact (phone/email)
            content: Message content
            channel: Preferred channel (auto-select if None)
            message_type: Type of message
            priority: Message priority
            template_data: Data for template processing
            
        Returns:
            True if sent successfully
        """
        try:
            # Auto-select channel if not specified
            if channel is None:
                channel = self._select_best_channel(to_contact, message_type, priority)
            
            # Apply template if template_data provided
            if template_data:
                content = self._apply_template(content, channel, message_type, template_data)
            
            # Send through selected channel
            success = await self._send_via_channel(channel, to_contact, content, priority)
            
            if success:
                # Create outbound message record
                message = CommunicationMessage(
                    id=self._generate_message_id(),
                    channel=channel,
                    direction='outbound',
                    from_contact=self._get_business_contact(channel),
                    to_contact=to_contact,
                    content=content,
                    message_type=message_type,
                    priority=priority,
                    timestamp=datetime.now(timezone.utc),
                    metadata={'template_applied': template_data is not None}
                )
                
                self._add_to_history(message)
                logger.info(f"Sent {channel.value} message to {to_contact}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending outbound message: {e}")
            return False
    
    async def _handle_emergency_message(self, message: CommunicationMessage):
        """Handle emergency/critical messages with immediate response"""
        try:
            logger.warning(f"EMERGENCY MESSAGE from {message.from_contact}: {message.content}")
            
            # Immediate auto-response
            emergency_response = "🚨 EMERGENCY RECEIVED: We're dispatching help immediately. Expect contact within 15 minutes. Stay safe!"
            
            # Send immediate confirmation via same channel
            await self._send_via_channel(
                message.channel, 
                message.from_contact, 
                emergency_response, 
                Priority.CRITICAL
            )
            
            # Also send via phone if not already phone message
            if message.channel != ChannelType.PHONE:
                self.phone_integration.make_outbound_call(
                    message.from_contact,
                    "This is Karen from the handyman service. We received your emergency request and are dispatching help immediately."
                )
            
            # Notify emergency response team (would integrate with dispatch system)
            await self._notify_emergency_team(message)
            
        except Exception as e:
            logger.error(f"Error handling emergency message: {e}")
    
    async def _handle_standard_message(self, message: CommunicationMessage):
        """Handle standard messages with intelligent routing"""
        try:
            # Generate intelligent response using LLM
            response_content = await self._generate_intelligent_response(message)
            
            # Determine best response channel
            response_channel = self._select_response_channel(message)
            
            # Send response
            await self._send_via_channel(
                response_channel,
                message.from_contact,
                response_content,
                message.priority
            )
            
            # Schedule follow-up if needed
            if self._needs_followup(message.message_type):
                await self._schedule_followup(message)
            
        except Exception as e:
            logger.error(f"Error handling standard message: {e}")
    
    async def _generate_intelligent_response(self, message: CommunicationMessage) -> str:
        """Generate contextual response using LLM"""
        try:
            # Get conversation history for context
            conversation = self._get_conversation_history(message.from_contact)
            
            # Build context for LLM
            context = {
                'current_message': message.content,
                'message_type': message.message_type.value,
                'channel': message.channel.value,
                'conversation_history': [msg.content for msg in conversation[-5:]],
                'customer_preferences': self.customer_preferences.get(message.from_contact, {}),
                'timestamp': message.timestamp.isoformat()
            }
            
            # Generate response using LLM with system prompt
            with open('src/llm_system_prompt.txt', 'r') as f:
                system_prompt = f.read()
            
            prompt = f"""
{system_prompt}

Current situation:
- Channel: {context['channel']}
- Message type: {context['message_type']}
- Customer message: "{context['current_message']}"
- Previous conversation: {context['conversation_history']}

Generate an appropriate response:"""

            response = self.llm_client.generate_response(prompt)
            
            # Ensure response is appropriate for channel
            response = self._optimize_for_channel(response, message.channel)
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating intelligent response: {e}")
            return self._get_fallback_response(message.message_type, message.channel)
    
    def _convert_to_unified_message(self, channel: ChannelType, raw_message: Any) -> Optional[CommunicationMessage]:
        """Convert channel-specific message to unified format"""
        try:
            if channel == ChannelType.SMS:
                if isinstance(raw_message, dict):
                    # Webhook data
                    return CommunicationMessage(
                        id=raw_message.get('MessageSid', self._generate_message_id()),
                        channel=ChannelType.SMS,
                        direction='inbound',
                        from_contact=raw_message.get('From', ''),
                        to_contact=raw_message.get('To', ''),
                        content=raw_message.get('Body', ''),
                        message_type=MessageType.GENERAL,  # Will be classified later
                        priority=Priority.NORMAL,  # Will be determined later
                        timestamp=datetime.now(timezone.utc),
                        metadata={'sms_sid': raw_message.get('MessageSid')}
                    )
                elif isinstance(raw_message, SMSMessage):
                    return CommunicationMessage(
                        id=raw_message.sid,
                        channel=ChannelType.SMS,
                        direction=raw_message.direction,
                        from_contact=raw_message.from_number,
                        to_contact=raw_message.to_number,
                        content=raw_message.body,
                        message_type=MessageType.GENERAL,
                        priority=Priority.NORMAL,
                        timestamp=raw_message.timestamp,
                        metadata={'sms_status': raw_message.status}
                    )
            
            elif channel == ChannelType.PHONE:
                if isinstance(raw_message, dict):
                    # Call webhook data
                    return CommunicationMessage(
                        id=raw_message.get('CallSid', self._generate_message_id()),
                        channel=ChannelType.PHONE,
                        direction='inbound',
                        from_contact=raw_message.get('From', ''),
                        to_contact=raw_message.get('To', ''),
                        content=raw_message.get('transcription', 'Phone call received'),
                        message_type=MessageType.GENERAL,
                        priority=Priority.NORMAL,
                        timestamp=datetime.now(timezone.utc),
                        metadata={'call_sid': raw_message.get('CallSid'), 'call_status': raw_message.get('CallStatus')}
                    )
                elif isinstance(raw_message, PhoneCall):
                    return CommunicationMessage(
                        id=raw_message.sid,
                        channel=ChannelType.PHONE,
                        direction=raw_message.direction,
                        from_contact=raw_message.from_number,
                        to_contact=raw_message.to_number,
                        content=raw_message.transcription or 'Phone call',
                        message_type=MessageType.GENERAL,
                        priority=Priority.NORMAL,
                        timestamp=raw_message.start_time,
                        metadata={'call_status': raw_message.status.value, 'duration': raw_message.duration}
                    )
            
            elif channel == ChannelType.EMAIL:
                # Email message conversion
                return CommunicationMessage(
                    id=raw_message.get('id', self._generate_message_id()),
                    channel=ChannelType.EMAIL,
                    direction='inbound',
                    from_contact=raw_message.get('from', ''),
                    to_contact=raw_message.get('to', ''),
                    content=raw_message.get('body', ''),
                    message_type=MessageType.GENERAL,
                    priority=Priority.NORMAL,
                    timestamp=datetime.now(timezone.utc),
                    metadata={'subject': raw_message.get('subject', ''), 'email_id': raw_message.get('id')}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error converting {channel.value} message: {e}")
            return None
    
    def _classify_message_type(self, content: str) -> MessageType:
        """Classify message type based on content"""
        content_lower = content.lower()
        
        # Emergency keywords
        emergency_words = ['emergency', 'urgent', 'asap', 'help', 'problem', 'leak', 'flood', 'electrical', 'gas', 'fire']
        if any(word in content_lower for word in emergency_words):
            return MessageType.EMERGENCY
        
        # Appointment keywords
        appointment_words = ['appointment', 'schedule', 'book', 'available', 'time', 'when can']
        if any(word in content_lower for word in appointment_words):
            return MessageType.APPOINTMENT
        
        # Quote keywords
        quote_words = ['quote', 'price', 'cost', 'estimate', 'how much', 'pricing']
        if any(word in content_lower for word in quote_words):
            return MessageType.QUOTE
        
        # Service inquiry keywords
        service_words = ['service', 'repair', 'fix', 'install', 'maintenance', 'handyman']
        if any(word in content_lower for word in service_words):
            return MessageType.SERVICE_INQUIRY
        
        return MessageType.GENERAL
    
    def _determine_priority(self, message_type: MessageType, content: str) -> Priority:
        """Determine message priority"""
        if message_type == MessageType.EMERGENCY:
            return Priority.CRITICAL
        
        # Check for urgency indicators
        urgent_words = ['urgent', 'asap', 'immediately', 'today', 'now']
        if any(word in content.lower() for word in urgent_words):
            return Priority.HIGH
        
        if message_type in [MessageType.APPOINTMENT, MessageType.QUOTE, MessageType.SERVICE_INQUIRY]:
            return Priority.NORMAL
        
        return Priority.LOW
    
    def _select_best_channel(self, contact: str, message_type: MessageType, priority: Priority) -> ChannelType:
        """Select best communication channel for response"""
        # Critical messages prefer phone
        if priority == Priority.CRITICAL:
            return ChannelType.PHONE
        
        # Check customer preferences
        prefs = self.customer_preferences.get(contact, {})
        preferred_channel = prefs.get('preferred_channel')
        
        if preferred_channel and self.channel_status.get(ChannelType(preferred_channel), False):
            return ChannelType(preferred_channel)
        
        # Default logic based on message type
        if message_type == MessageType.APPOINTMENT:
            return ChannelType.EMAIL  # Detailed confirmation
        elif message_type in [MessageType.QUOTE, MessageType.SERVICE_INQUIRY]:
            return ChannelType.EMAIL  # Detailed information
        else:
            return ChannelType.SMS  # Quick responses
    
    def _select_response_channel(self, original_message: CommunicationMessage) -> ChannelType:
        """Select channel for response based on original message"""
        # Emergency: Always respond via same channel + phone
        if original_message.priority == Priority.CRITICAL:
            return original_message.channel
        
        # For complex responses, prefer email
        if original_message.message_type in [MessageType.QUOTE, MessageType.SERVICE_INQUIRY]:
            return ChannelType.EMAIL
        
        # Otherwise, use same channel as original
        return original_message.channel
    
    async def _send_via_channel(self, channel: ChannelType, to_contact: str, content: str, priority: Priority) -> bool:
        """Send message via specified channel"""
        try:
            if channel == ChannelType.SMS:
                priority_str = 'urgent' if priority == Priority.CRITICAL else 'normal'
                sms_message = self.sms_integration.send_sms(to_contact, content, priority_str)
                return sms_message is not None
            
            elif channel == ChannelType.PHONE:
                call = self.phone_integration.make_outbound_call(to_contact, content)
                return call is not None
            
            elif channel == ChannelType.EMAIL:
                # Use email client to send
                subject = self._generate_email_subject(content)
                success = self.email_client.send_email(to_contact, subject, content)
                return success
            
            return False
            
        except Exception as e:
            logger.error(f"Error sending via {channel.value}: {e}")
            return False
    
    def _optimize_for_channel(self, content: str, channel: ChannelType) -> str:
        """Optimize content for specific channel"""
        if channel == ChannelType.SMS:
            # Limit SMS to 1600 characters, prefer 160
            if len(content) > 1500:
                content = content[:1500] + "... (cont'd in email)"
        
        elif channel == ChannelType.PHONE:
            # Add pauses and clear speech patterns
            content = content.replace('. ', '. [pause] ')
            content = content.replace('!', ' [emphasis]')
        
        # EMAIL doesn't need optimization - can be long
        return content
    
    def _get_fallback_response(self, message_type: MessageType, channel: ChannelType) -> str:
        """Get fallback response if LLM fails"""
        fallback_map = {
            MessageType.EMERGENCY: "We received your urgent message and are responding immediately. Please stay safe.",
            MessageType.APPOINTMENT: "Thank you for your appointment request. We'll get back to you with available times shortly.",
            MessageType.QUOTE: "We received your quote request. We'll review your needs and provide an estimate soon.",
            MessageType.SERVICE_INQUIRY: "Thank you for your service inquiry. We'll respond with details shortly.",
            MessageType.GENERAL: "Thank you for contacting us. We'll get back to you soon."
        }
        
        return fallback_map.get(message_type, "Thank you for your message. We'll respond shortly.")
    
    def _add_to_history(self, message: CommunicationMessage):
        """Add message to history and conversation tracking"""
        self.message_history.append(message)
        
        # Add to conversation history
        contact = message.from_contact if message.direction == 'inbound' else message.to_contact
        if contact not in self.active_conversations:
            self.active_conversations[contact] = []
        
        self.active_conversations[contact].append(message)
        
        # Keep only last 50 messages per conversation
        if len(self.active_conversations[contact]) > 50:
            self.active_conversations[contact] = self.active_conversations[contact][-50:]
    
    def _get_conversation_history(self, contact: str) -> List[CommunicationMessage]:
        """Get conversation history for contact"""
        return self.active_conversations.get(contact, [])
    
    def _generate_message_id(self) -> str:
        """Generate unique message ID"""
        return f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(self) % 10000}"
    
    def _generate_email_subject(self, content: str) -> str:
        """Generate email subject from content"""
        # Simple subject generation - could be enhanced with LLM
        first_sentence = content.split('.')[0]
        if len(first_sentence) > 50:
            return "Service Update - Karen AI Secretary"
        return f"Re: {first_sentence}"
    
    def _get_business_contact(self, channel: ChannelType) -> str:
        """Get business contact for channel"""
        contacts = {
            ChannelType.SMS: os.getenv('TWILIO_FROM_NUMBER', '+1234567890'),
            ChannelType.PHONE: os.getenv('TWILIO_PHONE_NUMBER', '+1234567890'),
            ChannelType.EMAIL: os.getenv('SECRETARY_EMAIL_ADDRESS', 'karen@business.com')
        }
        return contacts.get(channel, 'karen@business.com')
    
    async def _notify_emergency_team(self, message: CommunicationMessage):
        """Notify emergency response team"""
        # This would integrate with dispatch/notification systems
        emergency_data = {
            'contact': message.from_contact,
            'message': message.content,
            'timestamp': message.timestamp.isoformat(),
            'channel': message.channel.value
        }
        
        # Send to emergency dispatch system
        logger.critical(f"EMERGENCY DISPATCH: {emergency_data}")
    
    async def _schedule_followup(self, message: CommunicationMessage):
        """Schedule follow-up communication"""
        # This would integrate with scheduling system
        logger.info(f"Scheduling follow-up for {message.from_contact} - Type: {message.message_type.value}")
    
    def _needs_followup(self, message_type: MessageType) -> bool:
        """Determine if message type needs follow-up"""
        return message_type in [MessageType.APPOINTMENT, MessageType.QUOTE, MessageType.SERVICE_INQUIRY]
    
    def _load_routing_rules(self) -> Dict:
        """Load routing rules configuration"""
        # Default routing rules
        return {
            'emergency_channels': ['phone', 'sms'],
            'business_hours': {'start': 8, 'end': 18},
            'auto_response_enabled': True,
            'max_response_time_minutes': 15
        }
    
    def _load_customer_preferences(self) -> Dict:
        """Load customer communication preferences"""
        # This would load from database in production
        return {}
    
    def _apply_template(self, content: str, channel: ChannelType, message_type: MessageType, template_data: Dict) -> str:
        """Apply template formatting to content"""
        try:
            if channel == ChannelType.SMS:
                if message_type == MessageType.APPOINTMENT:
                    return SMSTemplates.appointment_confirmation(**template_data)
                elif message_type == MessageType.EMERGENCY:
                    return SMSTemplates.emergency_response(**template_data)
                # Add more SMS templates as needed
            
            elif channel == ChannelType.EMAIL:
                if message_type == MessageType.QUOTE:
                    return create_custom_email('estimate', template_data)['body']
                elif message_type == MessageType.APPOINTMENT:
                    return create_custom_email('appointment', template_data)['body']
                # Add more email templates as needed
            
            return content
            
        except Exception as e:
            logger.error(f"Error applying template: {e}")
            return content
    
    def get_communication_stats(self) -> Dict:
        """Get communication statistics"""
        total_messages = len(self.message_history)
        
        # Count by channel
        channel_counts = {}
        for channel in ChannelType:
            channel_counts[channel.value] = len([m for m in self.message_history if m.channel == channel])
        
        # Count by type
        type_counts = {}
        for msg_type in MessageType:
            type_counts[msg_type.value] = len([m for m in self.message_history if m.message_type == msg_type])
        
        return {
            'total_messages': total_messages,
            'active_conversations': len(self.active_conversations),
            'channel_breakdown': channel_counts,
            'message_type_breakdown': type_counts,
            'channel_status': {ch.value: status for ch, status in self.channel_status.items()}
        }
    
    def health_check(self) -> Dict:
        """Perform health check on all communication channels"""
        health_status = {
            'router_status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        try:
            # Check SMS integration
            sms_health = self.sms_integration.health_check()
            health_status['sms'] = sms_health
            
            # Check phone integration
            phone_health = self.phone_integration.health_check()
            health_status['phone'] = phone_health
            
            # Check email client
            # email_health = self.email_client.health_check()  # Implement if available
            # health_status['email'] = email_health
            
            # Overall status
            unhealthy_channels = []
            if sms_health.get('status') != 'healthy':
                unhealthy_channels.append('sms')
            if phone_health.get('status') != 'healthy':
                unhealthy_channels.append('phone')
            
            if unhealthy_channels:
                health_status['router_status'] = 'degraded'
                health_status['unhealthy_channels'] = unhealthy_channels
            
        except Exception as e:
            health_status['router_status'] = 'unhealthy'
            health_status['error'] = str(e)
        
        return health_status

# Global communication router instance
communication_router = None

def get_communication_router() -> CommunicationRouter:
    """Get or create communication router instance"""
    global communication_router
    if communication_router is None:
        communication_router = CommunicationRouter()
    return communication_router

# Webhook handlers for integration with web framework
async def handle_sms_webhook(webhook_data: Dict) -> str:
    """Handle SMS webhook through communication router"""
    router = get_communication_router()
    message = await router.route_inbound_message(ChannelType.SMS, webhook_data)
    
    # Return TwiML response
    if message and message.priority == Priority.CRITICAL:
        return router.sms_integration.create_twiml_response("Emergency response dispatched. Help is on the way.")
    else:
        return router.sms_integration.create_twiml_response("Thank you for your message. We'll respond shortly.")

async def handle_voice_webhook(webhook_data: Dict) -> str:
    """Handle voice webhook through communication router"""
    router = get_communication_router()
    message = await router.route_inbound_message(ChannelType.PHONE, webhook_data)
    
    # Return TwiML response
    return router.phone_integration.handle_incoming_call(webhook_data)

async def handle_email_webhook(email_data: Dict) -> bool:
    """Handle email webhook through communication router"""
    router = get_communication_router()
    message = await router.route_inbound_message(ChannelType.EMAIL, email_data)
    return message is not None
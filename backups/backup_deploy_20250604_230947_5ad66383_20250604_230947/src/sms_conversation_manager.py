"""
SMS Conversation Manager - Thread-based conversation tracking system
Handles conversation state, threading, and context management for SMS communications.
"""

import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConversationState(Enum):
    """Conversation state machine states"""
    INITIAL_CONTACT = "initial"
    GATHERING_INFO = "gathering"
    SCHEDULING = "scheduling"
    CONFIRMING = "confirming"
    COMPLETE = "complete"
    TIMEOUT = "timeout"
    ERROR = "error"

class MessageType(Enum):
    """Message types for classification"""
    GREETING = "greeting"
    QUESTION = "question"
    APPOINTMENT_REQUEST = "appointment_request"
    QUOTE_REQUEST = "quote_request"
    CONFIRMATION = "confirmation"
    EMERGENCY = "emergency"
    FOLLOW_UP = "follow_up"
    OTHER = "other"

@dataclass
class ConversationMessage:
    """Individual message in a conversation"""
    message_id: str
    phone_number: str
    content: str
    direction: str  # 'inbound' or 'outbound'
    timestamp: datetime
    message_type: MessageType
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return {
            'message_id': self.message_id,
            'phone_number': self.phone_number,
            'content': self.content,
            'direction': self.direction,
            'timestamp': self.timestamp.isoformat(),
            'message_type': self.message_type.value,
            'metadata': self.metadata
        }

@dataclass
class ConversationThread:
    """Individual conversation thread"""
    conversation_id: str
    phone_number: str
    state: ConversationState
    created_at: datetime
    last_activity: datetime
    messages: List[ConversationMessage]
    context: Dict[str, Any]
    customer_info: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return {
            'conversation_id': self.conversation_id,
            'phone_number': self.phone_number,
            'state': self.state.value,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'messages': [msg.to_dict() for msg in self.messages],
            'context': self.context,
            'customer_info': self.customer_info
        }

class ConversationManager:
    """Manages all SMS conversation threads"""
    
    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=0):
        """Initialize conversation manager"""
        # Redis connection for fast state storage
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(
                    host=redis_host, 
                    port=redis_port, 
                    db=redis_db, 
                    decode_responses=True
                )
                self.redis_client.ping()
                self.redis_available = True
                logger.info("Redis connection established for conversation storage")
            except (redis.ConnectionError, Exception):
                logger.warning("Redis connection failed, using memory storage")
                self.redis_available = False
                self._memory_storage = {}
        else:
            logger.info("Redis not installed, using memory storage")
            self.redis_available = False
            self._memory_storage = {}
        
        # Configuration
        self.conversation_timeout = timedelta(hours=24)
        self.max_messages_per_conversation = 100
        self.context_window = 10  # Last 10 messages for active context
        
        # State transition rules
        self.state_transitions = {
            ConversationState.INITIAL_CONTACT: [
                ConversationState.GATHERING_INFO, 
                ConversationState.SCHEDULING,
                ConversationState.COMPLETE
            ],
            ConversationState.GATHERING_INFO: [
                ConversationState.SCHEDULING, 
                ConversationState.COMPLETE,
                ConversationState.CONFIRMING
            ],
            ConversationState.SCHEDULING: [
                ConversationState.CONFIRMING,
                ConversationState.COMPLETE,
                ConversationState.GATHERING_INFO
            ],
            ConversationState.CONFIRMING: [
                ConversationState.COMPLETE,
                ConversationState.SCHEDULING
            ],
            ConversationState.COMPLETE: [
                ConversationState.INITIAL_CONTACT  # New conversation
            ],
            ConversationState.TIMEOUT: [
                ConversationState.INITIAL_CONTACT  # Can restart
            ]
        }
    
    def start_conversation(self, phone_number: str, initial_message: str, 
                         customer_info: Dict[str, Any] = None) -> ConversationThread:
        """Start a new conversation thread"""
        try:
            # Check for existing active conversation
            existing_conversation = self.get_active_conversation(phone_number)
            if existing_conversation and not self._is_conversation_expired(existing_conversation):
                logger.info(f"Resuming existing conversation for {phone_number}")
                return existing_conversation
            
            # Create new conversation
            conversation_id = f"conv_{phone_number}_{int(time.time())}"
            now = datetime.now()
            
            # Create initial message
            initial_msg = ConversationMessage(
                message_id=f"msg_{int(time.time() * 1000)}",
                phone_number=phone_number,
                content=initial_message,
                direction='inbound',
                timestamp=now,
                message_type=self._classify_message_type(initial_message),
                metadata={}
            )
            
            # Create conversation thread
            conversation = ConversationThread(
                conversation_id=conversation_id,
                phone_number=phone_number,
                state=ConversationState.INITIAL_CONTACT,
                created_at=now,
                last_activity=now,
                messages=[initial_msg],
                context={
                    'intent': self._extract_intent(initial_message),
                    'urgency': self._assess_urgency(initial_message),
                    'requires_human': False
                },
                customer_info=customer_info or {}
            )
            
            # Transition to appropriate state based on message
            self._transition_state(conversation, initial_msg)
            
            # Save conversation
            self._save_conversation(conversation)
            
            logger.info(f"Started new conversation {conversation_id} for {phone_number}")
            return conversation
            
        except Exception as e:
            logger.error(f"Error starting conversation for {phone_number}: {e}")
            raise
    
    def add_message(self, phone_number: str, content: str, direction: str,
                   message_id: str = None, metadata: Dict[str, Any] = None) -> ConversationThread:
        """Add a message to existing conversation"""
        try:
            # Get or create conversation
            conversation = self.get_active_conversation(phone_number)
            if not conversation:
                if direction == 'inbound':
                    conversation = self.start_conversation(phone_number, content)
                else:
                    raise ValueError(f"No active conversation for outbound message to {phone_number}")
            
            # Check if conversation is expired
            if self._is_conversation_expired(conversation):
                if direction == 'inbound':
                    logger.info(f"Conversation expired, starting new one for {phone_number}")
                    conversation = self.start_conversation(phone_number, content)
                else:
                    raise ValueError(f"Cannot send outbound message to expired conversation {phone_number}")
            
            # Create message
            message = ConversationMessage(
                message_id=message_id or f"msg_{int(time.time() * 1000)}",
                phone_number=phone_number,
                content=content,
                direction=direction,
                timestamp=datetime.now(),
                message_type=self._classify_message_type(content),
                metadata=metadata or {}
            )
            
            # Add to conversation
            conversation.messages.append(message)
            conversation.last_activity = datetime.now()
            
            # Update context based on new message
            self._update_context(conversation, message)
            
            # Handle state transitions
            if direction == 'inbound':
                self._transition_state(conversation, message)
            
            # Trim old messages if needed
            if len(conversation.messages) > self.max_messages_per_conversation:
                # Archive old messages and keep recent ones
                self._archive_old_messages(conversation)
            
            # Save updated conversation
            self._save_conversation(conversation)
            
            logger.info(f"Added {direction} message to conversation {conversation.conversation_id}")
            return conversation
            
        except Exception as e:
            logger.error(f"Error adding message to conversation {phone_number}: {e}")
            raise
    
    def get_context(self, phone_number: str) -> Dict[str, Any]:
        """Get conversation context for decision making"""
        try:
            conversation = self.get_active_conversation(phone_number)
            if not conversation:
                return {
                    'has_conversation': False,
                    'state': None,
                    'message_count': 0,
                    'context': {},
                    'recent_messages': []
                }
            
            # Get recent messages for context
            recent_messages = conversation.messages[-self.context_window:]
            
            # Build context summary
            context = {
                'has_conversation': True,
                'conversation_id': conversation.conversation_id,
                'state': conversation.state.value,
                'message_count': len(conversation.messages),
                'created_at': conversation.created_at.isoformat(),
                'last_activity': conversation.last_activity.isoformat(),
                'time_since_last_activity': self._time_since_last_activity(conversation),
                'context': conversation.context,
                'customer_info': conversation.customer_info,
                'recent_messages': [
                    {
                        'content': msg.content,
                        'direction': msg.direction,
                        'timestamp': msg.timestamp.isoformat(),
                        'type': msg.message_type.value,
                        'time_ago': self._time_ago(msg.timestamp)
                    } for msg in recent_messages
                ],
                'conversation_summary': self._generate_conversation_summary(conversation),
                'requires_human': conversation.context.get('requires_human', False)
            }
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting context for {phone_number}: {e}")
            return {'has_conversation': False, 'error': str(e)}
    
    def close_conversation(self, phone_number: str, reason: str = 'completed') -> bool:
        """Close an active conversation"""
        try:
            conversation = self.get_active_conversation(phone_number)
            if not conversation:
                logger.warning(f"No active conversation to close for {phone_number}")
                return False
            
            # Update state
            conversation.state = ConversationState.COMPLETE
            conversation.context['closure_reason'] = reason
            conversation.context['closed_at'] = datetime.now().isoformat()
            
            # Archive conversation
            self._archive_conversation(conversation)
            
            # Remove from active storage
            self._remove_conversation(phone_number)
            
            logger.info(f"Closed conversation {conversation.conversation_id} for {phone_number}")
            return True
            
        except Exception as e:
            logger.error(f"Error closing conversation for {phone_number}: {e}")
            return False
    
    def get_active_conversation(self, phone_number: str) -> Optional[ConversationThread]:
        """Get active conversation for phone number"""
        try:
            conv_key = f"conversation:{phone_number}"
            
            if self.redis_available:
                conv_data = self.redis_client.get(conv_key)
                if conv_data:
                    return self._dict_to_conversation(json.loads(conv_data))
            else:
                conv_data = self._memory_storage.get(conv_key)
                if conv_data:
                    return self._dict_to_conversation(conv_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting conversation for {phone_number}: {e}")
            return None
    
    def cleanup_expired_conversations(self) -> int:
        """Clean up expired conversations"""
        cleaned_count = 0
        
        try:
            if self.redis_available:
                # Get all conversation keys
                pattern = "conversation:*"
                for key in self.redis_client.scan_iter(match=pattern):
                    conv_data = self.redis_client.get(key)
                    if conv_data:
                        conversation = self._dict_to_conversation(json.loads(conv_data))
                        if self._is_conversation_expired(conversation):
                            # Archive and remove
                            conversation.state = ConversationState.TIMEOUT
                            self._archive_conversation(conversation)
                            self.redis_client.delete(key)
                            cleaned_count += 1
            else:
                # Clean memory storage
                keys_to_remove = []
                for key, conv_data in self._memory_storage.items():
                    if key.startswith("conversation:"):
                        conversation = self._dict_to_conversation(conv_data)
                        if self._is_conversation_expired(conversation):
                            conversation.state = ConversationState.TIMEOUT
                            self._archive_conversation(conversation)
                            keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    del self._memory_storage[key]
                    cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} expired conversations")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired conversations: {e}")
            return 0
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """Get statistics about active conversations"""
        try:
            stats = {
                'active_conversations': 0,
                'states': {},
                'average_messages': 0,
                'storage_type': 'redis' if self.redis_available else 'memory'
            }
            
            total_messages = 0
            
            if self.redis_available:
                pattern = "conversation:*"
                for key in self.redis_client.scan_iter(match=pattern):
                    conv_data = self.redis_client.get(key)
                    if conv_data:
                        conversation = self._dict_to_conversation(json.loads(conv_data))
                        stats['active_conversations'] += 1
                        
                        state = conversation.state.value
                        stats['states'][state] = stats['states'].get(state, 0) + 1
                        
                        total_messages += len(conversation.messages)
            else:
                for conv_data in self._memory_storage.values():
                    if isinstance(conv_data, dict) and 'conversation_id' in conv_data:
                        conversation = self._dict_to_conversation(conv_data)
                        stats['active_conversations'] += 1
                        
                        state = conversation.state.value
                        stats['states'][state] = stats['states'].get(state, 0) + 1
                        
                        total_messages += len(conversation.messages)
            
            if stats['active_conversations'] > 0:
                stats['average_messages'] = total_messages / stats['active_conversations']
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting conversation stats: {e}")
            return {'error': str(e)}
    
    # Private methods
    
    def _save_conversation(self, conversation: ConversationThread):
        """Save conversation to storage"""
        conv_key = f"conversation:{conversation.phone_number}"
        conv_data = conversation.to_dict()
        
        if self.redis_available:
            # Set with expiration
            self.redis_client.setex(
                conv_key,
                int(self.conversation_timeout.total_seconds()),
                json.dumps(conv_data)
            )
        else:
            self._memory_storage[conv_key] = conv_data
    
    def _remove_conversation(self, phone_number: str):
        """Remove conversation from active storage"""
        conv_key = f"conversation:{phone_number}"
        
        if self.redis_available:
            self.redis_client.delete(conv_key)
        else:
            self._memory_storage.pop(conv_key, None)
    
    def _dict_to_conversation(self, data: Dict) -> ConversationThread:
        """Convert dictionary to ConversationThread"""
        messages = []
        for msg_data in data['messages']:
            msg = ConversationMessage(
                message_id=msg_data['message_id'],
                phone_number=msg_data['phone_number'],
                content=msg_data['content'],
                direction=msg_data['direction'],
                timestamp=datetime.fromisoformat(msg_data['timestamp']),
                message_type=MessageType(msg_data['message_type']),
                metadata=msg_data['metadata']
            )
            messages.append(msg)
        
        return ConversationThread(
            conversation_id=data['conversation_id'],
            phone_number=data['phone_number'],
            state=ConversationState(data['state']),
            created_at=datetime.fromisoformat(data['created_at']),
            last_activity=datetime.fromisoformat(data['last_activity']),
            messages=messages,
            context=data['context'],
            customer_info=data['customer_info']
        )
    
    def _is_conversation_expired(self, conversation: ConversationThread) -> bool:
        """Check if conversation has expired"""
        return datetime.now() - conversation.last_activity > self.conversation_timeout
    
    def _classify_message_type(self, content: str) -> MessageType:
        """Classify message type based on content"""
        content_lower = content.lower()
        
        # Emergency detection
        if any(word in content_lower for word in ['emergency', 'urgent', 'asap', 'help', 'broken']):
            return MessageType.EMERGENCY
        
        # Greeting detection
        if any(word in content_lower for word in ['hello', 'hi', 'hey', 'good morning']):
            return MessageType.GREETING
        
        # Appointment request
        if any(word in content_lower for word in ['appointment', 'schedule', 'book', 'available']):
            return MessageType.APPOINTMENT_REQUEST
        
        # Quote request
        if any(word in content_lower for word in ['quote', 'price', 'cost', 'estimate']):
            return MessageType.QUOTE_REQUEST
        
        # Confirmation
        if any(word in content_lower for word in ['yes', 'confirm', 'ok', 'sure', 'sounds good']):
            return MessageType.CONFIRMATION
        
        # Follow up
        if any(word in content_lower for word in ['thanks', 'thank you', 'following up']):
            return MessageType.FOLLOW_UP
        
        # Question
        if '?' in content or any(word in content_lower for word in ['what', 'when', 'where', 'how']):
            return MessageType.QUESTION
        
        return MessageType.OTHER
    
    def _extract_intent(self, message: str) -> str:
        """Extract intent from message"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['schedule', 'appointment', 'book']):
            return 'schedule_appointment'
        elif any(word in message_lower for word in ['quote', 'price', 'cost']):
            return 'get_quote'
        elif any(word in message_lower for word in ['emergency', 'urgent']):
            return 'emergency_service'
        elif any(word in message_lower for word in ['question', 'info', 'tell me']):
            return 'get_information'
        else:
            return 'general_inquiry'
    
    def _assess_urgency(self, message: str) -> str:
        """Assess urgency level of message"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['emergency', 'urgent', 'asap', 'immediately']):
            return 'high'
        elif any(word in message_lower for word in ['soon', 'today', 'this week']):
            return 'medium'
        else:
            return 'low'
    
    def _transition_state(self, conversation: ConversationThread, message: ConversationMessage):
        """Handle state transitions based on message"""
        current_state = conversation.state
        new_state = current_state
        
        # State transition logic
        if current_state == ConversationState.INITIAL_CONTACT:
            if message.message_type == MessageType.APPOINTMENT_REQUEST:
                new_state = ConversationState.SCHEDULING
            elif message.message_type == MessageType.QUOTE_REQUEST:
                new_state = ConversationState.GATHERING_INFO
            elif message.message_type == MessageType.EMERGENCY:
                new_state = ConversationState.COMPLETE  # Immediate escalation
                conversation.context['requires_human'] = True
            else:
                new_state = ConversationState.GATHERING_INFO
        
        elif current_state == ConversationState.GATHERING_INFO:
            if message.message_type == MessageType.CONFIRMATION:
                new_state = ConversationState.SCHEDULING
            elif 'complete' in message.content.lower():
                new_state = ConversationState.COMPLETE
        
        elif current_state == ConversationState.SCHEDULING:
            if message.message_type == MessageType.CONFIRMATION:
                new_state = ConversationState.CONFIRMING
        
        elif current_state == ConversationState.CONFIRMING:
            if message.message_type == MessageType.CONFIRMATION:
                new_state = ConversationState.COMPLETE
        
        # Validate transition
        if new_state != current_state:
            allowed_transitions = self.state_transitions.get(current_state, [])
            if new_state in allowed_transitions:
                conversation.state = new_state
                conversation.context['state_history'] = conversation.context.get('state_history', [])
                conversation.context['state_history'].append({
                    'from': current_state.value,
                    'to': new_state.value,
                    'timestamp': datetime.now().isoformat(),
                    'trigger_message': message.message_id
                })
                logger.info(f"State transition: {current_state.value} -> {new_state.value}")
    
    def _update_context(self, conversation: ConversationThread, message: ConversationMessage):
        """Update conversation context based on new message"""
        # Extract entities and update context
        if message.direction == 'inbound':
            # Update customer preferences
            if 'morning' in message.content.lower():
                conversation.context['preferred_time'] = 'morning'
            elif 'afternoon' in message.content.lower():
                conversation.context['preferred_time'] = 'afternoon'
            elif 'evening' in message.content.lower():
                conversation.context['preferred_time'] = 'evening'
            
            # Update service type
            services = ['plumbing', 'electrical', 'hvac', 'handyman', 'repair']
            for service in services:
                if service in message.content.lower():
                    conversation.context['service_type'] = service
                    break
        
        # Update message type counts
        msg_type_counts = conversation.context.get('message_type_counts', {})
        msg_type = message.message_type.value
        msg_type_counts[msg_type] = msg_type_counts.get(msg_type, 0) + 1
        conversation.context['message_type_counts'] = msg_type_counts
    
    def _generate_conversation_summary(self, conversation: ConversationThread) -> str:
        """Generate summary of conversation for handoff"""
        summary_parts = []
        
        # Basic info
        summary_parts.append(f"Conversation started: {conversation.created_at.strftime('%Y-%m-%d %H:%M')}")
        summary_parts.append(f"Messages exchanged: {len(conversation.messages)}")
        summary_parts.append(f"Current state: {conversation.state.value}")
        
        # Context details
        context = conversation.context
        if context.get('intent'):
            summary_parts.append(f"Intent: {context['intent']}")
        if context.get('service_type'):
            summary_parts.append(f"Service type: {context['service_type']}")
        if context.get('urgency'):
            summary_parts.append(f"Urgency: {context['urgency']}")
        
        # Recent messages
        recent_messages = conversation.messages[-3:]
        summary_parts.append("Recent messages:")
        for msg in recent_messages:
            direction = "Customer" if msg.direction == 'inbound' else "Karen"
            summary_parts.append(f"  {direction}: {msg.content[:100]}...")
        
        return "\n".join(summary_parts)
    
    def _time_ago(self, timestamp: datetime) -> str:
        """Convert timestamp to human readable time ago"""
        delta = datetime.now() - timestamp
        
        if delta.days > 0:
            return f"{delta.days}d ago"
        elif delta.seconds > 3600:
            return f"{delta.seconds // 3600}h ago"
        elif delta.seconds > 60:
            return f"{delta.seconds // 60}m ago"
        else:
            return "just now"
    
    def _time_since_last_activity(self, conversation: ConversationThread) -> str:
        """Get time since last activity"""
        return self._time_ago(conversation.last_activity)
    
    def _archive_old_messages(self, conversation: ConversationThread):
        """Archive old messages and keep recent ones"""
        if len(conversation.messages) > self.max_messages_per_conversation:
            # Keep last 50 messages
            old_messages = conversation.messages[:-50]
            conversation.messages = conversation.messages[-50:]
            
            # Archive old messages (implement database storage)
            logger.info(f"Archived {len(old_messages)} old messages for conversation {conversation.conversation_id}")
    
    def _archive_conversation(self, conversation: ConversationThread):
        """Archive completed conversation"""
        # This would save to database in production
        archive_data = conversation.to_dict()
        archive_data['archived_at'] = datetime.now().isoformat()
        
        # For now, just log
        logger.info(f"Archived conversation {conversation.conversation_id}")

# Global instance
_conversation_manager = None

def get_conversation_manager() -> ConversationManager:
    """Get singleton conversation manager instance"""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationManager()
    return _conversation_manager
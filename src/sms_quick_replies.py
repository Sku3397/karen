"""
Quick Reply System for common SMS responses
Provides intelligent, contextual quick replies to make conversations feel natural
"""
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import json
import re
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ReplyCategory(Enum):
    """Categories of quick replies"""
    APPOINTMENT = "appointment"
    QUOTE = "quote"
    CONFIRMATION = "confirmation"
    SCHEDULING = "scheduling"
    EMERGENCY = "emergency"
    INFORMATION = "information"
    CLOSING = "closing"
    GREETING = "greeting"

@dataclass
class QuickReply:
    """Individual quick reply option"""
    id: str
    text: str
    category: ReplyCategory
    triggers: List[str]
    response_template: str
    action: str
    confidence_boost: float = 1.0
    context_required: Dict[str, Any] = None

class QuickReplySystem:
    """Intelligent quick reply system with contextual awareness"""
    
    def __init__(self):
        """Initialize with comprehensive quick reply database"""
        self.quick_replies = self._initialize_quick_replies()
        self.context_weights = {
            'recency': 0.3,
            'message_type': 0.4,
            'conversation_state': 0.2,
            'urgency': 0.1
        }
        
    def _initialize_quick_replies(self) -> Dict[str, QuickReply]:
        """Initialize comprehensive quick reply database"""
        replies = {}
        
        # Appointment-related replies
        appointment_replies = [
            QuickReply(
                id="appointment_confirm",
                text="✅ Confirm appointment",
                category=ReplyCategory.APPOINTMENT,
                triggers=['confirm', 'yes', 'ok', 'sounds good', 'perfect', 'great'],
                response_template="Perfect! Your appointment is confirmed for {appointment_time}. We'll send you a reminder the day before. Looking forward to helping you! 🔧",
                action='confirm_appointment'
            ),
            QuickReply(
                id="appointment_reschedule",
                text="📅 Need to reschedule",
                category=ReplyCategory.APPOINTMENT,
                triggers=['reschedule', 'change time', 'different day', 'move appointment', 'can\'t make it'],
                response_template="No problem at all! When would work better for you? I have these times available: {available_times}",
                action='start_reschedule_flow'
            ),
            QuickReply(
                id="appointment_cancel",
                text="❌ Cancel appointment",
                category=ReplyCategory.APPOINTMENT,
                triggers=['cancel', 'nevermind', 'don\'t need'],
                response_template="I understand. Your appointment has been cancelled. If you need anything in the future, just text me! 👍",
                action='cancel_appointment'
            ),
            QuickReply(
                id="appointment_time_check",
                text="🕒 What times are available?",
                category=ReplyCategory.SCHEDULING,
                triggers=['available', 'when', 'times', 'schedule', 'open slots'],
                response_template="I have these times available this week:\n{available_slots}\n\nWhich works best for you?",
                action='show_available_times'
            )
        ]
        
        # Quote-related replies
        quote_replies = [
            QuickReply(
                id="quote_request",
                text="💰 Get a quote",
                category=ReplyCategory.QUOTE,
                triggers=['how much', 'price', 'cost', 'quote', 'estimate', 'rate'],
                response_template="I'd be happy to provide a quote! To give you an accurate estimate, can you tell me:\n• What type of work you need\n• Location/room\n• Any photos if helpful",
                action='start_quote_flow'
            ),
            QuickReply(
                id="quote_accept",
                text="✅ Accept quote",
                category=ReplyCategory.QUOTE,
                triggers=['accept', 'sounds good', 'let\'s do it', 'book it', 'go ahead'],
                response_template="Excellent! I'll get this scheduled for you right away. When would you prefer: {available_times}?",
                action='accept_quote_and_schedule'
            ),
            QuickReply(
                id="quote_negotiate",
                text="💬 Discuss pricing",
                category=ReplyCategory.QUOTE,
                triggers=['too much', 'expensive', 'negotiate', 'lower price', 'discount'],
                response_template="I understand budget is important. Let me see what options we have. Can you share what range you were thinking?",
                action='start_price_discussion'
            )
        ]
        
        # Emergency replies
        emergency_replies = [
            QuickReply(
                id="emergency_immediate",
                text="🚨 Emergency service",
                category=ReplyCategory.EMERGENCY,
                triggers=['emergency', 'urgent', 'asap', 'broken', 'leak', 'no power'],
                response_template="I understand this is urgent! Our emergency technician will call you within 15 minutes. In the meantime, {safety_tip}",
                action='dispatch_emergency_tech',
                confidence_boost=2.0
            ),
            QuickReply(
                id="emergency_safety",
                text="⚠️ Safety first",
                category=ReplyCategory.EMERGENCY,
                triggers=['dangerous', 'unsafe', 'gas smell', 'electrical issue'],
                response_template="Safety first! Please {safety_instruction}. Our emergency team is dispatching now and will call you in 10 minutes.",
                action='provide_safety_guidance',
                confidence_boost=2.0
            )
        ]
        
        # Information replies
        info_replies = [
            QuickReply(
                id="business_hours",
                text="🕒 Business hours",
                category=ReplyCategory.INFORMATION,
                triggers=['hours', 'open', 'when', 'available'],
                response_template="We're open Monday-Friday 8am-6pm, Saturday 9am-4pm. For emergencies, we're available 24/7! 🔧",
                action='show_business_hours'
            ),
            QuickReply(
                id="services_offered",
                text="🔧 Our services",
                category=ReplyCategory.INFORMATION,
                triggers=['services', 'what do you do', 'help with'],
                response_template="We handle all kinds of home repairs:\n• Plumbing • Electrical • HVAC\n• General handyman work\n• Emergency repairs\n\nWhat can we help you with?",
                action='show_services'
            ),
            QuickReply(
                id="location_info",
                text="📍 Service area",
                category=ReplyCategory.INFORMATION,
                triggers=['location', 'where', 'service area', 'travel'],
                response_template="We service the greater {service_area} area. Travel time is usually included in our service calls. What's your zip code?",
                action='check_service_area'
            )
        ]
        
        # Confirmation replies
        confirmation_replies = [
            QuickReply(
                id="positive_confirmation",
                text="👍 Yes, that works",
                category=ReplyCategory.CONFIRMATION,
                triggers=['yes', 'sure', 'ok', 'sounds good', 'perfect'],
                response_template="Awesome! {confirmation_details} I'll send you a confirmation text shortly. 📱",
                action='process_confirmation'
            ),
            QuickReply(
                id="negative_response",
                text="👎 No, let's try again",
                category=ReplyCategory.CONFIRMATION,
                triggers=['no', 'not quite', 'different', 'actually'],
                response_template="No worries! Let's find something that works better. What would you prefer?",
                action='restart_process'
            )
        ]
        
        # Greeting replies
        greeting_replies = [
            QuickReply(
                id="friendly_greeting",
                text="👋 Hi there!",
                category=ReplyCategory.GREETING,
                triggers=['hello', 'hi', 'hey', 'good morning', 'good afternoon'],
                response_template="Hi! I'm Karen, your friendly AI assistant for 757 Handy. How can I help you today? 😊",
                action='start_conversation'
            ),
            QuickReply(
                id="returning_customer",
                text="🔄 Welcome back!",
                category=ReplyCategory.GREETING,
                triggers=['back', 'again', 'me again'],
                response_template="Welcome back! Great to hear from you again. What can I help you with this time?",
                action='greet_returning_customer'
            )
        ]
        
        # Closing replies
        closing_replies = [
            QuickReply(
                id="thank_you_close",
                text="🙏 Thanks!",
                category=ReplyCategory.CLOSING,
                triggers=['thanks', 'thank you', 'appreciate'],
                response_template="You're very welcome! We're always here if you need anything else. Have a great day! ☀️",
                action='close_conversation'
            ),
            QuickReply(
                id="satisfaction_check",
                text="😊 How did we do?",
                category=ReplyCategory.CLOSING,
                triggers=['done', 'finished', 'complete'],
                response_template="Glad we could help! How was your experience? Your feedback helps us improve. ⭐",
                action='request_feedback'
            )
        ]
        
        # Combine all replies
        all_replies = (appointment_replies + quote_replies + emergency_replies + 
                      info_replies + confirmation_replies + greeting_replies + closing_replies)
        
        # Convert to dictionary
        for reply in all_replies:
            replies[reply.id] = reply
            
        return replies
    
    def detect_quick_reply(self, message: str, conversation_context: Dict[str, Any] = None) -> Optional[Dict]:
        """
        Detect if message matches a quick reply trigger with contextual awareness
        """
        message_lower = message.lower().strip()
        context = conversation_context or {}
        
        candidates = []
        
        # Check each quick reply for matches
        for reply_id, reply in self.quick_replies.items():
            confidence = self._calculate_confidence(message_lower, reply, context)
            if confidence > 0:
                candidates.append({
                    'reply': reply,
                    'confidence': confidence,
                    'matched_triggers': self._get_matched_triggers(message_lower, reply.triggers)
                })
        
        # Sort by confidence and return best match if above threshold
        candidates.sort(key=lambda x: x['confidence'], reverse=True)
        
        if candidates and candidates[0]['confidence'] > 0.6:
            best_match = candidates[0]
            return {
                'type': best_match['reply'].id,
                'category': best_match['reply'].category.value,
                'response_template': best_match['reply'].response_template,
                'action': best_match['reply'].action,
                'confidence': best_match['confidence'],
                'matched_triggers': best_match['matched_triggers']
            }
        
        return None
    
    def _calculate_confidence(self, message: str, reply: QuickReply, context: Dict) -> float:
        """Calculate confidence score for a quick reply match"""
        base_confidence = 0.0
        
        # Check for trigger words
        matched_triggers = self._get_matched_triggers(message, reply.triggers)
        if not matched_triggers:
            return 0.0
        
        # Base confidence from trigger matching
        trigger_strength = len(matched_triggers) / len(reply.triggers)
        base_confidence = min(trigger_strength * 0.8, 0.8)
        
        # Context-based adjustments
        context_boost = self._get_context_boost(reply, context)
        
        # Apply reply-specific confidence boost
        total_confidence = (base_confidence + context_boost) * reply.confidence_boost
        
        return min(total_confidence, 1.0)
    
    def _get_matched_triggers(self, message: str, triggers: List[str]) -> List[str]:
        """Get list of triggers that match the message"""
        matched = []
        for trigger in triggers:
            if trigger.lower() in message:
                matched.append(trigger)
        return matched
    
    def _get_context_boost(self, reply: QuickReply, context: Dict) -> float:
        """Calculate context-based confidence boost"""
        boost = 0.0
        
        # Conversation state matching
        conv_state = context.get('state', '').lower()
        if reply.category == ReplyCategory.APPOINTMENT and 'schedul' in conv_state:
            boost += 0.2
        elif reply.category == ReplyCategory.QUOTE and 'gather' in conv_state:
            boost += 0.2
        elif reply.category == ReplyCategory.CONFIRMATION and 'confirm' in conv_state:
            boost += 0.3
        
        # Urgency matching
        urgency = context.get('urgency', '').lower()
        if reply.category == ReplyCategory.EMERGENCY and urgency == 'high':
            boost += 0.4
        
        # Recent message type
        recent_messages = context.get('recent_messages', [])
        if recent_messages:
            last_msg_type = recent_messages[-1].get('type', '')
            if reply.category.value in last_msg_type:
                boost += 0.15
        
        # Time-based adjustments
        time_since_last = context.get('time_since_last_activity', '')
        if 'just now' in time_since_last or 'ago' in time_since_last:
            boost += 0.1
        
        return boost
    
    def get_contextual_quick_replies(self, conversation_state: str, recent_messages: List[Dict] = None) -> List[Dict]:
        """
        Get relevant quick reply options based on conversation context
        Returns 3-4 most relevant quick reply buttons
        """
        state_lower = conversation_state.lower()
        recent_messages = recent_messages or []
        
        relevant_replies = []
        
        # State-based suggestions
        if 'schedul' in state_lower or 'appointment' in state_lower:
            relevant_replies.extend([
                self._format_quick_reply_option('appointment_confirm'),
                self._format_quick_reply_option('appointment_reschedule'),
                self._format_quick_reply_option('appointment_time_check')
            ])
        
        elif 'gather' in state_lower or 'quote' in state_lower:
            relevant_replies.extend([
                self._format_quick_reply_option('quote_request'),
                self._format_quick_reply_option('services_offered'),
                self._format_quick_reply_option('business_hours')
            ])
        
        elif 'confirm' in state_lower:
            relevant_replies.extend([
                self._format_quick_reply_option('positive_confirmation'),
                self._format_quick_reply_option('negative_response'),
                self._format_quick_reply_option('appointment_reschedule')
            ])
        
        elif 'initial' in state_lower:
            relevant_replies.extend([
                self._format_quick_reply_option('appointment_time_check'),
                self._format_quick_reply_option('quote_request'),
                self._format_quick_reply_option('services_offered')
            ])
        
        else:
            # Default suggestions
            relevant_replies.extend([
                self._format_quick_reply_option('appointment_time_check'),
                self._format_quick_reply_option('quote_request'),
                self._format_quick_reply_option('business_hours'),
                self._format_quick_reply_option('emergency_immediate')
            ])
        
        # Always include emergency option if not already present
        emergency_present = any('emergency' in reply['action'] for reply in relevant_replies)
        if not emergency_present:
            relevant_replies.append(self._format_quick_reply_option('emergency_immediate'))
        
        # Limit to 4 options and ensure variety
        unique_replies = self._deduplicate_replies(relevant_replies)
        return unique_replies[:4]
    
    def _format_quick_reply_option(self, reply_id: str) -> Dict:
        """Format a quick reply for display"""
        reply = self.quick_replies.get(reply_id)
        if not reply:
            return {}
        
        return {
            'id': reply.id,
            'text': reply.text,
            'category': reply.category.value,
            'action': reply.action
        }
    
    def _deduplicate_replies(self, replies: List[Dict]) -> List[Dict]:
        """Remove duplicate replies and ensure category variety"""
        seen_actions = set()
        seen_categories = set()
        unique_replies = []
        
        for reply in replies:
            action = reply.get('action', '')
            category = reply.get('category', '')
            
            # Prefer variety in categories
            if action not in seen_actions and len(seen_categories) < 4:
                unique_replies.append(reply)
                seen_actions.add(action)
                seen_categories.add(category)
            elif action not in seen_actions and category not in seen_categories:
                unique_replies.append(reply)
                seen_actions.add(action)
                seen_categories.add(category)
        
        return unique_replies
    
    def generate_smart_response(self, matched_reply: Dict, context: Dict[str, Any]) -> str:
        """
        Generate a smart, contextual response using the matched quick reply
        """
        template = matched_reply['response_template']
        
        # Context variables for template substitution
        template_vars = {
            'appointment_time': context.get('appointment_time', 'your selected time'),
            'available_times': self._format_available_times(context.get('available_slots', [])),
            'available_slots': self._format_available_slots(context.get('available_slots', [])),
            'service_area': context.get('service_area', 'Hampton Roads'),
            'safety_tip': self._get_safety_tip(context.get('emergency_type', '')),
            'safety_instruction': self._get_safety_instruction(context.get('emergency_type', '')),
            'confirmation_details': context.get('confirmation_details', 'Everything is set!'),
            'customer_name': context.get('customer_info', {}).get('name', ''),
            'service_type': context.get('service_type', 'service'),
            'eta': context.get('eta', '30 minutes'),
            'tech_name': context.get('tech_name', 'our technician')
        }
        
        # Safe template substitution
        try:
            response = template.format(**template_vars)
        except KeyError as e:
            logger.warning(f"Template variable missing: {e}")
            # Fallback to template without substitution
            response = re.sub(r'\{[^}]+\}', '[details]', template)
        
        # Add personality touches based on context
        response = self._add_personality_touches(response, context)
        
        return response
    
    def _format_available_times(self, slots: List[Dict]) -> str:
        """Format available time slots for display"""
        if not slots:
            return "this week - I'll check what's available!"
        
        formatted = []
        for i, slot in enumerate(slots[:3], 1):
            time_str = slot.get('display_time', slot.get('time', 'TBD'))
            formatted.append(f"{i}. {time_str}")
        
        return "\n".join(formatted)
    
    def _format_available_slots(self, slots: List[Dict]) -> str:
        """Format available slots in a more detailed format"""
        if not slots:
            return "Let me check our schedule and get back to you with options!"
        
        formatted = []
        for slot in slots[:4]:
            day = slot.get('day', 'TBD')
            time = slot.get('time', 'TBD')
            formatted.append(f"• {day} at {time}")
        
        return "\n".join(formatted)
    
    def _get_safety_tip(self, emergency_type: str) -> str:
        """Get safety tip based on emergency type"""
        tips = {
            'electrical': 'avoid touching any electrical components',
            'plumbing': 'turn off the main water valve if possible',
            'gas': 'evacuate immediately and call 911',
            'heating': 'turn off your heating system',
            'default': 'stay safe and avoid the affected area'
        }
        return tips.get(emergency_type.lower(), tips['default'])
    
    def _get_safety_instruction(self, emergency_type: str) -> str:
        """Get safety instruction based on emergency type"""
        instructions = {
            'electrical': 'turn off power at the breaker and avoid the area',
            'gas': 'evacuate immediately, don\'t use lights or phones, and call 911',
            'plumbing': 'turn off the main water valve if you can access it safely',
            'heating': 'turn off your heating system and open windows for ventilation',
            'default': 'stay clear of the problem area for your safety'
        }
        return instructions.get(emergency_type.lower(), instructions['default'])
    
    def _add_personality_touches(self, response: str, context: Dict) -> str:
        """Add personality touches to make response more conversational"""
        customer_name = context.get('customer_info', {}).get('name', '')
        
        # Add name if available
        if customer_name and not customer_name.lower() in response.lower():
            # Add name naturally to greeting
            if response.startswith('Hi!'):
                response = response.replace('Hi!', f'Hi {customer_name}!')
            elif 'welcome back' in response.lower():
                response = response.replace('Welcome back!', f'Welcome back, {customer_name}!')
        
        # Time-based adjustments
        current_hour = datetime.now().hour
        if 'good morning' not in response.lower() and 'good afternoon' not in response.lower():
            if 5 <= current_hour < 12:
                response = response.replace('Hi!', 'Good morning!')
            elif 12 <= current_hour < 17:
                response = response.replace('Hi!', 'Good afternoon!')
            elif 17 <= current_hour < 21:
                response = response.replace('Hi!', 'Good evening!')
        
        return response
    
    def get_smart_suggestions(self, message: str, context: Dict) -> List[str]:
        """Get smart follow-up suggestions based on message and context"""
        suggestions = []
        message_lower = message.lower()
        
        # Emergency suggestions
        if any(word in message_lower for word in ['broken', 'leak', 'emergency', 'urgent']):
            suggestions.extend([
                "📞 Get emergency help now",
                "📋 Schedule regular service",
                "💡 Get safety tips"
            ])
        
        # Appointment-related suggestions
        elif any(word in message_lower for word in ['schedule', 'appointment', 'book']):
            suggestions.extend([
                "📅 See available times",
                "💰 Get a quote first",
                "📞 Speak with someone"
            ])
        
        # Quote-related suggestions
        elif any(word in message_lower for word in ['price', 'cost', 'quote']):
            suggestions.extend([
                "📷 Send photos for accurate quote",
                "📅 Schedule appointment",
                "📋 Learn about our services"
            ])
        
        # Default suggestions
        else:
            suggestions.extend([
                "📅 Schedule service",
                "💰 Get a quote",
                "📞 Emergency help"
            ])
        
        return suggestions[:3]

# Global instance
_quick_reply_system = None

def get_quick_reply_system() -> QuickReplySystem:
    """Get singleton quick reply system instance"""
    global _quick_reply_system
    if _quick_reply_system is None:
        _quick_reply_system = QuickReplySystem()
    return _quick_reply_system
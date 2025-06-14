"""
Handyman SMS Response Engine - Extends HandymanResponseEngine for SMS-specific features
"""
import logging
import re
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import asyncio

# Import and extend the existing HandymanResponseEngine
from .handyman_response_engine import HandymanResponseEngine
# Import SMS configuration system
from .sms_config import SMSConfig, ServiceType, MessagePriority, ResponseTimeType

logger = logging.getLogger(__name__)

class HandymanSMSEngine(HandymanResponseEngine):
    """
    Extended response engine specifically for SMS communications.
    Inherits all functionality from HandymanResponseEngine and adds SMS-specific features.
    """
    
    def __init__(self, business_name: str = "Beach Handyman",
                 service_area: str = "Virginia Beach area", 
                 phone: str = "757-354-4577",
                 llm_client: Optional[Any] = None):
        # Initialize parent class
        super().__init__(business_name, service_area, phone, llm_client)
        
        # Initialize SMS configuration system
        self.sms_config = SMSConfig()
        
        # SMS-specific configuration
        self.sms_char_limit = 160  # Standard SMS character limit
        self.sms_multipart_limit = 1600  # Extended SMS limit
        
        # SMS-specific keywords for quick responses
        self.sms_quick_responses = {
            'yes': 'appointment confirmed',
            'no': 'appointment cancelled',
            'help': 'service information',
            'stop': 'unsubscribe',
            'info': 'business information'
        }
        
        # Common SMS abbreviations to expand
        self.sms_abbreviations = {
            'asap': 'as soon as possible',
            'appt': 'appointment',
            'avail': 'available',
            'thx': 'thanks',
            'pls': 'please',
            'tmrw': 'tomorrow',
            'wknd': 'weekend'
        }
        
        logger.info(f"HandymanSMSEngine initialized with SMS configuration system")

    def classify_sms_type(self, phone_from: str, sms_body: str) -> Dict[str, Any]:
        """
        Enhanced SMS classification using the new SMS configuration system.
        """
        # Use SMS config for service type classification
        service_type = self.sms_config.classify_service_type(sms_body)
        priority = self.sms_config.get_priority_for_service(service_type, sms_body)
        response_time_config = self.sms_config.get_response_time_config(service_type)
        
        # Legacy classification for compatibility
        legacy_classification = self._legacy_classify_sms_type(phone_from, sms_body)
        
        # Enhanced classification with SMS config
        enhanced_classification = {
            'service_type': service_type,
            'priority': priority,
            'response_time_config': response_time_config,
            'requires_immediate_response': service_type in [ServiceType.EMERGENCY] or priority == MessagePriority.EMERGENCY,
            'should_auto_respond': self.sms_config.should_auto_respond(service_type, priority),
            'business_hours_only': self.sms_config.service_configs.get(service_type, {}).business_hours_only if hasattr(self.sms_config.service_configs.get(service_type, {}), 'business_hours_only') else False,
            
            # Legacy fields for backward compatibility
            'is_emergency': legacy_classification.get('is_emergency', False),
            'is_appointment': legacy_classification.get('is_appointment', False),
            'is_quote_request': legacy_classification.get('is_quote_request', False),
            'is_quick_response': legacy_classification.get('is_quick_response', False),
            'quick_response_type': legacy_classification.get('quick_response_type'),
            'customer_sentiment': legacy_classification.get('customer_sentiment', 'neutral'),
            'estimated_urgency': self._map_priority_to_urgency(priority),
            'suggested_response_time': response_time_config['target_minutes']
        }
        
        # Update emergency status based on new classification
        if service_type == ServiceType.EMERGENCY or priority == MessagePriority.EMERGENCY:
            enhanced_classification['is_emergency'] = True
        
        logger.debug(f"Enhanced SMS classification: service={service_type.value}, priority={priority.value}")
        
        return enhanced_classification

    def _legacy_classify_sms_type(self, phone_from: str, sms_body: str) -> Dict[str, Any]:
        """
        Legacy classification method for backward compatibility.
        """
        # ... existing code ...
        # Emergency detection
        emergency_keywords = ['emergency', 'urgent', 'asap', 'help', 'leak', 'flood', 'fire', 'gas', 'electrical']
        is_emergency = any(keyword in sms_body.lower() for keyword in emergency_keywords)
        
        # Appointment detection
        appointment_keywords = ['appointment', 'schedule', 'book', 'visit', 'come', 'available', 'time']
        is_appointment = any(keyword in sms_body.lower() for keyword in appointment_keywords)
        
        # Quote request detection
        quote_keywords = ['quote', 'estimate', 'cost', 'price', 'how much', 'charge']
        is_quote_request = any(keyword in sms_body.lower() for keyword in quote_keywords)
        
        # Quick response detection (yes/no/stop/help) - more flexible
        quick_responses_mapping = {
            'yes': ['yes', 'y', 'confirm', 'ok', 'okay', 'sure', 'confirmed'],
            'no': ['no', 'n', 'cancel', 'nope', 'nah'],
            'stop': ['stop', 'unsubscribe', 'opt out', 'remove'],
            'help': ['help', 'info', 'information', '?'],
        }
        
        sms_words = sms_body.lower().strip().split()
        is_quick_response = False
        quick_response_type = None
        
        # Check for quick response patterns
        for response_type, patterns in quick_responses_mapping.items():
            for pattern in patterns:
                if pattern in sms_body.lower().strip() or (len(sms_words) == 1 and sms_words[0] == pattern):
                    is_quick_response = True
                    quick_response_type = self.sms_quick_responses.get(response_type, response_type)
                    break
            if is_quick_response:
                break
        
        # Sentiment analysis (basic)
        positive_words = ['thanks', 'thank you', 'great', 'excellent', 'good', 'perfect']
        negative_words = ['terrible', 'awful', 'bad', 'worst', 'horrible', 'disappointed']
        
        if any(word in sms_body.lower() for word in positive_words):
            sentiment = 'positive'
        elif any(word in sms_body.lower() for word in negative_words):
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'is_emergency': is_emergency,
            'is_appointment': is_appointment,
            'is_quote_request': is_quote_request,
            'is_quick_response': is_quick_response,
            'quick_response_type': quick_response_type,
            'customer_sentiment': sentiment
        }

    def _map_priority_to_urgency(self, priority: MessagePriority) -> str:
        """Map SMS config priority to legacy urgency scale."""
        mapping = {
            MessagePriority.EMERGENCY: 'critical',
            MessagePriority.HIGH: 'high',
            MessagePriority.NORMAL: 'medium',
            MessagePriority.LOW: 'low'
        }
        return mapping.get(priority, 'medium')

    def get_template_recommendation(self, service_type: ServiceType, intent: str = "general") -> Dict[str, Any]:
        """Get template recommendation based on service type and intent."""
        return self.sms_config.get_template_for_service(service_type, intent)

    def expand_sms_abbreviations(self, text: str) -> str:
        """Expand common SMS abbreviations to full words."""
        expanded = text
        for abbr, full in self.sms_abbreviations.items():
            # Use word boundaries to avoid partial replacements
            pattern = r'\b' + re.escape(abbr) + r'\b'
            expanded = re.sub(pattern, full, expanded, flags=re.IGNORECASE)
        return expanded

    def generate_sms_prompt(self, phone_from: str, sms_body: str, 
                           classification: Dict[str, Any]) -> str:
        """
        Enhanced SMS-specific prompt generation using configuration system.
        SMS responses need to be concise due to character limits.
        """
        # Expand abbreviations in the body
        expanded_body = self.expand_sms_abbreviations(sms_body)
        
        current_time = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
        
        # Get service type and configuration
        service_type = classification.get('service_type', ServiceType.GENERAL_HANDYMAN)
        priority = classification.get('priority', MessagePriority.NORMAL)
        response_time_config = classification.get('response_time_config', {})
        
        # Get template recommendation
        template_config = self.get_template_recommendation(service_type, "general")
        
        base_prompt = f"""You are Karen, the AI assistant for {self.business_name}, responding to an SMS message.

BUSINESS INFORMATION:
- Business: {self.business_name}
- Service Area: {self.service_area}
- Phone: {self.phone}
- Hours: {self.business_hours}
- Current Time: {current_time}

SERVICE CLASSIFICATION:
- Service Type: {service_type.value}
- Priority: {priority.value}
- Target Response Time: {response_time_config.get('target_minutes', 'N/A')} minutes
- Auto-respond Eligible: {classification.get('should_auto_respond', False)}
- Business Hours Only: {classification.get('business_hours_only', False)}

SMS RESPONSE GUIDELINES:
1. Keep responses VERY concise (under 160 characters if possible)
2. Use clear, simple language appropriate for {service_type.value} services
3. Match the urgency level: {priority.value}
4. Include essential information only
5. For appointments/quotes, suggest calling for details
6. Always include callback number for complex requests

TEMPLATE GUIDANCE:
- Primary Template: {template_config.get('primary_template', 'N/A')}
- Fallback Template: {template_config.get('fallback_template', 'N/A')}
- Required Variables: {', '.join(template_config.get('required_variables', []))}

"""

        # Add priority-specific handling
        if priority == MessagePriority.EMERGENCY:
            base_prompt += """
🚨 EMERGENCY RESPONSE PROTOCOL:
- IMMEDIATE response required (< 1 minute)
- Provide emergency phone number prominently  
- Suggest calling instead of texting
- Keep message under 160 characters
- Example: "EMERGENCY? Call us NOW: 757-354-4577. We're here to help!"
"""
        elif priority == MessagePriority.HIGH:
            base_prompt += """
HIGH PRIORITY RESPONSE:
- Respond within 15 minutes
- Show urgency in tone
- Prioritize scheduling/immediate help
"""

        # Add service-specific guidance
        if service_type == ServiceType.EMERGENCY:
            base_prompt += """
EMERGENCY SERVICE GUIDANCE:
- Emphasize immediate availability
- Provide clear next steps
- Use urgent but reassuring tone
"""
        elif service_type == ServiceType.QUOTE_REQUEST:
            base_prompt += """
QUOTE REQUEST GUIDANCE:
- Acknowledge request promptly
- Ask for basic details (address, service needed)
- Offer to call or schedule estimate
"""
        elif service_type == ServiceType.SCHEDULING:
            base_prompt += """
SCHEDULING GUIDANCE:
- Offer specific available times
- Confirm service type and location
- Keep booking process simple
"""

        # Add quick response handling
        if classification.get('is_quick_response'):
            response_type = classification.get('quick_response_type')
            base_prompt += f"""
QUICK RESPONSE DETECTED: {response_type}
- Provide immediate, appropriate response
- Keep under 160 characters
- Include relevant follow-up action
"""

        # Handle business hours consideration
        if classification.get('business_hours_only'):
            base_prompt += """
BUSINESS HOURS CONSIDERATION:
- Check if current time is within business hours
- If after hours, acknowledge and promise next-day response
- For urgent matters, provide emergency contact option
"""

        base_prompt += f"""
SMS MESSAGE TO RESPOND TO:
From: {phone_from}
Original Message: {sms_body}
Expanded Message: {expanded_body}
Detected Service: {service_type.value}
Priority Level: {priority.value}

IMPORTANT: Generate a concise SMS response following the guidelines above.
Focus on {service_type.value} services with {priority.value} priority level."""

        return base_prompt

    async def generate_sms_response_async(self, phone_from: str, sms_body: str) -> Tuple[str, Dict[str, Any]]:
        """
        Generate an SMS-optimized response using the extended engine.
        Returns both the response and classification.
        """
        if not self.llm_client:
            logger.error("LLMClient not initialized in HandymanSMSEngine.")
            classification = self.classify_sms_type(phone_from, sms_body)
            return self._generate_sms_fallback_response(phone_from, sms_body, classification), classification

        classification = self.classify_sms_type(phone_from, sms_body)
        
        # For quick responses, we might skip LLM entirely
        if classification.get('is_quick_response'):
            quick_type = classification.get('quick_response_type')
            if quick_type == 'appointment confirmed':
                return "Appointment confirmed! We'll see you then. Questions? Call 757-354-4577", classification
            elif quick_type == 'appointment cancelled':
                return "Appointment cancelled. To reschedule, call 757-354-4577. Thank you!", classification
            elif quick_type == 'unsubscribe':
                return "You've been unsubscribed from SMS. Email/call for service: 757-354-4577", classification

        # Generate prompt and get LLM response
        sms_prompt = self.generate_sms_prompt(phone_from, sms_body, classification)
        
        try:
            # Use parent's LLM client through asyncio
            response_text = await asyncio.to_thread(
                self.llm_client.generate_text,
                sms_prompt
            )
            
            # Ensure response fits SMS limits
            response_text = self._truncate_sms_response(response_text)
            
            logger.info(f"SMS response generated. Length: {len(response_text)} chars")
            return response_text, classification
            
        except Exception as e:
            logger.error(f"Error generating SMS response with LLM: {e}", exc_info=True)
            fallback = self._generate_sms_fallback_response(phone_from, sms_body, classification)
            return fallback, classification

    def _truncate_sms_response(self, response: str, preserve_phone: bool = True) -> str:
        """
        Truncate response to fit SMS limits while preserving key information.
        """
        # Remove any email-style signatures
        response = re.sub(r'\n\n(Best regards|Sincerely|Thanks),?\n.*', '', response, flags=re.IGNORECASE)
        
        # If response is within single SMS limit, return as-is
        if len(response) <= self.sms_char_limit:
            return response.strip()
        
        # For longer responses, try to fit in multipart limit
        if len(response) <= self.sms_multipart_limit:
            # Add continuation indicator if splitting would occur
            if len(response) > self.sms_char_limit * 2:
                response = response[:self.sms_multipart_limit - 20] + f"... Call {self.phone}"
            return response.strip()
        
        # For very long responses, truncate intelligently
        truncated = response[:self.sms_char_limit - 25]
        
        # Try to end at a sentence
        last_period = truncated.rfind('.')
        last_question = truncated.rfind('?')
        last_exclaim = truncated.rfind('!')
        
        last_sentence = max(last_period, last_question, last_exclaim)
        if last_sentence > 100:  # Ensure we keep reasonable content
            truncated = truncated[:last_sentence + 1]
        
        # Always preserve phone number for follow-up
        if preserve_phone and self.phone not in truncated:
            truncated += f" Call {self.phone}"
        else:
            truncated += "..."
            
        return truncated.strip()

    def _generate_sms_fallback_response(self, phone_from: str, sms_body: str, 
                                       classification: Dict[str, Any]) -> str:
        """Enhanced SMS fallback responses using configuration system."""
        
        service_type = classification.get('service_type', ServiceType.GENERAL_HANDYMAN)
        priority = classification.get('priority', MessagePriority.NORMAL)
        
        # Emergency responses based on priority
        if priority == MessagePriority.EMERGENCY or service_type == ServiceType.EMERGENCY:
            return f"🚨 EMERGENCY? Call NOW: {self.phone}. We're ready to help 24/7!"
        
        # Service-specific fallback responses
        if service_type == ServiceType.QUOTE_REQUEST:
            return f"Thanks for your quote request! Call {self.phone} or reply with your address for details."
        
        elif service_type == ServiceType.SCHEDULING:
            return f"Ready to schedule! Call {self.phone} or reply with preferred date/time. Thanks!"
        
        elif service_type == ServiceType.PLUMBING:
            return f"Plumbing help available! Call {self.phone} for immediate assistance."
        
        elif service_type == ServiceType.ELECTRICAL:
            return f"Electrical service needed? Call {self.phone} for quick help."
        
        elif service_type == ServiceType.HVAC:
            return f"HVAC issues? We can help! Call {self.phone} for service."
        
        # Quick response handling
        elif classification.get('is_quick_response'):
            quick_type = classification.get('quick_response_type')
            if quick_type == 'appointment confirmed':
                return f"✅ Confirmed! We'll see you then. Questions? {self.phone}"
            elif quick_type == 'appointment cancelled':
                return f"Cancelled. To reschedule: {self.phone}. Thank you!"
            elif quick_type == 'unsubscribe':
                return f"Unsubscribed from SMS. Call/email for service: {self.phone}"
        
        # High priority fallback
        elif priority == MessagePriority.HIGH:
            return f"Thanks for contacting {self.business_name}! We'll respond quickly. Call {self.phone} for immediate help."
        
        # Default fallback with service context
        service_display = self.sms_config.service_configs.get(service_type, type('obj', (object,), {'display_name': service_type.value})).display_name
        return f"Thanks for contacting {self.business_name} about {service_display}! Call {self.phone} or we'll respond soon."

    def should_send_multipart_sms(self, response: str) -> bool:
        """Determine if response should be sent as multipart SMS."""
        return len(response) > self.sms_char_limit

    def split_sms_response(self, response: str, max_parts: int = 3) -> list:
        """
        Split long response into multiple SMS parts.
        Each part will be numbered (1/3), (2/3), etc.
        """
        if len(response) <= self.sms_char_limit:
            return [response]
        
        # Calculate effective limit per part (leaving room for numbering)
        part_limit = self.sms_char_limit - 10  # Space for " (1/3)" etc.
        
        parts = []
        remaining = response
        
        while remaining and len(parts) < max_parts:
            if len(remaining) <= part_limit:
                parts.append(remaining)
                break
            
            # Find good break point
            chunk = remaining[:part_limit]
            
            # Try to break at sentence end
            for sep in ['. ', '! ', '? ', ', ', ' ']:
                last_sep = chunk.rfind(sep)
                if last_sep > part_limit * 0.7:  # At least 70% of limit
                    chunk = chunk[:last_sep + (1 if sep == ' ' else 2)]
                    break
            
            parts.append(chunk.strip())
            remaining = remaining[len(chunk):].strip()
        
        # Add part numbers
        total_parts = len(parts)
        if total_parts > 1:
            parts = [f"{part} ({i+1}/{total_parts})" for i, part in enumerate(parts)]
        
        return parts

    def format_appointment_confirmation_sms(self, appointment_details: Dict[str, Any]) -> str:
        """Format appointment details for SMS confirmation."""
        date = appointment_details.get('date', 'TBD')
        time = appointment_details.get('time', 'TBD')
        service = appointment_details.get('service', 'Service')
        
        # Keep it super concise for SMS
        confirmation = f"Appt confirmed: {date} @ {time} for {service}. "
        confirmation += f"Questions? {self.phone}"
        
        return self._truncate_sms_response(confirmation)


# Example usage
if __name__ == '__main__':
    import asyncio
    
    # Example SMS classification and response
    engine = HandymanSMSEngine()
    
    test_messages = [
        ("+17575551234", "yes"),
        ("+17575551234", "Need emergency plumber ASAP! Pipe burst!"),
        ("+17575551234", "How much to fix a leaky faucet?"),
        ("+17575551234", "Can you come tmrw afternoon for electrical work?"),
        ("+17575551234", "STOP"),
    ]
    
    print("SMS Classification Examples:")
    print("-" * 50)
    
    for phone, msg in test_messages:
        classification = engine.classify_sms_type(phone, msg)
        print(f"\nFrom: {phone}")
        print(f"Message: {msg}")
        print(f"Classification: {classification}")
        
        # Generate fallback response (no LLM)
        fallback = engine._generate_sms_fallback_response(phone, msg, classification)
        print(f"Fallback Response: {fallback}")
        print(f"Response Length: {len(fallback)} chars")
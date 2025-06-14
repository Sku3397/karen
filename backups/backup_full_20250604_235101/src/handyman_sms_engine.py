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

    def classify_sms_type(self, phone_number: str, body: str) -> Dict[str, Any]:
        """
        Classify SMS message with SMS-specific considerations.
        Extends the email classification for SMS context.
        """
        # First, use parent classification
        base_classification = self.classify_email_type("SMS Message", body)
        
        # Add SMS-specific classification
        sms_classification = base_classification.copy()
        
        # Check for quick response keywords
        body_lower = body.lower().strip()
        sms_classification['is_quick_response'] = body_lower in self.sms_quick_responses
        sms_classification['quick_response_type'] = self.sms_quick_responses.get(body_lower, None)
        
        # Check message length considerations
        sms_classification['is_short_message'] = len(body) <= 50
        sms_classification['requires_multipart'] = len(body) > self.sms_char_limit
        
        # Phone number analysis (could be extended for area code detection, etc.)
        sms_classification['sender_phone'] = phone_number
        sms_classification['is_local'] = phone_number.startswith('+1757') if phone_number else False
        
        return sms_classification

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
        Generate SMS-specific prompt for the LLM.
        SMS responses need to be concise due to character limits.
        """
        # Expand abbreviations in the body
        expanded_body = self.expand_sms_abbreviations(sms_body)
        
        current_time = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
        
        base_prompt = f"""You are Karen, the AI assistant for {self.business_name}, responding to an SMS message.

BUSINESS INFORMATION:
- Business: {self.business_name}
- Service Area: {self.service_area}
- Phone: {self.phone}
- Hours: {self.business_hours}
- Current Time: {current_time}

SMS RESPONSE GUIDELINES:
1. Keep responses VERY concise (under 160 characters if possible)
2. Use clear, simple language
3. Avoid complex formatting or long sentences
4. Include essential information only
5. For appointments/quotes, suggest calling for details
6. Always include callback number for complex requests

"""

        # Add quick response handling
        if classification.get('is_quick_response'):
            response_type = classification.get('quick_response_type')
            if response_type == 'appointment confirmed':
                base_prompt += """
QUICK RESPONSE: Appointment Confirmation
- Confirm the appointment briefly
- Include date/time if mentioned
- Add "Reply STOP to cancel"
"""
            elif response_type == 'appointment cancelled':
                base_prompt += """
QUICK RESPONSE: Appointment Cancellation
- Acknowledge cancellation
- Offer to reschedule
- Keep it brief and professional
"""
            elif response_type == 'unsubscribe':
                base_prompt += """
QUICK RESPONSE: Unsubscribe Request
- Confirm removal from SMS list
- Provide alternative contact method
- Be polite and brief
"""

        # Add emergency handling for SMS
        if classification.get('is_emergency'):
            base_prompt += """
🚨 SMS EMERGENCY PROTOCOL:
- Immediate response required
- Provide emergency phone number prominently  
- Suggest calling instead of texting
- Keep message under 160 characters
- Example: "EMERGENCY? Call us NOW: 757-354-4577. We're here to help!"
"""

        # Handle short messages
        if classification.get('is_short_message'):
            base_prompt += """
SHORT MESSAGE RESPONSE:
- Match the brevity of their message
- Get straight to the point
- Avoid unnecessary pleasantries
"""

        base_prompt += f"""
SMS MESSAGE TO RESPOND TO:
From: {phone_from}
Original Message: {sms_body}
Expanded Message: {expanded_body}

IMPORTANT: Generate a concise SMS response (preferably under 160 characters).
For the {self.business_name}, focus on the essential information only."""

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
        """Generate SMS-specific fallback responses."""
        
        if classification.get('is_emergency'):
            return f"URGENT? Call NOW: {self.phone}. We're ready to help!"
        
        elif classification.get('is_quote_request'):
            return f"Thanks for your interest! For a free quote, please call {self.phone} or reply with your address."
        
        elif classification.get('is_appointment_request'):
            return f"To schedule, call {self.phone} or reply with preferred date/time. Thank you!"
        
        elif classification.get('services_mentioned'):
            services = classification['services_mentioned'][0]  # First service
            return f"Yes, we handle {services}! Call {self.phone} for immediate assistance."
        
        else:
            return f"{self.business_name}: Thanks for your message! Call {self.phone} or reply with your needs."

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
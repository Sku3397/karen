"""
Complete Phone System Integration for Karen AI Secretary
Communications Agent (COMMS-001)

Handles all phone communications including:
- Making outbound calls
- Receiving incoming calls
- Voice transcription and processing
- Call routing and management
- Integration with Twilio Voice API
- TwiML generation for call handling
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather, Say, Record
from twilio.base.exceptions import TwilioException

from src.llm_client import LLMClient
from src.logging_config import setup_logger

logger = setup_logger(__name__)

class CallStatus(Enum):
    """Call status enumeration"""
    INITIATED = "initiated"
    RINGING = "ringing"
    ANSWERED = "answered"
    COMPLETED = "completed"
    BUSY = "busy"
    FAILED = "failed"
    NO_ANSWER = "no-answer"

@dataclass
class PhoneCall:
    """Data class for phone call structure"""
    sid: str
    from_number: str
    to_number: str
    status: CallStatus
    direction: str  # 'inbound' or 'outbound'
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[int] = None
    recording_url: Optional[str] = None
    transcription: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'sid': self.sid,
            'from_number': self.from_number,
            'to_number': self.to_number,
            'status': self.status.value,
            'direction': self.direction,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'recording_url': self.recording_url,
            'transcription': self.transcription
        }

class PhoneIntegration:
    """Complete phone system integration for Karen AI"""
    
    def __init__(self):
        """Initialize phone integration with Twilio credentials"""
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.phone_number = os.getenv('TWILIO_PHONE_NUMBER')
        self.webhook_url = os.getenv('TWILIO_VOICE_WEBHOOK_URL')
        self.recording_webhook_url = os.getenv('TWILIO_RECORDING_WEBHOOK_URL')
        
        # Validate required credentials
        if not all([self.account_sid, self.auth_token, self.phone_number]):
            raise ValueError("Missing required Twilio credentials for voice. Check environment variables.")
        
        # Initialize Twilio client
        try:
            self.client = Client(self.account_sid, self.auth_token)
            logger.info("Twilio Voice client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Twilio Voice client: {e}")
            raise
        
        # Initialize LLM client for intelligent responses
        self.llm_client = LLMClient()
        
        # Call history and active calls
        self.call_history: Dict[str, PhoneCall] = {}
        self.active_calls: Dict[str, PhoneCall] = {}
        
        # Business hours configuration
        self.business_hours = {
            'start': 8,  # 8 AM
            'end': 18,   # 6 PM
            'timezone': 'America/New_York',
            'weekends': False
        }
        
        # Emergency keywords for prioritization
        self.emergency_keywords = ['emergency', 'urgent', 'leak', 'flood', 'electrical', 'gas', 'fire']
    
    def make_outbound_call(self, to_number: str, message: str = None, callback_url: str = None) -> PhoneCall:
        """
        Make an outbound call
        
        Args:
            to_number: Phone number to call
            message: Optional message to speak
            callback_url: Optional callback URL for call events
            
        Returns:
            PhoneCall object
        """
        try:
            formatted_number = self._format_phone_number(to_number)
            
            # Create TwiML for the call
            twiml_url = self._create_outbound_twiml_url(message)
            
            # Make the call
            call = self.client.calls.create(
                to=formatted_number,
                from_=self.phone_number,
                url=twiml_url,
                status_callback=callback_url,
                record=True
            )
            
            # Create phone call object
            phone_call = PhoneCall(
                sid=call.sid,
                from_number=self.phone_number,
                to_number=formatted_number,
                status=CallStatus.INITIATED,
                direction='outbound',
                start_time=datetime.now(timezone.utc)
            )
            
            # Store in active calls
            self.active_calls[call.sid] = phone_call
            
            logger.info(f"Outbound call initiated to {formatted_number} - SID: {call.sid}")
            return phone_call
            
        except TwilioException as e:
            logger.error(f"Twilio error making call to {to_number}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error making call to {to_number}: {e}")
            raise
    
    def handle_incoming_call(self, call_data: Dict) -> str:
        """
        Handle incoming call webhook
        
        Args:
            call_data: Call data from Twilio webhook
            
        Returns:
            TwiML response string
        """
        try:
            call_sid = call_data.get('CallSid', '')
            from_number = call_data.get('From', '')
            to_number = call_data.get('To', '')
            call_status = call_data.get('CallStatus', '')
            
            # Create phone call object
            phone_call = PhoneCall(
                sid=call_sid,
                from_number=from_number,
                to_number=to_number,
                status=CallStatus(call_status.lower()) if call_status else CallStatus.INITIATED,
                direction='inbound',
                start_time=datetime.now(timezone.utc)
            )
            
            # Store in active calls
            self.active_calls[call_sid] = phone_call
            
            logger.info(f"Incoming call from {from_number} - SID: {call_sid}")
            
            # Generate TwiML response based on business logic
            twiml_response = self._create_incoming_call_twiml(phone_call)
            
            return twiml_response
            
        except Exception as e:
            logger.error(f"Error handling incoming call: {e}")
            return self._create_error_twiml()
    
    def _create_incoming_call_twiml(self, call: PhoneCall) -> str:
        """
        Create TwiML response for incoming calls
        
        Args:
            call: PhoneCall object
            
        Returns:
            TwiML XML string
        """
        response = VoiceResponse()
        
        # Check if during business hours
        if self._is_business_hours():
            # Business hours greeting
            response.say(
                "Hello! You've reached Karen, your AI assistant for handyman services. "
                "Please describe what you need help with after the beep, and I'll assist you.",
                voice='Polly.Joanna'
            )
            
            # Record the caller's message
            response.record(
                action=f"{self.recording_webhook_url}/process_recording",
                max_length=300,  # 5 minutes max
                transcribe=True,
                transcribe_callback=f"{self.recording_webhook_url}/process_transcription",
                play_beep=True
            )
            
            # Fallback if recording fails
            response.say(
                "I didn't receive your message. Please call back or send us a text message. Thank you!",
                voice='Polly.Joanna'
            )
            
        else:
            # After hours message
            response.say(
                "Thank you for calling! Our office hours are 8 AM to 6 PM, Monday through Friday. "
                "If this is an emergency, please stay on the line and I'll connect you. "
                "Otherwise, please call back during business hours or send us a text message. "
                "Press 1 if this is an emergency, or hang up to call back later.",
                voice='Polly.Joanna'
            )
            
            # Gather emergency response
            gather = Gather(
                num_digits=1,
                timeout=10,
                action=f"{self.webhook_url}/emergency_response"
            )
            response.append(gather)
            
            # Default action if no input
            response.say("Thank you for calling. Have a great day!", voice='Polly.Joanna')
        
        return str(response)
    
    def handle_recording_complete(self, recording_data: Dict) -> str:
        """
        Handle completed call recording
        
        Args:
            recording_data: Recording data from Twilio
            
        Returns:
            TwiML response string
        """
        try:
            call_sid = recording_data.get('CallSid', '')
            recording_url = recording_data.get('RecordingUrl', '')
            recording_duration = recording_data.get('RecordingDuration', 0)
            
            # Update call record
            if call_sid in self.active_calls:
                self.active_calls[call_sid].recording_url = recording_url
                self.active_calls[call_sid].duration = int(recording_duration)
            
            logger.info(f"Recording completed for call {call_sid} - Duration: {recording_duration}s")
            
            # Create response
            response = VoiceResponse()
            response.say(
                "Thank you for your message. I've recorded your request and will process it shortly. "
                "You should receive a response within the next few minutes. Have a great day!",
                voice='Polly.Joanna'
            )
            
            return str(response)
            
        except Exception as e:
            logger.error(f"Error handling recording completion: {e}")
            return self._create_error_twiml()
    
    def handle_transcription_complete(self, transcription_data: Dict) -> None:
        """
        Handle completed call transcription
        
        Args:
            transcription_data: Transcription data from Twilio
        """
        try:
            call_sid = transcription_data.get('CallSid', '')
            transcription_text = transcription_data.get('TranscriptionText', '')
            transcription_status = transcription_data.get('TranscriptionStatus', '')
            
            if transcription_status == 'completed' and call_sid in self.active_calls:
                # Update call record with transcription
                self.active_calls[call_sid].transcription = transcription_text
                
                logger.info(f"Transcription completed for call {call_sid}")
                
                # Process the transcription for response
                self._process_call_transcription(call_sid, transcription_text)
            
        except Exception as e:
            logger.error(f"Error handling transcription completion: {e}")
    
    def _process_call_transcription(self, call_sid: str, transcription: str) -> None:
        """
        Process call transcription and generate response
        
        Args:
            call_sid: Call SID
            transcription: Transcribed text
        """
        try:
            call = self.active_calls.get(call_sid)
            if not call:
                return
            
            # Classify the request
            intent = self._classify_call_intent(transcription)
            
            # Check for emergency keywords
            is_emergency = any(keyword in transcription.lower() for keyword in self.emergency_keywords)
            
            # Generate response using LLM
            context = {
                'transcription': transcription,
                'intent': intent,
                'is_emergency': is_emergency,
                'caller_number': call.from_number,
                'call_time': call.start_time.isoformat()
            }
            
            response = self._generate_call_response(context)
            
            # If emergency, make immediate callback
            if is_emergency:
                self._handle_emergency_call(call, transcription)
            else:
                # Send SMS response
                self._send_followup_sms(call.from_number, response)
            
            # Move to call history
            self.call_history[call_sid] = call
            if call_sid in self.active_calls:
                del self.active_calls[call_sid]
            
        except Exception as e:
            logger.error(f"Error processing call transcription: {e}")
    
    def _classify_call_intent(self, transcription: str) -> str:
        """
        Classify the intent of the call transcription
        
        Args:
            transcription: Transcribed text
            
        Returns:
            Intent classification
        """
        text_lower = transcription.lower()
        
        # Emergency
        if any(word in text_lower for word in self.emergency_keywords):
            return 'emergency'
        
        # Appointment scheduling
        if any(word in text_lower for word in ['appointment', 'schedule', 'book', 'available', 'when']):
            return 'appointment'
        
        # Quote request
        if any(word in text_lower for word in ['quote', 'price', 'cost', 'estimate', 'how much']):
            return 'quote'
        
        # Service request
        if any(word in text_lower for word in ['fix', 'repair', 'install', 'maintenance', 'service']):
            return 'service_request'
        
        return 'general_inquiry'
    
    def _generate_call_response(self, context: Dict) -> str:
        """
        Generate response using LLM
        
        Args:
            context: Call context
            
        Returns:
            Generated response
        """
        try:
            prompt = f"""
You are Karen, a professional AI secretary for a handyman service. A customer called and left this message:

"{context['transcription']}"

Intent: {context['intent']}
Emergency: {context['is_emergency']}

Generate a professional SMS response that:
1. Acknowledges their call
2. Addresses their specific need
3. Provides next steps
4. Includes contact information if needed

Keep it concise but helpful (under 160 characters if possible).

Response:"""

            response = self.llm_client.generate_response(prompt)
            return response
            
        except Exception as e:
            logger.error(f"Error generating call response: {e}")
            return self._get_fallback_call_response(context['intent'])
    
    def _get_fallback_call_response(self, intent: str) -> str:
        """Get fallback response for call"""
        responses = {
            'emergency': "We received your urgent call. Our team is being notified immediately. We'll contact you within 15 minutes.",
            'appointment': "Thanks for calling about an appointment. We'll review your request and text you available times shortly.",
            'quote': "We received your quote request. We'll review the details and send you an estimate within 24 hours.",
            'service_request': "Thank you for your service request. We'll review your needs and get back to you soon.",
            'general_inquiry': "Thanks for calling! We received your message and will respond shortly."
        }
        return responses.get(intent, "Thank you for calling. We received your message and will get back to you soon.")
    
    def _handle_emergency_call(self, call: PhoneCall, transcription: str) -> None:
        """
        Handle emergency call with immediate response
        
        Args:
            call: PhoneCall object
            transcription: Call transcription
        """
        try:
            # Log emergency
            logger.warning(f"EMERGENCY CALL from {call.from_number}: {transcription}")
            
            # Immediate callback within 5 minutes
            emergency_message = (
                "This is Karen from the handyman service. We received your emergency call and "
                "are dispatching someone immediately. Please stay safe."
            )
            
            # Schedule immediate callback
            self.make_outbound_call(call.from_number, emergency_message)
            
            # Also send emergency SMS
            emergency_sms = (
                "🚨 EMERGENCY RESPONSE: We received your call and are dispatching help immediately. "
                "We'll call you back within 5 minutes to confirm details."
            )
            self._send_followup_sms(call.from_number, emergency_sms)
            
        except Exception as e:
            logger.error(f"Error handling emergency call: {e}")
    
    def _send_followup_sms(self, phone_number: str, message: str) -> None:
        """
        Send follow-up SMS after call
        
        Args:
            phone_number: Phone number to send to
            message: SMS message content
        """
        try:
            # Import SMS integration to send follow-up
            from src.sms_integration import get_sms_integration
            sms = get_sms_integration()
            sms.send_sms(phone_number, message)
            logger.info(f"Follow-up SMS sent to {phone_number}")
        except Exception as e:
            logger.error(f"Error sending follow-up SMS to {phone_number}: {e}")
    
    def _is_business_hours(self) -> bool:
        """
        Check if current time is within business hours
        
        Returns:
            True if within business hours
        """
        try:
            import pytz
            tz = pytz.timezone(self.business_hours['timezone'])
            now = datetime.now(tz)
            
            # Check weekends
            if not self.business_hours['weekends'] and now.weekday() >= 5:
                return False
            
            # Check hours
            current_hour = now.hour
            return self.business_hours['start'] <= current_hour < self.business_hours['end']
            
        except Exception:
            # Default to business hours if timezone check fails
            return True
    
    def _create_outbound_twiml_url(self, message: str = None) -> str:
        """
        Create TwiML URL for outbound calls
        
        Args:
            message: Optional message to speak
            
        Returns:
            TwiML URL
        """
        # In production, this would be a dynamic URL that generates TwiML
        # For now, return a static webhook URL
        base_url = self.webhook_url or "https://your-domain.com/voice"
        if message:
            import urllib.parse
            encoded_message = urllib.parse.quote(message)
            return f"{base_url}/outbound_twiml?message={encoded_message}"
        return f"{base_url}/outbound_twiml"
    
    def _create_error_twiml(self) -> str:
        """Create error TwiML response"""
        response = VoiceResponse()
        response.say(
            "I'm sorry, we're experiencing technical difficulties. "
            "Please try calling back in a few minutes or send us a text message. Thank you!",
            voice='Polly.Joanna'
        )
        return str(response)
    
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
    
    def get_call_history(self, phone_number: str = None, limit: int = 50) -> List[PhoneCall]:
        """
        Get call history
        
        Args:
            phone_number: Optional filter by phone number
            limit: Maximum number of calls to return
            
        Returns:
            List of PhoneCall objects
        """
        calls = list(self.call_history.values())
        
        if phone_number:
            formatted_number = self._format_phone_number(phone_number)
            calls = [call for call in calls if 
                    call.from_number == formatted_number or call.to_number == formatted_number]
        
        # Sort by start time, newest first
        calls.sort(key=lambda x: x.start_time, reverse=True)
        return calls[:limit]
    
    def get_active_calls(self) -> List[PhoneCall]:
        """Get list of currently active calls"""
        return list(self.active_calls.values())
    
    def end_call(self, call_sid: str) -> bool:
        """
        End an active call
        
        Args:
            call_sid: Call SID to end
            
        Returns:
            True if successful
        """
        try:
            call = self.client.calls(call_sid).update(status='completed')
            
            # Move from active to history
            if call_sid in self.active_calls:
                phone_call = self.active_calls[call_sid]
                phone_call.status = CallStatus.COMPLETED
                phone_call.end_time = datetime.now(timezone.utc)
                self.call_history[call_sid] = phone_call
                del self.active_calls[call_sid]
            
            logger.info(f"Call {call_sid} ended successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error ending call {call_sid}: {e}")
            return False
    
    def health_check(self) -> Dict:
        """
        Perform health check on phone integration
        
        Returns:
            Health status dictionary
        """
        try:
            # Test Twilio connection
            account = self.client.api.account.fetch()
            
            # Check phone number
            phone_number_info = self.client.incoming_phone_numbers.list(
                phone_number=self.phone_number,
                limit=1
            )
            
            return {
                'status': 'healthy',
                'twilio_connected': True,
                'account_sid': account.sid[:8] + '...',
                'phone_number': self.phone_number,
                'phone_number_configured': len(phone_number_info) > 0,
                'webhook_configured': bool(self.webhook_url),
                'active_calls': len(self.active_calls),
                'business_hours': self._is_business_hours(),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Phone health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

# Global phone integration instance
phone_integration = None

def get_phone_integration() -> PhoneIntegration:
    """Get or create phone integration instance"""
    global phone_integration
    if phone_integration is None:
        phone_integration = PhoneIntegration()
    return phone_integration
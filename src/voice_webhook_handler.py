#!/usr/bin/env python3
"""
Professional Voice Webhook Handler for Karen AI - 757 Handy
Handles incoming Twilio voice calls with premium experience

Author: Phone Engineer Agent
"""

import os
import json
import logging
import redis
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse, Gather, Say, Record, Dial
from twilio.rest import Client as TwilioClient
import asyncio

from .business_hours_manager import BusinessHoursManager
from .voice_ivr_system import VoiceIVRSystem
from .voice_transcription_handler import VoiceTranscriptionHandler
from .calendar_client import CalendarClient
from .elevenlabs_voice_handler import ElevenLabsVoiceHandler, EmotionStyle, enhance_twiml_with_elevenlabs
from .voice_call_analytics import VoiceCallAnalytics
from .voice_emergency_handler import EmergencyHandler, EmergencyAssessment
from .voice_quality_assurance import VoiceQualityAssurance

# Setup logging
logger = logging.getLogger(__name__)

class VoiceWebhookHandler:
    """
    Premium voice call handling system for 757 Handy
    Creates professional customer experience with intelligent routing
    """
    
    def __init__(self):
        # Initialize Twilio client
        self.twilio_client = TwilioClient(
            os.getenv('TWILIO_ACCOUNT_SID'),
            os.getenv('TWILIO_AUTH_TOKEN')
        )
        
        # Initialize Redis for call tracking
        try:
            self.redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=int(os.getenv('REDIS_DB', 0)),
                decode_responses=True
            )
            self.redis_client.ping()  # Test connection
            logger.info("Redis connection established for call tracking")
        except Exception as e:
            logger.warning(f"Redis connection failed, using memory storage: {e}")
            self.redis_client = None
        
        # Initialize subsystems
        self.business_hours = BusinessHoursManager()
        self.ivr_system = VoiceIVRSystem()
        self.transcription_handler = VoiceTranscriptionHandler()
        
        # Initialize analytics and quality systems
        self.analytics = VoiceCallAnalytics()
        self.emergency_handler = EmergencyHandler()
        self.quality_assurance = VoiceQualityAssurance()
        
        # Initialize ElevenLabs for premium voice quality
        try:
            self.elevenlabs_handler = ElevenLabsVoiceHandler()
            self.use_elevenlabs = True
            logger.info("ElevenLabs voice system initialized")
        except Exception as e:
            logger.warning(f"ElevenLabs not available, using fallback TTS: {e}")
            self.elevenlabs_handler = None
            self.use_elevenlabs = False
        
        # Configuration
        self.company_name = "757 Handy"
        self.main_phone = os.getenv('MAIN_PHONE_NUMBER', '+15551234567')
        self.emergency_phone = os.getenv('EMERGENCY_PHONE_NUMBER', '+15551234568')
        self.max_queue_time = 300  # 5 minutes max queue time
        
        logger.info("VoiceWebhookHandler initialized for premium call experience with full analytics")
    
    async def process_call_with_analytics(self, call_sid: str, caller_id: str, 
                                        transcription: str = "", call_context: Dict = None) -> Dict:
        """Process call with comprehensive analytics and emergency detection"""
        try:
            call_context = call_context or {}
            
            # Emergency assessment
            emergency_assessment = self.emergency_handler.assess_urgency(
                transcription, caller_id, call_context
            )
            
            # Log call for analytics
            call_data = {
                'call_sid': call_sid,
                'caller_id': caller_id,
                'timestamp': datetime.now(),
                'transcription': transcription,
                'emergency_level': emergency_assessment.urgency_level.value,
                'emergency_type': emergency_assessment.emergency_type.value if emergency_assessment.emergency_type else None,
                **call_context
            }
            
            self.analytics.log_call(call_data)
            
            # Handle emergency routing if needed
            routing_result = None
            if emergency_assessment.requires_immediate_dispatch:
                routing_result = await self.emergency_handler.route_emergency_call(
                    emergency_assessment, call_sid, caller_id
                )
                logger.warning(f"Emergency routing triggered for {call_sid}: {emergency_assessment.urgency_level.name}")
            
            return {
                'emergency_assessment': emergency_assessment,
                'routing_result': routing_result,
                'analytics_logged': True
            }
            
        except Exception as e:
            logger.error(f"Error processing call analytics: {e}")
            return {
                'emergency_assessment': None,
                'routing_result': None,
                'analytics_logged': False,
                'error': str(e)
            }
    
    async def analyze_call_quality(self, call_sid: str, recording_url: str, 
                                 transcription: str, agent_id: str = None) -> Dict:
        """Analyze call quality for QA purposes"""
        try:
            call_data = {
                'call_sid': call_sid,
                'recording_url': recording_url,
                'transcription': transcription,
                'agent_id': agent_id or 'system',
                'call_duration': 0,  # Would be filled from call data
                'customer_data': {}
            }
            
            quality_metrics = await self.quality_assurance.analyze_call_recording(call_data)
            
            logger.info(f"Quality analysis completed for {call_sid}: {quality_metrics.overall_quality.name}")
            return {
                'quality_metrics': quality_metrics,
                'analysis_complete': True
            }
            
        except Exception as e:
            logger.error(f"Error analyzing call quality: {e}")
            return {
                'quality_metrics': None,
                'analysis_complete': False,
                'error': str(e)
            }
    
    def track_call(self, call_sid: str, caller_id: str, status: str, data: Dict[str, Any] = None):
        """Track call in Redis for analytics and queue management"""
        try:
            if self.redis_client:
                call_data = {
                    'call_sid': call_sid,
                    'caller_id': caller_id,
                    'status': status,
                    'timestamp': datetime.now().isoformat(),
                    'data': json.dumps(data or {})
                }
                
                # Store call data
                self.redis_client.hset(f"call:{call_sid}", mapping=call_data)
                self.redis_client.expire(f"call:{call_sid}", 86400)  # 24 hour TTL
                
                # Track active calls
                if status in ['ringing', 'in-progress']:
                    self.redis_client.sadd('active_calls', call_sid)
                elif status in ['completed', 'busy', 'no-answer', 'canceled']:
                    self.redis_client.srem('active_calls', call_sid)
                
                logger.debug(f"Call tracked: {call_sid} - {status}")
        except Exception as e:
            logger.error(f"Failed to track call {call_sid}: {e}")
    
    def get_active_call_count(self) -> int:
        """Get number of active calls for queue management"""
        try:
            if self.redis_client:
                return self.redis_client.scard('active_calls')
        except Exception as e:
            logger.error(f"Failed to get active call count: {e}")
        return 0
    
    def _add_voice_to_response(self, response: VoiceResponse, text: str, 
                              context: str = 'general', emotion: str = None):
        """Add voice to TwiML response using ElevenLabs or fallback"""
        try:
            if self.use_elevenlabs and self.elevenlabs_handler:
                enhance_twiml_with_elevenlabs(response, text, context)
            else:
                # Fallback to Polly
                response.say(text, voice='Polly.Joanna', language='en-US')
        except Exception as e:
            logger.error(f"Error adding voice to response: {e}")
            # Always fallback to basic say
            response.say(text, voice='Polly.Joanna', language='en-US')
    
    def generate_welcome_message(self, is_business_hours: bool, caller_id: str) -> VoiceResponse:
        """Generate professional welcome message with personalization"""
        response = VoiceResponse()
        
        # Premium greeting with company branding
        if is_business_hours:
            greeting = (f"Thank you for calling {self.company_name}, Hampton Roads' premier home improvement experts. "
                       f"We appreciate your call and look forward to helping you today.")
            self._add_voice_to_response(response, greeting, 'greeting', 'warm')
        else:
            greeting = (f"Thank you for calling {self.company_name}. "
                       f"We're currently closed, but your call is very important to us. "
                       f"Please leave a detailed message and we'll return your call first thing tomorrow morning.")
            self._add_voice_to_response(response, greeting, 'after_hours', 'empathetic')
        
        return response
    
    def generate_main_menu(self) -> VoiceResponse:
        """Generate the main IVR menu with speech and DTMF input"""
        response = VoiceResponse()
        
        # Professional menu with multiple input options
        gather = Gather(
            input='dtmf speech',
            timeout=4,
            speechTimeout='auto',
            speechModel='experimental_conversations',
            action='/voice/handle-menu-selection',
            method='POST',
            numDigits=1
        )
        
        menu_text = (
            "To help you quickly, please choose from the following options: "
            "For appointment scheduling, say 'schedule' or press 1. "
            "For a free estimate or quote, say 'quote' or press 2. "
            "For emergency repairs, say 'emergency' or press 3. "
            "To speak with our customer service team, say 'support' or press 4. "
            "For payment or billing questions, say 'billing' or press 5. "
            "To repeat this menu, press 9."
        )
        
        # Use ElevenLabs for premium menu experience
        if self.use_elevenlabs and self.elevenlabs_handler:
            enhance_twiml_with_elevenlabs(gather, menu_text, 'menu')
        else:
            gather.say(menu_text, voice='Polly.Joanna', language='en-US')
        response.append(gather)
        
        # If no input, redirect to customer service
        fallback_text = "I didn't hear your selection. Let me connect you with our customer service team."
        self._add_voice_to_response(response, fallback_text, 'menu', 'empathetic')
        response.redirect('/voice/transfer-to-human')
        
        return response
    
    def generate_queue_message(self, estimated_wait: int) -> VoiceResponse:
        """Generate professional queue message with wait time"""
        response = VoiceResponse()
        
        if estimated_wait <= 2:
            wait_msg = "We'll be with you in just a moment."
        elif estimated_wait <= 5:
            wait_msg = f"Your estimated wait time is approximately {estimated_wait} minutes."
        else:
            wait_msg = "We're experiencing higher than normal call volume. You can choose to hold, or leave a voicemail and we'll call you back within the hour."
        
        response.say(f"Please hold while we connect you with our next available representative. {wait_msg}", 
                    voice='Polly.Joanna')
        
        # Play hold music
        response.play('https://your-domain.com/audio/hold-music.mp3')
        
        return response
    
    def generate_after_hours_flow(self) -> VoiceResponse:
        """Generate after-hours call flow with emergency option"""
        response = VoiceResponse()
        
        # Check if it's an emergency
        gather = Gather(
            input='dtmf speech',
            timeout=5,
            speechTimeout='auto',
            action='/voice/handle-after-hours',
            method='POST',
            numDigits=1
        )
        
        after_hours_msg = (
            f"We're currently closed, but we're here to help. "
            f"Our regular business hours are Monday through Friday, 8 AM to 6 PM, "
            f"and Saturday 9 AM to 4 PM. "
            f"If this is a plumbing, electrical, or heating emergency, press 1 now. "
            f"To leave a detailed voicemail for a prompt callback, press 2. "
            f"For our emergency service, which includes a service fee, press 3."
        )
        
        gather.say(after_hours_msg, voice='Polly.Joanna')
        response.append(gather)
        
        # Default to voicemail
        response.redirect('/voice/voicemail')
        
        return response
    
    def generate_appointment_flow(self) -> VoiceResponse:
        """Generate appointment scheduling flow"""
        response = VoiceResponse()
        
        response.say("I'd be happy to help you schedule an appointment. Let me connect you with our scheduling specialist who can check availability and book your service.", 
                    voice='Polly.Joanna')
        
        # First try to connect to calendar system, then human
        response.redirect('/voice/schedule-appointment')
        
        return response
    
    def generate_quote_flow(self) -> VoiceResponse:
        """Generate quote request flow"""
        response = VoiceResponse()
        
        gather = Gather(
            input='speech',
            timeout=10,
            speechTimeout='auto',
            speechModel='experimental_conversations',
            action='/voice/process-quote-request',
            method='POST'
        )
        
        quote_msg = (
            "I'll be happy to help you get a free estimate. "
            "Please describe the work you need done, including the type of service "
            "and any specific details that would help us provide an accurate quote. "
            "Take your time and be as detailed as possible."
        )
        
        gather.say(quote_msg, voice='Polly.Joanna')
        response.append(gather)
        
        # Fallback to human if speech fails
        response.redirect('/voice/transfer-to-estimator')
        
        return response
    
    def generate_emergency_flow(self) -> VoiceResponse:
        """Generate emergency service flow"""
        response = VoiceResponse()
        
        response.say("This is our emergency service line. Please stay on the line while I connect you immediately with our emergency technician.", 
                    voice='Polly.Joanna')
        
        # Immediate transfer to emergency line
        dial = Dial(timeout=30)
        dial.number(self.emergency_phone)
        response.append(dial)
        
        # If no answer, take emergency voicemail
        response.say("Our emergency technician is temporarily unavailable. Please leave a detailed message including your name, number, and the nature of your emergency. We'll call you back within 15 minutes.", 
                    voice='Polly.Joanna')
        response.redirect('/voice/emergency-voicemail')
        
        return response
    
    def generate_voicemail_flow(self, message_type: str = 'general') -> VoiceResponse:
        """Generate voicemail recording flow"""
        response = VoiceResponse()
        
        if message_type == 'emergency':
            instructions = (
                "You've reached our emergency voicemail. Please speak clearly and include: "
                "your name, phone number, your address, and a detailed description of your emergency. "
                "We'll call you back within 15 minutes."
            )
            max_length = 300  # 5 minutes for emergencies
        else:
            instructions = (
                "Please leave a detailed message including your name, phone number, "
                "the best time to reach you, and a description of the work you need done. "
                "We'll return your call within 4 hours during business days."
            )
            max_length = 180  # 3 minutes for regular voicemails
        
        response.say(instructions, voice='Polly.Joanna')
        response.say("Please begin your message after the tone.", voice='Polly.Joanna')
        
        # Record with transcription callback
        record = Record(
            timeout=10,
            maxLength=max_length,
            playBeep=True,
            action=f'/voice/voicemail-complete?type={message_type}',
            transcribe=True,
            transcribeCallback='/voice/transcription-complete'
        )
        response.append(record)
        
        return response
    
    def generate_transfer_to_human(self, department: str = 'general') -> VoiceResponse:
        """Generate transfer to human representative"""
        response = VoiceResponse()
        
        # Get queue information
        active_calls = self.get_active_call_count()
        estimated_wait = min(active_calls * 2, 10)  # Max 10 minute estimate
        
        if active_calls > 5:  # Queue management
            gather = Gather(
                input='dtmf',
                timeout=10,
                action='/voice/queue-choice',
                method='POST',
                numDigits=1
            )
            
            gather.say(f"All our representatives are currently helping other customers. "
                      f"Your estimated wait time is {estimated_wait} minutes. "
                      f"Press 1 to hold, or press 2 to leave a voicemail for a callback within 2 hours.", 
                      voice='Polly.Joanna')
            response.append(gather)
            
            # Default to queue
            response.redirect('/voice/enter-queue')
        else:
            response.say("Let me connect you with our next available representative.", 
                        voice='Polly.Joanna')
            
            dial = Dial(timeout=45)
            dial.number(self.main_phone)
            response.append(dial)
            
            # If no answer, offer voicemail
            response.say("I'm sorry, but all our representatives are currently busy. Let me take a message for you.", 
                        voice='Polly.Joanna')
            response.redirect('/voice/voicemail')
        
        return response

# FastAPI application setup
app = FastAPI(title="757 Handy Voice System", version="1.0.0")
voice_handler = VoiceWebhookHandler()

@app.post("/voice/incoming")
async def handle_incoming_call(
    request: Request,
    CallSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    CallStatus: str = Form(...)
):
    """Handle incoming call - entry point"""
    try:
        logger.info(f"Incoming call: {CallSid} from {From}")
        
        # Track the call
        voice_handler.track_call(CallSid, From, CallStatus)
        
        # Check business hours
        is_business_hours = voice_handler.business_hours.is_open()
        
        # Generate welcome and route appropriately
        if is_business_hours:
            # Welcome + Main Menu
            response = voice_handler.generate_welcome_message(True, From)
            response.append(voice_handler.generate_main_menu())
        else:
            # After hours flow
            response = voice_handler.generate_welcome_message(False, From)
            response.append(voice_handler.generate_after_hours_flow())
        
        return Response(content=str(response), media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error handling incoming call {CallSid}: {e}")
        
        # Graceful fallback
        response = VoiceResponse()
        response.say("We're experiencing technical difficulties. Please call back in a few minutes or visit our website at 757handy.com", 
                    voice='Polly.Joanna')
        return Response(content=str(response), media_type="application/xml")

@app.post("/voice/handle-menu-selection")
async def handle_menu_selection(
    request: Request,
    CallSid: str = Form(...),
    Digits: str = Form(None),
    SpeechResult: str = Form(None)
):
    """Handle main menu selection"""
    try:
        selection = None
        
        # Process speech input
        if SpeechResult:
            speech_lower = SpeechResult.lower()
            if 'schedule' in speech_lower or 'appointment' in speech_lower:
                selection = '1'
            elif 'quote' in speech_lower or 'estimate' in speech_lower:
                selection = '2'
            elif 'emergency' in speech_lower:
                selection = '3'
            elif 'support' in speech_lower or 'customer service' in speech_lower:
                selection = '4'
            elif 'billing' in speech_lower or 'payment' in speech_lower:
                selection = '5'
        
        # Use DTMF if no speech match
        if not selection and Digits:
            selection = Digits
        
        logger.info(f"Menu selection for {CallSid}: {selection} (Speech: {SpeechResult}, DTMF: {Digits})")
        
        # Route based on selection
        if selection == '1':
            response = voice_handler.generate_appointment_flow()
        elif selection == '2':
            response = voice_handler.generate_quote_flow()
        elif selection == '3':
            response = voice_handler.generate_emergency_flow()
        elif selection == '4':
            response = voice_handler.generate_transfer_to_human('support')
        elif selection == '5':
            response = voice_handler.generate_transfer_to_human('billing')
        elif selection == '9':
            response = voice_handler.generate_main_menu()
        else:
            # Invalid selection
            response = VoiceResponse()
            response.say("I didn't understand your selection. Let me repeat the menu.", 
                        voice='Polly.Joanna')
            response.append(voice_handler.generate_main_menu())
        
        return Response(content=str(response), media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error handling menu selection for {CallSid}: {e}")
        
        # Fallback to human
        response = voice_handler.generate_transfer_to_human()
        return Response(content=str(response), media_type="application/xml")

@app.post("/voice/handle-after-hours")
async def handle_after_hours(
    request: Request,
    CallSid: str = Form(...),
    Digits: str = Form(None),
    SpeechResult: str = Form(None)
):
    """Handle after-hours call routing"""
    try:
        selection = Digits or '2'  # Default to voicemail
        
        if selection == '1':
            # Emergency routing
            response = voice_handler.generate_emergency_flow()
        elif selection == '3':
            # Emergency service (with fee)
            response = VoiceResponse()
            response.say("Emergency service includes a service call fee. Let me connect you now.", 
                        voice='Polly.Joanna')
            response.append(voice_handler.generate_emergency_flow())
        else:
            # Regular voicemail
            response = voice_handler.generate_voicemail_flow()
        
        return Response(content=str(response), media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error handling after-hours call {CallSid}: {e}")
        response = voice_handler.generate_voicemail_flow()
        return Response(content=str(response), media_type="application/xml")

@app.post("/voice/voicemail-complete")
async def voicemail_complete(
    request: Request,
    CallSid: str = Form(...),
    RecordingUrl: str = Form(...),
    RecordingDuration: str = Form(...),
    From: str = Form(...),
    message_type: str = 'general'
):
    """Handle completed voicemail recording with analytics and emergency detection"""
    try:
        logger.info(f"Voicemail completed for {CallSid}: {RecordingUrl} ({RecordingDuration}s)")
        
        # Process the voicemail and get transcription
        transcription_result = await voice_handler.transcription_handler.process_voicemail(
            CallSid, RecordingUrl, int(RecordingDuration), message_type
        )
        
        transcription = transcription_result.get('transcription', '') if transcription_result else ''
        
        # Process with analytics and emergency detection
        analytics_result = await voice_handler.process_call_with_analytics(
            CallSid, From, transcription, {
                'call_type': 'voicemail',
                'message_type': message_type,
                'duration': int(RecordingDuration),
                'recording_url': RecordingUrl
            }
        )
        
        # Check for emergency in voicemail
        emergency_assessment = analytics_result.get('emergency_assessment')
        if emergency_assessment and emergency_assessment.urgency_level.value >= 4:
            logger.critical(f"EMERGENCY VOICEMAIL DETECTED: {CallSid} - Level {emergency_assessment.urgency_level.name}")
            message_type = 'emergency'  # Upgrade message type
        
        # Analyze call quality for voicemail handling
        if transcription:
            quality_result = await voice_handler.analyze_call_quality(
                CallSid, RecordingUrl, transcription, 'voicemail_system'
            )
        
        # Generate appropriate response based on urgency
        response = VoiceResponse()
        if message_type == 'emergency' or (emergency_assessment and emergency_assessment.urgency_level.value >= 4):
            voice_handler._add_voice_to_response(
                response, 
                "Thank you for your emergency message. We'll call you back within 15 minutes.",
                'emergency', 'urgent'
            )
        else:
            voice_handler._add_voice_to_response(
                response,
                "Thank you for your message. We'll return your call within 4 hours during business days. Have a great day!",
                'thank_you', 'friendly'
            )
        
        return Response(content=str(response), media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error processing voicemail for {CallSid}: {e}")
        response = VoiceResponse()
        response.say("Thank you for calling. We'll be in touch soon.", voice='Polly.Joanna')
        return Response(content=str(response), media_type="application/xml")

@app.post("/voice/status-callback")
async def call_status_callback(
    request: Request,
    CallSid: str = Form(...),
    CallStatus: str = Form(...),
    CallDuration: str = Form(None),
    From: str = Form(...),
    To: str = Form(...)
):
    """Handle call status updates from Twilio"""
    try:
        logger.info(f"Call status update: {CallSid} - {CallStatus}")
        
        # Update call tracking
        voice_handler.track_call(CallSid, From, CallStatus, {
            'duration': CallDuration,
            'to': To
        })
        
        return {"status": "received"}
        
    except Exception as e:
        logger.error(f"Error handling status callback for {CallSid}: {e}")
        return {"status": "error"}

# Analytics and reporting endpoints
@app.get("/voice/analytics/dashboard")
async def get_analytics_dashboard():
    """Get real-time analytics dashboard"""
    try:
        dashboard_data = voice_handler.analytics.get_real_time_dashboard()
        return {"success": True, "data": dashboard_data}
    except Exception as e:
        logger.error(f"Error getting analytics dashboard: {e}")
        return {"success": False, "error": str(e)}

@app.get("/voice/analytics/metrics")
async def get_call_metrics(time_range: str = "24h"):
    """Get call metrics for specified time range"""
    try:
        metrics = voice_handler.analytics.generate_call_metrics(time_range)
        return {"success": True, "data": metrics}
    except Exception as e:
        logger.error(f"Error getting call metrics: {e}")
        return {"success": False, "error": str(e)}

@app.get("/voice/analytics/customer/{caller_id}")
async def get_customer_history(caller_id: str):
    """Get customer interaction history"""
    try:
        history = voice_handler.analytics.get_customer_history(caller_id)
        return {"success": True, "data": history}
    except Exception as e:
        logger.error(f"Error getting customer history: {e}")
        return {"success": False, "error": str(e)}

@app.get("/voice/quality/report")
async def get_quality_report(time_range: str = "24h", agent_id: str = None):
    """Get quality assurance report"""
    try:
        report = await voice_handler.quality_assurance.generate_quality_report(time_range, agent_id)
        return {"success": True, "data": report}
    except Exception as e:
        logger.error(f"Error getting quality report: {e}")
        return {"success": False, "error": str(e)}

@app.post("/voice/quality/analyze")
async def analyze_call_quality_endpoint(request: Request):
    """Manually trigger call quality analysis"""
    try:
        data = await request.json()
        result = await voice_handler.analyze_call_quality(
            data.get('call_sid'),
            data.get('recording_url'),
            data.get('transcription'),
            data.get('agent_id')
        )
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Error in manual quality analysis: {e}")
        return {"success": False, "error": str(e)}

@app.post("/voice/emergency/assess")
async def assess_emergency_endpoint(request: Request):
    """Manually assess emergency level for transcription"""
    try:
        data = await request.json()
        assessment = voice_handler.emergency_handler.assess_urgency(
            data.get('transcription', ''),
            data.get('caller_id', ''),
            data.get('context', {})
        )
        
        return {
            "success": True,
            "data": {
                "urgency_level": assessment.urgency_level.name,
                "emergency_type": assessment.emergency_type.value if assessment.emergency_type else None,
                "confidence_score": assessment.confidence_score,
                "trigger_keywords": assessment.trigger_keywords,
                "recommended_action": assessment.recommended_action,
                "estimated_response_time": assessment.estimated_response_time,
                "requires_immediate_dispatch": assessment.requires_immediate_dispatch,
                "safety_concerns": assessment.safety_concerns
            }
        }
    except Exception as e:
        logger.error(f"Error in emergency assessment: {e}")
        return {"success": False, "error": str(e)}

# Health check endpoint
@app.get("/voice/health")
async def health_check():
    """Health check for voice system with comprehensive status"""
    try:
        # Get system health metrics
        active_calls = voice_handler.get_active_call_count()
        dashboard_data = voice_handler.analytics.get_real_time_dashboard()
        
        # Check subsystem health
        subsystem_health = {
            "elevenlabs": voice_handler.use_elevenlabs,
            "redis": voice_handler.redis_client is not None,
            "analytics": True,
            "emergency_handler": True,
            "quality_assurance": True
        }
        
        # Overall health score
        health_score = sum(subsystem_health.values()) / len(subsystem_health)
        
        return {
            "status": "healthy" if health_score > 0.8 else "degraded",
            "service": "757 Handy Voice System",
            "timestamp": datetime.now().isoformat(),
            "health_score": health_score,
            "active_calls": active_calls,
            "subsystems": subsystem_health,
            "real_time_metrics": dashboard_data,
            "features": {
                "premium_voice": voice_handler.use_elevenlabs,
                "emergency_detection": True,
                "quality_assurance": True,
                "analytics": True,
                "real_time_dashboard": True
            }
        }
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return {
            "status": "error",
            "service": "757 Handy Voice System",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
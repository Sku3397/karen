#!/usr/bin/env python3
"""
Advanced Voice Transcription and Processing System for 757 Handy
Handles voicemail transcription, emergency detection, and intelligent notifications

Author: Phone Engineer Agent
"""

import os
import re
import json
import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import speech_recognition as sr
from google.cloud import speech
import openai

# Email and SMS notification imports
from .email_client import EmailClient
from .sms_client import SMSClient

logger = logging.getLogger(__name__)

class Priority(Enum):
    """Message priority levels"""
    EMERGENCY = "emergency"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"

class MessageType(Enum):
    """Types of voice messages"""
    GENERAL_VOICEMAIL = "general"
    EMERGENCY_VOICEMAIL = "emergency"
    QUOTE_REQUEST = "quote"
    APPOINTMENT_REQUEST = "appointment"
    COMPLAINT = "complaint"
    CALLBACK_REQUEST = "callback"

@dataclass
class VoicemailData:
    """Structured voicemail data"""
    call_sid: str
    caller_id: str
    recording_url: str
    duration: int
    timestamp: datetime
    transcription: str = ""
    confidence: float = 0.0
    priority: Priority = Priority.NORMAL
    message_type: MessageType = MessageType.GENERAL_VOICEMAIL
    keywords: List[str] = None
    entities: Dict[str, List[str]] = None
    sentiment: str = "neutral"
    action_items: List[str] = None
    customer_info: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = []
        if self.entities is None:
            self.entities = {}
        if self.action_items is None:
            self.action_items = []
        if self.customer_info is None:
            self.customer_info = {}

class VoiceTranscriptionHandler:
    """
    Advanced transcription system with:
    - Multiple transcription engines (Google Cloud Speech, OpenAI Whisper)
    - Emergency keyword detection
    - Smart categorization and routing
    - Priority-based notifications
    - Customer information extraction
    - Sentiment analysis
    """
    
    def __init__(self):
        # Initialize transcription services
        self.google_speech_client = None
        self.openai_client = None
        
        try:
            if os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
                self.google_speech_client = speech.SpeechClient()
                logger.info("Google Cloud Speech initialized")
        except Exception as e:
            logger.warning(f"Google Cloud Speech not available: {e}")
        
        try:
            if os.getenv('OPENAI_API_KEY'):
                openai.api_key = os.getenv('OPENAI_API_KEY')
                self.openai_client = openai
                logger.info("OpenAI Whisper initialized")
        except Exception as e:
            logger.warning(f"OpenAI not available: {e}")
        
        # Initialize notification systems
        self.email_client = EmailClient(
            email_address=os.getenv('ADMIN_EMAIL_ADDRESS', 'admin@757handy.com')
        )
        self.sms_client = SMSClient()
        
        # Emergency keywords (case-insensitive)
        self.emergency_keywords = {
            'immediate': ['emergency', 'urgent', 'asap', 'immediately', 'right now', 'help'],
            'water': ['flood', 'flooding', 'water damage', 'burst pipe', 'leak', 'overflowing'],
            'electrical': ['sparks', 'electrical fire', 'power out', 'shock', 'burning smell'],
            'gas': ['gas leak', 'smell gas', 'propane leak', 'carbon monoxide'],
            'security': ['break in', 'broken window', 'door won\'t lock', 'security'],
            'hvac': ['no heat', 'no air', 'freezing', 'too hot', 'furnace out'],
            'structural': ['ceiling falling', 'wall crack', 'foundation', 'structural damage']
        }
        
        # Service type keywords
        self.service_keywords = {
            'plumbing': ['plumber', 'plumbing', 'toilet', 'sink', 'drain', 'pipe', 'faucet', 'shower', 'bathtub'],
            'electrical': ['electrician', 'electrical', 'outlet', 'switch', 'light', 'wire', 'circuit', 'breaker'],
            'hvac': ['heating', 'cooling', 'air conditioning', 'furnace', 'hvac', 'thermostat', 'vent'],
            'carpentry': ['carpenter', 'wood', 'door', 'window', 'cabinet', 'deck', 'trim', 'molding'],
            'general': ['handyman', 'repair', 'fix', 'install', 'maintenance', 'general']
        }
        
        # Sentiment indicators
        self.sentiment_keywords = {
            'positive': ['happy', 'pleased', 'satisfied', 'great', 'excellent', 'wonderful', 'thank you'],
            'negative': ['frustrated', 'angry', 'upset', 'disappointed', 'terrible', 'awful', 'complaint'],
            'urgent': ['urgent', 'emergency', 'asap', 'immediately', 'critical', 'important']
        }
        
        # Notification contacts
        self.notification_contacts = {
            'emergency': {
                'email': os.getenv('EMERGENCY_EMAIL', 'emergency@757handy.com'),
                'sms': os.getenv('EMERGENCY_SMS', '+15551234567')
            },
            'management': {
                'email': os.getenv('MANAGEMENT_EMAIL', 'management@757handy.com'),
                'sms': os.getenv('MANAGEMENT_SMS', '+15551234568')
            },
            'admin': {
                'email': os.getenv('ADMIN_EMAIL_ADDRESS', 'admin@757handy.com'),
                'sms': os.getenv('ADMIN_SMS', '+15551234569')
            }
        }
        
        logger.info("VoiceTranscriptionHandler initialized with emergency detection")
    
    async def process_voicemail(self, call_sid: str, recording_url: str, 
                              duration: int, message_type: str = 'general') -> VoicemailData:
        """
        Process a voicemail recording with full analysis
        """
        try:
            logger.info(f"Processing voicemail: {call_sid} - {recording_url}")
            
            # Create voicemail data structure
            voicemail = VoicemailData(
                call_sid=call_sid,
                caller_id=self._extract_caller_id(call_sid),
                recording_url=recording_url,
                duration=duration,
                timestamp=datetime.now(),
                message_type=MessageType(message_type) if message_type in MessageType._value2member_map_ else MessageType.GENERAL_VOICEMAIL
            )
            
            # Download and transcribe audio
            transcription_result = await self._transcribe_audio(recording_url)
            voicemail.transcription = transcription_result['text']
            voicemail.confidence = transcription_result['confidence']
            
            if voicemail.transcription:
                # Analyze the transcription
                await self._analyze_transcription(voicemail)
                
                # Determine priority and routing
                self._determine_priority(voicemail)
                
                # Extract customer information
                self._extract_customer_info(voicemail)
                
                # Generate action items
                self._generate_action_items(voicemail)
                
                # Send appropriate notifications
                await self._send_notifications(voicemail)
                
                # Log the processed voicemail
                await self._log_voicemail(voicemail)
            
            logger.info(f"Voicemail processed: {call_sid} - Priority: {voicemail.priority.value}")
            return voicemail
            
        except Exception as e:
            logger.error(f"Error processing voicemail {call_sid}: {e}")
            # Send error notification
            await self._send_error_notification(call_sid, str(e))
            raise
    
    async def _transcribe_audio(self, recording_url: str) -> Dict[str, Any]:
        """
        Transcribe audio using multiple engines for best accuracy
        """
        transcription_result = {
            'text': '',
            'confidence': 0.0,
            'engine': 'none'
        }
        
        try:
            # Try Google Cloud Speech first (most accurate for phone calls)
            if self.google_speech_client:
                result = await self._transcribe_with_google(recording_url)
                if result['confidence'] > 0.7:
                    return result
                transcription_result = result
            
            # Fallback to OpenAI Whisper
            if self.openai_client:
                result = await self._transcribe_with_whisper(recording_url)
                if result['confidence'] > transcription_result['confidence']:
                    transcription_result = result
            
            # Ultimate fallback to speech_recognition library
            if transcription_result['confidence'] < 0.5:
                result = await self._transcribe_with_sr(recording_url)
                if result['confidence'] > transcription_result['confidence']:
                    transcription_result = result
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
        
        return transcription_result
    
    async def _transcribe_with_google(self, recording_url: str) -> Dict[str, Any]:
        """Transcribe using Google Cloud Speech-to-Text"""
        try:
            # Download audio
            audio_content = await self._download_audio(recording_url)
            
            # Configure recognition
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.MP3,
                sample_rate_hertz=8000,  # Phone quality
                language_code="en-US",
                enable_automatic_punctuation=True,
                enable_word_confidence=True,
                model="phone_call",
                use_enhanced=True
            )
            
            audio = speech.RecognitionAudio(content=audio_content)
            
            # Perform transcription
            response = self.google_speech_client.recognize(config=config, audio=audio)
            
            if response.results:
                result = response.results[0]
                confidence = result.alternatives[0].confidence if result.alternatives[0].confidence else 0.8
                
                return {
                    'text': result.alternatives[0].transcript,
                    'confidence': confidence,
                    'engine': 'google'
                }
        
        except Exception as e:
            logger.error(f"Google Speech transcription failed: {e}")
        
        return {'text': '', 'confidence': 0.0, 'engine': 'google_failed'}
    
    async def _transcribe_with_whisper(self, recording_url: str) -> Dict[str, Any]:
        """Transcribe using OpenAI Whisper"""
        try:
            # Download audio
            audio_file_path = await self._download_audio_to_file(recording_url)
            
            # Transcribe with Whisper
            with open(audio_file_path, 'rb') as audio_file:
                transcript = self.openai_client.Audio.transcribe(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json"
                )
            
            # Clean up temp file
            os.unlink(audio_file_path)
            
            # Estimate confidence based on Whisper's behavior
            confidence = 0.85 if len(transcript.text) > 10 else 0.6
            
            return {
                'text': transcript.text,
                'confidence': confidence,
                'engine': 'whisper'
            }
        
        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
        
        return {'text': '', 'confidence': 0.0, 'engine': 'whisper_failed'}
    
    async def _transcribe_with_sr(self, recording_url: str) -> Dict[str, Any]:
        """Transcribe using speech_recognition library (fallback)"""
        try:
            import speech_recognition as sr
            
            # Download audio
            audio_file_path = await self._download_audio_to_file(recording_url)
            
            # Initialize recognizer
            r = sr.Recognizer()
            
            with sr.AudioFile(audio_file_path) as source:
                audio = r.record(source)
            
            # Try Google Web Speech API
            text = r.recognize_google(audio)
            
            # Clean up temp file
            os.unlink(audio_file_path)
            
            return {
                'text': text,
                'confidence': 0.7,  # Estimate
                'engine': 'speech_recognition'
            }
        
        except Exception as e:
            logger.error(f"Speech recognition fallback failed: {e}")
        
        return {'text': '', 'confidence': 0.0, 'engine': 'sr_failed'}
    
    async def _download_audio(self, recording_url: str) -> bytes:
        """Download audio content"""
        async with aiohttp.ClientSession() as session:
            async with session.get(recording_url) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    raise Exception(f"Failed to download audio: {response.status}")
    
    async def _download_audio_to_file(self, recording_url: str) -> str:
        """Download audio to temporary file"""
        import tempfile
        
        audio_content = await self._download_audio(recording_url)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            temp_file.write(audio_content)
            return temp_file.name
    
    async def _analyze_transcription(self, voicemail: VoicemailData):
        """Analyze transcription for keywords, entities, and sentiment"""
        text = voicemail.transcription.lower()
        
        # Extract keywords
        for category, keywords in self.service_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    voicemail.keywords.append(f"{category}:{keyword}")
        
        # Extract entities (phone numbers, emails, addresses)
        entities = {
            'phone_numbers': re.findall(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', voicemail.transcription),
            'emails': re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', voicemail.transcription),
            'times': re.findall(r'\b(?:1[0-2]|[1-9])(?::[0-5][0-9])?\s?(?:am|pm|AM|PM)\b', voicemail.transcription),
            'addresses': re.findall(r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd)', voicemail.transcription)
        }
        
        voicemail.entities = {k: v for k, v in entities.items() if v}
        
        # Analyze sentiment
        for sentiment, keywords in self.sentiment_keywords.items():
            if any(keyword in text for keyword in keywords):
                voicemail.sentiment = sentiment
                break
    
    def _determine_priority(self, voicemail: VoicemailData):
        """Determine message priority based on content analysis"""
        text = voicemail.transcription.lower()
        
        # Check for emergency keywords
        emergency_score = 0
        for category, keywords in self.emergency_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    emergency_score += 3 if category == 'immediate' else 2
        
        # Check message type
        if voicemail.message_type == MessageType.EMERGENCY_VOICEMAIL:
            emergency_score += 5
        
        # Check sentiment
        if voicemail.sentiment == 'urgent':
            emergency_score += 2
        elif voicemail.sentiment == 'negative':
            emergency_score += 1
        
        # Check time sensitivity indicators
        time_sensitive = ['today', 'tonight', 'asap', 'urgent', 'emergency', 'now']
        if any(word in text for word in time_sensitive):
            emergency_score += 2
        
        # Determine priority
        if emergency_score >= 7:
            voicemail.priority = Priority.EMERGENCY
            voicemail.message_type = MessageType.EMERGENCY_VOICEMAIL
        elif emergency_score >= 4:
            voicemail.priority = Priority.HIGH
        elif emergency_score >= 2:
            voicemail.priority = Priority.NORMAL
        else:
            voicemail.priority = Priority.LOW
        
        logger.info(f"Priority determined: {voicemail.priority.value} (score: {emergency_score})")
    
    def _extract_customer_info(self, voicemail: VoicemailData):
        """Extract customer information from voicemail"""
        text = voicemail.transcription
        
        # Extract name patterns
        name_patterns = [
            r"(?:my name is|i'm|this is)\s+([A-Za-z\s]+?)(?:\s|$|\.)",
            r"([A-Za-z]+\s+[A-Za-z]+)(?:\s+calling)",
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                voicemail.customer_info['name'] = match.group(1).strip()
                break
        
        # Extract contact information
        if voicemail.entities.get('phone_numbers'):
            voicemail.customer_info['callback_number'] = voicemail.entities['phone_numbers'][0]
        
        if voicemail.entities.get('emails'):
            voicemail.customer_info['email'] = voicemail.entities['emails'][0]
        
        if voicemail.entities.get('addresses'):
            voicemail.customer_info['address'] = voicemail.entities['addresses'][0]
    
    def _generate_action_items(self, voicemail: VoicemailData):
        """Generate action items based on voicemail content"""
        text = voicemail.transcription.lower()
        
        # Standard action items based on priority
        if voicemail.priority == Priority.EMERGENCY:
            voicemail.action_items.append("🚨 EMERGENCY: Call back immediately")
            voicemail.action_items.append("Dispatch emergency technician if needed")
        elif voicemail.priority == Priority.HIGH:
            voicemail.action_items.append("📞 Call back within 1 hour")
        else:
            voicemail.action_items.append("📞 Call back within 4 hours")
        
        # Service-specific actions
        if any(keyword in text for keyword in ['quote', 'estimate', 'price']):
            voicemail.action_items.append("📋 Schedule estimate appointment")
            voicemail.message_type = MessageType.QUOTE_REQUEST
        
        if any(keyword in text for keyword in ['appointment', 'schedule', 'book']):
            voicemail.action_items.append("📅 Check calendar availability")
            voicemail.message_type = MessageType.APPOINTMENT_REQUEST
        
        if any(keyword in text for keyword in ['complaint', 'problem', 'issue', 'unsatisfied']):
            voicemail.action_items.append("🎯 Escalate to customer service manager")
            voicemail.message_type = MessageType.COMPLAINT
        
        # Add follow-up items
        if voicemail.customer_info.get('callback_number'):
            voicemail.action_items.append(f"Use callback number: {voicemail.customer_info['callback_number']}")
        
        if voicemail.entities.get('times'):
            voicemail.action_items.append(f"Preferred time mentioned: {voicemail.entities['times'][0]}")
    
    async def _send_notifications(self, voicemail: VoicemailData):
        """Send appropriate notifications based on priority"""
        try:
            # Determine notification recipients
            if voicemail.priority == Priority.EMERGENCY:
                await self._send_emergency_notifications(voicemail)
            elif voicemail.priority == Priority.HIGH:
                await self._send_high_priority_notifications(voicemail)
            else:
                await self._send_normal_notifications(voicemail)
        
        except Exception as e:
            logger.error(f"Failed to send notifications for {voicemail.call_sid}: {e}")
    
    async def _send_emergency_notifications(self, voicemail: VoicemailData):
        """Send emergency notifications via multiple channels"""
        # SMS to emergency contact
        emergency_sms = f"🚨 EMERGENCY VOICEMAIL\nFrom: {voicemail.caller_id}\nDuration: {voicemail.duration}s\nMessage: {voicemail.transcription[:100]}...\nAction: {voicemail.action_items[0] if voicemail.action_items else 'Call back immediately'}"
        
        await self.sms_client.send_sms(
            to=self.notification_contacts['emergency']['sms'],
            message=emergency_sms
        )
        
        # Email to emergency and management
        subject = f"🚨 EMERGENCY VOICEMAIL - {voicemail.caller_id}"
        await self._send_detailed_email(voicemail, subject, ['emergency', 'management'])
    
    async def _send_high_priority_notifications(self, voicemail: VoicemailData):
        """Send high priority notifications"""
        # SMS to management
        sms_message = f"📞 HIGH PRIORITY VOICEMAIL\nFrom: {voicemail.caller_id}\nType: {voicemail.message_type.value}\nMessage: {voicemail.transcription[:80]}..."
        
        await self.sms_client.send_sms(
            to=self.notification_contacts['management']['sms'],
            message=sms_message
        )
        
        # Email notification
        subject = f"📞 High Priority Voicemail - {voicemail.caller_id}"
        await self._send_detailed_email(voicemail, subject, ['management', 'admin'])
    
    async def _send_normal_notifications(self, voicemail: VoicemailData):
        """Send normal priority notifications"""
        # Email only for normal priority
        subject = f"New Voicemail - {voicemail.caller_id}"
        await self._send_detailed_email(voicemail, subject, ['admin'])
    
    async def _send_detailed_email(self, voicemail: VoicemailData, subject: str, recipient_types: List[str]):
        """Send detailed email notification"""
        # Create HTML email content
        html_content = self._generate_email_content(voicemail)
        
        # Send to specified recipients
        for recipient_type in recipient_types:
            if recipient_type in self.notification_contacts:
                try:
                    await self.email_client.send_email(
                        to=self.notification_contacts[recipient_type]['email'],
                        subject=subject,
                        html_content=html_content
                    )
                except Exception as e:
                    logger.error(f"Failed to send email to {recipient_type}: {e}")
    
    def _generate_email_content(self, voicemail: VoicemailData) -> str:
        """Generate detailed HTML email content"""
        priority_colors = {
            Priority.EMERGENCY: "#ff4444",
            Priority.HIGH: "#ff8800",
            Priority.NORMAL: "#4488ff",
            Priority.LOW: "#888888"
        }
        
        color = priority_colors.get(voicemail.priority, "#4488ff")
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 20px;">
            <div style="border-left: 5px solid {color}; padding-left: 20px; margin-bottom: 20px;">
                <h2 style="color: {color}; margin-top: 0;">
                    {voicemail.priority.value.upper()} Voicemail - 757 Handy
                </h2>
            </div>
            
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <h3>Call Details</h3>
                <p><strong>Caller ID:</strong> {voicemail.caller_id}</p>
                <p><strong>Duration:</strong> {voicemail.duration} seconds</p>
                <p><strong>Timestamp:</strong> {voicemail.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Message Type:</strong> {voicemail.message_type.value.title()}</p>
                <p><strong>Priority:</strong> <span style="color: {color}; font-weight: bold;">{voicemail.priority.value.upper()}</span></p>
                <p><strong>Sentiment:</strong> {voicemail.sentiment.title()}</p>
            </div>
            
            <div style="margin-bottom: 20px;">
                <h3>Transcription</h3>
                <div style="background: white; padding: 15px; border: 1px solid #ddd; border-radius: 5px;">
                    <p style="margin: 0; line-height: 1.6;">{voicemail.transcription}</p>
                </div>
                <p style="font-size: 0.9em; color: #666; margin-top: 5px;">
                    Confidence: {voicemail.confidence:.1%} | Engine: {getattr(voicemail, 'engine', 'unknown')}
                </p>
            </div>
        """
        
        if voicemail.customer_info:
            html += """
            <div style="margin-bottom: 20px;">
                <h3>Customer Information</h3>
                <div style="background: #e8f4fd; padding: 15px; border-radius: 5px;">
            """
            for key, value in voicemail.customer_info.items():
                html += f"<p><strong>{key.replace('_', ' ').title()}:</strong> {value}</p>"
            html += "</div></div>"
        
        if voicemail.action_items:
            html += """
            <div style="margin-bottom: 20px;">
                <h3>Action Items</h3>
                <ul style="background: #fff3cd; padding: 15px; border-radius: 5px;">
            """
            for item in voicemail.action_items:
                html += f"<li style='margin-bottom: 8px;'>{item}</li>"
            html += "</ul></div>"
        
        if voicemail.keywords:
            html += f"""
            <div style="margin-bottom: 20px;">
                <h3>Detected Keywords</h3>
                <p style="background: #f8f9fa; padding: 10px; border-radius: 5px; font-family: monospace;">
                    {', '.join(voicemail.keywords)}
                </p>
            </div>
            """
        
        html += f"""
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 0.9em; color: #666;">
                <p>Recording URL: <a href="{voicemail.recording_url}">Listen to Recording</a></p>
                <p>This is an automated notification from the 757 Handy voice system.</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    async def _send_error_notification(self, call_sid: str, error_message: str):
        """Send notification about transcription errors"""
        try:
            subject = f"Voice System Error - {call_sid}"
            message = f"Error processing voicemail {call_sid}: {error_message}"
            
            await self.email_client.send_email(
                to=self.notification_contacts['admin']['email'],
                subject=subject,
                text_content=message
            )
        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")
    
    async def _log_voicemail(self, voicemail: VoicemailData):
        """Log voicemail data for analytics and record keeping"""
        try:
            # Convert to JSON for logging
            voicemail_dict = asdict(voicemail)
            voicemail_dict['timestamp'] = voicemail.timestamp.isoformat()
            voicemail_dict['priority'] = voicemail.priority.value
            voicemail_dict['message_type'] = voicemail.message_type.value
            
            # Log to file (in production, this would go to a database)
            log_file = f"voicemails_{datetime.now().strftime('%Y%m%d')}.jsonl"
            with open(log_file, 'a') as f:
                f.write(json.dumps(voicemail_dict) + '\n')
            
            logger.info(f"Voicemail logged: {voicemail.call_sid}")
            
        except Exception as e:
            logger.error(f"Failed to log voicemail {voicemail.call_sid}: {e}")
    
    def _extract_caller_id(self, call_sid: str) -> str:
        """Extract caller ID from call SID (placeholder - would use Twilio API)"""
        # This would typically query Twilio's API to get caller information
        # For now, return a placeholder
        return "unknown"
    
    def get_voicemail_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get analytics on voicemail patterns"""
        # This would query stored voicemail data
        # Placeholder implementation
        return {
            'total_voicemails': 0,
            'by_priority': {},
            'by_type': {},
            'average_duration': 0,
            'transcription_accuracy': 0,
            'response_times': {}
        }

if __name__ == "__main__":
    # Test the transcription handler
    async def test():
        handler = VoiceTranscriptionHandler()
        
        # Test emergency detection
        test_transcription = "This is an emergency! I have a gas leak in my kitchen and can smell gas throughout the house. Please call me back immediately at 555-123-4567."
        
        # Create test voicemail
        voicemail = VoicemailData(
            call_sid="CA123456789",
            caller_id="+15551234567",
            recording_url="https://test.com/recording.mp3",
            duration=45,
            timestamp=datetime.now(),
            transcription=test_transcription
        )
        
        # Analyze
        await handler._analyze_transcription(voicemail)
        handler._determine_priority(voicemail)
        handler._extract_customer_info(voicemail)
        handler._generate_action_items(voicemail)
        
        print(f"Priority: {voicemail.priority.value}")
        print(f"Message Type: {voicemail.message_type.value}")
        print(f"Keywords: {voicemail.keywords}")
        print(f"Customer Info: {voicemail.customer_info}")
        print(f"Action Items: {voicemail.action_items}")
    
    asyncio.run(test())
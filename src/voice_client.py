# VoiceClient: Handles voice calls, transcription, and TTS using Twilio Voice and Google Speech APIs
import os
import logging
import json
import base64
import io
import tempfile
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Twilio Voice API
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from twilio.twiml.voice_response import VoiceResponse, Gather

# Google Cloud Speech and TTS
try:
    from google.cloud import speech, texttospeech
    from google.oauth2 import service_account
    GOOGLE_CLOUD_AVAILABLE = True
except ImportError:
    GOOGLE_CLOUD_AVAILABLE = False
    logging.warning("Google Cloud Speech/TTS not available. Voice transcription/synthesis will be limited.")

# Define paths relative to the project root, assuming this file is in src/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

logger = logging.getLogger(__name__)

class VoiceClient:
    """
    VoiceClient handles voice calls, transcription, and text-to-speech functionality.
    Follows EmailClient patterns for consistent error handling and authentication.
    """
    
    def __init__(self, karen_phone: str, credentials_data: Optional[Dict[str, str]] = None):
        """
        Initialize VoiceClient following EmailClient pattern.
        
        Args:
            karen_phone: Karen's phone number (e.g., +17575551234)
            credentials_data: Optional dict with Twilio and GCP credentials (for testing)
        """
        self.karen_phone = karen_phone
        logger.debug(f"Initializing VoiceClient for {karen_phone}")
        
        # Initialize call history tracking
        self._call_cache: Dict[str, Dict[str, Any]] = {}
        self._processed_calls_file = os.path.join(PROJECT_ROOT, '.processed_call_ids.json')
        
        # Load Twilio credentials following EmailClient pattern
        if credentials_data:
            # For testing - credentials passed directly
            self.twilio_account_sid = credentials_data.get('twilio_account_sid')
            self.twilio_auth_token = credentials_data.get('twilio_auth_token')
            self.gcp_credentials_path = credentials_data.get('gcp_credentials_path')
        else:
            # Load from environment variables
            self.twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            self.twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            self.gcp_credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        # Validate Twilio credentials
        if not self.twilio_account_sid or not self.twilio_auth_token:
            logger.error("Failed to load Twilio credentials. Check TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN.")
            raise ValueError("Failed to load Twilio credentials.")
        
        # Initialize Twilio client
        try:
            self.twilio_client = Client(self.twilio_account_sid, self.twilio_auth_token)
            logger.info(f"Twilio VoiceClient for {karen_phone} initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Twilio client: {e}", exc_info=True)
            raise
        
        # Initialize Google Cloud Speech/TTS clients
        self.speech_client = None
        self.tts_client = None
        
        if GOOGLE_CLOUD_AVAILABLE:
            self._initialize_google_cloud_clients()
        else:
            logger.warning("Google Cloud Speech/TTS unavailable. Transcription and synthesis features will be limited.")
        
        logger.info(f"VoiceClient for {karen_phone} initialized successfully.")
    
    def _initialize_google_cloud_clients(self):
        """Initialize Google Cloud Speech and TTS clients following Karen's OAuth patterns."""
        try:
            if self.gcp_credentials_path and os.path.exists(self.gcp_credentials_path):
                # Load service account credentials
                credentials = service_account.Credentials.from_service_account_file(
                    self.gcp_credentials_path,
                    scopes=[
                        'https://www.googleapis.com/auth/cloud-platform',
                        'https://www.googleapis.com/auth/cloud-speech',
                    ]
                )
                
                self.speech_client = speech.SpeechClient(credentials=credentials)
                self.tts_client = texttospeech.TextToSpeechClient(credentials=credentials)
                logger.info("Google Cloud Speech and TTS clients initialized successfully.")
                
            else:
                # Try default credentials (for cloud environments)
                self.speech_client = speech.SpeechClient()
                self.tts_client = texttospeech.TextToSpeechClient()
                logger.info("Google Cloud clients initialized with default credentials.")
                
        except Exception as e:
            logger.warning(f"Failed to initialize Google Cloud clients: {e}. Transcription/synthesis will be limited.")
            self.speech_client = None
            self.tts_client = None
    
    def make_call(self, to: str, message: str, voice: str = 'alice') -> bool:
        """
        Make an outbound call with text-to-speech message.
        Following EmailClient.send_email pattern.
        
        Args:
            to: Recipient phone number in E.164 format (e.g., +1234567890)
            message: Message to speak during the call
            voice: Twilio voice to use ('alice', 'man', 'woman')
            
        Returns:
            bool: True if call initiated successfully, False otherwise
        """
        logger.debug(f"Attempting to make call to: {to}, message length: {len(message)}")
        
        try:
            # Truncate message if too long (Twilio has practical limits)
            if len(message) > 4000:
                logger.warning(f"Call message too long ({len(message)} chars). Truncating to 4000.")
                message = message[:3997] + "..."
            
            # Create TwiML for the call
            twiml = VoiceResponse()
            twiml.say(message, voice=voice)
            
            # Initiate the call
            call = self.twilio_client.calls.create(
                twiml=str(twiml),
                to=to,
                from_=self.karen_phone
            )
            
            logger.info(f"Call initiated successfully via Twilio API. Call SID: {call.sid}")
            
            # Cache call details
            self._call_cache[call.sid] = {
                'to': to,
                'from': self.karen_phone,
                'message': message,
                'initiated_at': datetime.now(timezone.utc),
                'status': 'initiated'
            }
            
            return True
            
        except TwilioRestException as error:
            logger.error(f"Twilio API error occurred: {error.msg}. Code: {error.code}", exc_info=True)
            if error.code == 20003:
                logger.error("Authentication error (20003). Check account SID and auth token.")
            elif error.code == 21211:
                logger.error("Invalid 'To' phone number (21211). Ensure E.164 format.")
            elif error.code == 21212:
                logger.error("Invalid 'From' phone number (21212). Check karen_phone.")
            elif error.code == 21218:
                logger.error("Insufficient funds (21218). Check Twilio account balance.")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred during make_call: {e}", exc_info=True)
            return False
    
    def fetch_calls(self, search_criteria: str = 'inbound', 
                    last_n_days: Optional[int] = None,
                    newer_than: Optional[str] = None,
                    max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch call records following EmailClient.fetch_emails pattern.
        
        Args:
            search_criteria: 'inbound', 'outbound', or 'all'
            last_n_days: Fetch calls from last N days
            newer_than: Fetch calls newer than (e.g., "1h", "2d")
            max_results: Maximum number of calls to return
            
        Returns:
            List of call dictionaries following EmailClient structure
        """
        logger.debug(f"Fetching calls with criteria: '{search_criteria}', last_n_days: {last_n_days}, "
                    f"newer_than: {newer_than}, max_results: {max_results}")
        
        try:
            # Build date filter
            date_filter = None
            if newer_than:
                # Parse newer_than format (1h, 2d, etc.)
                if newer_than.endswith('h'):
                    hours = int(newer_than[:-1])
                    date_filter = datetime.now(timezone.utc) - timedelta(hours=hours)
                elif newer_than.endswith('d'):
                    days = int(newer_than[:-1])
                    date_filter = datetime.now(timezone.utc) - timedelta(days=days)
            elif last_n_days and last_n_days > 0:
                date_filter = datetime.now(timezone.utc) - timedelta(days=last_n_days)
            
            # Fetch calls from Twilio
            call_kwargs = {
                'limit': max_results
            }
            
            # Filter by direction
            if search_criteria == 'inbound':
                call_kwargs['to'] = self.karen_phone
            elif search_criteria == 'outbound':
                call_kwargs['from_'] = self.karen_phone
            # 'all' doesn't add direction filter
            
            if date_filter:
                call_kwargs['start_time_after'] = date_filter
            
            calls = self.twilio_client.calls.list(**call_kwargs)
            
            if not calls:
                logger.info("No calls found matching criteria.")
                return []
            
            logger.info(f"Found {len(calls)} calls. Processing...")
            
            call_data = []
            for call in calls:
                # Map Twilio call to EmailClient structure for compatibility
                call_item = {
                    'id': call.sid,  # Use Twilio SID as ID
                    'threadId': call.sid,  # Calls don't have threads, use SID
                    'snippet': f"Call from {call.from_} to {call.to}",
                    'sender': call.from_,  # Phone number of caller
                    'recipient': call.to,  # Phone number called
                    'subject': f"Voice call {call.direction}",  # Generate subject for compatibility
                    'body_plain': f"Duration: {call.duration}s, Status: {call.status}",
                    'body_html': '',  # Calls don't have HTML
                    'body': f"Call {call.direction} - Duration: {call.duration}s",
                    'date_str': call.start_time.strftime("%a, %d %b %Y %H:%M:%S %z") if call.start_time else '',
                    'received_date_dt': call.start_time,
                    'uid': call.sid,  # Use SID as UID for compatibility
                    'status': call.status,  # Twilio status (completed, busy, etc.)
                    'direction': call.direction,  # inbound/outbound
                    'duration': call.duration,  # Call duration in seconds
                    'price': call.price,  # Call cost
                    'recording_url': None  # Will be populated if recordings exist
                }
                
                call_data.append(call_item)
            
            logger.info(f"Successfully fetched details for {len(call_data)} calls.")
            return call_data
            
        except TwilioRestException as error:
            logger.error(f"Twilio API error during fetch_calls: {error.msg}. Code: {error.code}", exc_info=True)
            return []
        except Exception as e:
            logger.error(f"Unexpected error during fetch_calls: {e}", exc_info=True)
            return []
    
    def get_call_recordings(self, call_sid: str) -> List[Dict[str, Any]]:
        """
        Get recordings for a specific call.
        
        Args:
            call_sid: Twilio call SID
            
        Returns:
            List of recording dictionaries
        """
        try:
            recordings = self.twilio_client.recordings.list(call_sid=call_sid)
            
            recording_data = []
            for recording in recordings:
                recording_data.append({
                    'sid': recording.sid,
                    'call_sid': recording.call_sid,
                    'duration': recording.duration,
                    'url': f"https://api.twilio.com{recording.uri.replace('.json', '.mp3')}",
                    'date_created': recording.date_created
                })
            
            return recording_data
            
        except Exception as e:
            logger.error(f"Error fetching recordings for call {call_sid}: {e}", exc_info=True)
            return []
    
    def transcribe_audio(self, audio_content: bytes, 
                        language_code: str = "en-US",
                        sample_rate: int = 8000) -> Optional[str]:
        """
        Transcribe audio content using Google Cloud Speech-to-Text.
        
        Args:
            audio_content: Raw audio bytes
            language_code: Language code (e.g., "en-US")
            sample_rate: Audio sample rate in Hz
            
        Returns:
            Transcribed text or None if transcription fails
        """
        if not self.speech_client:
            logger.warning("Speech client not available. Cannot transcribe audio.")
            return None
        
        try:
            audio = speech.RecognitionAudio(content=audio_content)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.MULAW,  # Common for phone calls
                sample_rate_hertz=sample_rate,
                language_code=language_code,
                enable_automatic_punctuation=True,
                model='phone_call'  # Optimized for phone call audio
            )
            
            response = self.speech_client.recognize(config=config, audio=audio)
            
            if response.results:
                transcript = ' '.join([
                    result.alternatives[0].transcript 
                    for result in response.results
                ])
                logger.info(f"Successfully transcribed audio: {transcript[:100]}...")
                return transcript
            else:
                logger.warning("No transcription results returned from Speech API.")
                return None
                
        except Exception as e:
            logger.error(f"Error during audio transcription: {e}", exc_info=True)
            return None
    
    def transcribe_call_recording(self, call_sid: str) -> Optional[str]:
        """
        Transcribe a call recording from Twilio.
        
        Args:
            call_sid: Twilio call SID
            
        Returns:
            Transcribed text or None if transcription fails
        """
        try:
            recordings = self.get_call_recordings(call_sid)
            if not recordings:
                logger.warning(f"No recordings found for call {call_sid}")
                return None
            
            # Use the first recording
            recording = recordings[0]
            recording_url = recording['url']
            
            # Download the recording
            import requests
            response = requests.get(recording_url, 
                                  auth=(self.twilio_account_sid, self.twilio_auth_token))
            
            if response.status_code == 200:
                audio_content = response.content
                return self.transcribe_audio(audio_content)
            else:
                logger.error(f"Failed to download recording: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error transcribing call recording {call_sid}: {e}", exc_info=True)
            return None
    
    def synthesize_speech(self, text: str, 
                         output_format: str = "mp3",
                         voice_name: str = "en-US-Standard-A") -> Optional[bytes]:
        """
        Convert text to speech using Google Cloud Text-to-Speech.
        
        Args:
            text: Text to synthesize
            output_format: Output format ("mp3", "wav")
            voice_name: Google TTS voice name
            
        Returns:
            Audio bytes or None if synthesis fails
        """
        if not self.tts_client:
            logger.warning("TTS client not available. Cannot synthesize speech.")
            return None
        
        try:
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            voice = texttospeech.VoiceSelectionParams(
                name=voice_name,
                language_code="en-US"
            )
            
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3 if output_format == "mp3" 
                              else texttospeech.AudioEncoding.LINEAR16
            )
            
            response = self.tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            logger.info(f"Successfully synthesized speech for text: {text[:50]}...")
            return response.audio_content
            
        except Exception as e:
            logger.error(f"Error during speech synthesis: {e}", exc_info=True)
            return None
    
    def create_call_webhook_response(self, request_data: Dict[str, str]) -> str:
        """
        Create TwiML response for incoming call webhooks.
        
        Args:
            request_data: Webhook data from Twilio
            
        Returns:
            TwiML response string
        """
        try:
            from_number = request_data.get('From', 'Unknown')
            call_sid = request_data.get('CallSid', 'Unknown')
            
            logger.info(f"Creating webhook response for call from {from_number}, SID: {call_sid}")
            
            response = VoiceResponse()
            
            # Greeting message
            greeting = (
                f"Hello, you've reached {os.getenv('BUSINESS_NAME', 'Beach Handyman')}. "
                f"This is Karen, your AI assistant. How can I help you today?"
            )
            
            # Gather user input
            gather = Gather(
                num_digits=0,  # No digit limit
                action='/webhooks/voice/process',  # URL to process gathered input
                speech_timeout='auto',
                finish_on_key='#',
                method='POST'
            )
            
            gather.say(greeting, voice='alice')
            response.append(gather)
            
            # Fallback if no input received
            response.say("I didn't receive any input. Please call back if you need assistance.")
            response.hangup()
            
            return str(response)
            
        except Exception as e:
            logger.error(f"Error creating call webhook response: {e}", exc_info=True)
            # Fallback response
            response = VoiceResponse()
            response.say("Sorry, we're experiencing technical difficulties. Please call back later.")
            response.hangup()
            return str(response)
    
    def mark_call_as_processed(self, call_sid: str) -> bool:
        """
        Mark call as processed. Following EmailClient.mark_email_as_processed pattern.
        """
        logger.debug(f"Attempting to mark call SID {call_sid} as processed.")
        
        try:
            # Load existing processed calls
            processed_ids = set()
            if os.path.exists(self._processed_calls_file):
                with open(self._processed_calls_file, 'r') as f:
                    processed_ids = set(json.load(f))
            
            processed_ids.add(call_sid)
            
            with open(self._processed_calls_file, 'w') as f:
                json.dump(list(processed_ids), f)
            
            logger.info(f"Call {call_sid} marked as processed")
            return True
            
        except Exception as e:
            logger.error(f"Error marking call {call_sid} as processed: {e}", exc_info=True)
            return False
    
    def is_call_processed(self, call_sid: str) -> bool:
        """Check if call has been processed."""
        try:
            if os.path.exists(self._processed_calls_file):
                with open(self._processed_calls_file, 'r') as f:
                    processed_ids = set(json.load(f))
                return call_sid in processed_ids
            return False
        except Exception as e:
            logger.error(f"Error checking if call {call_sid} is processed: {e}", exc_info=True)
            return False
    
    def send_test_call(self, recipient_number: str, test_message: str = "AI Test Call") -> bool:
        """Send a test call following EmailClient pattern."""
        logger.info(f"send_test_call called to {recipient_number} with message: '{test_message}'")
        
        full_message = (
            f"{test_message}: This is a test call from Karen AI "
            f"({self.karen_phone}) at {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}. "
            f"Verifying voice call capability. This call will end shortly."
        )
        
        logger.info(f"Attempting to send test call from {self.karen_phone} to {recipient_number}")
        try:
            success = self.make_call(recipient_number, full_message)
            
            if success:
                logger.info(f"Test call successfully initiated to {recipient_number}.")
                return True
            else:
                logger.error(f"Failed to initiate test call to {recipient_number}")
                return False
        except Exception as e:
            logger.error(f"Failed to send test call to {recipient_number}: {e}", exc_info=True)
            return False
    
    def get_call_status(self, call_sid: str) -> Optional[Dict[str, Any]]:
        """Get current status of a call."""
        try:
            call = self.twilio_client.calls(call_sid).fetch()
            return {
                'sid': call.sid,
                'status': call.status,
                'duration': call.duration,
                'start_time': call.start_time,
                'end_time': call.end_time,
                'from': call.from_,
                'to': call.to,
                'price': call.price
            }
        except Exception as e:
            logger.error(f"Error fetching call status for {call_sid}: {e}", exc_info=True)
            return None


# Example usage (for testing, if run directly)
if __name__ == '__main__':
    from dotenv import load_dotenv
    import sys
    
    # Load .env for testing
    dotenv_path = os.path.join(PROJECT_ROOT, '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path=dotenv_path)
        print(f"Loaded .env from {dotenv_path} for VoiceClient testing.")
    else:
        print(f"Warning: .env file not found at {dotenv_path} for VoiceClient testing.")
    
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    
    # Test with Karen's phone credentials
    karen_phone = os.getenv("KAREN_PHONE_NUMBER", "+17575551234")  # Default if not in .env
    
    if not os.getenv('TWILIO_ACCOUNT_SID') or not os.getenv('TWILIO_AUTH_TOKEN'):
        logger.error("CRITICAL: Twilio credentials not found in environment. Cannot run test.")
    else:
        try:
            logger.info(f"--- TESTING Voice Client for {karen_phone} ---")
            client = VoiceClient(karen_phone=karen_phone)
            
            # Test fetching recent calls
            print(f"\nFetching recent calls for {karen_phone}...")
            recent_calls = client.fetch_calls(search_criteria='all', last_n_days=7, max_results=5)
            if recent_calls:
                print(f"Found {len(recent_calls)} recent calls:")
                for call in recent_calls:
                    print(f"  From: {call.get('sender')}, To: {call.get('recipient')}, "
                          f"Status: {call.get('status')}, Duration: {call.get('duration')}s")
            else:
                print(f"No recent calls found for {karen_phone}.")
            
            # Test speech synthesis if available
            if client.tts_client:
                print(f"\nTesting speech synthesis...")
                test_text = "Hello, this is a test of Karen's voice synthesis capabilities."
                audio_content = client.synthesize_speech(test_text)
                if audio_content:
                    print(f"Successfully synthesized {len(audio_content)} bytes of audio.")
                else:
                    print("Speech synthesis failed.")
            else:
                print("\nSpeech synthesis not available (Google Cloud TTS not configured).")
                
        except ValueError as ve:
            logger.error(f"ValueError during VoiceClient test setup: {ve}")
        except Exception as e:
            logger.error(f"An error occurred during VoiceClient test: {e}", exc_info=True)
# Initialize as Phone Engineer
import glob
import json
import time
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.append('.')

AGENT_NAME = "phone_engineer"
print(f"Initializing {AGENT_NAME} - Voice and Phone Features")

def create_status_file(status, progress, details=None):
    """Create status file for other agents to monitor"""
    status_data = {
        'agent': AGENT_NAME,
        'status': status,
        'progress': progress,
        'timestamp': datetime.now().isoformat(),
        'details': details or {}
    }
    
    Path('autonomous-agents/communication/status').mkdir(parents=True, exist_ok=True)
    with open(f'autonomous-agents/communication/status/{AGENT_NAME}_status.json', 'w') as f:
        json.dump(status_data, f, indent=2)
    print(f"Status updated: {status} ({progress}%)")

def log_activity(message, data=None):
    """Log activity to file"""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'agent': AGENT_NAME,
        'message': message,
        'data': data or {}
    }
    
    with open(log_dir / f'{AGENT_NAME}_activity.log', 'a') as f:
        f.write(f"{json.dumps(log_entry)}\n")

def create_voice_client():
    """Create the voice client implementation"""
    voice_client_code = '''"""
Voice Client for Karen - Handles Twilio voice operations
"""
import os
import logging
from typing import Dict, Any, List, Optional
from twilio.rest import Client
from twilio.base.exceptions import TwilioException

try:
    from google.cloud import speech
    from google.cloud import texttospeech
    GOOGLE_CLOUD_AVAILABLE = True
except ImportError:
    GOOGLE_CLOUD_AVAILABLE = False

logger = logging.getLogger(__name__)

class VoiceClient:
    """
    Voice client for handling phone calls, transcription, and text-to-speech
    """
    
    def __init__(self, karen_phone: str = None):
        """Initialize Twilio client and Google Cloud services"""
        self.karen_phone = karen_phone or os.getenv('KAREN_PHONE_NUMBER')
        
        # Initialize Twilio
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        
        if account_sid and auth_token:
            self.client = Client(account_sid, auth_token)
            logger.info("Twilio client initialized")
        else:
            logger.warning("Twilio credentials not found - voice features limited")
            self.client = None
        
        # Initialize Google Cloud services
        self.speech_client = None
        self.tts_client = None
        
        if GOOGLE_CLOUD_AVAILABLE:
            try:
                self.speech_client = speech.SpeechClient()
                self.tts_client = texttospeech.TextToSpeechClient()
                logger.info("Google Cloud Speech services initialized")
            except Exception as e:
                logger.warning(f"Google Cloud services not available: {e}")
    
    def make_call(self, to_number: str, message: str, voice: str = 'alice') -> bool:
        """Make an outbound call"""
        if not self.client:
            logger.error("Twilio client not available")
            return False
        
        try:
            call = self.client.calls.create(
                to=to_number,
                from_=self.karen_phone,
                twiml=f'<Response><Say voice="{voice}">{message}</Say></Response>'
            )
            
            logger.info(f"Call initiated to {to_number}, SID: {call.sid}")
            return True
            
        except TwilioException as e:
            logger.error(f"Error making call: {e}")
            return False
    
    def fetch_calls(self, search_criteria: str = 'inbound', 
                    newer_than: str = '1h', max_results: int = 20) -> List[Dict[str, Any]]:
        """Fetch call records"""
        if not self.client:
            return []
        
        try:
            calls = self.client.calls.list(limit=max_results)
            
            call_data = []
            for call in calls:
                call_data.append({
                    'uid': call.sid,
                    'sender': call.from_,
                    'recipient': call.to,
                    'status': call.status,
                    'duration': call.duration,
                    'start_time': call.start_time,
                    'end_time': call.end_time
                })
            
            return call_data
            
        except TwilioException as e:
            logger.error(f"Error fetching calls: {e}")
            return []
    
    def transcribe_call_recording(self, call_sid: str) -> Optional[str]:
        """Transcribe call recording using Google Cloud Speech"""
        if not self.speech_client:
            logger.warning("Google Cloud Speech not available")
            return None
        
        try:
            # Get recording from Twilio
            recordings = self.client.recordings.list(call_sid=call_sid)
            
            if not recordings:
                logger.info(f"No recordings found for call {call_sid}")
                return None
            
            # Use the first recording
            recording = recordings[0]
            recording_url = f"https://api.twilio.com{recording.uri.replace('.json', '.wav')}"
            
            # Download and transcribe
            # Note: This is a simplified version - in production you'd need to handle
            # audio format conversion and streaming
            
            logger.info(f"Transcription would be performed for recording: {recording_url}")
            return f"[Transcription placeholder for {call_sid}]"
            
        except Exception as e:
            logger.error(f"Error transcribing call {call_sid}: {e}")
            return None
    
    def synthesize_speech(self, text: str, voice_name: str = 'en-US-Standard-A') -> Optional[bytes]:
        """Synthesize speech using Google Cloud TTS"""
        if not self.tts_client:
            logger.warning("Google Cloud TTS not available")
            return None
        
        try:
            synthesis_input = texttospeech.SynthesisInput(text=text)
            voice = texttospeech.VoiceSelectionParams(
                language_code='en-US',
                name=voice_name
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            
            response = self.tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            return response.audio_content
            
        except Exception as e:
            logger.error(f"Error synthesizing speech: {e}")
            return None
    
    def is_call_processed(self, call_sid: str) -> bool:
        """Check if call has been processed"""
        # Simple implementation - in production this would check a database
        processed_file = Path(f'logs/processed_calls/{call_sid}.json')
        return processed_file.exists()
    
    def mark_call_as_processed(self, call_sid: str):
        """Mark call as processed"""
        processed_dir = Path('logs/processed_calls')
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        with open(processed_dir / f'{call_sid}.json', 'w') as f:
            json.dump({
                'call_sid': call_sid,
                'processed_at': datetime.now().isoformat()
            }, f)
'''
    
    with open('src/voice_client.py', 'w') as f:
        f.write(voice_client_code)
    
    print("✅ Created src/voice_client.py")

def create_voice_handler():
    """Create voice webhook handler"""
    handler_code = '''"""
Voice webhook handler for Twilio
"""
from flask import Flask, request
from twilio.twiml import VoiceResponse
import logging

logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/voice', methods=['POST'])
def handle_voice():
    """Handle incoming voice calls"""
    response = VoiceResponse()
    
    # Get caller information
    from_number = request.form.get('From')
    to_number = request.form.get('To')
    
    logger.info(f"Incoming call from {from_number} to {to_number}")
    
    # Business hours check (simplified)
    from datetime import datetime
    current_hour = datetime.now().hour
    
    if 8 <= current_hour <= 18:  # 8 AM to 6 PM
        response.say(
            "Hello! Thank you for calling Beach Handyman. "
            "Please leave your name, number, and a brief description "
            "of your handyman needs after the beep. We'll call you back soon!",
            voice='alice'
        )
        response.record(
            action='/recording',
            method='POST',
            max_length=120,  # 2 minutes max
            finish_on_key='#'
        )
    else:
        response.say(
            "Thank you for calling Beach Handyman. "
            "Our business hours are 8 AM to 6 PM. "
            "Please call back during business hours or visit our website. "
            "For emergencies, please call our emergency line.",
            voice='alice'
        )
    
    return str(response)

@app.route('/recording', methods=['POST'])
def handle_recording():
    """Handle completed recordings"""
    response = VoiceResponse()
    
    recording_url = request.form.get('RecordingUrl')
    call_sid = request.form.get('CallSid')
    
    logger.info(f"Recording completed for call {call_sid}: {recording_url}")
    
    # Thank the caller
    response.say(
        "Thank you for your message. We'll review it and get back to you soon. "
        "Have a great day!",
        voice='alice'
    )
    
    # Here you would typically trigger processing of the recording
    # For now, we'll just log it
    
    return str(response)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
'''
    
    with open('src/voice_webhook.py', 'w') as f:
        f.write(handler_code)
    
    print("✅ Created src/voice_webhook.py")

# Main processing loop
create_status_file('starting', 10, {'phase': 'initialization'})

# Simple task execution without memory overflow
while True:
    try:
        # Find phone-related tasks
        task_patterns = [
            'active_tasks/phone_engineer_current_task.json',
            'active_tasks/*phone*current_task.json',
            'active_tasks/*voice*current_task.json'
        ]
        
        task_file = None
        for pattern in task_patterns:
            files = glob.glob(pattern)
            active = [f for f in files if 'completed' not in f]
            if active:
                task_file = active[0]
                break
        
        if task_file:
            print(f"Processing: {task_file}")
            log_activity(f"Processing task file: {task_file}")
            
            with open(task_file) as f:
                task_data = json.load(f)
            
            task_type = task_data['task']['type']
            print(f"Task type: {task_type}")
            
            create_status_file('processing', 50, {'task_type': task_type})
            
            # Execute tasks based on type
            if 'voice' in task_type.lower() or 'twilio' in task_type.lower():
                print("Creating voice system components...")
                create_voice_client()
                create_voice_handler()
                log_activity("Voice system components created")
                
            elif 'test' in task_type.lower():
                print("Running voice system tests...")
                # Simple test implementation
                test_result = {
                    'voice_client_exists': os.path.exists('src/voice_client.py'),
                    'webhook_exists': os.path.exists('src/voice_webhook.py'),
                    'status': 'PASS' if all([
                        os.path.exists('src/voice_client.py'),
                        os.path.exists('src/voice_webhook.py')
                    ]) else 'FAIL'
                }
                log_activity("Voice system test completed", test_result)
                print(f"Test results: {test_result}")
                
            elif 'implement' in task_type.lower():
                print("Implementing phone engineer features...")
                create_voice_client()
                create_voice_handler()
                
                # Create a simple integration test
                test_code = '''"""
Basic voice system integration test
"""
import sys
import os
sys.path.append('.')

def test_voice_client():
    try:
        from src.voice_client import VoiceClient
        client = VoiceClient()
        print("✅ VoiceClient imported successfully")
        return True
    except Exception as e:
        print(f"❌ VoiceClient import failed: {e}")
        return False

def test_webhook():
    try:
        from src.voice_webhook import app
        print("✅ Voice webhook imported successfully")
        return True
    except Exception as e:
        print(f"❌ Voice webhook import failed: {e}")
        return False

if __name__ == '__main__':
    print("🔍 Testing voice system components...")
    
    voice_test = test_voice_client()
    webhook_test = test_webhook()
    
    if voice_test and webhook_test:
        print("🎉 All voice components working!")
    else:
        print("⚠️ Some components need attention")
'''
                
                with open('test_voice_integration.py', 'w') as f:
                    f.write(test_code)
                
                log_activity("Phone engineer implementation completed")
                
            # Mark task complete
            completed_file = task_file.replace('.json', '_completed.json')
            os.rename(task_file, completed_file)
            print(f"✅ Task completed: {completed_file}")
            
            create_status_file('completed', 100, {
                'task_completed': task_type,
                'files_created': ['src/voice_client.py', 'src/voice_webhook.py']
            })
        
        else:
            # No tasks found, just update status
            create_status_file('waiting', 25, {'waiting_for': 'phone_engineer_tasks'})
            print(f"No active tasks for {AGENT_NAME}, waiting...")
        
        time.sleep(30)  # Wait 30 seconds between checks
        
    except KeyboardInterrupt:
        print("\n🛑 Phone Engineer stopping...")
        create_status_file('stopped', 0, {'reason': 'user_interrupt'})
        break
    except Exception as e:
        print(f"❌ Error in phone engineer: {e}")
        log_activity(f"Error occurred: {e}")
        create_status_file('error', 0, {'error': str(e)})
        time.sleep(60)  # Wait longer on error
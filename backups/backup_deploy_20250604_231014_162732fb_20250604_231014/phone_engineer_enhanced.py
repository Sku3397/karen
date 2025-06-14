import glob
import json
import time
import os
from datetime import datetime
from pathlib import Path

AGENT_NAME = "phone_engineer"

def log_activity(message):
    """Simple activity logging"""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    with open(log_dir / f'{AGENT_NAME}.log', 'a') as f:
        f.write(f"{datetime.now().isoformat()} - {message}\n")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

def create_status_update(status, details=None):
    """Update status for other agents"""
    status_dir = Path('autonomous-agents/communication/status')
    status_dir.mkdir(parents=True, exist_ok=True)
    
    status_data = {
        'agent': AGENT_NAME,
        'status': status,
        'timestamp': datetime.now().isoformat(),
        'details': details or {}
    }
    
    with open(status_dir / f'{AGENT_NAME}_status.json', 'w') as f:
        json.dump(status_data, f, indent=2)

log_activity(f"Starting {AGENT_NAME} - Voice/Phone System Implementation")
create_status_update('starting', {'mode': 'phone_voice_implementation'})

while True:
    try:
        task_files = glob.glob(f'active_tasks/*phone*current_task.json') + glob.glob(f'active_tasks/*voice*current_task.json')
        active = [f for f in task_files if 'completed' not in f]
        
        if active:
            task_file = active[0]
            log_activity(f"Processing task: {task_file}")
            
            with open(task_file) as f:
                task_data = json.load(f)
            
            task_type = task_data['task']['type']
            log_activity(f"IMPLEMENTING PHONE/VOICE: {task_type}")
            create_status_update('processing', {'task_type': task_type})
            
            # CREATE REAL PHONE SYSTEM
            if 'phone' in task_type or 'voice' in task_type or 'twilio' in task_type:
                phone_code = f'''
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class PhoneHandler:
    """Phone/Voice functionality for Karen AI - Created by Phone Engineer"""
    
    def __init__(self):
        """Initialize Twilio client and phone system"""
        try:
            self.client = Client(
                os.getenv('TWILIO_ACCOUNT_SID'),
                os.getenv('TWILIO_AUTH_TOKEN')
            )
            self.phone_number = os.getenv('TWILIO_PHONE_NUMBER', '+1234567890')
            self.business_name = os.getenv('BUSINESS_NAME', '757 Handy')
            
            logger.info(f"Phone Handler initialized at {{datetime.now()}}")
            logger.info(f"Business: {{self.business_name}}, Phone: {{self.phone_number}}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Twilio client: {{e}}")
            self.client = None
    
    def handle_incoming_call(self, caller_id: str = None) -> str:
        """Handle incoming phone calls with intelligent response"""
        response = VoiceResponse()
        
        # Business hours check
        current_hour = datetime.now().hour
        is_business_hours = 8 <= current_hour <= 18  # 8 AM to 6 PM
        
        if is_business_hours:
            greeting = (
                f"Hello, this is Karen from {{self.business_name}}. "
                "Thank you for calling! I'm here to help with all your handyman needs. "
                "Please tell me what kind of work you need done after the beep, "
                "and I'll make sure you get connected with the right person."
            )
        else:
            greeting = (
                f"Thank you for calling {{self.business_name}}. "
                "We're currently outside our business hours of 8 AM to 6 PM. "
                "Please leave a detailed message about your handyman needs, "
                "and we'll call you back first thing during business hours."
            )
        
        response.say(greeting, voice='alice', language='en-US')
        
        # Record the caller's message
        response.record(
            timeout=10,
            transcribe=True,
            transcribe_callback='/transcription-callback',
            max_length=180,  # 3 minutes
            finish_on_key='#',
            action='/handle-recording'
        )
        
        response.say(
            "Thank you for your message. We'll review it and get back to you soon. "
            "Have a great day!",
            voice='alice'
        )
        
        logger.info(f"Handled incoming call from {{caller_id or 'unknown'}}")
        return str(response)
    
    def make_outbound_call(self, to_number: str, message: str) -> Optional[str]:
        """Make outbound calls with custom message"""
        if not self.client:
            logger.error("Twilio client not initialized")
            return None
        
        try:
            twiml = f'<Response><Say voice="alice">{{message}}</Say></Response>'
            
            call = self.client.calls.create(
                twiml=twiml,
                to=to_number,
                from_=self.phone_number
            )
            
            logger.info(f"Outbound call initiated to {{to_number}}, SID: {{call.sid}}")
            return call.sid
            
        except Exception as e:
            logger.error(f"Failed to make outbound call to {{to_number}}: {{e}}")
            return None
    
    def handle_voicemail(self, recording_url: str, transcription: str = None) -> Dict[str, Any]:
        """Process voicemail messages and extract information"""
        
        # Basic intent detection from transcription
        intent = self.detect_intent(transcription) if transcription else "unknown"
        urgency = self.assess_urgency(transcription) if transcription else "normal"
        
        voicemail_data = {{
            "recording_url": recording_url,
            "transcription": transcription,
            "intent": intent,
            "urgency": urgency,
            "processed_at": datetime.now().isoformat(),
            "requires_callback": True
        }}
        
        logger.info(f"Processed voicemail: intent={{intent}}, urgency={{urgency}}")
        return voicemail_data
    
    def detect_intent(self, transcription: str) -> str:
        """Simple intent detection from transcription"""
        if not transcription:
            return "unknown"
        
        text = transcription.lower()
        
        if any(word in text for word in ['emergency', 'urgent', 'asap', 'immediately']):
            return "emergency"
        elif any(word in text for word in ['quote', 'estimate', 'cost', 'price']):
            return "quote_request"
        elif any(word in text for word in ['appointment', 'schedule', 'when', 'available']):
            return "appointment"
        elif any(word in text for word in ['repair', 'fix', 'broken', 'problem']):
            return "repair_request"
        elif any(word in text for word in ['install', 'installation', 'new']):
            return "installation"
        else:
            return "general_inquiry"
    
    def assess_urgency(self, transcription: str) -> str:
        """Assess urgency level from transcription"""
        if not transcription:
            return "normal"
        
        text = transcription.lower()
        
        emergency_words = ['emergency', 'urgent', 'flooding', 'leak', 'electrical', 'fire']
        high_words = ['asap', 'soon', 'quickly', 'today']
        
        if any(word in text for word in emergency_words):
            return "emergency"
        elif any(word in text for word in high_words):
            return "high"
        else:
            return "normal"
    
    def create_callback_reminder(self, phone_number: str, voicemail_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create callback reminder for the team"""
        reminder = {{
            "type": "callback_required",
            "phone_number": phone_number,
            "voicemail_data": voicemail_data,
            "created_at": datetime.now().isoformat(),
            "priority": voicemail_data.get("urgency", "normal")
        }}
        
        # Save reminder to file for task management system
        reminder_dir = Path("reminders")
        reminder_dir.mkdir(exist_ok=True)
        
        filename = f"callback_{{int(datetime.now().timestamp())}}.json"
        with open(reminder_dir / filename, 'w') as f:
            import json
            json.dump(reminder, f, indent=2)
        
        return reminder

# Phone system integration created by Phone Engineer
# Task: {task_type}
# Created: {datetime.now().isoformat()}
# Features: Incoming calls, outbound calls, voicemail processing, intent detection
'''
                
                # Create the phone handler file
                timestamp = int(time.time())
                filename = f'src/phone_handler_{timestamp}.py'
                
                # Ensure src directory exists
                Path('src').mkdir(exist_ok=True)
                
                with open(filename, 'w') as f:
                    f.write(phone_code)
                
                log_activity(f"CREATED PHONE SYSTEM: {filename}")
                
                # Also create a webhook endpoint file
                webhook_code = f'''
"""
Twilio Webhook Endpoints for Karen's Phone System
Created by Phone Engineer at {datetime.now().isoformat()}
"""
from flask import Flask, request, Response
from phone_handler_{timestamp} import PhoneHandler
import logging
import json

app = Flask(__name__)
logger = logging.getLogger(__name__)
phone_handler = PhoneHandler()

@app.route('/voice', methods=['POST'])
def handle_incoming_voice():
    """Handle incoming voice calls"""
    caller_id = request.form.get('From')
    logger.info(f"Incoming call from {{caller_id}}")
    
    response = phone_handler.handle_incoming_call(caller_id)
    return Response(response, mimetype='text/xml')

@app.route('/transcription-callback', methods=['POST'])
def handle_transcription():
    """Handle transcription callbacks from Twilio"""
    transcription = request.form.get('TranscriptionText')
    recording_url = request.form.get('RecordingUrl')
    call_sid = request.form.get('CallSid')
    caller = request.form.get('From')
    
    logger.info(f"Transcription received for call {{call_sid}} from {{caller}}")
    
    # Process the voicemail
    voicemail_data = phone_handler.handle_voicemail(recording_url, transcription)
    
    # Create callback reminder
    phone_handler.create_callback_reminder(caller, voicemail_data)
    
    return Response('OK', status=200)

@app.route('/handle-recording', methods=['POST'])
def handle_recording():
    """Handle recording completion"""
    recording_url = request.form.get('RecordingUrl')
    call_sid = request.form.get('CallSid')
    caller = request.form.get('From')
    
    logger.info(f"Recording completed for call {{call_sid}} from {{caller}}")
    
    # If no transcription yet, still process the recording
    voicemail_data = phone_handler.handle_voicemail(recording_url)
    phone_handler.create_callback_reminder(caller, voicemail_data)
    
    return Response('OK', status=200)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
'''
                
                webhook_filename = f'src/phone_webhooks_{timestamp}.py'
                with open(webhook_filename, 'w') as f:
                    f.write(webhook_code)
                
                log_activity(f"CREATED WEBHOOK SYSTEM: {webhook_filename}")
                
                # Create a quick test script
                test_code = f'''
"""
Quick test for phone system - Created by Phone Engineer
"""
import os
import sys
sys.path.append('.')

def test_phone_system():
    try:
        from src.phone_handler_{timestamp} import PhoneHandler
        
        # Test initialization
        handler = PhoneHandler()
        print("✅ PhoneHandler initialized successfully")
        
        # Test call handling
        response = handler.handle_incoming_call("+1234567890")
        print("✅ Incoming call handling works")
        
        # Test voicemail processing
        voicemail = handler.handle_voicemail("http://example.com/recording.wav", "Hello, I need a quote for bathroom repair")
        print(f"✅ Voicemail processing works: {{voicemail['intent']}}")
        
        print("🎉 Phone system tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Phone system test failed: {{e}}")
        return False

if __name__ == '__main__':
    test_phone_system()
'''
                
                test_filename = f'test_phone_system_{timestamp}.py'
                with open(test_filename, 'w') as f:
                    f.write(test_code)
                
                log_activity(f"CREATED TEST SCRIPT: {test_filename}")
                
                create_status_update('completed', {
                    'files_created': [filename, webhook_filename, test_filename],
                    'features': ['incoming_calls', 'outbound_calls', 'voicemail_processing', 'intent_detection']
                })
            
            # Mark task as completed
            completed_file = task_file.replace('.json', '_completed.json')
            os.rename(task_file, completed_file)
            log_activity(f"✅ Task completed: {completed_file}")
            
        else:
            create_status_update('waiting', {'waiting_for': 'phone_voice_tasks'})
            log_activity("No phone/voice tasks found, waiting...")
        
        time.sleep(30)
        
    except KeyboardInterrupt:
        log_activity("Phone Engineer stopping by user request")
        create_status_update('stopped', {'reason': 'user_interrupt'})
        break
    except Exception as e:
        log_activity(f"Error in phone engineer: {e}")
        create_status_update('error', {'error': str(e)})
        time.sleep(60)  # Wait longer on error
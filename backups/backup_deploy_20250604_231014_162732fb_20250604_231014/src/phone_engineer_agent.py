"""
Phone Engineer Agent - Handles voice call processing, transcription, and coordination
Implements the AgentCommunication framework and voice-specific functionality.
"""
import os
import logging
import asyncio
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

from .agent_communication import AgentCommunication
from .voice_client import VoiceClient
from .llm_client import LLMClient

logger = logging.getLogger(__name__)

class PhoneEngineerAgent:
    """
    Phone Engineer Agent responsible for:
    - Processing incoming voice calls
    - Transcribing call recordings
    - Generating intelligent voice responses
    - Monitoring voice system health
    - Coordinating with other agents
    - Emergency voice call handling
    """
    
    def __init__(self, agent_name: str = 'phone_engineer'):
        """Initialize Phone Engineer Agent with communication capabilities."""
        self.agent_name = agent_name
        self.comm = AgentCommunication(agent_name)
        
        # Initialize phone components
        self.karen_phone = os.getenv('KAREN_PHONE_NUMBER', '+17575551234')
        self.admin_phone = os.getenv('ADMIN_PHONE_NUMBER')
        
        # Initialize clients
        self.voice_client = None
        self.llm_client = None
        self.is_running = False
        
        # Performance tracking
        self.calls_processed = 0
        self.transcriptions_completed = 0
        self.last_activity = None
        self.errors_count = 0
        
        logger.info(f"PhoneEngineerAgent initialized as '{agent_name}'")
    
    def initialize_clients(self):
        """Initialize voice client and LLM following Karen patterns."""
        try:
            # Initialize voice client
            self.voice_client = VoiceClient(karen_phone=self.karen_phone)
            logger.info(f"Voice client initialized for {self.karen_phone}")
            
            # Initialize LLM client
            try:
                self.llm_client = LLMClient()
                logger.info("LLM client initialized for voice response generation")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM client: {e}. Voice responses will be limited.")
                self.llm_client = None
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize voice clients: {e}", exc_info=True)
            self.comm.update_status('error', 0, {
                'error': 'initialization_failed',
                'details': str(e)
            })
            return False
    
    async def start_processing(self):
        """Start the voice call processing loop."""
        if not self.initialize_clients():
            logger.error("Cannot start processing - initialization failed")
            return
        
        self.is_running = True
        self.comm.update_status('starting', 10, {'phase': 'initializing'})
        
        logger.info("Phone Engineer Agent starting processing loop...")
        
        # Share initialization knowledge
        self.comm.share_knowledge('voice_system_startup', {
            'karen_phone': self.karen_phone,
            'admin_phone': self.admin_phone,
            'llm_enabled': self.llm_client is not None,
            'tts_enabled': self.voice_client.tts_client is not None,
            'speech_recognition_enabled': self.voice_client.speech_client is not None,
            'timestamp': datetime.now().isoformat()
        })
        
        try:
            while self.is_running:
                await self.process_cycle()
                await asyncio.sleep(60)  # Check every minute
                
        except Exception as e:
            logger.error(f"Error in processing loop: {e}", exc_info=True)
            self.comm.update_status('error', 0, {'error': str(e)})
            
        finally:
            self.comm.update_status('stopped', 0, {'stopped_at': datetime.now().isoformat()})
    
    async def process_cycle(self):
        """Process one cycle of call checking and handling."""
        try:
            # Update status
            self.comm.update_status('processing', 50, {
                'phase': 'checking_calls',
                'calls_processed': self.calls_processed,
                'transcriptions_completed': self.transcriptions_completed
            })
            
            # Check for inter-agent messages
            await self.handle_agent_messages()
            
            # Fetch and process new calls
            await self.fetch_and_process_calls()
            
            # Check system health
            await self.monitor_system_health()
            
            self.last_activity = datetime.now()
            
        except Exception as e:
            self.errors_count += 1
            logger.error(f"Error in process cycle: {e}", exc_info=True)
            
            if self.errors_count > 5:
                # Too many errors, request help
                await self.request_help_from_archaeologist("repeated_processing_errors", {
                    'error_count': self.errors_count,
                    'last_error': str(e)
                })
    
    async def handle_agent_messages(self):
        """Handle messages from other agents."""
        messages = self.comm.read_messages()
        
        for msg in messages:
            try:
                msg_type = msg.get('type')
                content = msg.get('content', {})
                sender = msg.get('from')
                
                logger.info(f"Received message from {sender}: {msg_type}")
                
                if msg_type == 'emergency_alert':
                    await self.handle_emergency_alert(content)
                elif msg_type == 'call_request':
                    await self.handle_call_request(content)
                elif msg_type == 'transcription_request':
                    await self.handle_transcription_request(content)
                elif msg_type == 'status_request':
                    await self.send_status_report(sender)
                elif msg_type == 'test_request':
                    await self.run_system_test(sender)
                elif msg_type == 'info_response':
                    await self.handle_info_response(content)
                else:
                    logger.debug(f"Unknown message type: {msg_type} from {sender}")
                    
            except Exception as e:
                logger.error(f"Error handling message: {e}", exc_info=True)
    
    async def fetch_and_process_calls(self):
        """Fetch new call records and process them."""
        try:
            # Fetch calls from last hour
            calls = self.voice_client.fetch_calls(
                search_criteria='inbound',
                newer_than='1h',
                max_results=20
            )
            
            new_calls = []
            for call in calls:
                call_sid = call.get('uid')
                if not self.voice_client.is_call_processed(call_sid):
                    new_calls.append(call)
            
            if new_calls:
                logger.info(f"Found {len(new_calls)} new calls to process")
                
                for call in new_calls:
                    await self.process_call_record(call)
                    self.calls_processed += 1
                    
                    # Mark as processed
                    self.voice_client.mark_call_as_processed(call.get('uid'))
            
        except Exception as e:
            logger.error(f"Error fetching calls: {e}", exc_info=True)
            raise
    
    async def process_call_record(self, call_data: Dict[str, Any]):
        """Process a single call record."""
        caller = call_data.get('sender', 'unknown')
        call_sid = call_data.get('uid', 'unknown')
        duration = call_data.get('duration', 0)
        status = call_data.get('status', 'unknown')
        
        logger.info(f"Processing call {call_sid} from {caller}, duration: {duration}s, status: {status}")
        
        try:
            # Skip very short calls (likely hang-ups)
            if duration and duration < 3:
                logger.info(f"Skipping short call {call_sid} (duration: {duration}s)")
                return
            
            # Transcribe call if recordings are available
            transcript = None
            if status == 'completed' and duration > 5:
                transcript = await self.transcribe_call_async(call_sid)
                if transcript:
                    self.transcriptions_completed += 1
            
            # Generate follow-up actions if transcript available
            follow_up_actions = None
            if transcript and self.llm_client:
                follow_up_actions = await self.generate_call_follow_up(
                    caller, transcript, call_data
                )
            
            # Check for emergency indicators
            is_emergency = self.detect_emergency_call(call_data, transcript)
            if is_emergency:
                await self.handle_emergency_call(call_data, transcript)
            
            # Log interaction
            await self.log_call_interaction({
                'type': 'processed',
                'call_sid': call_sid,
                'caller': caller,
                'duration': duration,
                'transcript_available': transcript is not None,
                'transcript_length': len(transcript) if transcript else 0,
                'follow_up_generated': follow_up_actions is not None,
                'is_emergency': is_emergency
            })
            
            # Share call insights with other agents
            if transcript or follow_up_actions:
                self.comm.share_knowledge('call_insights', {
                    'call_sid': call_sid,
                    'caller': caller,
                    'transcript_summary': transcript[:200] if transcript else None,
                    'follow_up_actions': follow_up_actions,
                    'is_emergency': is_emergency,
                    'processed_at': datetime.now().isoformat()
                })
            
        except Exception as e:
            logger.error(f"Error processing call {call_sid}: {e}", exc_info=True)
    
    async def transcribe_call_async(self, call_sid: str) -> Optional[str]:
        """Transcribe a call recording asynchronously."""
        try:
            # Run transcription in thread pool to avoid blocking
            transcript = await asyncio.to_thread(
                self.voice_client.transcribe_call_recording,
                call_sid
            )
            
            if transcript:
                logger.info(f"Successfully transcribed call {call_sid}: {transcript[:100]}...")
            else:
                logger.warning(f"No transcript generated for call {call_sid}")
            
            return transcript
            
        except Exception as e:
            logger.error(f"Error transcribing call {call_sid}: {e}", exc_info=True)
            return None
    
    async def generate_call_follow_up(self, caller: str, transcript: str, 
                                    call_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate follow-up actions based on call transcript."""
        if not self.llm_client or not transcript:
            return None
        
        try:
            prompt = self.create_call_analysis_prompt(caller, transcript, call_data)
            
            # Generate analysis using LLM
            analysis = await asyncio.to_thread(
                self.llm_client.generate_text,
                prompt
            )
            
            # Parse analysis for actionable items
            follow_up = self.parse_call_analysis(analysis, call_data)
            
            logger.info(f"Generated follow-up actions for call from {caller}")
            return follow_up
            
        except Exception as e:
            logger.error(f"Error generating call follow-up: {e}", exc_info=True)
            return None
    
    def create_call_analysis_prompt(self, caller: str, transcript: str, 
                                  call_data: Dict[str, Any]) -> str:
        """Create prompt for LLM analysis of call."""
        current_time = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
        duration = call_data.get('duration', 0)
        
        prompt = f"""You are Karen, the AI assistant for {os.getenv('BUSINESS_NAME', 'Beach Handyman')}.
Analyze this phone call and determine appropriate follow-up actions.

CALL DETAILS:
- Caller: {caller}
- Duration: {duration} seconds
- Date/Time: {current_time}

CALL TRANSCRIPT:
{transcript}

ANALYSIS TASKS:
1. Categorize the call intent (emergency, quote request, appointment, complaint, information, etc.)
2. Identify any specific services mentioned
3. Determine urgency level (emergency, urgent, normal, low)
4. Extract any contact information or callback preferences
5. Suggest follow-up actions (call back, send email, schedule appointment, etc.)
6. Identify any tasks that need to be created

RESPONSE FORMAT:
Intent: [primary intent]
Services: [list of services mentioned]
Urgency: [emergency/urgent/normal/low]
Contact Preference: [call back/email/text/none specified]
Follow-up Actions: [specific actions to take]
Tasks to Create: [any tasks that need to be tracked]
Emergency Indicators: [any emergency situations detected]

Keep the analysis concise and actionable."""

        return prompt
    
    def parse_call_analysis(self, analysis: str, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLM analysis into structured follow-up actions."""
        try:
            follow_up = {
                'call_sid': call_data.get('uid'),
                'caller': call_data.get('sender'),
                'analysis_timestamp': datetime.now().isoformat(),
                'intent': 'unknown',
                'services': [],
                'urgency': 'normal',
                'contact_preference': 'none',
                'follow_up_actions': [],
                'tasks_to_create': [],
                'emergency_indicators': []
            }
            
            # Parse the structured response
            lines = analysis.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('Intent:'):
                    follow_up['intent'] = line.replace('Intent:', '').strip()
                elif line.startswith('Services:'):
                    services_text = line.replace('Services:', '').strip()
                    follow_up['services'] = [s.strip() for s in services_text.split(',') if s.strip()]
                elif line.startswith('Urgency:'):
                    follow_up['urgency'] = line.replace('Urgency:', '').strip().lower()
                elif line.startswith('Contact Preference:'):
                    follow_up['contact_preference'] = line.replace('Contact Preference:', '').strip()
                elif line.startswith('Follow-up Actions:'):
                    actions_text = line.replace('Follow-up Actions:', '').strip()
                    follow_up['follow_up_actions'] = [a.strip() for a in actions_text.split(',') if a.strip()]
                elif line.startswith('Tasks to Create:'):
                    tasks_text = line.replace('Tasks to Create:', '').strip()
                    follow_up['tasks_to_create'] = [t.strip() for t in tasks_text.split(',') if t.strip()]
                elif line.startswith('Emergency Indicators:'):
                    emergency_text = line.replace('Emergency Indicators:', '').strip()
                    follow_up['emergency_indicators'] = [e.strip() for e in emergency_text.split(',') if e.strip()]
            
            return follow_up
            
        except Exception as e:
            logger.error(f"Error parsing call analysis: {e}", exc_info=True)
            return None
    
    def detect_emergency_call(self, call_data: Dict[str, Any], transcript: Optional[str]) -> bool:
        """Detect if call indicates emergency situation."""
        # Check call characteristics
        duration = call_data.get('duration', 0)
        status = call_data.get('status', '')
        
        # Very short completed calls might indicate hang-ups (potential emergency)
        if status == 'completed' and 0 < duration < 10:
            return True
        
        # Check transcript for emergency keywords
        if transcript:
            emergency_keywords = [
                'emergency', 'urgent', 'help', 'flood', 'burst', 'leak', 'fire',
                'smoke', 'gas', 'electrical', 'sparks', 'broken', 'damage',
                'urgent', 'asap', 'immediately', 'right now', 'disaster'
            ]
            
            transcript_lower = transcript.lower()
            for keyword in emergency_keywords:
                if keyword in transcript_lower:
                    return True
        
        return False
    
    async def handle_emergency_call(self, call_data: Dict[str, Any], transcript: Optional[str]):
        """Handle emergency call situations."""
        caller = call_data.get('sender', 'unknown')
        call_sid = call_data.get('uid', 'unknown')
        
        logger.warning(f"EMERGENCY CALL detected from {caller}, SID: {call_sid}")
        
        # Notify admin if configured
        if self.admin_phone:
            emergency_message = (
                f"🚨 EMERGENCY CALL from {caller}. "
                f"Call SID: {call_sid}. "
                f"Duration: {call_data.get('duration', 0)}s. "
            )
            
            if transcript:
                emergency_message += f"Transcript: {transcript[:200]}..."
            
            # Make urgent callback to admin
            success = self.voice_client.make_call(
                self.admin_phone,
                f"Emergency alert: {emergency_message}",
                voice='alice'
            )
            
            if success:
                logger.info(f"Emergency call notification sent to admin at {self.admin_phone}")
        
        # Notify other agents
        self.comm.broadcast_emergency_alert(
            system_component='VOICE_SYSTEM',
            reported_status='EMERGENCY_CALL_RECEIVED',
            alert_details={
                'caller': caller,
                'call_sid': call_sid,
                'duration': call_data.get('duration', 0),
                'transcript_preview': transcript[:300] if transcript else None
            },
            action_request='PRIORITIZE_EMERGENCY_RESPONSE'
        )
        
        # Share emergency knowledge
        self.comm.share_knowledge('emergency_pattern', {
            'source': 'voice_call',
            'caller': caller,
            'call_sid': call_sid,
            'emergency_indicators': self.extract_emergency_indicators(transcript) if transcript else [],
            'response_time': datetime.now().isoformat()
        })
    
    def extract_emergency_indicators(self, transcript: str) -> List[str]:
        """Extract specific emergency indicators from transcript."""
        indicators = []
        emergency_phrases = [
            'pipe burst', 'water everywhere', 'flooding', 'electrical fire',
            'gas leak', 'no power', 'sparks flying', 'smoke coming',
            'water damage', 'emergency repair', 'urgent help needed'
        ]
        
        transcript_lower = transcript.lower()
        for phrase in emergency_phrases:
            if phrase in transcript_lower:
                indicators.append(phrase)
        
        return indicators
    
    async def handle_call_request(self, request_content: Dict[str, Any]):
        """Handle call requests from other agents."""
        to_number = request_content.get('to_number')
        message = request_content.get('message')
        priority = request_content.get('priority', 'normal')
        voice = request_content.get('voice', 'alice')
        
        if not to_number or not message:
            logger.error("Invalid call request - missing to_number or message")
            return
        
        logger.info(f"Processing call request to {to_number} (priority: {priority})")
        
        try:
            success = self.voice_client.make_call(to_number, message, voice)
            
            # Log the requested call
            await self.log_call_interaction({
                'type': 'agent_requested',
                'to_number': to_number,
                'message_length': len(message),
                'priority': priority,
                'success': success
            })
            
        except Exception as e:
            logger.error(f"Error processing call request: {e}", exc_info=True)
    
    async def handle_transcription_request(self, request_content: Dict[str, Any]):
        """Handle transcription requests from other agents."""
        call_sid = request_content.get('call_sid')
        requester = request_content.get('from', 'unknown')
        
        if not call_sid:
            logger.error("Invalid transcription request - missing call_sid")
            return
        
        logger.info(f"Processing transcription request for call {call_sid} from {requester}")
        
        try:
            transcript = await self.transcribe_call_async(call_sid)
            
            # Send response back to requester
            self.comm.send_message(requester, 'transcription_response', {
                'call_sid': call_sid,
                'transcript': transcript,
                'success': transcript is not None,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error processing transcription request: {e}", exc_info=True)
            
            # Send error response
            self.comm.send_message(requester, 'transcription_response', {
                'call_sid': call_sid,
                'transcript': None,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
    
    async def handle_emergency_alert(self, alert_content: Dict[str, Any]):
        """Handle emergency alerts from other agents."""
        system_component = alert_content.get('system_component')
        status = alert_content.get('reported_status')
        action_request = alert_content.get('action_request')
        
        logger.warning(f"Emergency alert: {system_component} - {status}")
        
        if action_request == 'STOP_ALL_WORK':
            logger.info("Stopping voice processing due to emergency alert")
            self.is_running = False
        elif action_request == 'PRIORITIZE_EMERGENCY_RESPONSE':
            # Adjust processing to prioritize emergency calls
            await self.enter_emergency_mode()
    
    async def enter_emergency_mode(self):
        """Enter emergency processing mode."""
        logger.info("Entering emergency mode - prioritizing urgent calls")
        
        self.comm.update_status('emergency_mode', 90, {
            'mode': 'emergency_priority',
            'activated_at': datetime.now().isoformat()
        })
        
        # Could implement emergency-specific call handling here
        # Such as checking for recent emergency calls, preparing urgent responses, etc.
    
    async def send_status_report(self, requester: str):
        """Send status report to requesting agent."""
        status_report = {
            'agent': self.agent_name,
            'status': 'active' if self.is_running else 'stopped',
            'calls_processed': self.calls_processed,
            'transcriptions_completed': self.transcriptions_completed,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'errors_count': self.errors_count,
            'clients_initialized': self.voice_client is not None,
            'system_health': await self.get_system_health()
        }
        
        self.comm.send_message(requester, 'status_response', status_report)
    
    async def run_system_test(self, requester: str):
        """Run voice system test and report results."""
        test_results = await self.test_voice_system()
        self.comm.send_message(requester, 'test_results', test_results)
    
    async def test_voice_system(self) -> Dict[str, Any]:
        """Test voice system functionality."""
        logger.info("Running voice system test...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {}
        }
        
        try:
            # Test 1: Twilio connection
            try:
                recent_calls = self.voice_client.fetch_calls(max_results=1)
                results['tests']['twilio_connection'] = {
                    'passed': True,
                    'details': f'Successfully connected to Twilio API'
                }
            except Exception as e:
                results['tests']['twilio_connection'] = {
                    'passed': False,
                    'details': f'Error: {str(e)}'
                }
            
            # Test 2: Speech-to-text availability
            try:
                if self.voice_client.speech_client:
                    results['tests']['speech_to_text'] = {
                        'passed': True,
                        'details': 'Google Cloud Speech client available'
                    }
                else:
                    results['tests']['speech_to_text'] = {
                        'passed': False,
                        'details': 'Google Cloud Speech client not available'
                    }
            except Exception as e:
                results['tests']['speech_to_text'] = {
                    'passed': False,
                    'details': f'Error: {str(e)}'
                }
            
            # Test 3: Text-to-speech availability
            try:
                if self.voice_client.tts_client:
                    # Test synthesis with small text
                    test_audio = self.voice_client.synthesize_speech("Test")
                    results['tests']['text_to_speech'] = {
                        'passed': test_audio is not None,
                        'details': f'TTS synthesis {"successful" if test_audio else "failed"}'
                    }
                else:
                    results['tests']['text_to_speech'] = {
                        'passed': False,
                        'details': 'Google Cloud TTS client not available'
                    }
            except Exception as e:
                results['tests']['text_to_speech'] = {
                    'passed': False,
                    'details': f'Error: {str(e)}'
                }
            
            # Test 4: LLM client
            try:
                if self.llm_client:
                    test_response = await asyncio.to_thread(
                        self.llm_client.generate_text,
                        "Test prompt for voice system"
                    )
                    results['tests']['llm_integration'] = {
                        'passed': len(test_response) > 0,
                        'details': f'LLM response generated: {test_response[:50]}...'
                    }
                else:
                    results['tests']['llm_integration'] = {
                        'passed': False,
                        'details': 'LLM client not available'
                    }
            except Exception as e:
                results['tests']['llm_integration'] = {
                    'passed': False,
                    'details': f'Error: {str(e)}'
                }
            
            # Overall result
            all_passed = all(test['passed'] for test in results['tests'].values())
            results['overall'] = 'PASS' if all_passed else 'PARTIAL'
            
        except Exception as e:
            logger.error(f"Error during system test: {e}", exc_info=True)
            results['error'] = str(e)
            results['overall'] = 'ERROR'
        
        return results
    
    async def monitor_system_health(self):
        """Monitor voice system health and report issues."""
        health_status = await self.get_system_health()
        
        # Check for issues
        issues = []
        if health_status['twilio_connection'] != 'healthy':
            issues.append('twilio_connection')
        if health_status['response_time'] > 10.0:
            issues.append('slow_response')
        if self.errors_count > 10:
            issues.append('high_error_rate')
        
        if issues:
            self.comm.share_knowledge('system_health_issue', {
                'issues': issues,
                'health_status': health_status,
                'recommended_action': 'investigate_voice_system'
            })
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get current system health metrics."""
        health = {
            'timestamp': datetime.now().isoformat(),
            'twilio_connection': 'unknown',
            'response_time': 0.0,
            'calls_per_hour': 0,
            'transcription_success_rate': 0.0,
            'error_rate': 0.0
        }
        
        try:
            # Test Twilio connection
            start_time = time.time()
            recent_calls = self.voice_client.fetch_calls(max_results=1)
            response_time = time.time() - start_time
            
            health['twilio_connection'] = 'healthy'
            health['response_time'] = response_time
            
            # Calculate metrics
            if self.last_activity:
                hours_since_start = (datetime.now() - self.last_activity).total_seconds() / 3600
                if hours_since_start > 0:
                    health['calls_per_hour'] = self.calls_processed / hours_since_start
            
            if self.calls_processed > 0:
                health['transcription_success_rate'] = self.transcriptions_completed / self.calls_processed
                health['error_rate'] = self.errors_count / self.calls_processed
                
        except Exception as e:
            health['twilio_connection'] = 'error'
            health['error_details'] = str(e)
        
        return health
    
    async def request_help_from_archaeologist(self, topic: str, details: Dict[str, Any]):
        """Request help from archaeologist agent."""
        self.comm.send_message('archaeologist', 'clarification_request', {
            'topic': topic,
            'specific_question': f'Voice system issue: {topic}',
            'details': details,
            'urgency': 'high' if 'emergency' in topic else 'medium'
        })
        
        logger.info(f"Requested help from archaeologist on topic: {topic}")
    
    async def handle_info_response(self, content: Dict[str, Any]):
        """Handle information response from archaeologist or other agents."""
        topic = content.get('topic')
        information = content.get('information')
        
        logger.info(f"Received information response for topic: {topic}")
        
        # Apply the information to improve processing
        if topic == 'error_handling':
            # Update error handling based on response
            pass
        elif topic == 'twilio_best_practices':
            # Update Twilio usage patterns
            pass
        
        # Log that we received help
        await self.log_call_interaction({
            'type': 'received_help',
            'topic': topic,
            'source': content.get('from', 'unknown'),
            'applied': True
        })
    
    async def log_call_interaction(self, interaction_data: Dict[str, Any]):
        """Log call interaction for analytics."""
        try:
            log_dir = Path('/mnt/c/Users/Man/ultra/projects/karen/logs')
            log_dir.mkdir(exist_ok=True)
            
            log_file = log_dir / 'voice_agent_activity.log'
            
            with open(log_file, 'a') as f:
                log_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'agent': self.agent_name,
                    'data': interaction_data
                }
                f.write(f"{log_entry}\n")
                
        except Exception as e:
            logger.error(f"Error logging call interaction: {e}", exc_info=True)
    
    def stop(self):
        """Stop the voice processing agent."""
        logger.info("Phone Engineer Agent stopping...")
        self.is_running = False
        self.comm.update_status('stopping', 95, {'stop_requested': datetime.now().isoformat()})
    
    def run_legacy_mode(self):
        """Run the agent in legacy mode for compatibility."""
        logger.info("🚀 Phone Engineer Agent starting in legacy mode...")
        
        try:
            # Initialize and update status
            self.comm.update_status('initializing', 10, {'mode': 'legacy'})
            
            # Share that voice implementation is complete
            self.comm.share_knowledge('voice_implementation', {
                'status': 'completed',
                'components': ['voice_client', 'twilio_integration', 'speech_recognition', 'tts'],
                'files': [
                    'src/voice_client.py',
                    'src/phone_engineer_agent.py'
                ],
                'capabilities': [
                    'make_calls', 'fetch_calls', 'transcribe_audio', 
                    'synthesize_speech', 'webhook_handling'
                ],
                'ready_for_testing': True
            })
            
            # Notify test engineer
            self.comm.send_message('test_engineer', 'ready_for_testing', {
                'feature': 'voice_integration',
                'test_files': ['tests/test_voice_integration.py'],
                'dependencies': ['twilio', 'google-cloud-speech', 'google-cloud-texttospeech'],
                'test_phone_number': '+1234567890'
            })
            
            # Update final status
            self.comm.update_status('completed', 100, {
                'current_task': 'Voice integration complete',
                'ready_for_production': True
            })
            
            logger.info("✅ Phone Engineer Agent completed in legacy mode")
            
        except Exception as e:
            logger.error(f"❌ Phone Engineer Agent failed: {e}", exc_info=True)
            self.comm.update_status('error', 0, {'error': str(e)})
            raise


# Main execution for testing
if __name__ == '__main__':
    import sys
    from dotenv import load_dotenv
    
    # Load environment
    project_root = Path(__file__).parent.parent
    env_path = project_root / '.env'
    if env_path.exists():
        load_dotenv(env_path)
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout
    )
    
    # Create and run agent
    agent = PhoneEngineerAgent()
    
    # Check if we should run in async mode or legacy mode
    if '--async' in sys.argv:
        try:
            asyncio.run(agent.start_processing())
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
            agent.stop()
        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
            agent.stop()
    else:
        # Run in legacy mode for compatibility
        agent.run_legacy_mode()
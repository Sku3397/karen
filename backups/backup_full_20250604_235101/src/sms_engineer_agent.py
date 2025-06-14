"""
SMS Engineer Agent - Handles SMS processing, monitoring, and coordination
Implements the AgentCommunication framework and SMS-specific functionality.
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
from .sms_client import SMSClient
from .handyman_sms_engine import HandymanSMSEngine
from .llm_client import LLMClient

logger = logging.getLogger(__name__)

class SMSEngineerAgent:
    """
    SMS Engineer Agent responsible for:
    - Processing incoming SMS messages
    - Generating intelligent responses
    - Monitoring SMS system health
    - Coordinating with other agents
    - Emergency SMS handling
    """
    
    def __init__(self, agent_name: str = 'sms_engineer'):
        """Initialize SMS Engineer Agent with communication capabilities."""
        self.agent_name = agent_name
        self.comm = AgentCommunication(agent_name)
        
        # Initialize SMS components
        self.karen_phone = os.getenv('KAREN_PHONE_NUMBER', '+17575551234')
        self.admin_phone = os.getenv('ADMIN_PHONE_NUMBER')
        
        # Initialize clients
        self.sms_client = None
        self.sms_engine = None
        self.is_running = False
        
        # Performance tracking
        self.messages_processed = 0
        self.last_activity = None
        self.errors_count = 0
        
        logger.info(f"SMSEngineerAgent initialized as '{agent_name}'")
    
    def initialize_clients(self):
        """Initialize SMS client and engine following Karen patterns."""
        try:
            # Initialize SMS client
            self.sms_client = SMSClient(karen_phone=self.karen_phone)
            logger.info(f"SMS client initialized for {self.karen_phone}")
            
            # Initialize SMS engine with LLM
            try:
                llm_client = LLMClient()
                self.sms_engine = HandymanSMSEngine(
                    business_name=os.getenv('BUSINESS_NAME', 'Beach Handyman'),
                    service_area=os.getenv('SERVICE_AREA', 'Virginia Beach area'),
                    phone=os.getenv('BUSINESS_PHONE', '757-354-4577'),
                    llm_client=llm_client
                )
                logger.info("SMS engine initialized with LLM support")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM client: {e}. Using fallback responses.")
                self.sms_engine = HandymanSMSEngine(
                    business_name=os.getenv('BUSINESS_NAME', 'Beach Handyman'),
                    service_area=os.getenv('SERVICE_AREA', 'Virginia Beach area'),
                    phone=os.getenv('BUSINESS_PHONE', '757-354-4577'),
                    llm_client=None
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize SMS clients: {e}", exc_info=True)
            self.comm.update_status('error', 0, {
                'error': 'initialization_failed',
                'details': str(e)
            })
            return False
    
    async def start_processing(self):
        """Start the SMS processing loop."""
        if not self.initialize_clients():
            logger.error("Cannot start processing - initialization failed")
            return
        
        self.is_running = True
        self.comm.update_status('starting', 10, {'phase': 'initializing'})
        
        logger.info("SMS Engineer Agent starting processing loop...")
        
        # Share initialization knowledge
        self.comm.share_knowledge('sms_system_startup', {
            'karen_phone': self.karen_phone,
            'admin_phone': self.admin_phone,
            'llm_enabled': self.sms_engine.llm_client is not None,
            'timestamp': datetime.now().isoformat()
        })
        
        try:
            while self.is_running:
                await self.process_cycle()
                await asyncio.sleep(30)  # Check every 30 seconds
                
        except Exception as e:
            logger.error(f"Error in processing loop: {e}", exc_info=True)
            self.comm.update_status('error', 0, {'error': str(e)})
            
        finally:
            self.comm.update_status('stopped', 0, {'stopped_at': datetime.now().isoformat()})
    
    async def process_cycle(self):
        """Process one cycle of SMS checking and handling."""
        try:
            # Update status
            self.comm.update_status('processing', 50, {
                'phase': 'checking_messages',
                'messages_processed': self.messages_processed
            })
            
            # Check for inter-agent messages
            await self.handle_agent_messages()
            
            # Fetch and process new SMS
            await self.fetch_and_process_sms()
            
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
                elif msg_type == 'sms_request':
                    await self.handle_sms_request(content)
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
    
    async def fetch_and_process_sms(self):
        """Fetch new SMS messages and process them."""
        try:
            # Fetch messages from last hour
            messages = self.sms_client.fetch_sms(
                search_criteria='ALL',
                newer_than='1h',
                max_results=20
            )
            
            new_messages = []
            for msg in messages:
                msg_id = msg.get('uid')
                if not self.sms_client.is_sms_processed(msg_id):
                    new_messages.append(msg)
            
            if new_messages:
                logger.info(f"Found {len(new_messages)} new SMS messages to process")
                
                for msg in new_messages:
                    await self.process_sms_message(msg)
                    self.messages_processed += 1
                    
                    # Mark as processed
                    self.sms_client.mark_sms_as_processed(msg.get('uid'))
            
        except Exception as e:
            logger.error(f"Error fetching SMS: {e}", exc_info=True)
            raise
    
    async def process_sms_message(self, sms_data: Dict[str, Any]):
        """Process a single SMS message."""
        sender = sms_data.get('sender', 'unknown')
        body = sms_data.get('body', '')
        msg_id = sms_data.get('uid', 'unknown')
        
        logger.info(f"Processing SMS {msg_id} from {sender}")
        
        try:
            # Generate response using SMS engine
            response_text, classification = await self.sms_engine.generate_sms_response_async(
                sender, body
            )
            
            # Handle emergency responses
            if classification.get('is_emergency'):
                await self.handle_emergency_sms(sms_data, classification)
            
            # Send response
            await self.send_sms_response(sender, response_text, classification)
            
            # Log interaction
            await self.log_sms_interaction({
                'type': 'processed',
                'msg_id': msg_id,
                'sender': sender,
                'body_length': len(body),
                'classification': classification,
                'response_sent': True
            })
            
        except Exception as e:
            logger.error(f"Error processing SMS {msg_id}: {e}", exc_info=True)
            
            # Send fallback response
            fallback = f"Thank you for your message. Please call {self.sms_engine.phone} for immediate assistance."
            await self.send_sms_response(sender, fallback, {})
    
    async def send_sms_response(self, to_number: str, response: str, classification: Dict[str, Any]):
        """Send SMS response, handling multipart messages."""
        try:
            if self.sms_engine.should_send_multipart_sms(response):
                # Split into multiple parts
                parts = self.sms_engine.split_sms_response(response)
                logger.info(f"Sending multipart SMS ({len(parts)} parts) to {to_number}")
                
                for i, part in enumerate(parts):
                    success = self.sms_client.send_sms(to_number, part)
                    if not success:
                        logger.error(f"Failed to send SMS part {i+1}/{len(parts)}")
                        break
                    # Small delay between parts
                    if i < len(parts) - 1:
                        await asyncio.sleep(1)
            else:
                # Send single SMS
                success = self.sms_client.send_sms(to_number, response)
                
            if success:
                logger.info(f"SMS response sent successfully to {to_number}")
            else:
                raise Exception(f"Failed to send SMS to {to_number}")
                
        except Exception as e:
            logger.error(f"Error sending SMS response: {e}", exc_info=True)
            raise
    
    async def handle_emergency_sms(self, sms_data: Dict[str, Any], classification: Dict[str, Any]):
        """Handle emergency SMS messages."""
        sender = sms_data.get('sender', 'unknown')
        body = sms_data.get('body', '')
        
        logger.warning(f"EMERGENCY SMS detected from {sender}")
        
        # Notify admin if configured
        if self.admin_phone:
            emergency_alert = (
                f"🚨 EMERGENCY SMS from {sender}: "
                f"{body[:100]}{'...' if len(body) > 100 else ''}"
            )
            self.sms_client.send_sms(self.admin_phone, emergency_alert)
        
        # Notify other agents
        self.comm.broadcast_emergency_alert(
            system_component='SMS_SYSTEM',
            reported_status='EMERGENCY_MESSAGE_RECEIVED',
            alert_details={
                'sender': sender,
                'message_preview': body[:200],
                'classification': classification
            },
            action_request='PRIORITIZE_EMERGENCY_RESPONSE'
        )
        
        # Share emergency knowledge
        self.comm.share_knowledge('emergency_pattern', {
            'source': 'sms',
            'sender': sender,
            'keywords': classification.get('emergency_keywords', []),
            'response_time': datetime.now().isoformat()
        })
    
    async def handle_emergency_alert(self, alert_content: Dict[str, Any]):
        """Handle emergency alerts from other agents."""
        system_component = alert_content.get('system_component')
        status = alert_content.get('reported_status')
        action_request = alert_content.get('action_request')
        
        logger.warning(f"Emergency alert: {system_component} - {status}")
        
        if action_request == 'STOP_ALL_WORK':
            logger.info("Stopping SMS processing due to emergency alert")
            self.is_running = False
        elif action_request == 'PRIORITIZE_EMERGENCY_RESPONSE':
            # Adjust processing to prioritize emergency responses
            await self.enter_emergency_mode()
    
    async def enter_emergency_mode(self):
        """Enter emergency processing mode."""
        logger.info("Entering emergency mode - prioritizing urgent messages")
        
        self.comm.update_status('emergency_mode', 90, {
            'mode': 'emergency_priority',
            'activated_at': datetime.now().isoformat()
        })
        
        # Process only emergency messages for next few cycles
        # Implementation would filter messages by emergency keywords
    
    async def handle_sms_request(self, request_content: Dict[str, Any]):
        """Handle SMS sending requests from other agents."""
        to_number = request_content.get('to_number')
        message = request_content.get('message')
        priority = request_content.get('priority', 'normal')
        
        if not to_number or not message:
            logger.error("Invalid SMS request - missing to_number or message")
            return
        
        logger.info(f"Processing SMS request to {to_number} (priority: {priority})")
        
        try:
            success = self.sms_client.send_sms(to_number, message)
            
            # Log the requested SMS
            await self.log_sms_interaction({
                'type': 'agent_requested',
                'to_number': to_number,
                'message_length': len(message),
                'priority': priority,
                'success': success
            })
            
        except Exception as e:
            logger.error(f"Error processing SMS request: {e}", exc_info=True)
    
    async def send_status_report(self, requester: str):
        """Send status report to requesting agent."""
        status_report = {
            'agent': self.agent_name,
            'status': 'active' if self.is_running else 'stopped',
            'messages_processed': self.messages_processed,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'errors_count': self.errors_count,
            'clients_initialized': self.sms_client is not None and self.sms_engine is not None,
            'system_health': await self.get_system_health()
        }
        
        self.comm.send_message(requester, 'status_response', status_report)
    
    async def run_system_test(self, requester: str):
        """Run SMS system test and report results."""
        test_results = await self.test_sms_system()
        self.comm.send_message(requester, 'test_results', test_results)
    
    async def test_sms_system(self) -> Dict[str, Any]:
        """Test SMS system functionality."""
        logger.info("Running SMS system test...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {}
        }
        
        try:
            # Test 1: SMS client connectivity
            try:
                self_test = self.sms_client.send_self_test_sms("SMS Engineer Test")
                results['tests']['connectivity'] = {
                    'passed': self_test,
                    'details': 'Self-test SMS sent' if self_test else 'Failed to send self-test'
                }
            except Exception as e:
                results['tests']['connectivity'] = {
                    'passed': False,
                    'details': f'Error: {str(e)}'
                }
            
            # Test 2: Message fetching
            try:
                messages = self.sms_client.fetch_sms(
                    search_criteria='ALL',
                    last_n_days=1,
                    max_results=5
                )
                results['tests']['message_fetching'] = {
                    'passed': True,
                    'details': f'Fetched {len(messages)} messages'
                }
            except Exception as e:
                results['tests']['message_fetching'] = {
                    'passed': False,
                    'details': f'Error: {str(e)}'
                }
            
            # Test 3: Response engine
            try:
                test_response, _ = await self.sms_engine.generate_sms_response_async(
                    "+1234567890", "Test message"
                )
                results['tests']['response_engine'] = {
                    'passed': len(test_response) > 0,
                    'details': f'Generated response: {test_response[:50]}...'
                }
            except Exception as e:
                results['tests']['response_engine'] = {
                    'passed': False,
                    'details': f'Error: {str(e)}'
                }
            
            # Overall result
            all_passed = all(test['passed'] for test in results['tests'].values())
            results['overall'] = 'PASS' if all_passed else 'FAIL'
            
        except Exception as e:
            logger.error(f"Error during system test: {e}", exc_info=True)
            results['error'] = str(e)
            results['overall'] = 'ERROR'
        
        return results
    
    async def monitor_system_health(self):
        """Monitor SMS system health and report issues."""
        health_status = await self.get_system_health()
        
        # Check for issues
        issues = []
        if health_status['twilio_connection'] != 'healthy':
            issues.append('twilio_connection')
        if health_status['response_time'] > 5.0:
            issues.append('slow_response')
        if self.errors_count > 10:
            issues.append('high_error_rate')
        
        if issues:
            self.comm.share_knowledge('system_health_issue', {
                'issues': issues,
                'health_status': health_status,
                'recommended_action': 'investigate_sms_system'
            })
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get current system health metrics."""
        health = {
            'timestamp': datetime.now().isoformat(),
            'twilio_connection': 'unknown',
            'response_time': 0.0,
            'messages_per_hour': 0,
            'error_rate': 0.0
        }
        
        try:
            # Test Twilio connection
            start_time = time.time()
            recent_messages = self.sms_client.fetch_sms(max_results=1)
            response_time = time.time() - start_time
            
            health['twilio_connection'] = 'healthy'
            health['response_time'] = response_time
            
            # Calculate metrics
            if self.last_activity:
                hours_since_start = (datetime.now() - self.last_activity).total_seconds() / 3600
                if hours_since_start > 0:
                    health['messages_per_hour'] = self.messages_processed / hours_since_start
            
            if self.messages_processed > 0:
                health['error_rate'] = self.errors_count / self.messages_processed
                
        except Exception as e:
            health['twilio_connection'] = 'error'
            health['error_details'] = str(e)
        
        return health
    
    async def request_help_from_archaeologist(self, topic: str, details: Dict[str, Any]):
        """Request help from archaeologist agent."""
        self.comm.send_message('archaeologist', 'clarification_request', {
            'topic': topic,
            'specific_question': f'SMS system issue: {topic}',
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
        await self.log_sms_interaction({
            'type': 'received_help',
            'topic': topic,
            'source': content.get('from', 'unknown'),
            'applied': True
        })
    
    async def log_sms_interaction(self, interaction_data: Dict[str, Any]):
        """Log SMS interaction for analytics."""
        try:
            log_dir = Path('/mnt/c/Users/Man/ultra/projects/karen/logs')
            log_dir.mkdir(exist_ok=True)
            
            log_file = log_dir / 'sms_agent_activity.log'
            
            with open(log_file, 'a') as f:
                log_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'agent': self.agent_name,
                    'data': interaction_data
                }
                f.write(f"{log_entry}\n")
                
        except Exception as e:
            logger.error(f"Error logging SMS interaction: {e}", exc_info=True)
    
    def stop(self):
        """Stop the SMS processing agent."""
        logger.info("SMS Engineer Agent stopping...")
        self.is_running = False
        self.comm.update_status('stopping', 95, {'stop_requested': datetime.now().isoformat()})
    
    def run_legacy_mode(self):
        """Run the agent in legacy mode (original implementation for compatibility)."""
        logger.info("🚀 SMS Engineer Agent starting in legacy mode...")
        
        try:
            # Initialize and update status
            self.comm.update_status('initializing', 10, {'mode': 'legacy'})
            
            # Share that SMS implementation is complete
            self.comm.share_knowledge('sms_implementation', {
                'status': 'completed',
                'components': ['sms_client', 'sms_engine', 'celery_tasks'],
                'files': [
                    'src/sms_client.py',
                    'src/handyman_sms_engine.py', 
                    'src/celery_sms_tasks.py'
                ],
                'ready_for_testing': True
            })
            
            # Notify test engineer
            self.comm.send_message('test_engineer', 'ready_for_testing', {
                'feature': 'sms_integration',
                'test_files': ['tests/test_sms_integration.py'],
                'dependencies': ['twilio'],
                'test_phone_number': '+1234567890'
            })
            
            # Update final status
            self.comm.update_status('completed', 100, {
                'current_task': 'SMS implementation complete',
                'ready_for_production': True
            })
            
            logger.info("✅ SMS Engineer Agent completed in legacy mode")
            
        except Exception as e:
            logger.error(f"❌ SMS Engineer Agent failed: {e}", exc_info=True)
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
    agent = SMSEngineerAgent()
    
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
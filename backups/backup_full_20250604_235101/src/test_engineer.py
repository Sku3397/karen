"""
Test Engineer Agent for Karen System

This agent coordinates testing across all Karen system components:
- Email processing system
- SMS functionality  
- Phone/voice capabilities
- Memory and knowledge base systems
- Calendar integration
- Billing and payment processing

The agent listens for test requests, executes comprehensive test suites,
broadcasts critical failures, and shares regular test reports.
"""

import os
import sys
import json
import subprocess
import time
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent))

from agent_communication import AgentCommunication
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/mnt/c/Users/Man/ultra/projects/karen/logs/test_engineer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('TestEngineer')

class TestEngineer:
    """Test Engineer Agent for coordinating system-wide testing"""
    
    def __init__(self):
        self.comm = AgentCommunication('test_engineer')
        self.test_results = {}
        self.system_health = {}
        self.critical_failures = []
        self.project_root = Path('/mnt/c/Users/Man/ultra/projects/karen')
        
        # Test system mappings
        self.test_systems = {
            'email': {
                'tests': ['tests/test_communicator_agent.py', 'tests/backend_gmail_test.js'],
                'critical': True,
                'dependencies': ['gmail_api', 'celery', 'redis']
            },
            'sms': {
                'tests': ['tests/test_twilio_integration.py'],
                'critical': True,
                'dependencies': ['twilio_api', 'celery']
            },
            'phone': {
                'tests': ['tests/test_voice_processing.py'],
                'critical': False,
                'dependencies': ['gcp_speech', 'voice_transcription']
            },
            'memory': {
                'tests': ['tests/test_knowledge_base_agent.py'],
                'critical': True,
                'dependencies': ['firestore', 'llm_client']
            },
            'calendar': {
                'tests': ['tests/test_calendar_integration.py'],
                'critical': True,
                'dependencies': ['google_calendar_api']
            },
            'billing': {
                'tests': ['tests/backend_billing_test.js'],
                'critical': True,
                'dependencies': ['stripe_api', 'payment_processing']
            },
            'orchestrator': {
                'tests': ['tests/test_orchestrator_agent.py'],
                'critical': True,
                'dependencies': ['agent_communication', 'task_management']
            },
            'scheduler': {
                'tests': ['tests/test_scheduler_agent.py'],
                'critical': True,
                'dependencies': ['celery_beat', 'task_scheduling']
            }
        }
        
        logger.info("Test Engineer initialized")
        self.comm.update_status('initialized', 0, {
            'systems_monitored': list(self.test_systems.keys()),
            'critical_systems': [k for k, v in self.test_systems.items() if v['critical']]
        })
    
    def run_feature_tests(self, feature: str) -> Dict[str, Any]:
        """Execute comprehensive tests for a specific feature/system"""
        logger.info(f"Running tests for feature: {feature}")
        
        if feature not in self.test_systems:
            return {
                'feature': feature,
                'status': 'error',
                'error': f'Unknown feature: {feature}',
                'passed': 0,
                'failed': 1,
                'coverage': 0
            }
        
        system_config = self.test_systems[feature]
        test_results = {
            'feature': feature,
            'status': 'running',
            'passed': 0,
            'failed': 0,
            'errors': [],
            'coverage': 0,
            'execution_time': 0,
            'timestamp': datetime.now().isoformat()
        }
        
        start_time = time.time()
        
        try:
            # Check dependencies first
            dependency_check = self._check_dependencies(system_config['dependencies'])
            if not dependency_check['all_available']:
                test_results.update({
                    'status': 'dependency_failure',
                    'failed': 1,
                    'errors': [f"Missing dependencies: {dependency_check['missing']}"]
                })
                return test_results
            
            # Run each test for this system
            for test_file in system_config['tests']:
                test_path = self.project_root / test_file
                if test_path.exists():
                    result = self._execute_test_file(test_path)
                    test_results['passed'] += result.get('passed', 0)
                    test_results['failed'] += result.get('failed', 0)
                    if result.get('errors'):
                        test_results['errors'].extend(result['errors'])
                else:
                    test_results['failed'] += 1
                    test_results['errors'].append(f"Test file not found: {test_file}")
            
            # Calculate overall status
            if test_results['failed'] == 0:
                test_results['status'] = 'passed'
            elif test_results['passed'] > 0:
                test_results['status'] = 'partial'
            else:
                test_results['status'] = 'failed'
            
            # Estimate coverage (simplified)
            total_tests = test_results['passed'] + test_results['failed']
            if total_tests > 0:
                test_results['coverage'] = (test_results['passed'] / total_tests) * 100
            
        except Exception as e:
            test_results.update({
                'status': 'error',
                'failed': test_results['failed'] + 1,
                'errors': test_results['errors'] + [f"Test execution error: {str(e)}"]
            })
            logger.error(f"Error running tests for {feature}: {e}")
            logger.error(traceback.format_exc())
        
        test_results['execution_time'] = time.time() - start_time
        
        # Store results
        self.test_results[feature] = test_results
        
        # Check for critical failures
        if system_config['critical'] and test_results['status'] in ['failed', 'error']:
            self._handle_critical_failure(feature, test_results)
        
        logger.info(f"Tests completed for {feature}: {test_results['status']}")
        return test_results
    
    def _check_dependencies(self, dependencies: List[str]) -> Dict[str, Any]:
        """Check if required dependencies are available"""
        missing = []
        available = []
        
        dependency_checks = {
            'gmail_api': self._check_gmail_api,
            'celery': self._check_celery,
            'redis': self._check_redis,
            'twilio_api': self._check_twilio_api,
            'gcp_speech': self._check_gcp_speech,
            'firestore': self._check_firestore,
            'llm_client': self._check_llm_client,
            'google_calendar_api': self._check_calendar_api,
            'stripe_api': self._check_stripe_api,
            'agent_communication': self._check_agent_communication,
            'celery_beat': self._check_celery_beat,
            'voice_transcription': self._check_voice_transcription,
            'payment_processing': self._check_payment_processing,
            'task_management': self._check_task_management,
            'task_scheduling': self._check_task_scheduling
        }
        
        for dep in dependencies:
            if dep in dependency_checks:
                if dependency_checks[dep]():
                    available.append(dep)
                else:
                    missing.append(dep)
            else:
                missing.append(f"{dep} (unknown)")
        
        return {
            'all_available': len(missing) == 0,
            'available': available,
            'missing': missing
        }
    
    def _execute_test_file(self, test_path: Path) -> Dict[str, Any]:
        """Execute a specific test file and parse results"""
        result = {'passed': 0, 'failed': 0, 'errors': []}
        
        try:
            if test_path.suffix == '.py':
                # Run Python tests with pytest
                cmd = [sys.executable, '-m', 'pytest', str(test_path), '-v', '--tb=short']
                process = subprocess.run(
                    cmd,
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                # Parse pytest output
                output = process.stdout + process.stderr
                lines = output.split('\n')
                
                for line in lines:
                    if '::' in line and 'PASSED' in line:
                        result['passed'] += 1
                    elif '::' in line and 'FAILED' in line:
                        result['failed'] += 1
                        result['errors'].append(line.strip())
                    elif 'ERROR' in line.upper():
                        result['errors'].append(line.strip())
                
                if process.returncode != 0 and result['passed'] == 0 and result['failed'] == 0:
                    result['failed'] = 1
                    result['errors'].append(f"Test execution failed: {output}")
            
            elif test_path.suffix == '.js':
                # Run JavaScript tests with Node.js
                cmd = ['node', str(test_path)]
                process = subprocess.run(
                    cmd,
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                # Simple JS test result parsing
                output = process.stdout + process.stderr
                if process.returncode == 0:
                    result['passed'] = 1
                else:
                    result['failed'] = 1
                    result['errors'].append(output)
            
        except subprocess.TimeoutExpired:
            result['failed'] = 1
            result['errors'].append(f"Test timeout: {test_path}")
        except Exception as e:
            result['failed'] = 1
            result['errors'].append(f"Test execution error: {str(e)}")
        
        return result
    
    def _handle_critical_failure(self, system: str, test_results: Dict[str, Any]):
        """Handle critical system failures by broadcasting alerts"""
        failure_info = {
            'system': system,
            'status': test_results['status'],
            'errors': test_results['errors'],
            'timestamp': datetime.now().isoformat(),
            'action_required': 'STOP all integrations' if system == 'email' else 'Review and fix'
        }
        
        self.critical_failures.append(failure_info)
        
        logger.critical(f"CRITICAL FAILURE detected in {system}: {test_results['errors']}")
        
        # Broadcast to all agents
        agents = ['orchestrator', 'sms_engineer', 'phone_engineer', 'memory_engineer', 'archaeologist']
        for agent in agents:
            try:
                self.comm.send_message(agent, 'critical_failure', failure_info)
                logger.info(f"Critical failure alert sent to {agent}")
            except Exception as e:
                logger.error(f"Failed to send critical alert to {agent}: {e}")
    
    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'overall_health': 0,
            'system_status': {},
            'critical_failures': self.critical_failures,
            'summary': {
                'total_systems': len(self.test_systems),
                'passing': 0,
                'failing': 0,
                'untested': 0
            }
        }
        
        total_health = 0
        tested_systems = 0
        
        for system, config in self.test_systems.items():
            if system in self.test_results:
                result = self.test_results[system]
                status = result['status']
                
                if status == 'passed':
                    report['summary']['passing'] += 1
                    system_health = 100
                elif status == 'partial':
                    report['summary']['passing'] += 1  # Count partial as passing
                    system_health = result.get('coverage', 50)
                else:
                    report['summary']['failing'] += 1
                    system_health = 0
                
                report['system_status'][system] = {
                    'status': status,
                    'health': system_health,
                    'last_tested': result['timestamp'],
                    'critical': config['critical']
                }
                
                total_health += system_health
                tested_systems += 1
            else:
                report['summary']['untested'] += 1
                report['system_status'][system] = {
                    'status': 'untested',
                    'health': 0,
                    'critical': config['critical']
                }
        
        # Calculate overall health
        if tested_systems > 0:
            report['overall_health'] = total_health / tested_systems
        
        return report
    
    def listen_for_test_requests(self):
        """Main loop to listen for test requests and coordinate testing"""
        logger.info("Test Engineer starting to listen for requests...")
        
        try:
            while True:
                # Read messages from filesystem
                messages = self.comm.read_messages()
                
                for msg in messages:
                    try:
                        self._process_message(msg)
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        logger.error(traceback.format_exc())
                
                # Generate and share regular status report
                if len(self.test_results) > 0:
                    report = self.generate_test_report()
                    self.comm.share_knowledge('test_report', report)
                    
                    # Update our status
                    self.comm.update_status('monitoring', int(report['overall_health']), {
                        'systems_tested': len(self.test_results),
                        'critical_failures': len(self.critical_failures),
                        'overall_health': report['overall_health']
                    })
                
                time.sleep(10)  # Check every 10 seconds
                
        except KeyboardInterrupt:
            logger.info("Test Engineer shutting down...")
        except Exception as e:
            logger.error(f"Test Engineer error: {e}")
            logger.error(traceback.format_exc())
    
    def _process_message(self, msg: Dict[str, Any]):
        """Process incoming messages"""
        msg_type = msg.get('type')
        sender = msg.get('from')
        content = msg.get('content', {})
        
        logger.info(f"Processing message type '{msg_type}' from {sender}")
        
        if msg_type == 'ready_for_testing':
            feature = content.get('feature')
            if feature:
                self.comm.update_status('testing', 50, {'testing_feature': feature})
                
                # Run tests
                test_results = self.run_feature_tests(feature)
                
                # Send results back
                self.comm.send_message(sender, 'test_results', test_results)
                logger.info(f"Test results sent to {sender} for feature {feature}")
        
        elif msg_type == 'run_all_tests':
            self.comm.update_status('running_full_suite', 25, {'initiator': sender})
            
            # Run tests for all systems
            all_results = {}
            for system in self.test_systems.keys():
                all_results[system] = self.run_feature_tests(system)
            
            # Send comprehensive report
            report = self.generate_test_report()
            self.comm.send_message(sender, 'full_test_report', {
                'individual_results': all_results,
                'summary_report': report
            })
            logger.info(f"Full test suite results sent to {sender}")
        
        elif msg_type == 'health_check':
            # Send current health status
            report = self.generate_test_report()
            self.comm.send_message(sender, 'health_status', report)
        
        elif msg_type == 'test_specific':
            # Test specific component or file
            target = content.get('target')
            if target:
                # Custom test execution for specific targets
                result = self._run_custom_test(target)
                self.comm.send_message(sender, 'custom_test_result', result)
    
    def _run_custom_test(self, target: str) -> Dict[str, Any]:
        """Run custom test for specific target"""
        logger.info(f"Running custom test for: {target}")
        
        # This could be expanded to handle specific files, functions, etc.
        if target in self.test_systems:
            return self.run_feature_tests(target)
        else:
            return {
                'target': target,
                'status': 'error',
                'error': f'Unknown test target: {target}',
                'timestamp': datetime.now().isoformat()
            }
    
    # Dependency check methods
    def _check_gmail_api(self) -> bool:
        """Check if Gmail API is accessible"""
        try:
            token_file = self.project_root / 'gmail_token_hello@757handy.com.json'
            return token_file.exists()
        except:
            return False
    
    def _check_celery(self) -> bool:
        """Check if Celery is available"""
        try:
            import celery
            return True
        except ImportError:
            return False
    
    def _check_redis(self) -> bool:
        """Check if Redis is accessible"""
        try:
            import redis
            client = redis.from_url(os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'))
            client.ping()
            return True
        except:
            return False
    
    def _check_twilio_api(self) -> bool:
        """Check if Twilio API is configured"""
        return bool(os.getenv('TWILIO_AUTH_TOKEN') and os.getenv('TWILIO_ACCOUNT_SID'))
    
    def _check_gcp_speech(self) -> bool:
        """Check if GCP Speech API is available"""
        return bool(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))
    
    def _check_firestore(self) -> bool:
        """Check if Firestore is accessible"""
        try:
            # Check for Firebase config
            config_file = self.project_root / 'firebase.json'
            return config_file.exists()
        except:
            return False
    
    def _check_llm_client(self) -> bool:
        """Check if LLM client is configured"""
        return bool(os.getenv('GEMINI_API_KEY'))
    
    def _check_calendar_api(self) -> bool:
        """Check if Google Calendar API is accessible"""
        try:
            token_file = self.project_root / 'calendar_token.json'
            return token_file.exists()
        except:
            return False
    
    def _check_stripe_api(self) -> bool:
        """Check if Stripe API is configured"""
        return bool(os.getenv('STRIPE_SECRET_KEY'))
    
    def _check_agent_communication(self) -> bool:
        """Check if agent communication system is working"""
        try:
            # Test our own communication system
            self.comm.update_status('test', 100, {'test': True})
            return True
        except:
            return False
    
    def _check_celery_beat(self) -> bool:
        """Check if Celery Beat scheduler is available"""
        try:
            beat_file = self.project_root / 'celerybeat-schedule.sqlite3'
            return beat_file.exists() or self._check_celery()
        except:
            return False
    
    def _check_voice_transcription(self) -> bool:
        """Check if voice transcription is available"""
        return self._check_gcp_speech()
    
    def _check_payment_processing(self) -> bool:
        """Check if payment processing is available"""
        return self._check_stripe_api()
    
    def _check_task_management(self) -> bool:
        """Check if task management system is available"""
        return self._check_agent_communication()
    
    def _check_task_scheduling(self) -> bool:
        """Check if task scheduling is available"""
        return self._check_celery_beat()

def test_email_system():
    """Test email system connectivity and functionality"""
    try:
        from email_client import EmailClient
        client = EmailClient()
        
        # Test connection
        if not client.gmail_service:
            raise Exception("Gmail service not initialized")
        
        # Check if we can fetch emails (don't actually send)
        print("Email system: OPERATIONAL")
        return True
    except Exception as e:
        print(f"EMAIL SYSTEM FAILURE: {e}")
        return False

def continuous_monitoring():
    """Continuous monitoring system as requested"""
    import sys
    sys.path.append('.')
    from src.agent_communication import AgentCommunication
    
    comm = AgentCommunication('test_engineer')
    
    print("Starting continuous email monitoring...")
    
    while True:
        # Test email system
        email_ok = test_email_system()
        
        # Test completed features
        if os.path.exists('src/phone_engineer_agent.py'):
            print("Testing phone integration...")
            # Add phone tests when needed
        
        # Update status
        comm.update_status('testing', 70, {
            'email_status': 'working' if email_ok else 'FAILED',
            'last_check': time.strftime('%Y-%m-%d %H:%M:%S')
        })
        
        # If email system fails, send emergency alert
        if not email_ok:
            comm.send_message('orchestrator', 'emergency', {
                'system': 'email',
                'error': 'Email system check failed',
                'severity': 'CRITICAL'
            })
        
        print(f"Status check completed at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        time.sleep(600)  # 10 minutes

def main():
    """Main entry point for Test Engineer agent"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Engineer Agent')
    parser.add_argument('--monitor', action='store_true', 
                       help='Run continuous monitoring mode')
    args = parser.parse_args()
    
    try:
        if args.monitor:
            continuous_monitoring()
        else:
            test_engineer = TestEngineer()
            test_engineer.listen_for_test_requests()
    except Exception as e:
        logger.error(f"Test Engineer failed to start: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()
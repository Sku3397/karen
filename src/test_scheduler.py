"""
Automated Test Scheduler for Karen AI System
==========================================

This module provides automated testing that runs every 30 minutes to ensure
the email system is always functional. It integrates with the Test Engineer
agent to coordinate testing across all system components.

CRITICAL: Email system tests MUST pass - any failures trigger immediate alerts.
"""

import asyncio
import os
import sys
import time
import subprocess
import threading
import schedule
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from agent_communication import AgentCommunication
from test_engineer import TestEngineer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/mnt/c/Users/Man/ultra/projects/karen/logs/test_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('TestScheduler')

class TestScheduler:
    """Automated test scheduler that runs tests every 30 minutes"""
    
    def __init__(self):
        self.comm = AgentCommunication('test_scheduler')
        self.test_engineer = TestEngineer()
        self.project_root = Path('/mnt/c/Users/Man/ultra/projects/karen')
        self.last_email_test_time = None
        self.email_test_failures = 0
        self.running = False
        
        # Critical system monitoring
        self.critical_systems = ['email', 'sms', 'memory', 'calendar', 'billing', 'orchestrator']
        self.system_health_history = {}
        
        logger.info("TestScheduler initialized")
        self.comm.update_status('initialized', 0, {
            'schedule_interval': '30_minutes',
            'critical_systems': self.critical_systems,
            'auto_testing': True
        })
    
    def start_scheduler(self):
        """Start the automated testing scheduler"""
        logger.info("Starting automated test scheduler...")
        self.running = True
        
        # Schedule email baseline tests every 30 minutes
        schedule.every(30).minutes.do(self.run_email_baseline_tests)
        
        # Schedule full system tests every 2 hours
        schedule.every(2).hours.do(self.run_full_system_tests)
        
        # Schedule health checks every 10 minutes
        schedule.every(10).minutes.do(self.run_health_checks)
        
        # Run initial tests immediately
        self.run_email_baseline_tests()
        
        self.comm.update_status('running', 100, {
            'scheduler_active': True,
            'next_email_test': self._get_next_test_time(),
            'tests_scheduled': ['email_baseline', 'full_system', 'health_checks']
        })
        
        # Main scheduler loop
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logger.info("Test scheduler interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                self.comm.broadcast_emergency_alert(
                    'test_scheduler',
                    'SCHEDULER_ERROR',
                    {'error': str(e), 'time': datetime.now().isoformat()},
                    'INVESTIGATE_IMMEDIATELY'
                )
                time.sleep(60)  # Wait before retrying
    
    def stop_scheduler(self):
        """Stop the automated testing scheduler"""
        logger.info("Stopping automated test scheduler...")
        self.running = False
        schedule.clear()
        self.comm.update_status('stopped', 0, {
            'scheduler_active': False,
            'stop_time': datetime.now().isoformat()
        })
    
    def run_email_baseline_tests(self):
        """Run critical email baseline tests"""
        logger.info("Running scheduled email baseline tests...")
        self.last_email_test_time = datetime.now()
        
        self.comm.update_status('testing_email', 25, {
            'test_type': 'email_baseline',
            'start_time': self.last_email_test_time.isoformat()
        })
        
        try:
            # Run email baseline tests
            result = self._run_pytest_tests('tests/test_email_baseline.py')
            
            if result['success']:
                self.email_test_failures = 0
                logger.info("Email baseline tests PASSED")
                
                self.comm.update_status('email_tests_passed', 100, {
                    'test_type': 'email_baseline',
                    'passed_tests': result.get('passed', 0),
                    'execution_time': result.get('execution_time', 0),
                    'next_test': self._get_next_test_time()
                })
                
                # Share success with knowledge base
                self.comm.share_knowledge('email_test_success', {
                    'timestamp': datetime.now().isoformat(),
                    'test_results': result,
                    'system_health': 'GOOD'
                })
                
            else:
                self.email_test_failures += 1
                logger.error(f"Email baseline tests FAILED ({self.email_test_failures} consecutive failures)")
                
                # CRITICAL: Email failure - alert everyone immediately
                self._handle_email_system_failure(result)
                
        except Exception as e:
            self.email_test_failures += 1
            logger.error(f"Email test execution error: {e}")
            self._handle_email_system_failure({
                'success': False,
                'error': str(e),
                'exception': True
            })
    
    def run_full_system_tests(self):
        """Run comprehensive tests for all system components"""
        logger.info("Running full system test suite...")
        
        self.comm.update_status('testing_full_system', 10, {
            'test_type': 'full_system',
            'systems_under_test': self.critical_systems
        })
        
        system_results = {}
        overall_success = True
        
        for system in self.critical_systems:
            logger.info(f"Testing system: {system}")
            
            try:
                result = self.test_engineer.run_feature_tests(system)
                system_results[system] = result
                
                if result['status'] not in ['passed', 'partial']:
                    overall_success = False
                    logger.warning(f"System {system} test failed: {result}")
                
            except Exception as e:
                logger.error(f"Error testing system {system}: {e}")
                system_results[system] = {
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                overall_success = False
        
        # Generate comprehensive report
        report = self.test_engineer.generate_test_report()
        
        if overall_success:
            self.comm.update_status('full_system_tests_passed', 100, {
                'test_type': 'full_system',
                'overall_health': report['overall_health'],
                'systems_tested': len(system_results),
                'report': report
            })
        else:
            self.comm.update_status('full_system_tests_failed', 50, {
                'test_type': 'full_system',
                'failed_systems': [k for k, v in system_results.items() if v.get('status') not in ['passed', 'partial']],
                'report': report
            })
        
        # Share results with all agents
        self.comm.share_knowledge('full_system_test_report', {
            'timestamp': datetime.now().isoformat(),
            'system_results': system_results,
            'overall_success': overall_success,
            'report': report
        })
    
    def run_health_checks(self):
        """Run quick health checks on critical systems"""
        logger.debug("Running system health checks...")
        
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'systems': {}
        }
        
        # Check Redis connectivity
        try:
            test_comm = AgentCommunication('health_check')
            test_comm.update_status('health_check', 100, {'test': True})
            health_status['systems']['redis'] = {'status': 'healthy', 'response_time': 'fast'}
        except Exception as e:
            health_status['systems']['redis'] = {'status': 'unhealthy', 'error': str(e)}
            logger.warning(f"Redis health check failed: {e}")
        
        # Check email system dependencies
        try:
            token_files = [
                'gmail_token_karen.json',
                'gmail_token_monitor.json'
            ]
            
            email_health = {'status': 'healthy', 'tokens_checked': 0}
            
            for token_file in token_files:
                token_path = self.project_root / token_file
                if token_path.exists():
                    email_health['tokens_checked'] += 1
                else:
                    email_health['status'] = 'unhealthy'
                    email_health['missing_token'] = token_file
            
            health_status['systems']['email_tokens'] = email_health
            
        except Exception as e:
            health_status['systems']['email_tokens'] = {'status': 'error', 'error': str(e)}
        
        # Check LLM API availability
        try:
            if os.getenv('GEMINI_API_KEY'):
                health_status['systems']['llm_api'] = {'status': 'api_key_present'}
            else:
                health_status['systems']['llm_api'] = {'status': 'no_api_key'}
        except Exception as e:
            health_status['systems']['llm_api'] = {'status': 'error', 'error': str(e)}
        
        # Store health history
        self.system_health_history[datetime.now().isoformat()] = health_status
        
        # Keep only last 24 hours of health data
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.system_health_history = {
            k: v for k, v in self.system_health_history.items()
            if datetime.fromisoformat(k) > cutoff_time
        }
        
        # Update status
        unhealthy_systems = [
            name for name, status in health_status['systems'].items()
            if status.get('status') != 'healthy' and status.get('status') != 'api_key_present'
        ]
        
        if unhealthy_systems:
            self.comm.update_status('health_check_warnings', 75, {
                'unhealthy_systems': unhealthy_systems,
                'health_status': health_status
            })
        else:
            self.comm.update_status('health_check_passed', 100, {
                'all_systems_healthy': True,
                'health_status': health_status
            })
    
    def _handle_email_system_failure(self, test_result: Dict[str, Any]):
        """Handle critical email system failures"""
        logger.critical("CRITICAL EMAIL SYSTEM FAILURE DETECTED!")
        
        failure_details = {
            'system': 'email',
            'test_result': test_result,
            'consecutive_failures': self.email_test_failures,
            'last_success': self.last_email_test_time,
            'timestamp': datetime.now().isoformat(),
            'severity': 'CRITICAL'
        }
        
        # Update our status to indicate critical failure
        self.comm.update_status('email_system_failure', 0, failure_details)
        
        # Broadcast emergency alert to all agents using the enhanced method
        self.comm.broadcast_emergency_alert(
            system_component='email',
            reported_status='FAILED',
            alert_details=failure_details,
            action_request='STOP_ALL_EMAIL_WORK'
        )
        
        # Send individual messages to critical agents
        critical_agents = ['orchestrator', 'sms_engineer', 'phone_engineer', 'memory_engineer']
        for agent in critical_agents:
            try:
                self.comm.send_message(agent, 'email_system_failure', {
                    'severity': 'CRITICAL',
                    'system': 'email',
                    'action_required': 'STOP all email integrations immediately',
                    'details': failure_details,
                    'from_test_engineer': True
                })
                logger.info(f"Emergency alert sent to {agent}")
            except Exception as e:
                logger.error(f"Failed to send emergency alert to {agent}: {e}")
        
        # If multiple consecutive failures, escalate further
        if self.email_test_failures >= 3:
            logger.critical(f"EMAIL SYSTEM DOWN: {self.email_test_failures} consecutive failures!")
            
            # This would trigger additional escalation procedures
            # Like notifying external monitoring systems, paging admins, etc.
            self.comm.share_knowledge('email_system_down', {
                'severity': 'EMERGENCY',
                'consecutive_failures': self.email_test_failures,
                'recommended_action': 'MANUAL_INTERVENTION_REQUIRED',
                'timestamp': datetime.now().isoformat()
            })
    
    def _run_pytest_tests(self, test_file: str) -> Dict[str, Any]:
        """Run pytest tests and return results"""
        test_path = self.project_root / test_file
        
        if not test_path.exists():
            return {
                'success': False,
                'error': f'Test file not found: {test_file}',
                'passed': 0,
                'failed': 1
            }
        
        start_time = time.time()
        
        try:
            # Run pytest with JSON output
            cmd = [
                sys.executable, '-m', 'pytest',
                str(test_path),
                '-v', '--tb=short',
                '--json-report', '--json-report-file=/tmp/test_results.json'
            ]
            
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            execution_time = time.time() - start_time
            
            # Parse results
            try:
                with open('/tmp/test_results.json', 'r') as f:
                    test_data = json.load(f)
                
                return {
                    'success': result.returncode == 0,
                    'returncode': result.returncode,
                    'passed': len([t for t in test_data.get('tests', []) if t.get('outcome') == 'passed']),
                    'failed': len([t for t in test_data.get('tests', []) if t.get('outcome') == 'failed']),
                    'execution_time': execution_time,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'detailed_results': test_data
                }
            except Exception as parse_error:
                # Fallback to basic parsing
                passed_count = result.stdout.count(' PASSED')
                failed_count = result.stdout.count(' FAILED')
                
                return {
                    'success': result.returncode == 0,
                    'returncode': result.returncode,
                    'passed': passed_count,
                    'failed': failed_count,
                    'execution_time': execution_time,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'parse_error': str(parse_error)
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Test execution timeout',
                'passed': 0,
                'failed': 1,
                'execution_time': time.time() - start_time
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'passed': 0,
                'failed': 1,
                'execution_time': time.time() - start_time
            }
    
    def _get_next_test_time(self) -> str:
        """Get the next scheduled test time"""
        next_time = datetime.now() + timedelta(minutes=30)
        return next_time.isoformat()
    
    def get_test_history(self, hours: int = 24) -> Dict[str, Any]:
        """Get test execution history for the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Filter health history
        recent_health = {
            k: v for k, v in self.system_health_history.items()
            if datetime.fromisoformat(k) > cutoff_time
        }
        
        return {
            'time_range_hours': hours,
            'health_checks': recent_health,
            'email_test_failures': self.email_test_failures,
            'last_email_test': self.last_email_test_time.isoformat() if self.last_email_test_time else None,
            'scheduler_running': self.running
        }

def main():
    """Main entry point for test scheduler"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Karen AI Test Scheduler')
    parser.add_argument('--start', action='store_true', help='Start the automated test scheduler')
    parser.add_argument('--run-email-tests', action='store_true', help='Run email baseline tests once')
    parser.add_argument('--run-full-tests', action='store_true', help='Run full system tests once')
    parser.add_argument('--health-check', action='store_true', help='Run health checks once')
    
    args = parser.parse_args()
    
    scheduler = TestScheduler()
    
    try:
        if args.start:
            logger.info("Starting automated test scheduler...")
            scheduler.start_scheduler()
        elif args.run_email_tests:
            logger.info("Running email baseline tests...")
            scheduler.run_email_baseline_tests()
        elif args.run_full_tests:
            logger.info("Running full system tests...")
            scheduler.run_full_system_tests()
        elif args.health_check:
            logger.info("Running health checks...")
            scheduler.run_health_checks()
        else:
            print("No action specified. Use --help for options.")
            
    except KeyboardInterrupt:
        logger.info("Test scheduler interrupted by user")
    except Exception as e:
        logger.error(f"Test scheduler error: {e}")
    finally:
        scheduler.stop_scheduler()

if __name__ == "__main__":
    main()
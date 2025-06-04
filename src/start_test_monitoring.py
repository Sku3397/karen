"""
Start Test Monitoring System for Karen AI
========================================

This script initializes and starts the complete test monitoring system:
1. Test Engineer agent for coordinating tests
2. Automated test scheduler running every 30 minutes
3. Email baseline test monitoring
4. Agent communication system integration

Usage:
    python src/start_test_monitoring.py
"""

import os
import sys
import time
import threading
import logging
import signal
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from test_engineer import TestEngineer
from test_scheduler import TestScheduler
from agent_communication import AgentCommunication

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/mnt/c/Users/Man/ultra/projects/karen/logs/test_monitoring.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('TestMonitoring')

class TestMonitoringSystem:
    """Complete test monitoring system for Karen AI"""
    
    def __init__(self):
        self.comm = AgentCommunication('test_monitoring_system')
        self.test_engineer = None
        self.test_scheduler = None
        self.running = False
        
        # Thread management
        self.threads = []
        self.shutdown_event = threading.Event()
        
        logger.info("Test Monitoring System initialized")
    
    def start(self):
        """Start the complete test monitoring system"""
        logger.info("=== STARTING KAREN AI TEST MONITORING SYSTEM ===")
        
        try:
            self.running = True
            
            # Initialize components
            self.test_engineer = TestEngineer()
            self.test_scheduler = TestScheduler()
            
            # Update system status
            self.comm.update_status('starting', 25, {
                'components': ['test_engineer', 'test_scheduler'],
                'start_time': datetime.now().isoformat()
            })
            
            # Start Test Engineer in background thread
            logger.info("Starting Test Engineer agent...")
            test_engineer_thread = threading.Thread(
                target=self._run_test_engineer,
                name="TestEngineer",
                daemon=True
            )
            test_engineer_thread.start()
            self.threads.append(test_engineer_thread)
            
            # Start Test Scheduler in background thread
            logger.info("Starting Test Scheduler...")
            test_scheduler_thread = threading.Thread(
                target=self._run_test_scheduler,
                name="TestScheduler",
                daemon=True
            )
            test_scheduler_thread.start()
            self.threads.append(test_scheduler_thread)
            
            # Run immediate email baseline test
            logger.info("Running initial email baseline test...")
            self._run_initial_tests()
            
            # Update status to running
            self.comm.update_status('running', 100, {
                'test_engineer_active': True,
                'test_scheduler_active': True,
                'email_monitoring': True,
                'automatic_testing': True,
                'start_complete_time': datetime.now().isoformat()
            })
            
            # Announce system readiness
            self._announce_system_ready()
            
            # Main monitoring loop
            self._main_monitoring_loop()
            
        except Exception as e:
            logger.error(f"Failed to start test monitoring system: {e}")
            self.comm.broadcast_emergency_alert(
                'test_monitoring_system',
                'STARTUP_FAILURE',
                {'error': str(e), 'time': datetime.now().isoformat()},
                'MANUAL_INTERVENTION_REQUIRED'
            )
            raise
    
    def stop(self):
        """Stop the test monitoring system"""
        logger.info("Stopping Test Monitoring System...")
        
        self.running = False
        self.shutdown_event.set()
        
        # Stop scheduler
        if self.test_scheduler:
            self.test_scheduler.stop_scheduler()
        
        # Wait for threads to finish
        for thread in self.threads:
            if thread.is_alive():
                logger.info(f"Waiting for {thread.name} to finish...")
                thread.join(timeout=10)
        
        self.comm.update_status('stopped', 0, {
            'stop_time': datetime.now().isoformat(),
            'graceful_shutdown': True
        })
        
        logger.info("Test Monitoring System stopped")
    
    def _run_test_engineer(self):
        """Run the Test Engineer agent"""
        try:
            logger.info("Test Engineer agent starting...")
            self.test_engineer.listen_for_test_requests()
        except Exception as e:
            logger.error(f"Test Engineer error: {e}")
            self.comm.broadcast_emergency_alert(
                'test_engineer',
                'AGENT_FAILURE',
                {'error': str(e)},
                'RESTART_REQUIRED'
            )
    
    def _run_test_scheduler(self):
        """Run the Test Scheduler"""
        try:
            logger.info("Test Scheduler starting...")
            self.test_scheduler.start_scheduler()
        except Exception as e:
            logger.error(f"Test Scheduler error: {e}")
            self.comm.broadcast_emergency_alert(
                'test_scheduler',
                'SCHEDULER_FAILURE',
                {'error': str(e)},
                'RESTART_REQUIRED'
            )
    
    def _run_initial_tests(self):
        """Run initial tests to verify system health"""
        logger.info("Running initial system health verification...")
        
        try:
            # Test Redis connectivity
            self.comm.update_status('initial_test', 30, {'testing': 'redis_connectivity'})
            self.comm.send_message('test_monitoring_system', 'health_check', {
                'test': 'redis_connectivity',
                'timestamp': datetime.now().isoformat()
            })
            
            # Run email baseline tests immediately
            self.comm.update_status('initial_test', 60, {'testing': 'email_baseline'})
            if self.test_scheduler:
                self.test_scheduler.run_email_baseline_tests()
            
            # Run health checks
            self.comm.update_status('initial_test', 90, {'testing': 'health_checks'})
            if self.test_scheduler:
                self.test_scheduler.run_health_checks()
            
            logger.info("Initial tests completed successfully")
            
        except Exception as e:
            logger.error(f"Initial tests failed: {e}")
            self.comm.broadcast_emergency_alert(
                'initial_tests',
                'INITIAL_TEST_FAILURE',
                {'error': str(e)},
                'INVESTIGATE_IMMEDIATELY'
            )
    
    def _announce_system_ready(self):
        """Announce that the test monitoring system is ready"""
        logger.info("🎯 TEST MONITORING SYSTEM READY 🎯")
        
        # Send messages to all agents
        agents = ['orchestrator', 'sms_engineer', 'phone_engineer', 'memory_engineer', 'archaeologist']
        
        for agent in agents:
            try:
                self.comm.send_message(agent, 'test_monitoring_ready', {
                    'system': 'test_monitoring',
                    'features': [
                        'automated_email_testing_every_30min',
                        'critical_failure_alerts',
                        'system_health_monitoring',
                        'test_coordination'
                    ],
                    'email_system_critical': True,
                    'ready_time': datetime.now().isoformat()
                })
                logger.info(f"Notified {agent} that test monitoring is ready")
            except Exception as e:
                logger.warning(f"Failed to notify {agent}: {e}")
        
        # Share knowledge about system readiness
        self.comm.share_knowledge('test_monitoring_system_ready', {
            'system_version': '1.0.0',
            'capabilities': [
                'email_baseline_testing',
                'automated_30min_schedule',
                'critical_failure_detection',
                'agent_coordination',
                'health_monitoring'
            ],
            'email_protection': 'ACTIVE',
            'ready_timestamp': datetime.now().isoformat()
        })
    
    def _main_monitoring_loop(self):
        """Main monitoring loop"""
        logger.info("Entering main monitoring loop...")
        
        last_status_update = datetime.now()
        
        while self.running and not self.shutdown_event.is_set():
            try:
                # Update status every 5 minutes
                if (datetime.now() - last_status_update).total_seconds() > 300:
                    self._update_system_status()
                    last_status_update = datetime.now()
                
                # Check for any critical messages
                messages = self.comm.read_messages()
                for msg in messages:
                    self._process_monitoring_message(msg)
                
                # Sleep for a short period
                time.sleep(30)
                
            except KeyboardInterrupt:
                logger.info("Monitoring loop interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)
    
    def _update_system_status(self):
        """Update system status periodically"""
        try:
            thread_status = {
                'test_engineer_alive': any(t.name == 'TestEngineer' and t.is_alive() for t in self.threads),
                'test_scheduler_alive': any(t.name == 'TestScheduler' and t.is_alive() for t in self.threads),
                'active_threads': len([t for t in self.threads if t.is_alive()])
            }
            
            self.comm.update_status('monitoring', 100, {
                'uptime_status': 'healthy',
                'threads': thread_status,
                'last_update': datetime.now().isoformat(),
                'email_monitoring': 'ACTIVE'
            })
            
        except Exception as e:
            logger.error(f"Error updating system status: {e}")
    
    def _process_monitoring_message(self, msg: Dict[str, Any]):
        """Process messages received by the monitoring system"""
        msg_type = msg.get('type')
        sender = msg.get('from')
        content = msg.get('content', {})
        
        logger.debug(f"Processing monitoring message: {msg_type} from {sender}")
        
        if msg_type == 'system_status_request':
            # Send current system status
            if self.test_scheduler:
                history = self.test_scheduler.get_test_history(hours=24)
                self.comm.send_message(sender, 'system_status_response', {
                    'monitoring_system': 'ACTIVE',
                    'test_history': history,
                    'timestamp': datetime.now().isoformat()
                })
        
        elif msg_type == 'emergency_test_request':
            # Run emergency tests immediately
            logger.warning(f"Emergency test request from {sender}")
            if self.test_scheduler:
                threading.Thread(
                    target=self.test_scheduler.run_email_baseline_tests,
                    daemon=True
                ).start()
        
        elif msg_type == 'shutdown_request':
            logger.info(f"Shutdown request received from {sender}")
            self.running = False
            self.shutdown_event.set()

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    if hasattr(signal_handler, 'monitoring_system'):
        signal_handler.monitoring_system.stop()
    sys.exit(0)

def main():
    """Main entry point"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start monitoring system
    monitoring_system = TestMonitoringSystem()
    signal_handler.monitoring_system = monitoring_system
    
    try:
        monitoring_system.start()
    except KeyboardInterrupt:
        logger.info("Monitoring system interrupted")
    except Exception as e:
        logger.error(f"Monitoring system failed: {e}")
    finally:
        monitoring_system.stop()

if __name__ == "__main__":
    main()
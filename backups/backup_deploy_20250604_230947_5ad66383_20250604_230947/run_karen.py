#!/usr/bin/env python3
"""
Karen AI Secretary - Main Entry Point
Instance ID: ORCHESTRATOR-001 Master Control
Domain: System initialization, main loop, graceful shutdown
"""
import os
import sys
import time
import signal
import logging
import argparse
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import core components
from src.orchestrator import get_orchestrator_instance, AgentType, TaskPriority
from agent_task_system import get_task_system_instance
from src.config import *

# Set up main logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/system/karen_main.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('karen_main')

class KarenAISecretary:
    """
    Main Karen AI Secretary application controller
    Coordinates all system components and manages the main execution loop
    """
    
    def __init__(self, config_overrides: Optional[Dict] = None):
        """Initialize Karen AI Secretary system"""
        logger.info("Initializing Karen AI Secretary System")
        
        # System state
        self.running = False
        self.startup_time = datetime.now()
        self.shutdown_requested = False
        
        # Configuration
        self.config = {
            "email_check_interval": 60,  # seconds
            "health_check_interval": 300,  # 5 minutes
            "system_report_interval": 1800,  # 30 minutes
            "enable_email_monitoring": True,
            "enable_sms_monitoring": True,
            "enable_voice_monitoring": True,
            "max_email_processing_threads": 3,
            "debug_mode": False
        }
        
        if config_overrides:
            self.config.update(config_overrides)
        
        # Core components
        self.orchestrator = None
        self.task_system = None
        self.celery_app = None
        self.email_monitor = None
        
        # Performance metrics
        self.metrics = {
            "emails_processed": 0,
            "sms_processed": 0,
            "voice_calls_handled": 0,
            "tasks_completed": 0,
            "system_uptime": 0,
            "last_health_check": None
        }
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("Karen AI Secretary initialized")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_requested = True
    
    def _setup_directories(self):
        """Create necessary directory structure"""
        directories = [
            "logs/system",
            "logs/agents", 
            "logs/orchestrator",
            "logs/tasks",
            "logs/workflows",
            "logs/email",
            "logs/sms",
            "logs/voice",
            "data/conversations",
            "data/knowledge_base",
            "data/metrics",
            "reports/daily",
            "reports/weekly",
            "reports/system"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
        
        logger.info("Directory structure created")
    
    def _initialize_core_components(self):
        """Initialize all core system components"""
        logger.info("Initializing core components...")
        
        try:
            # Initialize orchestrator (this also creates logs/agents/* structure)
            self.orchestrator = get_orchestrator_instance()
            logger.info("✓ Orchestrator initialized")
            
            # Initialize enhanced task system
            self.task_system = get_task_system_instance()
            logger.info("✓ Task system initialized")
            
            # Initialize Celery for background tasks
            self._initialize_celery()
            logger.info("✓ Celery initialized")
            
            # Initialize communication monitoring
            if self.config["enable_email_monitoring"]:
                self._initialize_email_monitoring()
                logger.info("✓ Email monitoring initialized")
            
            if self.config["enable_sms_monitoring"]:
                self._initialize_sms_monitoring()
                logger.info("✓ SMS monitoring initialized")
            
            if self.config["enable_voice_monitoring"]:
                self._initialize_voice_monitoring()
                logger.info("✓ Voice monitoring initialized")
            
            logger.info("All core components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize core components: {e}", exc_info=True)
            raise
    
    def _initialize_celery(self):
        """Initialize Celery for background task processing"""
        try:
            from src.celery_app import celery_app
            self.celery_app = celery_app
            
            # Create initial email monitoring task
            if self.config["enable_email_monitoring"]:
                # Start email checking task
                self.orchestrator.create_task(
                    agent_type=AgentType.SMS_ENGINEER,  # Email handling agent
                    task_type="start_email_monitoring",
                    description="Initialize email monitoring system",
                    priority=TaskPriority.HIGH,
                    params={
                        "check_interval": self.config["email_check_interval"],
                        "monitored_account": MONITORED_EMAIL_ACCOUNT,
                        "secretary_account": SECRETARY_EMAIL_ADDRESS
                    }
                )
            
        except ImportError as e:
            logger.warning(f"Celery not available: {e}")
            self.celery_app = None
        except Exception as e:
            logger.error(f"Failed to initialize Celery: {e}")
            raise
    
    def _initialize_email_monitoring(self):
        """Initialize email monitoring system"""
        try:
            # Create email monitoring task
            self.orchestrator.create_task(
                agent_type=AgentType.SMS_ENGINEER,  # Handles communication
                task_type="setup_email_monitoring",
                description="Set up continuous email monitoring",
                priority=TaskPriority.HIGH,
                params={
                    "monitored_accounts": [MONITORED_EMAIL_ACCOUNT],
                    "response_account": SECRETARY_EMAIL_ADDRESS,
                    "admin_notifications": ADMIN_EMAIL_ADDRESS,
                    "check_interval": self.config["email_check_interval"]
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize email monitoring: {e}")
    
    def _initialize_sms_monitoring(self):
        """Initialize SMS monitoring system"""
        try:
            # Create SMS monitoring task
            self.orchestrator.create_task(
                agent_type=AgentType.SMS_ENGINEER,
                task_type="setup_sms_monitoring", 
                description="Set up SMS webhook monitoring and response system",
                priority=TaskPriority.HIGH,
                params={
                    "webhook_enabled": True,
                    "auto_response": True,
                    "twilio_integration": True
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize SMS monitoring: {e}")
    
    def _initialize_voice_monitoring(self):
        """Initialize voice call monitoring system"""
        try:
            # Create voice monitoring task
            self.orchestrator.create_task(
                agent_type=AgentType.PHONE_ENGINEER,
                task_type="setup_voice_monitoring",
                description="Set up voice call handling and transcription",
                priority=TaskPriority.HIGH,
                params={
                    "call_screening": True,
                    "auto_transcription": True,
                    "voice_responses": True
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize voice monitoring: {e}")
    
    def _create_initial_workflows(self):
        """Create initial system workflows"""
        logger.info("Creating initial system workflows...")
        
        # System health monitoring workflow
        health_check_task = self.task_system.create_scheduled_task(
            agent_type="test_engineer",
            task_type="system_health_check",
            description="Perform comprehensive system health check",
            execution_time=datetime.now(),
            priority="high",
            params={
                "check_email_system": True,
                "check_sms_system": True,
                "check_voice_system": True,
                "check_database": True,
                "generate_report": True
            }
        )
        
        # Create system analysis workflow
        analysis_workflow = self.orchestrator.execute_workflow(
            "system_initialization",
            params={
                "focus_areas": ["email_processing", "communication_systems", "task_management"],
                "generate_documentation": True,
                "optimize_performance": True
            }
        )
        
        logger.info(f"Created initial workflows: health_check={health_check_task}, analysis={analysis_workflow}")
    
    def _system_health_check(self):
        """Perform system health check"""
        try:
            # Get orchestrator status
            orchestrator_status = self.orchestrator.get_system_overview()
            
            # Get task system status
            task_system_status = self.task_system.get_system_status()
            
            # Update metrics
            self.metrics["last_health_check"] = datetime.now().isoformat()
            self.metrics["system_uptime"] = (datetime.now() - self.startup_time).total_seconds()
            
            # Create health report
            health_report = {
                "timestamp": datetime.now().isoformat(),
                "system_status": "healthy",
                "uptime_seconds": self.metrics["system_uptime"],
                "orchestrator": orchestrator_status,
                "task_system": task_system_status,
                "metrics": self.metrics,
                "config": self.config
            }
            
            # Save health report
            report_file = f"reports/system/health_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                import json
                json.dump(health_report, f, indent=2)
            
            logger.info(f"System health check completed, report saved to {report_file}")
            
            return health_report
            
        except Exception as e:
            logger.error(f"System health check failed: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}
    
    def _generate_system_report(self):
        """Generate comprehensive system report"""
        try:
            report = {
                "timestamp": datetime.now().isoformat(),
                "system_info": {
                    "startup_time": self.startup_time.isoformat(),
                    "uptime_seconds": (datetime.now() - self.startup_time).total_seconds(),
                    "version": "1.0.0",
                    "instance_id": "ORCHESTRATOR-001"
                },
                "orchestrator_status": self.orchestrator.get_system_overview(),
                "task_system_status": self.task_system.get_system_status(),
                "performance_metrics": self.metrics,
                "configuration": self.config
            }
            
            # Save daily report
            report_file = f"reports/daily/system_report_{datetime.now().strftime('%Y%m%d')}.json"
            with open(report_file, 'w') as f:
                import json
                json.dump(report, f, indent=2)
            
            logger.info(f"System report generated: {report_file}")
            
            return report_file
            
        except Exception as e:
            logger.error(f"Failed to generate system report: {e}", exc_info=True)
            return None
    
    def start(self):
        """Start the Karen AI Secretary system"""
        logger.info("Starting Karen AI Secretary System...")
        
        try:
            # Setup directory structure
            self._setup_directories()
            
            # Initialize all components
            self._initialize_core_components()
            
            # Create initial workflows
            self._create_initial_workflows()
            
            # System is now running
            self.running = True
            
            logger.info("🎉 Karen AI Secretary System started successfully!")
            logger.info(f"System startup completed in {(datetime.now() - self.startup_time).total_seconds():.2f} seconds")
            
            # Start main loop
            self._main_loop()
            
        except Exception as e:
            logger.error(f"Failed to start Karen AI Secretary: {e}", exc_info=True)
            self.shutdown()
            raise
    
    def _main_loop(self):
        """Main system monitoring and coordination loop"""
        logger.info("Entering main system loop...")
        
        last_health_check = datetime.now()
        last_system_report = datetime.now()
        
        while self.running and not self.shutdown_requested:
            try:
                current_time = datetime.now()
                
                # Periodic health checks
                if (current_time - last_health_check).total_seconds() >= self.config["health_check_interval"]:
                    self._system_health_check()
                    last_health_check = current_time
                
                # Periodic system reports
                if (current_time - last_system_report).total_seconds() >= self.config["system_report_interval"]:
                    self._generate_system_report()
                    last_system_report = current_time
                
                # Brief pause to prevent CPU overload
                time.sleep(10)
                
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received, shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(30)  # Wait longer on error
        
        logger.info("Main loop ended")
    
    def shutdown(self):
        """Gracefully shutdown the system"""
        logger.info("Initiating system shutdown...")
        
        self.running = False
        self.shutdown_requested = True
        
        try:
            # Generate final system report
            final_report = self._generate_system_report()
            
            # Log shutdown metrics
            shutdown_metrics = {
                "shutdown_time": datetime.now().isoformat(),
                "total_uptime": (datetime.now() - self.startup_time).total_seconds(),
                "final_metrics": self.metrics,
                "graceful_shutdown": True
            }
            
            with open(f"logs/system/shutdown_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
                import json
                json.dump(shutdown_metrics, f, indent=2)
            
            logger.info("System shutdown completed successfully")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            "running": self.running,
            "startup_time": self.startup_time.isoformat(),
            "uptime_seconds": (datetime.now() - self.startup_time).total_seconds(),
            "metrics": self.metrics,
            "config": self.config,
            "orchestrator_status": self.orchestrator.get_system_overview() if self.orchestrator else None,
            "task_system_status": self.task_system.get_system_status() if self.task_system else None
        }

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Karen AI Secretary - Personal Assistant System")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--email-only", action="store_true", help="Enable only email monitoring")
    parser.add_argument("--check-interval", type=int, default=60, help="Email check interval in seconds")
    
    args = parser.parse_args()
    
    # Prepare configuration overrides
    config_overrides = {}
    
    if args.debug:
        config_overrides["debug_mode"] = True
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.email_only:
        config_overrides.update({
            "enable_sms_monitoring": False,
            "enable_voice_monitoring": False
        })
    
    if args.check_interval:
        config_overrides["email_check_interval"] = args.check_interval
    
    # Initialize and start Karen
    karen = KarenAISecretary(config_overrides)
    
    try:
        karen.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
    finally:
        karen.shutdown()

if __name__ == "__main__":
    main()
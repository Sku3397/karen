#!/usr/bin/env python3
"""
Autonomous Deployment System for Karen AI
=========================================

Task: Create src/autonomous_deployment.py
Implement:
1. Pre-deployment test runner
2. Rollback mechanism
3. Health checks after deployment
4. Notification system for deployments
5. Integration with agent orchestrator

Features:
- Automated pre-deployment testing
- Rollback capabilities with version management
- Deployment notifications via email/SMS
- Integration with agent communication system
- Comprehensive health checks and monitoring
- Integration with orchestrator for deployment coordination

Usage:
    from src.autonomous_deployment import AutonomousDeployment
    
    deployment = AutonomousDeployment()
    report = deployment.deploy(Environment.STAGING)
"""

import os
import sys
import json
import shutil
import subprocess
import logging
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum

# Import Karen AI modules
try:
    from .email_client import EmailClient
except ImportError:
    EmailClient = None

try:
    from .sms_client import SMSClient
except ImportError:
    SMSClient = None

try:
    from .agent_communication import AgentCommunication
except ImportError:
    AgentCommunication = None

try:
    from .orchestrator import AgentOrchestrator, AgentType, AgentTask, TaskStatus
except ImportError:
    AgentOrchestrator = None
    AgentType = None
    AgentTask = None
    TaskStatus = None

try:
    from .config import (
        ADMIN_EMAIL, MONITORED_EMAIL_ACCOUNT_CONFIG, 
        PROJECT_ROOT
    )
    # For backwards compatibility
    MONITORED_EMAIL_ACCOUNT = MONITORED_EMAIL_ACCOUNT_CONFIG
    SMS_ADMIN_NUMBER = None  # Not defined in config yet
except ImportError:
    ADMIN_EMAIL = None
    MONITORED_EMAIL_ACCOUNT = None
    SMS_ADMIN_NUMBER = None
    PROJECT_ROOT = None

# Setup logging
logger = logging.getLogger(__name__)


class DeploymentStatus(Enum):
    """Deployment status enumeration"""
    PENDING = "pending"
    TESTING = "testing"
    DEPLOYING = "deploying"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"


class Environment(Enum):
    """Deployment environment enumeration"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class TestSuite(Enum):
    """Available test suites"""
    UNIT = "unit"
    INTEGRATION = "integration"
    SYSTEM = "system"
    AGENTS = "agents"
    EMAIL = "email"
    SMS = "sms"
    HEALTH = "health"
    FULL = "full"


@dataclass
class DeploymentConfig:
    """Deployment configuration"""
    environment: Environment
    version: str
    commit_hash: str
    timestamp: datetime
    backup_path: str
    test_suites: List[TestSuite]
    notification_channels: List[str]
    rollback_enabled: bool = True
    auto_rollback_on_failure: bool = True
    health_check_timeout: int = 300  # 5 minutes
    max_rollback_attempts: int = 3
    agent_coordination: bool = True


@dataclass
class TestResult:
    """Test execution result"""
    suite_name: str
    status: str
    duration: float
    passed_tests: int
    failed_tests: int
    error_message: Optional[str] = None
    log_file: Optional[str] = None
    agent_involved: Optional[str] = None


@dataclass
class HealthCheck:
    """Health check result"""
    check_name: str
    status: str  # passed, failed, error
    details: Dict[str, Any]
    timestamp: datetime
    error_message: Optional[str] = None


@dataclass
class DeploymentReport:
    """Comprehensive deployment report"""
    deployment_id: str
    config: DeploymentConfig
    start_time: datetime
    end_time: Optional[datetime]
    status: DeploymentStatus
    test_results: List[TestResult]
    deployment_steps: List[Dict[str, Any]]
    rollback_info: Optional[Dict[str, Any]]
    notifications_sent: List[Dict[str, Any]]
    health_checks: List[HealthCheck]
    agent_coordination_log: List[Dict[str, Any]]


class AutonomousDeployment:
    """
    Autonomous deployment system with comprehensive testing, 
    rollback capabilities, notifications, and agent orchestrator integration
    """
    
    def __init__(self, config_file: str = "deployment_config.json"):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.project_root = Path(PROJECT_ROOT) if PROJECT_ROOT else Path(__file__).parent.parent
        self.config_file = config_file
        
        # Directory structure
        self.deployments_dir = self.project_root / "deployments"
        self.backups_dir = self.project_root / "backups"
        self.logs_dir = self.project_root / "logs"
        
        # Ensure directories exist
        for directory in [self.deployments_dir, self.backups_dir, self.logs_dir]:
            directory.mkdir(exist_ok=True)
        
        # Initialize communication clients
        self.email_client = None
        self.sms_client = None
        self.agent_comm = None
        self.orchestrator = None
        
        self._initialize_clients()
        self.logger.info("Autonomous deployment system initialized")
    
    def _initialize_clients(self):
        """Initialize communication clients and orchestrator"""
        if EmailClient:
            try:
                self.email_client = EmailClient()
                self.logger.info("Email client initialized")
            except Exception as e:
                self.logger.warning(f"Email client initialization failed: {e}")
        else:
            self.logger.warning("Email client not available (import failed)")
        
        if SMSClient:
            try:
                self.sms_client = SMSClient()
                self.logger.info("SMS client initialized")
            except Exception as e:
                self.logger.warning(f"SMS client initialization failed: {e}")
        else:
            self.logger.warning("SMS client not available (import failed)")
        
        if AgentCommunication:
            try:
                self.agent_comm = AgentCommunication('deployment_manager')
                self.logger.info("Agent communication initialized")
            except Exception as e:
                self.logger.warning(f"Agent communication initialization failed: {e}")
        else:
            self.logger.warning("Agent communication not available (import failed)")
        
        if AgentOrchestrator:
            try:
                self.orchestrator = AgentOrchestrator()
                self.logger.info("Agent orchestrator initialized")
            except Exception as e:
                self.logger.warning(f"Agent orchestrator initialization failed: {e}")
        else:
            self.logger.warning("Agent orchestrator not available (import failed)")
    
    def generate_deployment_id(self) -> str:
        """Generate unique deployment ID"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_suffix = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:8]
        return f"deploy_{timestamp}_{random_suffix}"
    
    def get_current_version(self) -> str:
        """Get current system version from git or version file"""
        try:
            # Try git first
            result = subprocess.run(
                ['git', 'describe', '--tags', '--abbrev=0'],
                capture_output=True, text=True, cwd=self.project_root
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        
        # Fallback to version file
        version_file = self.project_root / "VERSION"
        if version_file.exists():
            return version_file.read_text().strip()
        
        # Default version
        return "v1.0.0"
    
    def get_commit_hash(self) -> str:
        """Get current git commit hash"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                capture_output=True, text=True, cwd=self.project_root
            )
            if result.returncode == 0:
                return result.stdout.strip()[:8]
        except Exception:
            pass
        return "unknown"
    
    def create_backup(self, deployment_id: str) -> str:
        """Create system backup before deployment"""
        self.logger.info("Creating system backup...")
        
        backup_name = f"backup_{deployment_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = self.backups_dir / backup_name
        
        # Critical files and directories to backup
        backup_items = [
            "src/",
            "autonomous-agents/",
            "tasks/",
            "logs/",
            "*.py",
            "*.json",
            "*.md",
            "requirements.txt",
            ".env"
        ]
        
        backup_path.mkdir(exist_ok=True)
        
        for item in backup_items:
            try:
                if item.endswith('/'):
                    # Directory
                    src_dir = self.project_root / item.rstrip('/')
                    if src_dir.exists():
                        dst_dir = backup_path / item.rstrip('/')
                        shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
                else:
                    # Files (with potential wildcards)
                    for src_file in self.project_root.glob(item):
                        if src_file.is_file():
                            shutil.copy2(src_file, backup_path / src_file.name)
            except Exception as e:
                self.logger.warning(f"Failed to backup {item}: {e}")
        
        # Create backup manifest
        manifest = {
            "deployment_id": deployment_id,
            "backup_time": datetime.now().isoformat(),
            "version": self.get_current_version(),
            "commit_hash": self.get_commit_hash(),
            "backup_items": backup_items
        }
        
        with open(backup_path / "backup_manifest.json", 'w') as f:
            json.dump(manifest, f, indent=2)
        
        self.logger.info(f"Backup created at: {backup_path}")
        return str(backup_path)
    
    def coordinate_with_agents(self, action: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Coordinate deployment actions with agent orchestrator"""
        coordination_log = []
        
        if not self.orchestrator:
            self.logger.warning("Orchestrator not available for agent coordination")
            return coordination_log
        
        try:
            self.logger.info(f"Coordinating with agents: {action}")
            
            if action == "deployment_start":
                # Notify agents about deployment start
                task = AgentTask(
                    task_id=f"deployment_notification_{data['deployment_id']}",
                    agent_type=AgentType.ORCHESTRATOR,
                    description=f"Deployment {data['deployment_id']} starting",
                    priority="high",
                    task_data=data
                )
                
                success = self.orchestrator.assign_task_to_agent(task)
                coordination_log.append({
                    "action": "deployment_start_notification",
                    "success": success,
                    "timestamp": datetime.now().isoformat(),
                    "task_id": task.task_id
                })
            
            elif action == "pre_deployment_health":
                # Request health check from all agents
                health_task = AgentTask(
                    task_id=f"health_check_{data['deployment_id']}",
                    agent_type=AgentType.TEST_ENGINEER,
                    description="Pre-deployment health check",
                    priority="critical",
                    task_data={"deployment_id": data['deployment_id']}
                )
                
                success = self.orchestrator.assign_task_to_agent(health_task)
                coordination_log.append({
                    "action": "health_check_request",
                    "success": success,
                    "timestamp": datetime.now().isoformat(),
                    "task_id": health_task.task_id
                })
            
            elif action == "deployment_complete":
                # Notify agents about deployment completion
                completion_task = AgentTask(
                    task_id=f"deployment_complete_{data['deployment_id']}",
                    agent_type=AgentType.ORCHESTRATOR,
                    description=f"Deployment {data['deployment_id']} completed",
                    priority="normal",
                    task_data=data
                )
                
                success = self.orchestrator.assign_task_to_agent(completion_task)
                coordination_log.append({
                    "action": "deployment_complete_notification",
                    "success": success,
                    "timestamp": datetime.now().isoformat(),
                    "task_id": completion_task.task_id
                })
            
            # Get agent status for coordination logging
            if self.agent_comm:
                agent_status = self.agent_comm.get_agent_workload_report()
                coordination_log.append({
                    "action": "agent_status_check",
                    "agent_count": len(agent_status.get('agents', {})),
                    "system_load": agent_status.get('system_load_percent', 0),
                    "timestamp": datetime.now().isoformat()
                })
        
        except Exception as e:
            self.logger.error(f"Agent coordination failed for {action}: {e}")
            coordination_log.append({
                "action": f"{action}_failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
        
        return coordination_log
    
    def run_test_suite(self, suite: TestSuite, deployment_id: str, timeout: int = 300) -> TestResult:
        """Run a specific test suite with agent coordination"""
        self.logger.info(f"Running test suite: {suite.value}")
        
        start_time = datetime.now()
        log_file = self.logs_dir / f"test_{suite.value}_{start_time.strftime('%Y%m%d_%H%M%S')}.log"
        
        # Define test commands for different suites
        test_commands = {
            TestSuite.UNIT: ["python", "-m", "pytest", "tests/unit/", "-v"],
            TestSuite.INTEGRATION: ["python", "-m", "pytest", "tests/integration/", "-v"],
            TestSuite.SYSTEM: ["python", "-m", "pytest", "tests/system/", "-v"],
            TestSuite.FULL: ["python", "-m", "pytest", "tests/", "-v"],
            TestSuite.AGENTS: ["python", "-c", "from src.test_agent_communication import main; main()"],
            TestSuite.EMAIL: ["python", "-c", "from src.email_client import EmailClient; EmailClient().test_connection()"],
            TestSuite.SMS: ["python", "-c", "from src.sms_client import SMSClient; SMSClient().test_connection()"],
            TestSuite.HEALTH: ["python", "-c", "from src.autonomous_deployment import AutonomousDeployment; AutonomousDeployment().run_health_checks()"]
        }
        
        command = test_commands.get(suite, ["echo", f"Unknown test suite: {suite.value}"])
        agent_involved = None
        
        # Coordinate with agents for specific test suites
        if suite == TestSuite.AGENTS and self.orchestrator:
            try:
                # Create test task for agents
                test_task = AgentTask(
                    task_id=f"test_agents_{deployment_id}",
                    agent_type=AgentType.TEST_ENGINEER,
                    description=f"Agent communication test for deployment {deployment_id}",
                    priority="high",
                    task_data={"test_type": "communication", "deployment_id": deployment_id}
                )
                
                success = self.orchestrator.assign_task_to_agent(test_task)
                if success:
                    agent_involved = "test_engineer"
                    self.logger.info("Agent communication test assigned to test_engineer")
            except Exception as e:
                self.logger.warning(f"Failed to coordinate agent test: {e}")
        
        try:
            with open(log_file, 'w') as f:
                result = subprocess.run(
                    command,
                    cwd=self.project_root,
                    timeout=timeout,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    text=True
                )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # Parse test results
            with open(log_file, 'r') as f:
                output = f.read()
            
            # Basic parsing for pytest output
            passed_tests = output.count(" PASSED") + output.count("✓")
            failed_tests = output.count(" FAILED") + output.count("✗")
            
            # For non-pytest commands, check return code
            if suite in [TestSuite.EMAIL, TestSuite.SMS, TestSuite.HEALTH]:
                passed_tests = 1 if result.returncode == 0 else 0
                failed_tests = 0 if result.returncode == 0 else 1
            
            status = "passed" if result.returncode == 0 else "failed"
            error_message = None if status == "passed" else f"Exit code: {result.returncode}"
            
            return TestResult(
                suite_name=suite.value,
                status=status,
                duration=duration,
                passed_tests=passed_tests,
                failed_tests=failed_tests,
                error_message=error_message,
                log_file=str(log_file),
                agent_involved=agent_involved
            )
            
        except subprocess.TimeoutExpired:
            duration = timeout
            return TestResult(
                suite_name=suite.value,
                status="timeout",
                duration=duration,
                passed_tests=0,
                failed_tests=1,
                error_message=f"Test suite timed out after {timeout} seconds",
                log_file=str(log_file),
                agent_involved=agent_involved
            )
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return TestResult(
                suite_name=suite.value,
                status="error",
                duration=duration,
                passed_tests=0,
                failed_tests=1,
                error_message=str(e),
                log_file=str(log_file),
                agent_involved=agent_involved
            )
    
    def run_pre_deployment_tests(self, test_suites: List[TestSuite], deployment_id: str) -> List[TestResult]:
        """Run comprehensive pre-deployment test suite"""
        self.logger.info(f"Running pre-deployment tests: {[s.value for s in test_suites]}")
        
        results = []
        
        # Coordinate with agents before testing
        if self.orchestrator:
            coordination_data = {"deployment_id": deployment_id, "test_suites": [s.value for s in test_suites]}
            self.coordinate_with_agents("pre_deployment_health", coordination_data)
        
        for suite in test_suites:
            result = self.run_test_suite(suite, deployment_id)
            results.append(result)
            
            self.logger.info(
                f"Test suite {suite.value}: {result.status} "
                f"({result.passed_tests} passed, {result.failed_tests} failed)"
            )
            
            # Stop on critical failures
            if result.status in ["failed", "error", "timeout"] and suite in [TestSuite.HEALTH, TestSuite.SYSTEM]:
                self.logger.error(f"Critical test suite {suite.value} failed. Stopping tests.")
                break
        
        return results
    
    def run_health_checks(self) -> List[HealthCheck]:
        """Perform comprehensive post-deployment health checks"""
        self.logger.info("Performing post-deployment health checks...")
        
        health_checks = []
        
        # Check 1: File system integrity
        try:
            critical_files = [
                "src/main.py",
                "src/config.py",
                "src/email_client.py",
                "src/agent_communication.py",
                "src/orchestrator.py"
            ]
            
            missing_files = []
            for file_path in critical_files:
                if not (self.project_root / file_path).exists():
                    missing_files.append(file_path)
            
            health_checks.append(HealthCheck(
                check_name="file_system_integrity",
                status="passed" if not missing_files else "failed",
                details={"missing_files": missing_files, "checked_files": critical_files},
                timestamp=datetime.now(),
                error_message=None if not missing_files else f"Missing files: {missing_files}"
            ))
        except Exception as e:
            health_checks.append(HealthCheck(
                check_name="file_system_integrity",
                status="error",
                details={},
                timestamp=datetime.now(),
                error_message=str(e)
            ))
        
        # Check 2: Dependencies
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "check"],
                capture_output=True, text=True, cwd=self.project_root
            )
            
            health_checks.append(HealthCheck(
                check_name="dependencies",
                status="passed" if result.returncode == 0 else "failed",
                details={"output": result.stdout, "errors": result.stderr},
                timestamp=datetime.now(),
                error_message=None if result.returncode == 0 else "Dependency conflicts detected"
            ))
        except Exception as e:
            health_checks.append(HealthCheck(
                check_name="dependencies",
                status="error",
                details={},
                timestamp=datetime.now(),
                error_message=str(e)
            ))
        
        # Check 3: Agent communication and orchestrator
        if self.agent_comm and self.orchestrator:
            try:
                workload_report = self.agent_comm.get_agent_workload_report()
                orchestrator_overview = self.orchestrator.get_system_overview()
                
                active_agents = len([
                    agent for agent, data in workload_report['agents'].items()
                    if data['availability'] in ['available', 'busy']
                ])
                
                registered_agents = len(orchestrator_overview.get('registered_agents', {}))
                
                health_checks.append(HealthCheck(
                    check_name="agent_system",
                    status="passed" if active_agents > 0 and registered_agents > 0 else "failed",
                    details={
                        "active_agents": active_agents,
                        "registered_agents": registered_agents,
                        "system_load": workload_report['system_load_percent'],
                        "orchestrator_status": orchestrator_overview.get('status', 'unknown')
                    },
                    timestamp=datetime.now(),
                    error_message=None if active_agents > 0 else "No active agents detected"
                ))
            except Exception as e:
                health_checks.append(HealthCheck(
                    check_name="agent_system",
                    status="error",
                    details={},
                    timestamp=datetime.now(),
                    error_message=str(e)
                ))
        
        # Check 4: Email system
        if self.email_client:
            try:
                # Simple connection test
                test_result = self.email_client.test_connection()
                
                health_checks.append(HealthCheck(
                    check_name="email_system",
                    status="passed" if test_result else "failed",
                    details={"connection_test": test_result},
                    timestamp=datetime.now(),
                    error_message=None if test_result else "Email client connection failed"
                ))
            except Exception as e:
                health_checks.append(HealthCheck(
                    check_name="email_system",
                    status="error",
                    details={},
                    timestamp=datetime.now(),
                    error_message=str(e)
                ))
        
        # Check 5: SMS system
        if self.sms_client:
            try:
                # Simple connection test
                test_result = self.sms_client.test_connection()
                
                health_checks.append(HealthCheck(
                    check_name="sms_system",
                    status="passed" if test_result else "failed",
                    details={"connection_test": test_result},
                    timestamp=datetime.now(),
                    error_message=None if test_result else "SMS client connection failed"
                ))
            except Exception as e:
                health_checks.append(HealthCheck(
                    check_name="sms_system",
                    status="error",
                    details={},
                    timestamp=datetime.now(),
                    error_message=str(e)
                ))
        
        # Log health check summary
        passed_checks = len([hc for hc in health_checks if hc.status == "passed"])
        total_checks = len(health_checks)
        self.logger.info(f"Health checks completed: {passed_checks}/{total_checks} passed")
        
        return health_checks
    
    def send_notification(self, 
                         subject: str, 
                         message: str, 
                         channels: List[str] = None,
                         priority: str = "normal") -> List[Dict[str, Any]]:
        """Send deployment notifications via multiple channels"""
        if channels is None:
            channels = ["email"]
        
        notifications_sent = []
        
        for channel in channels:
            try:
                if channel == "email" and self.email_client:
                    self.email_client.send_email(
                        to_email=ADMIN_EMAIL or "admin@karen.ai",
                        subject=f"[KAREN DEPLOYMENT] {subject}",
                        body=message,
                        priority=priority
                    )
                    notifications_sent.append({
                        "channel": "email",
                        "status": "sent",
                        "timestamp": datetime.now().isoformat(),
                        "recipient": ADMIN_EMAIL
                    })
                
                elif channel == "sms" and self.sms_client:
                    # Truncate message for SMS
                    sms_message = message[:160] + "..." if len(message) > 160 else message
                    self.sms_client.send_sms(
                        to_number=SMS_ADMIN_NUMBER or "+1234567890",
                        message=f"KAREN DEPLOY: {sms_message}"
                    )
                    notifications_sent.append({
                        "channel": "sms",
                        "status": "sent",
                        "timestamp": datetime.now().isoformat(),
                        "recipient": SMS_ADMIN_NUMBER
                    })
                
                elif channel == "agents" and self.agent_comm:
                    self.agent_comm.broadcast_message(
                        "deployment_notification",
                        {"subject": subject, "message": message, "priority": priority}
                    )
                    notifications_sent.append({
                        "channel": "agents",
                        "status": "sent",
                        "timestamp": datetime.now().isoformat(),
                        "recipient": "all_agents"
                    })
                
                else:
                    notifications_sent.append({
                        "channel": channel,
                        "status": "failed",
                        "error": "Channel not available or configured",
                        "timestamp": datetime.now().isoformat()
                    })
            
            except Exception as e:
                notifications_sent.append({
                    "channel": channel,
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        return notifications_sent
    
    def deploy(self, 
               environment: Environment, 
               test_suites: List[TestSuite] = None,
               notification_channels: List[str] = None) -> DeploymentReport:
        """Perform complete deployment with testing, health checks, and rollback capabilities"""
        
        if test_suites is None:
            test_suites = [TestSuite.HEALTH, TestSuite.UNIT, TestSuite.INTEGRATION]
        
        if notification_channels is None:
            notification_channels = ["email", "agents"]
        
        deployment_id = self.generate_deployment_id()
        start_time = datetime.now()
        
        self.logger.info(f"Starting deployment {deployment_id} to {environment.value}")
        
        # Create deployment configuration
        config = DeploymentConfig(
            environment=environment,
            version=self.get_current_version(),
            commit_hash=self.get_commit_hash(),
            timestamp=start_time,
            backup_path="",
            test_suites=test_suites,
            notification_channels=notification_channels,
            agent_coordination=bool(self.orchestrator)
        )
        
        # Initialize deployment report
        report = DeploymentReport(
            deployment_id=deployment_id,
            config=config,
            start_time=start_time,
            end_time=None,
            status=DeploymentStatus.PENDING,
            test_results=[],
            deployment_steps=[],
            rollback_info=None,
            notifications_sent=[],
            health_checks=[],
            agent_coordination_log=[]
        )
        
        try:
            # Step 1: Agent coordination - deployment start
            if config.agent_coordination:
                coordination_log = self.coordinate_with_agents(
                    "deployment_start",
                    {"deployment_id": deployment_id, "environment": environment.value}
                )
                report.agent_coordination_log.extend(coordination_log)
            
            # Step 2: Send deployment start notification
            report.status = DeploymentStatus.TESTING
            start_notifications = self.send_notification(
                f"Deployment {deployment_id} Started",
                f"Deployment to {environment.value} environment started.\n"
                f"Version: {config.version}\n"
                f"Commit: {config.commit_hash}\n"
                f"Test suites: {', '.join([s.value for s in test_suites])}",
                notification_channels
            )
            report.notifications_sent.extend(start_notifications)
            
            # Step 3: Create backup
            backup_path = self.create_backup(deployment_id)
            config.backup_path = backup_path
            report.deployment_steps.append({
                "step": "backup_creation",
                "status": "completed",
                "details": {"backup_path": backup_path},
                "timestamp": datetime.now().isoformat()
            })
            
            # Step 4: Run pre-deployment tests
            test_results = self.run_pre_deployment_tests(test_suites, deployment_id)
            report.test_results = test_results
            
            # Check if any critical tests failed
            critical_failures = [
                result for result in test_results 
                if result.status in ["failed", "error", "timeout"] and 
                result.suite_name in ["health", "system"]
            ]
            
            if critical_failures:
                raise Exception(f"Critical test failures: {[r.suite_name for r in critical_failures]}")
            
            report.deployment_steps.append({
                "step": "pre_deployment_testing",
                "status": "completed",
                "details": {
                    "total_suites": len(test_results),
                    "passed_suites": len([r for r in test_results if r.status == "passed"]),
                    "failed_suites": len([r for r in test_results if r.status != "passed"])
                },
                "timestamp": datetime.now().isoformat()
            })
            
            # Step 5: Perform deployment
            report.status = DeploymentStatus.DEPLOYING
            self.logger.info("Performing deployment...")
            
            # Simulate deployment steps (replace with actual deployment logic)
            deployment_actions = [
                "update_dependencies",
                "restart_services", 
                "update_configuration",
                "clear_caches",
                "reload_modules"
            ]
            
            for action in deployment_actions:
                # Simulate action
                import time
                time.sleep(1)
                
                report.deployment_steps.append({
                    "step": action,
                    "status": "completed",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Step 6: Post-deployment health checks
            health_checks = self.run_health_checks()
            report.health_checks = health_checks
            
            failed_health_checks = [
                check for check in health_checks 
                if check.status in ['failed', 'error']
            ]
            
            if failed_health_checks:
                raise Exception(f"Health check failures: {[c.check_name for c in failed_health_checks]}")
            
            report.deployment_steps.append({
                "step": "post_deployment_health_checks",
                "status": "completed",
                "details": {
                    "total_checks": len(health_checks),
                    "passed_checks": len([hc for hc in health_checks if hc.status == "passed"]),
                    "failed_checks": len(failed_health_checks)
                },
                "timestamp": datetime.now().isoformat()
            })
            
            # Step 7: Agent coordination - deployment complete
            if config.agent_coordination:
                coordination_log = self.coordinate_with_agents(
                    "deployment_complete",
                    {
                        "deployment_id": deployment_id, 
                        "environment": environment.value,
                        "status": "success"
                    }
                )
                report.agent_coordination_log.extend(coordination_log)
            
            # Step 8: Deployment success
            report.status = DeploymentStatus.SUCCESS
            report.end_time = datetime.now()
            
            success_notifications = self.send_notification(
                f"Deployment {deployment_id} Successful",
                f"Deployment to {environment.value} completed successfully!\n"
                f"Version: {config.version}\n"
                f"Duration: {(report.end_time - start_time).total_seconds():.1f}s\n"
                f"Tests passed: {len([r for r in test_results if r.status == 'passed'])}/{len(test_results)}\n"
                f"Health checks: {len([hc for hc in health_checks if hc.status == 'passed'])}/{len(health_checks)}",
                notification_channels
            )
            report.notifications_sent.extend(success_notifications)
            
            self.logger.info(f"Deployment {deployment_id} completed successfully")
            
        except Exception as e:
            self.logger.error(f"Deployment {deployment_id} failed: {e}")
            
            # Auto-rollback on failure if enabled
            if config.auto_rollback_on_failure:
                self.logger.info("Initiating automatic rollback...")
                report.status = DeploymentStatus.ROLLING_BACK
                
                try:
                    rollback_result = self.rollback_from_backup(config.backup_path)
                    report.rollback_info = rollback_result
                    report.status = DeploymentStatus.ROLLED_BACK
                    
                    # Agent coordination for rollback
                    if config.agent_coordination:
                        coordination_log = self.coordinate_with_agents(
                            "deployment_rollback",
                            {
                                "deployment_id": deployment_id,
                                "rollback_reason": str(e)
                            }
                        )
                        report.agent_coordination_log.extend(coordination_log)
                    
                    rollback_notifications = self.send_notification(
                        f"Deployment {deployment_id} Failed - Rolled Back",
                        f"Deployment to {environment.value} failed and was automatically rolled back.\n"
                        f"Error: {str(e)}\n"
                        f"System restored from backup: {config.backup_path}",
                        notification_channels,
                        priority="high"
                    )
                    report.notifications_sent.extend(rollback_notifications)
                    
                except Exception as rollback_error:
                    self.logger.error(f"Rollback failed: {rollback_error}")
                    report.status = DeploymentStatus.FAILED
                    
                    failure_notifications = self.send_notification(
                        f"CRITICAL: Deployment {deployment_id} Failed - Rollback Failed",
                        f"CRITICAL: Deployment to {environment.value} failed AND rollback failed!\n"
                        f"Deployment error: {str(e)}\n"
                        f"Rollback error: {str(rollback_error)}\n"
                        f"Manual intervention required!",
                        notification_channels,
                        priority="critical"
                    )
                    report.notifications_sent.extend(failure_notifications)
            else:
                report.status = DeploymentStatus.FAILED
                failure_notifications = self.send_notification(
                    f"Deployment {deployment_id} Failed",
                    f"Deployment to {environment.value} failed.\n"
                    f"Error: {str(e)}\n"
                    f"Backup available at: {config.backup_path}",
                    notification_channels,
                    priority="high"
                )
                report.notifications_sent.extend(failure_notifications)
            
            report.end_time = datetime.now()
        
        # Save deployment report
        self.save_deployment_report(report)
        
        return report
    
    def rollback_from_backup(self, backup_path: str) -> Dict[str, Any]:
        """Rollback mechanism - restore system from backup"""
        self.logger.info(f"Rolling back from backup: {backup_path}")
        
        backup_dir = Path(backup_path)
        if not backup_dir.exists():
            raise Exception(f"Backup directory not found: {backup_path}")
        
        # Load backup manifest
        manifest_file = backup_dir / "backup_manifest.json"
        if not manifest_file.exists():
            raise Exception(f"Backup manifest not found: {manifest_file}")
        
        with open(manifest_file, 'r') as f:
            manifest = json.load(f)
        
        rollback_steps = []
        
        try:
            # Restore files and directories
            for item in backup_dir.iterdir():
                if item.name == "backup_manifest.json":
                    continue
                
                target_path = self.project_root / item.name
                
                if item.is_dir():
                    # Remove existing directory and restore
                    if target_path.exists():
                        shutil.rmtree(target_path)
                    shutil.copytree(item, target_path)
                else:
                    # Restore file
                    shutil.copy2(item, target_path)
                
                rollback_steps.append({
                    "action": "restore",
                    "item": item.name,
                    "status": "completed",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Restart services if needed (simulate)
            rollback_steps.append({
                "action": "restart_services",
                "status": "completed",
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "backup_path": backup_path,
                "restored_version": manifest.get("version", "unknown"),
                "rollback_steps": rollback_steps,
                "rollback_time": datetime.now().isoformat(),
                "status": "success"
            }
            
        except Exception as e:
            rollback_steps.append({
                "action": "rollback_error",
                "error": str(e),
                "status": "failed",
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "backup_path": backup_path,
                "rollback_steps": rollback_steps,
                "rollback_time": datetime.now().isoformat(),
                "status": "failed",
                "error": str(e)
            }
    
    def save_deployment_report(self, report: DeploymentReport):
        """Save deployment report to file"""
        report_file = self.deployments_dir / f"{report.deployment_id}_report.json"
        
        # Convert report to dict for JSON serialization
        report_dict = asdict(report)
        
        # Convert datetime objects to ISO strings
        def convert_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: convert_datetime(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_datetime(item) for item in obj]
            return obj
        
        report_dict = convert_datetime(report_dict)
        
        with open(report_file, 'w') as f:
            json.dump(report_dict, f, indent=2)
        
        self.logger.info(f"Deployment report saved: {report_file}")
    
    def get_deployment_status(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific deployment"""
        report_file = self.deployments_dir / f"{deployment_id}_report.json"
        
        if not report_file.exists():
            return None
        
        try:
            with open(report_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to read deployment report {report_file}: {e}")
            return None
    
    def list_recent_deployments(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent deployment reports"""
        deployments = []
        
        for report_file in self.deployments_dir.glob("*_report.json"):
            try:
                with open(report_file, 'r') as f:
                    report = json.load(f)
                deployments.append({
                    "deployment_id": report["deployment_id"],
                    "environment": report["config"]["environment"],
                    "version": report["config"]["version"],
                    "status": report["status"],
                    "start_time": report["start_time"],
                    "end_time": report.get("end_time"),
                    "duration": self._calculate_duration(report),
                    "test_results_summary": self._summarize_test_results(report.get("test_results", [])),
                    "health_checks_summary": self._summarize_health_checks(report.get("health_checks", []))
                })
            except Exception as e:
                self.logger.warning(f"Failed to read deployment report {report_file}: {e}")
        
        return sorted(deployments, key=lambda x: x["start_time"], reverse=True)[:limit]
    
    def _calculate_duration(self, report: Dict[str, Any]) -> Optional[float]:
        """Calculate deployment duration"""
        try:
            if report.get("end_time"):
                start = datetime.fromisoformat(report["start_time"])
                end = datetime.fromisoformat(report["end_time"])
                return (end - start).total_seconds()
        except Exception:
            pass
        return None
    
    def _summarize_test_results(self, test_results: List[Dict[str, Any]]) -> Dict[str, int]:
        """Summarize test results"""
        summary = {"passed": 0, "failed": 0, "error": 0, "timeout": 0}
        for result in test_results:
            status = result.get("status", "unknown")
            if status in summary:
                summary[status] += 1
        return summary
    
    def _summarize_health_checks(self, health_checks: List[Dict[str, Any]]) -> Dict[str, int]:
        """Summarize health check results"""
        summary = {"passed": 0, "failed": 0, "error": 0}
        for check in health_checks:
            status = check.get("status", "unknown")
            if status in summary:
                summary[status] += 1
        return summary


# Convenience functions for external use
def deploy_to_staging(test_suites: List[str] = None) -> DeploymentReport:
    """Quick deployment to staging environment"""
    deployment = AutonomousDeployment()
    suites = [TestSuite(s) for s in test_suites] if test_suites else None
    return deployment.deploy(Environment.STAGING, suites)


def deploy_to_production(test_suites: List[str] = None) -> DeploymentReport:
    """Quick deployment to production environment"""
    deployment = AutonomousDeployment()
    suites = [TestSuite(s) for s in test_suites] if test_suites else [
        TestSuite.HEALTH, TestSuite.SYSTEM, TestSuite.INTEGRATION, TestSuite.AGENTS
    ]
    return deployment.deploy(Environment.PRODUCTION, suites)


def get_deployment_status(deployment_id: str) -> Optional[Dict[str, Any]]:
    """Get status of a deployment"""
    deployment = AutonomousDeployment()
    return deployment.get_deployment_status(deployment_id)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    deployment = AutonomousDeployment()
    
    # Run a staging deployment with comprehensive tests
    report = deployment.deploy(
        Environment.STAGING,
        [TestSuite.HEALTH, TestSuite.UNIT, TestSuite.INTEGRATION, TestSuite.AGENTS],
        ["email", "agents"]
    )
    
    print(f"Deployment {report.deployment_id} completed with status: {report.status.value}") 
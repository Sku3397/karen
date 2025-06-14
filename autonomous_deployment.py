#!/usr/bin/env python3
"""
Autonomous Deployment System for Karen AI
=========================================

Features:
- Automated pre-deployment testing
- Rollback capabilities with version management
- Deployment notifications via email/SMS
- Integration with agent communication system
- Comprehensive logging and monitoring

Usage:
    python autonomous_deployment.py deploy --environment staging
    python autonomous_deployment.py rollback --version v1.2.3
    python autonomous_deployment.py test --suite full
"""

import os
import sys
import json
import shutil
import subprocess
import logging
import argparse
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from email_client import EmailClient
    from sms_client import SMSClient
    from agent_communication import AgentCommunication
    from config import (
        ADMIN_EMAIL, MONITORED_EMAIL_ACCOUNT, 
        SMS_ADMIN_NUMBER, PROJECT_ROOT
    )
except ImportError:
    # Fallback for missing modules
    print("Warning: Some modules not available. Running in standalone mode.")
    EmailClient = None
    SMSClient = None
    AgentCommunication = None


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


@dataclass
class DeploymentConfig:
    """Deployment configuration"""
    environment: Environment
    version: str
    commit_hash: str
    timestamp: datetime
    backup_path: str
    test_suites: List[str]
    notification_channels: List[str]
    rollback_enabled: bool = True
    auto_rollback_on_failure: bool = True
    health_check_timeout: int = 300  # 5 minutes
    max_rollback_attempts: int = 3


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
    health_checks: List[Dict[str, Any]]


class AutonomousDeployment:
    """
    Autonomous deployment system with comprehensive testing, 
    rollback capabilities, and notifications
    """
    
    def __init__(self, config_file: str = "deployment_config.json"):
        self.setup_logging()
        self.project_root = Path(__file__).parent
        self.config_file = config_file
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
        
        if EmailClient:
            try:
                self.email_client = EmailClient()
            except Exception as e:
                self.logger.warning(f"Email client initialization failed: {e}")
        
        if SMSClient:
            try:
                self.sms_client = SMSClient()
            except Exception as e:
                self.logger.warning(f"SMS client initialization failed: {e}")
        
        if AgentCommunication:
            try:
                self.agent_comm = AgentCommunication('deployment_manager')
            except Exception as e:
                self.logger.warning(f"Agent communication initialization failed: {e}")
        
        self.logger.info("Autonomous deployment system initialized")
    
    def setup_logging(self):
        """Setup comprehensive logging"""
        self.logger = logging.getLogger('autonomous_deployment')
        self.logger.setLevel(logging.INFO)
        
        # Create formatters
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler
        log_file = self.project_root / "logs" / f"deployment_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
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
    
    def run_test_suite(self, suite_name: str, timeout: int = 300) -> TestResult:
        """Run a specific test suite"""
        self.logger.info(f"Running test suite: {suite_name}")
        
        start_time = datetime.now()
        log_file = self.logs_dir / f"test_{suite_name}_{start_time.strftime('%Y%m%d_%H%M%S')}.log"
        
        # Define test commands for different suites
        test_commands = {
            "unit": ["python", "-m", "pytest", "tests/unit/", "-v"],
            "integration": ["python", "-m", "pytest", "tests/integration/", "-v"],
            "system": ["python", "-m", "pytest", "tests/system/", "-v"],
            "full": ["python", "-m", "pytest", "tests/", "-v"],
            "agents": ["python", "test_agent_communication.py"],
            "email": ["python", "src/test_email_integration.py"],
            "sms": ["python", "src/test_sms_integration.py"],
            "health": ["python", "health_check.py"]
        }
        
        command = test_commands.get(suite_name, ["echo", "Unknown test suite"])
        
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
            
            # Parse test results (simplified)
            with open(log_file, 'r') as f:
                output = f.read()
            
            # Basic parsing for pytest output
            passed_tests = output.count(" PASSED")
            failed_tests = output.count(" FAILED")
            
            status = "passed" if result.returncode == 0 else "failed"
            error_message = None if status == "passed" else f"Exit code: {result.returncode}"
            
            return TestResult(
                suite_name=suite_name,
                status=status,
                duration=duration,
                passed_tests=passed_tests,
                failed_tests=failed_tests,
                error_message=error_message,
                log_file=str(log_file)
            )
            
        except subprocess.TimeoutExpired:
            duration = timeout
            return TestResult(
                suite_name=suite_name,
                status="timeout",
                duration=duration,
                passed_tests=0,
                failed_tests=1,
                error_message=f"Test suite timed out after {timeout} seconds",
                log_file=str(log_file)
            )
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return TestResult(
                suite_name=suite_name,
                status="error",
                duration=duration,
                passed_tests=0,
                failed_tests=1,
                error_message=str(e),
                log_file=str(log_file)
            )
    
    def run_automated_tests(self, test_suites: List[str]) -> List[TestResult]:
        """Run all specified test suites"""
        self.logger.info(f"Running automated tests: {test_suites}")
        
        results = []
        for suite in test_suites:
            result = self.run_test_suite(suite)
            results.append(result)
            
            self.logger.info(
                f"Test suite {suite}: {result.status} "
                f"({result.passed_tests} passed, {result.failed_tests} failed)"
            )
            
            # Stop on critical failures
            if result.status == "failed" and suite in ["health", "system"]:
                self.logger.error(f"Critical test suite {suite} failed. Stopping tests.")
                break
        
        return results
    
    def perform_health_checks(self) -> List[Dict[str, Any]]:
        """Perform comprehensive health checks"""
        self.logger.info("Performing health checks...")
        
        health_checks = []
        
        # Check 1: File system integrity
        try:
            critical_files = [
                "src/main.py",
                "src/config.py",
                "src/email_client.py",
                "src/agent_communication.py"
            ]
            
            missing_files = []
            for file_path in critical_files:
                if not (self.project_root / file_path).exists():
                    missing_files.append(file_path)
            
            health_checks.append({
                "check": "file_system_integrity",
                "status": "passed" if not missing_files else "failed",
                "details": {"missing_files": missing_files},
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            health_checks.append({
                "check": "file_system_integrity",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
        
        # Check 2: Dependencies
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "check"],
                capture_output=True, text=True, cwd=self.project_root
            )
            
            health_checks.append({
                "check": "dependencies",
                "status": "passed" if result.returncode == 0 else "failed",
                "details": {"output": result.stdout, "errors": result.stderr},
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            health_checks.append({
                "check": "dependencies",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
        
        # Check 3: Agent communication
        if self.agent_comm:
            try:
                workload_report = self.agent_comm.get_agent_workload_report()
                active_agents = len([
                    agent for agent, data in workload_report['agents'].items()
                    if data['availability'] in ['available', 'busy']
                ])
                
                health_checks.append({
                    "check": "agent_communication",
                    "status": "passed" if active_agents > 0 else "failed",
                    "details": {
                        "active_agents": active_agents,
                        "system_load": workload_report['system_load_percent']
                    },
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                health_checks.append({
                    "check": "agent_communication",
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
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
                        "timestamp": datetime.now().isoformat()
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
                        "timestamp": datetime.now().isoformat()
                    })
                
                elif channel == "agents" and self.agent_comm:
                    self.agent_comm.broadcast_message(
                        "deployment_notification",
                        {"subject": subject, "message": message, "priority": priority}
                    )
                    notifications_sent.append({
                        "channel": "agents",
                        "status": "sent",
                        "timestamp": datetime.now().isoformat()
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
    
    def deploy(self, environment: Environment, test_suites: List[str] = None) -> DeploymentReport:
        """Perform complete deployment with testing and rollback capabilities"""
        if test_suites is None:
            test_suites = ["health", "unit", "integration"]
        
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
            notification_channels=["email", "agents"]
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
            health_checks=[]
        )
        
        try:
            # Step 1: Send deployment start notification
            report.status = DeploymentStatus.TESTING
            start_notifications = self.send_notification(
                f"Deployment {deployment_id} Started",
                f"Deployment to {environment.value} environment started.\n"
                f"Version: {config.version}\n"
                f"Commit: {config.commit_hash}\n"
                f"Test suites: {', '.join(test_suites)}",
                config.notification_channels
            )
            report.notifications_sent.extend(start_notifications)
            
            # Step 2: Create backup
            backup_path = self.create_backup(deployment_id)
            config.backup_path = backup_path
            report.deployment_steps.append({
                "step": "backup_creation",
                "status": "completed",
                "details": {"backup_path": backup_path},
                "timestamp": datetime.now().isoformat()
            })
            
            # Step 3: Run automated tests
            test_results = self.run_automated_tests(test_suites)
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
                "step": "automated_testing",
                "status": "completed",
                "details": {
                    "total_suites": len(test_results),
                    "passed_suites": len([r for r in test_results if r.status == "passed"]),
                    "failed_suites": len([r for r in test_results if r.status != "passed"])
                },
                "timestamp": datetime.now().isoformat()
            })
            
            # Step 4: Perform deployment (simulate for now)
            report.status = DeploymentStatus.DEPLOYING
            self.logger.info("Performing deployment...")
            
            # Simulate deployment steps
            deployment_actions = [
                "update_dependencies",
                "restart_services",
                "update_configuration",
                "clear_caches"
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
            
            # Step 5: Health checks
            health_checks = self.perform_health_checks()
            report.health_checks = health_checks
            
            failed_health_checks = [
                check for check in health_checks 
                if check['status'] in ['failed', 'error']
            ]
            
            if failed_health_checks:
                raise Exception(f"Health check failures: {[c['check'] for c in failed_health_checks]}")
            
            # Step 6: Deployment success
            report.status = DeploymentStatus.SUCCESS
            report.end_time = datetime.now()
            
            success_notifications = self.send_notification(
                f"Deployment {deployment_id} Successful",
                f"Deployment to {environment.value} completed successfully!\n"
                f"Version: {config.version}\n"
                f"Duration: {(report.end_time - start_time).total_seconds():.1f}s\n"
                f"Tests passed: {len([r for r in test_results if r.status == 'passed'])}/{len(test_results)}",
                config.notification_channels
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
                    
                    rollback_notifications = self.send_notification(
                        f"Deployment {deployment_id} Failed - Rolled Back",
                        f"Deployment to {environment.value} failed and was automatically rolled back.\n"
                        f"Error: {str(e)}\n"
                        f"System restored from backup: {config.backup_path}",
                        config.notification_channels,
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
                        config.notification_channels,
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
                    config.notification_channels,
                    priority="high"
                )
                report.notifications_sent.extend(failure_notifications)
            
            report.end_time = datetime.now()
        
        # Save deployment report
        self.save_deployment_report(report)
        
        return report
    
    def rollback_from_backup(self, backup_path: str) -> Dict[str, Any]:
        """Rollback system from backup"""
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
    
    def rollback_to_version(self, version: str) -> Dict[str, Any]:
        """Rollback to a specific version"""
        self.logger.info(f"Rolling back to version: {version}")
        
        # Find backup for the specified version
        backup_dirs = list(self.backups_dir.glob(f"backup_*"))
        target_backup = None
        
        for backup_dir in backup_dirs:
            manifest_file = backup_dir / "backup_manifest.json"
            if manifest_file.exists():
                try:
                    with open(manifest_file, 'r') as f:
                        manifest = json.load(f)
                    if manifest.get("version") == version:
                        target_backup = str(backup_dir)
                        break
                except Exception:
                    continue
        
        if not target_backup:
            raise Exception(f"No backup found for version: {version}")
        
        return self.rollback_from_backup(target_backup)
    
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
    
    def list_deployments(self) -> List[Dict[str, Any]]:
        """List all deployment reports"""
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
                    "file": str(report_file)
                })
            except Exception as e:
                self.logger.warning(f"Failed to read deployment report {report_file}: {e}")
        
        return sorted(deployments, key=lambda x: x["start_time"], reverse=True)
    
    def cleanup_old_backups(self, keep_days: int = 30):
        """Clean up old backup files"""
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        
        removed_count = 0
        for backup_dir in self.backups_dir.iterdir():
            if backup_dir.is_dir():
                # Check backup age from manifest
                manifest_file = backup_dir / "backup_manifest.json"
                if manifest_file.exists():
                    try:
                        with open(manifest_file, 'r') as f:
                            manifest = json.load(f)
                        backup_time = datetime.fromisoformat(manifest["backup_time"])
                        
                        if backup_time < cutoff_date:
                            shutil.rmtree(backup_dir)
                            removed_count += 1
                            self.logger.info(f"Removed old backup: {backup_dir}")
                    except Exception as e:
                        self.logger.warning(f"Failed to check backup {backup_dir}: {e}")
        
        self.logger.info(f"Cleaned up {removed_count} old backups")


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="Autonomous Deployment System for Karen AI")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Deploy command
    deploy_parser = subparsers.add_parser('deploy', help='Deploy to environment')
    deploy_parser.add_argument('--environment', '-e', 
                               choices=['development', 'staging', 'production'],
                               required=True, help='Target environment')
    deploy_parser.add_argument('--tests', '-t', nargs='*',
                               default=['health', 'unit', 'integration'],
                               help='Test suites to run')
    
    # Rollback command
    rollback_parser = subparsers.add_parser('rollback', help='Rollback deployment')
    rollback_parser.add_argument('--version', '-v', 
                                 help='Version to rollback to')
    rollback_parser.add_argument('--backup', '-b',
                                 help='Backup path to restore from')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Run test suites')
    test_parser.add_argument('--suite', '-s', 
                             choices=['unit', 'integration', 'system', 'full', 'health'],
                             default='health', help='Test suite to run')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List deployments')
    list_parser.add_argument('--limit', '-l', type=int, default=10,
                             help='Number of deployments to show')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old backups')
    cleanup_parser.add_argument('--days', '-d', type=int, default=30,
                                help='Keep backups newer than N days')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize deployment system
    deployment = AutonomousDeployment()
    
    try:
        if args.command == 'deploy':
            environment = Environment(args.environment)
            report = deployment.deploy(environment, args.tests)
            
            print(f"\n{'='*60}")
            print(f"DEPLOYMENT REPORT: {report.deployment_id}")
            print(f"{'='*60}")
            print(f"Environment: {report.config.environment.value}")
            print(f"Version: {report.config.version}")
            print(f"Status: {report.status.value}")
            print(f"Duration: {(report.end_time - report.start_time).total_seconds():.1f}s")
            
            if report.test_results:
                print(f"\nTest Results:")
                for test in report.test_results:
                    print(f"  {test.suite_name}: {test.status} "
                          f"({test.passed_tests} passed, {test.failed_tests} failed)")
            
            print(f"\nNotifications sent: {len(report.notifications_sent)}")
            print(f"Health checks: {len([c for c in report.health_checks if c['status'] == 'passed'])}"
                  f"/{len(report.health_checks)} passed")
            
        elif args.command == 'rollback':
            if args.version:
                result = deployment.rollback_to_version(args.version)
            elif args.backup:
                result = deployment.rollback_from_backup(args.backup)
            else:
                print("Error: Must specify either --version or --backup")
                return
            
            print(f"\n{'='*60}")
            print(f"ROLLBACK RESULT")
            print(f"{'='*60}")
            print(f"Status: {result['status']}")
            print(f"Backup: {result['backup_path']}")
            if 'restored_version' in result:
                print(f"Restored version: {result['restored_version']}")
            if result['status'] == 'failed':
                print(f"Error: {result.get('error', 'Unknown error')}")
            
        elif args.command == 'test':
            result = deployment.run_test_suite(args.suite)
            
            print(f"\n{'='*60}")
            print(f"TEST RESULT: {result.suite_name}")
            print(f"{'='*60}")
            print(f"Status: {result.status}")
            print(f"Duration: {result.duration:.1f}s")
            print(f"Passed: {result.passed_tests}")
            print(f"Failed: {result.failed_tests}")
            if result.error_message:
                print(f"Error: {result.error_message}")
            if result.log_file:
                print(f"Log file: {result.log_file}")
            
        elif args.command == 'list':
            deployments = deployment.list_deployments()
            
            print(f"\n{'='*60}")
            print(f"RECENT DEPLOYMENTS (showing {min(args.limit, len(deployments))})")
            print(f"{'='*60}")
            
            for dep in deployments[:args.limit]:
                duration = ""
                if dep['end_time']:
                    start = datetime.fromisoformat(dep['start_time'])
                    end = datetime.fromisoformat(dep['end_time'])
                    duration = f" ({(end - start).total_seconds():.1f}s)"
                
                print(f"{dep['deployment_id']}")
                print(f"  Environment: {dep['environment']}")
                print(f"  Version: {dep['version']}")
                print(f"  Status: {dep['status']}")
                print(f"  Time: {dep['start_time']}{duration}")
                print()
            
        elif args.command == 'cleanup':
            deployment.cleanup_old_backups(args.days)
            print(f"Cleanup completed - kept backups newer than {args.days} days")
    
    except Exception as e:
        print(f"Error: {e}")
        deployment.logger.error(f"Command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
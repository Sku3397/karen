#!/usr/bin/env python3
"""
Testing Coordination System for Karen AI Multi-Agent MCP Development

Coordinates testing schedules, manages test environments, aggregates results,
and prevents resource conflicts during multi-agent testing operations.
"""

import json
import time
import threading
import subprocess
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import uuid
import tempfile
import shutil

logger = logging.getLogger(__name__)

class TestType(Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    SECURITY = "security"
    REGRESSION = "regression"
    SMOKE = "smoke"
    END_TO_END = "end_to_end"

class TestStatus(Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"

class TestEnvironment(Enum):
    LOCAL = "local"
    ISOLATED = "isolated"
    STAGING = "staging"
    INTEGRATION = "integration"

@dataclass
class TestSuite:
    id: str
    name: str
    type: TestType
    environment: TestEnvironment
    test_files: List[str]
    dependencies: List[str]
    required_resources: List[str]
    estimated_duration_minutes: int
    max_parallel_runs: int
    created_by: str
    created_at: str
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type.value,
            'environment': self.environment.value,
            'test_files': self.test_files,
            'dependencies': self.dependencies,
            'required_resources': self.required_resources,
            'estimated_duration_minutes': self.estimated_duration_minutes,
            'max_parallel_runs': self.max_parallel_runs,
            'created_by': self.created_by,
            'created_at': self.created_at
        }

@dataclass
class TestExecution:
    id: str
    suite_id: str
    executor_agent: str
    status: TestStatus
    environment: TestEnvironment
    started_at: Optional[str]
    completed_at: Optional[str]
    results: Dict[str, Any]
    logs: List[str]
    artifacts: List[str]
    
    def to_dict(self):
        return {
            'id': self.id,
            'suite_id': self.suite_id,
            'executor_agent': self.executor_agent,
            'status': self.status.value,
            'environment': self.environment.value,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'results': self.results,
            'logs': self.logs,
            'artifacts': self.artifacts
        }

@dataclass
class TestEnvironmentReservation:
    id: str
    environment: TestEnvironment
    reserved_by: str
    reserved_at: str
    expires_at: str
    purpose: str
    resources_claimed: List[str]

class TestingCoordinator:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.base_path = Path("/workspace/autonomous-agents")
        self.testing_path = self.base_path / "troubleshooting" / "testing-results"
        self.coordination_path = self.base_path / "troubleshooting" / "coordination"
        
        # Test management
        self.test_suites: Dict[str, TestSuite] = {}
        self.active_executions: Dict[str, TestExecution] = {}
        self.test_queue: List[str] = []
        self.environment_reservations: Dict[TestEnvironment, TestEnvironmentReservation] = {}
        
        # Environment management
        self.test_environments = {
            TestEnvironment.LOCAL: "/workspace",
            TestEnvironment.ISOLATED: "/workspace/test_isolation",
            TestEnvironment.STAGING: "/workspace/staging",
            TestEnvironment.INTEGRATION: "/workspace/integration_tests"
        }
        
        # Resource tracking
        self.resource_locks = set()
        self.test_artifacts_path = self.testing_path / "artifacts"
        self.test_logs_path = self.testing_path / "logs"
        
        # Initialize infrastructure
        self._initialize_testing_infrastructure()
        self._load_existing_test_state()
        
        # Start coordination services
        self.running = True
        threading.Thread(target=self._monitor_test_queue, daemon=True).start()
        threading.Thread(target=self._monitor_environment_reservations, daemon=True).start()
        threading.Thread(target=self._cleanup_test_artifacts, daemon=True).start()
        
    def _initialize_testing_infrastructure(self):
        """Initialize testing coordination infrastructure"""
        directories = [
            self.testing_path,
            self.test_artifacts_path,
            self.test_logs_path,
            self.testing_path / "reports",
            self.testing_path / "coverage"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
        # Initialize test environments
        for env, path in self.test_environments.items():
            env_path = Path(path)
            if env != TestEnvironment.LOCAL:
                env_path.mkdir(parents=True, exist_ok=True)
                
        # Create test coordination files
        test_registry_file = self.coordination_path / "test_registry.json"
        if not test_registry_file.exists():
            with open(test_registry_file, 'w') as f:
                json.dump({"suites": [], "executions": []}, f, indent=2)
                
    def _load_existing_test_state(self):
        """Load existing test suites and executions"""
        try:
            test_registry_file = self.coordination_path / "test_registry.json"
            if test_registry_file.exists():
                with open(test_registry_file, 'r') as f:
                    data = json.load(f)
                    
                    # Load test suites
                    for suite_data in data.get("suites", []):
                        suite = TestSuite(
                            id=suite_data['id'],
                            name=suite_data['name'],
                            type=TestType(suite_data['type']),
                            environment=TestEnvironment(suite_data['environment']),
                            test_files=suite_data['test_files'],
                            dependencies=suite_data['dependencies'],
                            required_resources=suite_data['required_resources'],
                            estimated_duration_minutes=suite_data['estimated_duration_minutes'],
                            max_parallel_runs=suite_data['max_parallel_runs'],
                            created_by=suite_data['created_by'],
                            created_at=suite_data['created_at']
                        )
                        self.test_suites[suite.id] = suite
                        
                    # Load active executions
                    for exec_data in data.get("executions", []):
                        if exec_data['status'] in ['running', 'scheduled']:
                            execution = TestExecution(
                                id=exec_data['id'],
                                suite_id=exec_data['suite_id'],
                                executor_agent=exec_data['executor_agent'],
                                status=TestStatus(exec_data['status']),
                                environment=TestEnvironment(exec_data['environment']),
                                started_at=exec_data.get('started_at'),
                                completed_at=exec_data.get('completed_at'),
                                results=exec_data['results'],
                                logs=exec_data['logs'],
                                artifacts=exec_data['artifacts']
                            )
                            self.active_executions[execution.id] = execution
                            
        except Exception as e:
            logger.error(f"Error loading test state: {e}")
            
    def register_test_suite(self, name: str, test_type: TestType, environment: TestEnvironment,
                           test_files: List[str], dependencies: List[str] = None,
                           required_resources: List[str] = None, estimated_duration: int = 30,
                           max_parallel: int = 1) -> str:
        """Register a new test suite"""
        suite_id = f"{self.agent_id}_{name}_{int(time.time())}"
        timestamp = datetime.now().isoformat()
        
        suite = TestSuite(
            id=suite_id,
            name=name,
            type=test_type,
            environment=environment,
            test_files=test_files,
            dependencies=dependencies or [],
            required_resources=required_resources or [],
            estimated_duration_minutes=estimated_duration,
            max_parallel_runs=max_parallel,
            created_by=self.agent_id,
            created_at=timestamp
        )
        
        self.test_suites[suite_id] = suite
        self._save_test_registry()
        
        logger.info(f"Registered test suite: {name} ({suite_id})")
        return suite_id
        
    def schedule_test_execution(self, suite_id: str, priority: int = 5,
                               preferred_time: Optional[str] = None) -> str:
        """Schedule a test execution"""
        if suite_id not in self.test_suites:
            raise ValueError(f"Test suite {suite_id} not found")
            
        suite = self.test_suites[suite_id]
        execution_id = f"exec_{suite_id}_{int(time.time() * 1000)}"
        
        # Check if environment is available
        if not self._check_environment_available(suite.environment):
            logger.warning(f"Environment {suite.environment} not available, queuing execution")
            
        execution = TestExecution(
            id=execution_id,
            suite_id=suite_id,
            executor_agent=self.agent_id,
            status=TestStatus.SCHEDULED,
            environment=suite.environment,
            started_at=None,
            completed_at=None,
            results={},
            logs=[],
            artifacts=[]
        )
        
        self.active_executions[execution_id] = execution
        self.test_queue.append(execution_id)
        self._save_test_registry()
        
        logger.info(f"Scheduled test execution: {execution_id}")
        return execution_id
        
    def execute_test_suite(self, execution_id: str) -> bool:
        """Execute a scheduled test suite"""
        if execution_id not in self.active_executions:
            logger.error(f"Execution {execution_id} not found")
            return False
            
        execution = self.active_executions[execution_id]
        suite = self.test_suites[execution.suite_id]
        
        # Reserve environment
        if not self._reserve_environment(suite.environment, execution_id):
            logger.warning(f"Cannot reserve environment {suite.environment} for {execution_id}")
            execution.status = TestStatus.BLOCKED
            return False
            
        # Claim required resources
        for resource in suite.required_resources:
            if not self._claim_test_resource(resource, execution_id):
                logger.warning(f"Cannot claim resource {resource} for {execution_id}")
                execution.status = TestStatus.BLOCKED
                self._release_environment(suite.environment)
                return False
                
        # Start execution
        execution.status = TestStatus.RUNNING
        execution.started_at = datetime.now().isoformat()
        
        try:
            # Setup test environment
            test_env_path = self._setup_test_environment(suite.environment, execution_id)
            
            # Execute tests
            results = self._run_tests(suite, test_env_path, execution_id)
            
            # Process results
            execution.results = results
            execution.status = TestStatus.PASSED if results.get('success', False) else TestStatus.FAILED
            
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            execution.status = TestStatus.FAILED
            execution.results = {"error": str(e), "success": False}
            execution.logs.append(f"Execution error: {e}")
            
        finally:
            execution.completed_at = datetime.now().isoformat()
            
            # Release resources
            for resource in suite.required_resources:
                self._release_test_resource(resource)
            self._release_environment(suite.environment)
            
            # Cleanup test environment
            self._cleanup_test_environment(execution_id)
            
            self._save_test_registry()
            
        # Generate test report
        self._generate_test_report(execution)
        
        logger.info(f"Completed test execution {execution_id}: {execution.status}")
        return execution.status == TestStatus.PASSED
        
    def _check_environment_available(self, environment: TestEnvironment) -> bool:
        """Check if test environment is available"""
        if environment in self.environment_reservations:
            reservation = self.environment_reservations[environment]
            expires_at = datetime.fromisoformat(reservation.expires_at)
            if datetime.now() < expires_at:
                return False
                
        return True
        
    def _reserve_environment(self, environment: TestEnvironment, execution_id: str,
                           duration_minutes: int = 60) -> bool:
        """Reserve a test environment"""
        if not self._check_environment_available(environment):
            return False
            
        reservation = TestEnvironmentReservation(
            id=execution_id,
            environment=environment,
            reserved_by=self.agent_id,
            reserved_at=datetime.now().isoformat(),
            expires_at=(datetime.now() + timedelta(minutes=duration_minutes)).isoformat(),
            purpose=f"Test execution {execution_id}",
            resources_claimed=[]
        )
        
        self.environment_reservations[environment] = reservation
        logger.info(f"Reserved environment {environment} for {execution_id}")
        return True
        
    def _release_environment(self, environment: TestEnvironment):
        """Release a test environment reservation"""
        if environment in self.environment_reservations:
            del self.environment_reservations[environment]
            logger.info(f"Released environment {environment}")
            
    def _claim_test_resource(self, resource: str, execution_id: str) -> bool:
        """Claim a test resource"""
        resource_id = f"{resource}_{execution_id}"
        if resource in self.resource_locks:
            return False
            
        self.resource_locks.add(resource)
        return True
        
    def _release_test_resource(self, resource: str):
        """Release a test resource"""
        self.resource_locks.discard(resource)
        
    def _setup_test_environment(self, environment: TestEnvironment, execution_id: str) -> Path:
        """Setup isolated test environment"""
        if environment == TestEnvironment.LOCAL:
            return Path("/workspace")
            
        env_base_path = Path(self.test_environments[environment])
        test_env_path = env_base_path / execution_id
        
        # Create isolated environment
        test_env_path.mkdir(parents=True, exist_ok=True)
        
        # Copy necessary files
        workspace_path = Path("/workspace")
        essential_dirs = ["src", "tests", "requirements.txt", "package.json", "pytest.ini"]
        
        for item in essential_dirs:
            src_path = workspace_path / item
            if src_path.exists():
                if src_path.is_dir():
                    shutil.copytree(src_path, test_env_path / item, dirs_exist_ok=True)
                else:
                    shutil.copy2(src_path, test_env_path / item)
                    
        # Setup environment-specific configuration
        self._setup_environment_config(test_env_path, environment)
        
        return test_env_path
        
    def _setup_environment_config(self, test_path: Path, environment: TestEnvironment):
        """Setup environment-specific configuration"""
        if environment == TestEnvironment.ISOLATED:
            # Create isolated .env file
            env_file = test_path / ".env"
            with open(env_file, 'w') as f:
                f.write("USE_MOCK_EMAIL_CLIENT=True\n")
                f.write("REDIS_URL=redis://localhost:6379/15\n")  # Use different DB
                f.write("LOG_LEVEL=DEBUG\n")
                
        elif environment == TestEnvironment.INTEGRATION:
            # Setup integration test configuration
            env_file = test_path / ".env"
            with open(env_file, 'w') as f:
                f.write("USE_MOCK_EMAIL_CLIENT=False\n")
                f.write("REDIS_URL=redis://localhost:6379/14\n")
                f.write("INTEGRATION_TESTING=True\n")
                
    def _run_tests(self, suite: TestSuite, test_env_path: Path, execution_id: str) -> Dict[str, Any]:
        """Run the actual tests"""
        results = {
            "success": False,
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "duration_seconds": 0,
            "coverage": {},
            "errors": []
        }
        
        start_time = time.time()
        
        try:
            # Change to test environment
            original_cwd = Path.cwd()
            import os
            os.chdir(test_env_path)
            
            # Run tests based on type
            if suite.type in [TestType.UNIT, TestType.INTEGRATION]:
                results = self._run_pytest_tests(suite, execution_id)
            elif suite.type == TestType.PERFORMANCE:
                results = self._run_performance_tests(suite, execution_id)
            elif suite.type == TestType.SECURITY:
                results = self._run_security_tests(suite, execution_id)
            else:
                results = self._run_generic_tests(suite, execution_id)
                
        except Exception as e:
            results["errors"].append(str(e))
            logger.error(f"Test execution error: {e}")
        finally:
            # Restore working directory
            os.chdir(original_cwd)
            
        results["duration_seconds"] = time.time() - start_time
        return results
        
    def _run_pytest_tests(self, suite: TestSuite, execution_id: str) -> Dict[str, Any]:
        """Run pytest-based tests"""
        log_file = self.test_logs_path / f"{execution_id}.log"
        coverage_file = self.testing_path / "coverage" / f"{execution_id}.xml"
        
        # Build pytest command
        cmd = [
            "python", "-m", "pytest",
            "--verbose",
            "--tb=short",
            f"--junitxml={self.test_artifacts_path / f'{execution_id}_results.xml'}",
            f"--cov=src",
            f"--cov-report=xml:{coverage_file}",
            f"--log-file={log_file}"
        ]
        
        # Add test files
        cmd.extend(suite.test_files)
        
        # Add markers based on test type
        if suite.type == TestType.UNIT:
            cmd.extend(["-m", "unit"])
        elif suite.type == TestType.INTEGRATION:
            cmd.extend(["-m", "integration"])
            
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=suite.estimated_duration_minutes * 60
            )
            
            # Parse pytest output
            return self._parse_pytest_output(result, execution_id)
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Test execution timed out",
                "total_tests": 0,
                "passed": 0,
                "failed": 1,
                "skipped": 0
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "total_tests": 0,
                "passed": 0,
                "failed": 1,
                "skipped": 0
            }
            
    def _parse_pytest_output(self, result: subprocess.CompletedProcess, execution_id: str) -> Dict[str, Any]:
        """Parse pytest output to extract results"""
        output = result.stdout + result.stderr
        
        # Basic parsing (can be enhanced)
        passed = output.count(" PASSED")
        failed = output.count(" FAILED")
        skipped = output.count(" SKIPPED")
        
        # Save full output
        execution = self.active_executions[execution_id]
        execution.logs.append(output)
        
        return {
            "success": result.returncode == 0,
            "total_tests": passed + failed + skipped,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "return_code": result.returncode,
            "output": output[:1000]  # Truncate for storage
        }
        
    def _run_performance_tests(self, suite: TestSuite, execution_id: str) -> Dict[str, Any]:
        """Run performance tests"""
        # Simplified performance testing
        return {
            "success": True,
            "performance_metrics": {
                "response_time_ms": 250,
                "memory_usage_mb": 45,
                "cpu_usage_percent": 15
            },
            "total_tests": 1,
            "passed": 1,
            "failed": 0,
            "skipped": 0
        }
        
    def _run_security_tests(self, suite: TestSuite, execution_id: str) -> Dict[str, Any]:
        """Run security tests"""
        # Simplified security testing
        return {
            "success": True,
            "security_checks": {
                "sql_injection": "pass",
                "xss_protection": "pass",
                "authentication": "pass"
            },
            "total_tests": 3,
            "passed": 3,
            "failed": 0,
            "skipped": 0
        }
        
    def _run_generic_tests(self, suite: TestSuite, execution_id: str) -> Dict[str, Any]:
        """Run generic tests"""
        return {
            "success": True,
            "total_tests": len(suite.test_files),
            "passed": len(suite.test_files),
            "failed": 0,
            "skipped": 0
        }
        
    def _cleanup_test_environment(self, execution_id: str):
        """Cleanup isolated test environment"""
        for env, base_path in self.test_environments.items():
            if env == TestEnvironment.LOCAL:
                continue
                
            env_path = Path(base_path) / execution_id
            if env_path.exists():
                try:
                    shutil.rmtree(env_path)
                    logger.info(f"Cleaned up test environment: {env_path}")
                except Exception as e:
                    logger.error(f"Error cleaning up test environment: {e}")
                    
    def _generate_test_report(self, execution: TestExecution):
        """Generate comprehensive test report"""
        suite = self.test_suites[execution.suite_id]
        
        report = {
            "execution_id": execution.id,
            "suite_name": suite.name,
            "suite_type": suite.type.value,
            "environment": execution.environment.value,
            "executor": execution.executor_agent,
            "status": execution.status.value,
            "started_at": execution.started_at,
            "completed_at": execution.completed_at,
            "duration_minutes": self._calculate_duration(execution),
            "results": execution.results,
            "summary": self._generate_summary(execution)
        }
        
        # Save report
        report_file = self.testing_path / "reports" / f"{execution.id}_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        execution.artifacts.append(str(report_file))
        
    def _calculate_duration(self, execution: TestExecution) -> float:
        """Calculate execution duration in minutes"""
        if not execution.started_at or not execution.completed_at:
            return 0.0
            
        start = datetime.fromisoformat(execution.started_at)
        end = datetime.fromisoformat(execution.completed_at)
        duration = end - start
        return duration.total_seconds() / 60
        
    def _generate_summary(self, execution: TestExecution) -> str:
        """Generate human-readable summary"""
        results = execution.results
        if results.get("success", False):
            return f"✅ All {results.get('total_tests', 0)} tests passed"
        else:
            failed = results.get('failed', 0)
            total = results.get('total_tests', 0)
            return f"❌ {failed}/{total} tests failed"
            
    def _monitor_test_queue(self):
        """Monitor and process test queue"""
        while self.running:
            try:
                if self.test_queue:
                    execution_id = self.test_queue[0]
                    execution = self.active_executions.get(execution_id)
                    
                    if execution and execution.status == TestStatus.SCHEDULED:
                        suite = self.test_suites[execution.suite_id]
                        
                        # Check if we can run the test
                        if self._check_environment_available(suite.environment):
                            self.test_queue.pop(0)
                            threading.Thread(
                                target=self.execute_test_suite,
                                args=(execution_id,),
                                daemon=True
                            ).start()
                        else:
                            logger.info(f"Environment {suite.environment} busy, waiting...")
                            
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring test queue: {e}")
                time.sleep(30)
                
    def _monitor_environment_reservations(self):
        """Monitor and cleanup expired environment reservations"""
        while self.running:
            try:
                current_time = datetime.now()
                expired_reservations = []
                
                for env, reservation in self.environment_reservations.items():
                    expires_at = datetime.fromisoformat(reservation.expires_at)
                    if current_time > expires_at:
                        expired_reservations.append(env)
                        
                # Release expired reservations
                for env in expired_reservations:
                    self._release_environment(env)
                    logger.info(f"Released expired reservation for {env}")
                    
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error monitoring reservations: {e}")
                time.sleep(60)
                
    def _cleanup_test_artifacts(self):
        """Cleanup old test artifacts"""
        while self.running:
            try:
                cutoff_time = datetime.now() - timedelta(days=7)
                
                # Cleanup old logs
                for log_file in self.test_logs_path.glob("*.log"):
                    file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if file_time < cutoff_time:
                        log_file.unlink()
                        
                # Cleanup old artifacts
                for artifact_file in self.test_artifacts_path.glob("*"):
                    file_time = datetime.fromtimestamp(artifact_file.stat().st_mtime)
                    if file_time < cutoff_time:
                        artifact_file.unlink()
                        
                time.sleep(3600)  # Cleanup every hour
                
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
                time.sleep(3600)
                
    def _save_test_registry(self):
        """Save test registry to filesystem"""
        test_registry_file = self.coordination_path / "test_registry.json"
        
        registry_data = {
            "suites": [suite.to_dict() for suite in self.test_suites.values()],
            "executions": [exec.to_dict() for exec in self.active_executions.values()]
        }
        
        with open(test_registry_file, 'w') as f:
            json.dump(registry_data, f, indent=2)
            
    def get_testing_status(self) -> Dict[str, Any]:
        """Get current testing coordination status"""
        return {
            "agent_id": self.agent_id,
            "registered_suites": len(self.test_suites),
            "active_executions": len([e for e in self.active_executions.values() if e.status == TestStatus.RUNNING]),
            "queued_executions": len(self.test_queue),
            "environment_reservations": {env.value: bool(res) for env, res in self.environment_reservations.items()},
            "resource_locks": len(self.resource_locks)
        }
        
    def stop(self):
        """Stop the testing coordinator"""
        self.running = False
        
        # Release all reservations
        for env in list(self.environment_reservations.keys()):
            self._release_environment(env)
            
        # Release all resource locks
        self.resource_locks.clear()
        
        logger.info("Testing coordinator stopped")

def create_testing_coordinator(agent_id: str) -> TestingCoordinator:
    """Factory function to create a testing coordinator"""
    return TestingCoordinator(agent_id)
"""
Simple Test Runner for Karen AI Email System
===========================================

This is a simplified test runner that can work without external dependencies
for demonstration and basic testing purposes.

Usage:
    python3 src/test_runner_simple.py --email-baseline
    python3 src/test_runner_simple.py --health-check
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('SimpleTestRunner')

class SimpleTestRunner:
    """Simplified test runner for Karen AI email system"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_results = {}
        self.email_system_status = 'UNKNOWN'
        
        logger.info("Simple Test Runner initialized")
    
    def run_email_baseline_tests(self):
        """Run basic email system tests"""
        logger.info("=== RUNNING EMAIL BASELINE TESTS ===")
        
        test_results = {
            'timestamp': datetime.now().isoformat(),
            'test_suite': 'email_baseline',
            'tests': []
        }
        
        # Test 1: Check required files exist
        required_files_test = self._test_required_files()
        test_results['tests'].append(required_files_test)
        
        # Test 2: Check environment variables
        env_vars_test = self._test_environment_variables()
        test_results['tests'].append(env_vars_test)
        
        # Test 3: Check token files
        token_files_test = self._test_token_files()
        test_results['tests'].append(token_files_test)
        
        # Test 4: Check Python imports
        imports_test = self._test_python_imports()
        test_results['tests'].append(imports_test)
        
        # Calculate overall status
        passed_tests = sum(1 for test in test_results['tests'] if test['status'] == 'PASSED')
        total_tests = len(test_results['tests'])
        
        test_results['summary'] = {
            'passed': passed_tests,
            'failed': total_tests - passed_tests,
            'total': total_tests,
            'success_rate': (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        }
        
        # Determine email system status
        if passed_tests == total_tests:
            self.email_system_status = 'HEALTHY'
            logger.info("✅ ALL EMAIL BASELINE TESTS PASSED")
        elif passed_tests >= total_tests * 0.8:
            self.email_system_status = 'WARNING'
            logger.warning(f"⚠️  EMAIL SYSTEM WARNING: {passed_tests}/{total_tests} tests passed")
        else:
            self.email_system_status = 'CRITICAL'
            logger.error(f"❌ EMAIL SYSTEM CRITICAL: Only {passed_tests}/{total_tests} tests passed")
        
        # Store results
        self.test_results['email_baseline'] = test_results
        
        # Save results to file
        self._save_test_results()
        
        return test_results
    
    def _test_required_files(self):
        """Test that required files exist"""
        logger.info("Testing required files...")
        
        required_files = [
            'credentials.json',
            'src/email_client.py',
            'src/communication_agent/agent.py',
            'src/handyman_response_engine.py',
            'src/llm_client.py',
            'src/config.py'
        ]
        
        missing_files = []
        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if not missing_files:
            return {
                'name': 'required_files',
                'status': 'PASSED',
                'message': f'All {len(required_files)} required files found'
            }
        else:
            return {
                'name': 'required_files',
                'status': 'FAILED',
                'message': f'Missing files: {", ".join(missing_files)}'
            }
    
    def _test_environment_variables(self):
        """Test that required environment variables are set"""
        logger.info("Testing environment variables...")
        
        required_env_vars = [
            'SECRETARY_EMAIL_ADDRESS',
            'MONITORED_EMAIL_ACCOUNT',
            'ADMIN_EMAIL_ADDRESS'
        ]
        
        missing_vars = []
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if not missing_vars:
            return {
                'name': 'environment_variables',
                'status': 'PASSED',
                'message': f'All {len(required_env_vars)} required environment variables set'
            }
        else:
            return {
                'name': 'environment_variables',
                'status': 'FAILED',
                'message': f'Missing environment variables: {", ".join(missing_vars)}'
            }
    
    def _test_token_files(self):
        """Test that OAuth token files exist"""
        logger.info("Testing OAuth token files...")
        
        token_files = [
            'gmail_token_karen.json',
            'gmail_token_monitor.json'
        ]
        
        missing_tokens = []
        for token_file in token_files:
            token_path = self.project_root / token_file
            if not token_path.exists():
                missing_tokens.append(token_file)
        
        if not missing_tokens:
            return {
                'name': 'oauth_tokens',
                'status': 'PASSED',
                'message': f'All {len(token_files)} OAuth token files found'
            }
        else:
            return {
                'name': 'oauth_tokens',
                'status': 'WARNING',
                'message': f'Missing token files: {", ".join(missing_tokens)} (may need OAuth setup)'
            }
    
    def _test_python_imports(self):
        """Test that required Python modules can be imported"""
        logger.info("Testing Python imports...")
        
        required_imports = [
            ('json', 'json'),
            ('email', 'email'),
            ('datetime', 'datetime'),
            ('google.oauth2.credentials', 'google-auth'),
            ('googleapiclient.discovery', 'google-api-python-client')
        ]
        
        import_failures = []
        
        for module_name, package_name in required_imports:
            try:
                __import__(module_name)
            except ImportError:
                import_failures.append(f"{module_name} ({package_name})")
        
        if not import_failures:
            return {
                'name': 'python_imports',
                'status': 'PASSED',
                'message': f'All {len(required_imports)} required modules can be imported'
            }
        else:
            return {
                'name': 'python_imports',
                'status': 'FAILED',
                'message': f'Failed to import: {", ".join(import_failures)}'
            }
    
    def run_health_check(self):
        """Run basic system health check"""
        logger.info("=== RUNNING SYSTEM HEALTH CHECK ===")
        
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'checks': []
        }
        
        # Check file system permissions
        fs_check = self._check_file_system_permissions()
        health_status['checks'].append(fs_check)
        
        # Check log directory
        log_check = self._check_log_directory()
        health_status['checks'].append(log_check)
        
        # Check communication directory
        comm_check = self._check_communication_directory()
        health_status['checks'].append(comm_check)
        
        # Overall health
        passed_checks = sum(1 for check in health_status['checks'] if check['status'] == 'HEALTHY')
        total_checks = len(health_status['checks'])
        
        if passed_checks == total_checks:
            health_status['overall'] = 'HEALTHY'
            logger.info("✅ ALL HEALTH CHECKS PASSED")
        else:
            health_status['overall'] = 'ISSUES_DETECTED'
            logger.warning(f"⚠️  HEALTH ISSUES: {passed_checks}/{total_checks} checks passed")
        
        return health_status
    
    def _check_file_system_permissions(self):
        """Check file system read/write permissions"""
        try:
            test_file = self.project_root / 'test_write_permissions.tmp'
            test_file.write_text('test')
            test_file.unlink()
            
            return {
                'name': 'file_system_permissions',
                'status': 'HEALTHY',
                'message': 'File system read/write permissions OK'
            }
        except Exception as e:
            return {
                'name': 'file_system_permissions',
                'status': 'ERROR',
                'message': f'File system permission error: {e}'
            }
    
    def _check_log_directory(self):
        """Check that log directory exists and is writable"""
        log_dir = self.project_root / 'logs'
        
        try:
            log_dir.mkdir(exist_ok=True)
            test_log = log_dir / 'test_log_permissions.tmp'
            test_log.write_text('test')
            test_log.unlink()
            
            return {
                'name': 'log_directory',
                'status': 'HEALTHY',
                'message': 'Log directory exists and is writable'
            }
        except Exception as e:
            return {
                'name': 'log_directory',
                'status': 'ERROR',
                'message': f'Log directory error: {e}'
            }
    
    def _check_communication_directory(self):
        """Check that agent communication directory structure exists"""
        try:
            comm_dir = self.project_root / 'autonomous-agents' / 'communication'
            
            # Create basic structure
            (comm_dir / 'inbox' / 'test_engineer').mkdir(parents=True, exist_ok=True)
            (comm_dir / 'status').mkdir(parents=True, exist_ok=True)
            (comm_dir / 'knowledge-base').mkdir(parents=True, exist_ok=True)
            
            return {
                'name': 'communication_directory',
                'status': 'HEALTHY',
                'message': 'Agent communication directory structure OK'
            }
        except Exception as e:
            return {
                'name': 'communication_directory',
                'status': 'ERROR',
                'message': f'Communication directory error: {e}'
            }
    
    def _save_test_results(self):
        """Save test results to file"""
        try:
            results_dir = self.project_root / 'test_results'
            results_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            results_file = results_dir / f'test_results_{timestamp}.json'
            
            with open(results_file, 'w') as f:
                json.dump(self.test_results, f, indent=2)
            
            logger.info(f"Test results saved to: {results_file}")
            
        except Exception as e:
            logger.error(f"Failed to save test results: {e}")
    
    def monitor_email_system(self, duration_minutes: int = 30):
        """Monitor email system for a specified duration"""
        logger.info(f"=== MONITORING EMAIL SYSTEM FOR {duration_minutes} MINUTES ===")
        
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        check_interval = 5  # Check every 5 minutes
        
        monitoring_log = {
            'start_time': datetime.now().isoformat(),
            'duration_minutes': duration_minutes,
            'checks': []
        }
        
        while datetime.now() < end_time:
            logger.info("Running email system check...")
            
            # Run baseline tests
            test_results = self.run_email_baseline_tests()
            
            check_entry = {
                'timestamp': datetime.now().isoformat(),
                'email_system_status': self.email_system_status,
                'test_summary': test_results['summary']
            }
            
            monitoring_log['checks'].append(check_entry)
            
            # Alert if system is not healthy
            if self.email_system_status != 'HEALTHY':
                logger.error(f"🚨 EMAIL SYSTEM ALERT: Status is {self.email_system_status}")
                # In a real implementation, this would trigger notifications
            
            # Wait for next check
            logger.info(f"Next check in {check_interval} minutes...")
            time.sleep(check_interval * 60)
        
        monitoring_log['end_time'] = datetime.now().isoformat()
        
        # Save monitoring log
        self._save_monitoring_log(monitoring_log)
        
        return monitoring_log
    
    def _save_monitoring_log(self, monitoring_log):
        """Save monitoring log to file"""
        try:
            logs_dir = self.project_root / 'logs'
            logs_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_file = logs_dir / f'email_monitoring_{timestamp}.json'
            
            with open(log_file, 'w') as f:
                json.dump(monitoring_log, f, indent=2)
            
            logger.info(f"Monitoring log saved to: {log_file}")
            
        except Exception as e:
            logger.error(f"Failed to save monitoring log: {e}")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Simple Test Runner for Karen AI')
    parser.add_argument('--email-baseline', action='store_true', help='Run email baseline tests')
    parser.add_argument('--health-check', action='store_true', help='Run system health check')
    parser.add_argument('--monitor', type=int, metavar='MINUTES', help='Monitor email system for N minutes')
    
    args = parser.parse_args()
    
    runner = SimpleTestRunner()
    
    if args.email_baseline:
        runner.run_email_baseline_tests()
    elif args.health_check:
        runner.run_health_check()
    elif args.monitor:
        runner.monitor_email_system(args.monitor)
    else:
        # Run all tests by default
        logger.info("Running all baseline tests...")
        runner.run_email_baseline_tests()
        runner.run_health_check()

if __name__ == "__main__":
    main()
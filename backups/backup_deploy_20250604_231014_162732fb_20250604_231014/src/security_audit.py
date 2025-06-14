#!/usr/bin/env python3
"""
Security Audit Tool for Karen AI System
Scans for exposed credentials, API keys, and security vulnerabilities.

Security Domain: SECURITY-001
Author: Karen AI Security Agent
"""

import os
import re
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
import hashlib
import stat

# Setup security audit logging
logger = logging.getLogger(__name__)

class SecurityVulnerability:
    """Represents a security vulnerability found during audit"""
    
    def __init__(self, vuln_type: str, severity: str, file_path: str, line_number: int = None, 
                 description: str = "", recommendation: str = ""):
        self.vuln_type = vuln_type
        self.severity = severity  # 'critical', 'high', 'medium', 'low'
        self.file_path = file_path
        self.line_number = line_number
        self.description = description
        self.recommendation = recommendation
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.vuln_type,
            'severity': self.severity,
            'file_path': self.file_path,
            'line_number': self.line_number,
            'description': self.description,
            'recommendation': self.recommendation,
            'timestamp': self.timestamp
        }

class SecurityAuditor:
    """
    Comprehensive security auditor for Karen AI system
    
    Scans for:
    - Exposed API keys and credentials
    - Insecure file permissions
    - Hardcoded secrets
    - OAuth token files in unsafe locations
    - Configuration security issues
    """
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent
        self.vulnerabilities: List[SecurityVulnerability] = []
        
        # Security patterns to detect
        self.credential_patterns = {
            'api_key': re.compile(r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?', re.MULTILINE),
            'secret_key': re.compile(r'(?i)(secret[_-]?key|secretkey)\s*[=:]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?', re.MULTILINE),
            'access_token': re.compile(r'(?i)(access[_-]?token|accesstoken)\s*[=:]\s*["\']?([a-zA-Z0-9_.-]{20,})["\']?', re.MULTILINE),
            'private_key': re.compile(r'-----BEGIN\s+(RSA\s+)?PRIVATE KEY-----', re.MULTILINE),
            'google_client_secret': re.compile(r'(?i)client_secret["\']?\s*[=:]\s*["\']([a-zA-Z0-9_-]{20,})["\']', re.MULTILINE),
            'stripe_key': re.compile(r'(?i)(sk_live_|pk_live_|sk_test_|pk_test_)[a-zA-Z0-9]{20,}', re.MULTILINE),
            'aws_key': re.compile(r'(?i)(AKIA[0-9A-Z]{16})', re.MULTILINE),
            'jwt_secret': re.compile(r'(?i)(jwt[_-]?secret|jwtsecret)\s*[=:]\s*["\']?([a-zA-Z0-9_-]{20,})["\']?', re.MULTILINE),
            'database_url': re.compile(r'(?i)(database[_-]?url|db[_-]?url)\s*[=:]\s*["\']?(postgres|mysql|mongodb)://[^"\s]+["\']?', re.MULTILINE),
            'password': re.compile(r'(?i)password\s*[=:]\s*["\']([^"\']{8,})["\']', re.MULTILINE)
        }
        
        # File extensions to scan
        self.scannable_extensions = {'.py', '.js', '.json', '.env', '.conf', '.cfg', '.ini', '.yml', '.yaml', '.toml'}
        
        # Files that should not contain credentials
        self.high_risk_files = {'README.md', 'requirements.txt', 'package.json', 'Dockerfile'}
        
        # Directories to exclude from scanning
        self.excluded_dirs = {'node_modules', '.git', '__pycache__', '.venv', 'venv', 'dist', 'build'}
        
        logger.info(f"SecurityAuditor initialized for project: {self.project_root}")
    
    def scan_all(self) -> Dict[str, Any]:
        """Run comprehensive security audit"""
        logger.info("Starting comprehensive security audit")
        
        audit_results = {
            'timestamp': datetime.now().isoformat(),
            'project_root': str(self.project_root),
            'vulnerabilities': [],
            'summary': {},
            'recommendations': []
        }
        
        # Clear previous vulnerabilities
        self.vulnerabilities = []
        
        # Run all audit checks
        self._scan_for_exposed_credentials()
        self._check_file_permissions()
        self._scan_token_files()
        self._check_configuration_security()
        self._scan_source_code_security()
        
        # Compile results
        audit_results['vulnerabilities'] = [v.to_dict() for v in self.vulnerabilities]
        audit_results['summary'] = self._generate_summary()
        audit_results['recommendations'] = self._generate_recommendations()
        
        logger.info(f"Security audit completed. Found {len(self.vulnerabilities)} vulnerabilities")
        return audit_results
    
    def _scan_for_exposed_credentials(self):
        """Scan for exposed credentials in source files"""
        logger.info("Scanning for exposed credentials")
        
        for file_path in self._get_scannable_files():
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Check each credential pattern
                for cred_type, pattern in self.credential_patterns.items():
                    matches = pattern.finditer(content)
                    
                    for match in matches:
                        line_number = content[:match.start()].count('\n') + 1
                        
                        # Skip if it's just a variable name or comment
                        if self._is_false_positive(match.group(0), content, match.start()):
                            continue
                        
                        severity = self._determine_severity(cred_type, file_path)
                        
                        vuln = SecurityVulnerability(
                            vuln_type=f"exposed_{cred_type}",
                            severity=severity,
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=line_number,
                            description=f"Potential {cred_type} found in source code",
                            recommendation=f"Move {cred_type} to environment variables or secure credential store"
                        )
                        
                        self.vulnerabilities.append(vuln)
                        
            except Exception as e:
                logger.warning(f"Error scanning file {file_path}: {e}")
    
    def _check_file_permissions(self):
        """Check for insecure file permissions"""
        logger.info("Checking file permissions")
        
        # Check for world-readable sensitive files
        sensitive_patterns = ['*token*.json', '*key*', '*secret*', '*.env', 'credentials.*']
        
        for pattern in sensitive_patterns:
            for file_path in self.project_root.rglob(pattern):
                if file_path.is_file():
                    try:
                        file_stat = file_path.stat()
                        mode = stat.filemode(file_stat.st_mode)
                        
                        # Check if file is world-readable or group-readable
                        if file_stat.st_mode & (stat.S_IRGRP | stat.S_IROTH):
                            severity = 'high' if 'token' in file_path.name.lower() else 'medium'
                            
                            vuln = SecurityVulnerability(
                                vuln_type="insecure_file_permissions",
                                severity=severity,
                                file_path=str(file_path.relative_to(self.project_root)),
                                description=f"Sensitive file has permissive permissions: {mode}",
                                recommendation="Set file permissions to 600 (owner read/write only)"
                            )
                            
                            self.vulnerabilities.append(vuln)
                            
                    except Exception as e:
                        logger.warning(f"Error checking permissions for {file_path}: {e}")
    
    def _scan_token_files(self):
        """Scan for OAuth token files and check their security"""
        logger.info("Scanning OAuth token files")
        
        # Look for token files
        token_patterns = ['*token*.json', 'gmail_token_*.json', 'calendar_token_*.json']
        
        for pattern in token_patterns:
            for file_path in self.project_root.rglob(pattern):
                if file_path.is_file():
                    try:
                        # Check if token file is in a secure location
                        if 'secure_tokens' not in str(file_path):
                            vuln = SecurityVulnerability(
                                vuln_type="insecure_token_location",
                                severity="high",
                                file_path=str(file_path.relative_to(self.project_root)),
                                description="OAuth token file not in secure location",
                                recommendation="Move token files to secure_tokens directory with proper permissions"
                            )
                            
                            self.vulnerabilities.append(vuln)
                        
                        # Check token file content
                        with open(file_path, 'r') as f:
                            token_data = json.load(f)
                        
                        # Check for unencrypted tokens
                        if 'token' in token_data and isinstance(token_data['token'], str):
                            if not token_data['token'].startswith('eyJ'):  # Basic JWT check
                                vuln = SecurityVulnerability(
                                    vuln_type="unencrypted_token",
                                    severity="medium",
                                    file_path=str(file_path.relative_to(self.project_root)),
                                    description="Token file contains unencrypted credential data",
                                    recommendation="Use encrypted token storage"
                                )
                                
                                self.vulnerabilities.append(vuln)
                        
                        # Check token age
                        if 'created_at' in token_data:
                            created_at = datetime.fromisoformat(token_data['created_at'])
                            age_days = (datetime.now() - created_at).days
                            
                            if age_days > 7:
                                vuln = SecurityVulnerability(
                                    vuln_type="old_token",
                                    severity="low",
                                    file_path=str(file_path.relative_to(self.project_root)),
                                    description=f"Token file is {age_days} days old",
                                    recommendation="Consider refreshing old tokens"
                                )
                                
                                self.vulnerabilities.append(vuln)
                        
                    except Exception as e:
                        logger.warning(f"Error analyzing token file {file_path}: {e}")
    
    def _check_configuration_security(self):
        """Check configuration files for security issues"""
        logger.info("Checking configuration security")
        
        config_files = ['config.py', 'settings.py', '.env', 'docker-compose.yml']
        
        for config_file in config_files:
            file_path = self.project_root / config_file
            
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Check for debug mode in production
                    if re.search(r'(?i)debug\s*[=:]\s*true', content):
                        vuln = SecurityVulnerability(
                            vuln_type="debug_mode_enabled",
                            severity="medium",
                            file_path=config_file,
                            description="Debug mode may be enabled",
                            recommendation="Ensure debug mode is disabled in production"
                        )
                        
                        self.vulnerabilities.append(vuln)
                    
                    # Check for default passwords
                    default_passwords = ['password', 'admin', '123456', 'secret']
                    for pwd in default_passwords:
                        if pwd in content.lower():
                            vuln = SecurityVulnerability(
                                vuln_type="default_password",
                                severity="high",
                                file_path=config_file,
                                description=f"Possible default password '{pwd}' found",
                                recommendation="Use strong, unique passwords"
                            )
                            
                            self.vulnerabilities.append(vuln)
                    
                except Exception as e:
                    logger.warning(f"Error checking config file {file_path}: {e}")
    
    def _scan_source_code_security(self):
        """Scan source code for security anti-patterns"""
        logger.info("Scanning source code for security issues")
        
        # Security anti-patterns
        security_patterns = {
            'sql_injection': re.compile(r'(?i)(execute|query)\s*\(\s*["\'].*%s.*["\']', re.MULTILINE),
            'command_injection': re.compile(r'(?i)(os\.system|subprocess\.call|exec|eval)\s*\(.*input', re.MULTILINE),
            'hardcoded_url': re.compile(r'https?://[^/\s]+\.(com|org|net|io)', re.MULTILINE),
            'todo_security': re.compile(r'(?i)#.*TODO.*(?:security|auth|encrypt|password|token)', re.MULTILINE)
        }
        
        for file_path in self._get_scannable_files():
            if file_path.suffix == '.py':  # Focus on Python files
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    for pattern_name, pattern in security_patterns.items():
                        matches = pattern.finditer(content)
                        
                        for match in matches:
                            line_number = content[:match.start()].count('\n') + 1
                            
                            severity = 'medium' if pattern_name == 'todo_security' else 'low'
                            
                            vuln = SecurityVulnerability(
                                vuln_type=pattern_name,
                                severity=severity,
                                file_path=str(file_path.relative_to(self.project_root)),
                                line_number=line_number,
                                description=f"Potential {pattern_name.replace('_', ' ')} detected",
                                recommendation="Review code for security implications"
                            )
                            
                            self.vulnerabilities.append(vuln)
                    
                except Exception as e:
                    logger.warning(f"Error scanning source file {file_path}: {e}")
    
    def _get_scannable_files(self) -> List[Path]:
        """Get list of files to scan"""
        files = []
        
        for file_path in self.project_root.rglob('*'):
            if file_path.is_file():
                # Skip excluded directories
                if any(excluded in file_path.parts for excluded in self.excluded_dirs):
                    continue
                
                # Include files with scannable extensions
                if file_path.suffix in self.scannable_extensions:
                    files.append(file_path)
                
                # Include high-risk files regardless of extension
                elif file_path.name in self.high_risk_files:
                    files.append(file_path)
        
        return files
    
    def _is_false_positive(self, match_text: str, content: str, match_start: int) -> bool:
        """Check if a credential match is likely a false positive"""
        # Get the line containing the match
        line_start = content.rfind('\n', 0, match_start) + 1
        line_end = content.find('\n', match_start)
        if line_end == -1:
            line_end = len(content)
        
        line = content[line_start:line_end]
        
        # Skip comments
        if line.strip().startswith('#') or line.strip().startswith('//'):
            return True
        
        # Skip variable names without values
        if '=' not in match_text and ':' not in match_text:
            return True
        
        # Skip obvious examples or placeholders
        placeholders = ['example', 'placeholder', 'your_key_here', 'xxx', 'yyy', 'zzz']
        if any(placeholder in match_text.lower() for placeholder in placeholders):
            return True
        
        return False
    
    def _determine_severity(self, cred_type: str, file_path: Path) -> str:
        """Determine vulnerability severity based on credential type and location"""
        # Critical if in high-risk files
        if file_path.name in self.high_risk_files:
            return 'critical'
        
        # High severity for production keys
        high_severity_types = ['private_key', 'stripe_key', 'aws_key', 'google_client_secret']
        if cred_type in high_severity_types:
            return 'high'
        
        # Medium for most API keys
        if cred_type in ['api_key', 'secret_key', 'access_token']:
            return 'medium'
        
        return 'low'
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate audit summary"""
        summary = {
            'total_vulnerabilities': len(self.vulnerabilities),
            'by_severity': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0},
            'by_type': {},
            'most_vulnerable_files': []
        }
        
        # Count by severity and type
        file_vuln_count = {}
        
        for vuln in self.vulnerabilities:
            summary['by_severity'][vuln.severity] += 1
            
            if vuln.vuln_type not in summary['by_type']:
                summary['by_type'][vuln.vuln_type] = 0
            summary['by_type'][vuln.vuln_type] += 1
            
            if vuln.file_path not in file_vuln_count:
                file_vuln_count[vuln.file_path] = 0
            file_vuln_count[vuln.file_path] += 1
        
        # Most vulnerable files
        sorted_files = sorted(file_vuln_count.items(), key=lambda x: x[1], reverse=True)
        summary['most_vulnerable_files'] = sorted_files[:5]
        
        return summary
    
    def _generate_recommendations(self) -> List[str]:
        """Generate security recommendations"""
        recommendations = [
            "Implement the OAuth token manager for secure credential handling",
            "Move all sensitive files to secure directories with proper permissions",
            "Use environment variables for configuration secrets",
            "Regularly rotate API keys and access tokens",
            "Enable automatic token refresh before expiration",
            "Implement secret scanning in CI/CD pipeline",
            "Review and remove any hardcoded credentials",
            "Set up proper file permissions (600) for sensitive files"
        ]
        
        # Add specific recommendations based on vulnerabilities found
        vuln_types = {vuln.vuln_type for vuln in self.vulnerabilities}
        
        if 'exposed_api_key' in vuln_types:
            recommendations.append("Move API keys to secure environment variables")
        
        if 'insecure_token_location' in vuln_types:
            recommendations.append("Migrate all token files to the secure_tokens directory")
        
        if 'debug_mode_enabled' in vuln_types:
            recommendations.append("Disable debug mode in production configuration")
        
        return recommendations
    
    def save_audit_report(self, audit_results: Dict[str, Any], output_file: str = None):
        """Save audit report to file"""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"security_audit_{timestamp}.json"
        
        output_path = self.project_root / output_file
        
        try:
            with open(output_path, 'w') as f:
                json.dump(audit_results, f, indent=2, default=str)
            
            logger.info(f"Security audit report saved to {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Failed to save audit report: {e}")
            return None


def main():
    """Main entry point for security audit"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("Karen AI Security Audit Tool")
    print("="*50)
    
    # Initialize auditor
    auditor = SecurityAuditor()
    
    # Run comprehensive audit
    results = auditor.scan_all()
    
    # Display summary
    summary = results['summary']
    print(f"\nAudit Results Summary:")
    print(f"Total Vulnerabilities: {summary['total_vulnerabilities']}")
    print(f"Critical: {summary['by_severity']['critical']}")
    print(f"High: {summary['by_severity']['high']}")
    print(f"Medium: {summary['by_severity']['medium']}")
    print(f"Low: {summary['by_severity']['low']}")
    
    # Save report
    report_file = auditor.save_audit_report(results)
    print(f"\nDetailed report saved to: {report_file}")
    
    # Display top recommendations
    print(f"\nTop Security Recommendations:")
    for i, rec in enumerate(results['recommendations'][:5], 1):
        print(f"{i}. {rec}")


if __name__ == "__main__":
    main()
"""
Eigencode Configuration Manager
Centralized configuration management for Karen AI system
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class EmailConfiguration:
    """Email system configuration."""
    secretary_email: str = ""
    monitored_email: str = ""
    admin_email: str = ""
    gmail_credentials_path: str = ""
    use_mock_client: bool = False
    
    def __post_init__(self):
        self.secretary_email = os.getenv('SECRETARY_EMAIL_ADDRESS', self.secretary_email)
        self.monitored_email = os.getenv('MONITORED_EMAIL_ACCOUNT', self.monitored_email)
        self.admin_email = os.getenv('ADMIN_EMAIL_ADDRESS', self.admin_email)
        self.use_mock_client = os.getenv('USE_MOCK_EMAIL_CLIENT', 'false').lower() == 'true'
    
    def validate(self) -> bool:
        """Validate email configuration."""
        required_fields = [self.secretary_email, self.monitored_email, self.admin_email]
        return all(field for field in required_fields)

@dataclass
class AgentConfiguration:
    """Agent system configuration."""
    redis_url: str = ""
    status_check_interval: int = 300
    task_retention_days: int = 30
    eigencode_monitoring: bool = True
    
    def __post_init__(self):
        self.redis_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
        self.status_check_interval = int(os.getenv('AGENT_STATUS_CHECK_INTERVAL', '300'))
        self.task_retention_days = int(os.getenv('AGENT_TASK_RETENTION_DAYS', '30'))
        self.eigencode_monitoring = os.getenv('EIGENCODE_MONITORING_ENABLED', 'true').lower() == 'true'

@dataclass
class APIConfiguration:
    """API system configuration."""
    gemini_api_key: str = ""
    google_project_id: str = ""
    default_timezone: str = "America/New_York"
    
    def __post_init__(self):
        self.gemini_api_key = os.getenv('GEMINI_API_KEY', self.gemini_api_key)
        self.google_project_id = os.getenv('GOOGLE_PROJECT_ID', self.google_project_id)
        self.default_timezone = os.getenv('DEFAULT_TIMEZONE', self.default_timezone)
    
    def validate(self) -> bool:
        """Validate API configuration."""
        return bool(self.gemini_api_key and self.google_project_id)

@dataclass
class SMSConfiguration:
    """SMS system configuration."""
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    
    def __post_init__(self):
        self.twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID', self.twilio_account_sid)
        self.twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN', self.twilio_auth_token)
        self.twilio_phone_number = os.getenv('TWILIO_PHONE_NUMBER', self.twilio_phone_number)
    
    def validate(self) -> bool:
        """Validate SMS configuration."""
        required_fields = [self.twilio_account_sid, self.twilio_auth_token, self.twilio_phone_number]
        return all(field for field in required_fields)

class ConfigurationManager:
    """Centralized configuration manager for Karen AI system."""
    
    def __init__(self):
        """Initialize configuration manager."""
        self.email = EmailConfiguration()
        self.agent = AgentConfiguration()
        self.api = APIConfiguration()
        self.sms = SMSConfiguration()
        
        self._validation_errors = []
    
    def validate_all_configs(self) -> bool:
        """Validate all configurations."""
        self._validation_errors = []
        
        configurations = {
            'email': self.email,
            'api': self.api,
            'sms': self.sms
        }
        
        all_valid = True
        for name, config in configurations.items():
            if hasattr(config, 'validate') and not config.validate():
                self._validation_errors.append(f"{name} configuration invalid")
                all_valid = False
        
        return all_valid
    
    def get_validation_errors(self) -> list:
        """Get validation errors."""
        return self._validation_errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'email': asdict(self.email),
            'agent': asdict(self.agent),
            'api': asdict(self.api),
            'sms': asdict(self.sms)
        }
    
    def save_config_report(self, file_path: str = "logs/config_report.json"):
        """Save configuration report."""
        report = {
            'configuration': self.to_dict(),
            'validation_status': self.validate_all_configs(),
            'validation_errors': self.get_validation_errors(),
            'timestamp': datetime.now().isoformat()
        }
        
        Path(file_path).parent.mkdir(exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Configuration report saved to {file_path}")

# Global configuration instance
config_manager = ConfigurationManager()

def get_config() -> ConfigurationManager:
    """Get global configuration manager instance."""
    return config_manager

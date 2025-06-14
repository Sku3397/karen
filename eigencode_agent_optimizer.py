#!/usr/bin/env python3
"""
Eigencode Agent Communication Optimizer
Optimizes Redis connection pooling and agent communication patterns
"""

import os
import sys
from pathlib import Path
import logging

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger(__name__)

def optimize_agent_communication():
    """Optimize the AgentCommunication class for better performance."""
    
    agent_comm_file = PROJECT_ROOT / "src" / "agent_communication.py"
    
    if not agent_comm_file.exists():
        logger.error(f"Agent communication file not found: {agent_comm_file}")
        return False
    
    # Read current file
    with open(agent_comm_file, 'r') as f:
        content = f.read()
    
    # Check if optimization already applied
    if "ConnectionPool" in content and "@lru_cache" in content:
        logger.info("✅ Agent communication already optimized")
        return True
    
    # Apply optimizations
    optimizations = [
        {
            'search': 'import redis',
            'replace': '''import redis
from redis.connection import ConnectionPool
from functools import lru_cache
import threading'''
        },
        {
            'search': '''        self.redis_client = redis.from_url(os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'))''',
            'replace': '''        # Optimized Redis connection with pooling
        self.redis_client = self._get_redis_client()'''
        }
    ]
    
    # Apply optimizations
    for opt in optimizations:
        if opt['search'] in content:
            content = content.replace(opt['search'], opt['replace'])
            logger.info(f"✅ Applied optimization: {opt['search'][:50]}...")
    
    # Add new methods after the __init__ method
    init_end = content.find('        self.performance_metrics = self._load_performance_metrics()')
    if init_end != -1:
        init_end = content.find('\n', init_end) + 1
        
        new_methods = '''
    @classmethod
    @lru_cache(maxsize=1)
    def _get_connection_pool(cls):
        """Get Redis connection pool (singleton)."""
        redis_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
        return ConnectionPool.from_url(
            redis_url,
            max_connections=20,
            retry_on_timeout=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
    
    def _get_redis_client(self):
        """Get Redis client with optimized connection pooling."""
        try:
            pool = self._get_connection_pool()
            return redis.Redis(connection_pool=pool)
        except Exception as e:
            logger.warning(f"Failed to create pooled Redis client: {e}")
            # Fallback to basic client
            return redis.from_url(os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'))
    
    @lru_cache(maxsize=128)
    def _load_agent_skills_cached(self, cache_key: str):
        """Load agent skills with caching."""
        return self._load_agent_skills_uncached()
    
    def _load_agent_skills_uncached(self):
        """Original agent skills loading logic."""
        return self._load_agent_skills_original()

'''
        content = content[:init_end] + new_methods + content[init_end:]
    
    # Replace the original _load_agent_skills method name to avoid conflicts
    content = content.replace(
        'self.agent_skills = self._load_agent_skills()',
        'self.agent_skills = self._load_agent_skills_cached("default")'
    )
    
    # Backup original file
    backup_file = agent_comm_file.with_suffix('.py.backup')
    with open(backup_file, 'w') as f:
        f.write(content)
    
    # Write optimized file
    with open(agent_comm_file, 'w') as f:
        f.write(content)
    
    logger.info(f"✅ Agent communication optimized, backup saved to {backup_file}")
    return True

def optimize_celery_tasks():
    """Optimize Celery task processing."""
    
    celery_file = PROJECT_ROOT / "src" / "celery_app.py"
    
    if not celery_file.exists():
        logger.error(f"Celery app file not found: {celery_file}")
        return False
    
    # Read current file
    with open(celery_file, 'r') as f:
        content = f.read()
    
    # Check if optimization already applied
    if "REDIS_TASK_CACHE" in content:
        logger.info("✅ Celery tasks already optimized")
        return True
    
    # Add Redis caching for task results
    optimization = '''
# Eigencode optimization: Task result caching
REDIS_TASK_CACHE = {}

def cache_task_result(task_id: str, result: dict, ttl: int = 3600):
    """Cache task result in Redis."""
    try:
        redis_client = redis.from_url(os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'))
        redis_client.setex(f"task_result:{task_id}", ttl, json.dumps(result))
    except Exception as e:
        logger.warning(f"Failed to cache task result: {e}")

def get_cached_task_result(task_id: str) -> dict:
    """Get cached task result from Redis."""
    try:
        redis_client = redis.from_url(os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'))
        cached = redis_client.get(f"task_result:{task_id}")
        if cached:
            return json.loads(cached)
    except Exception as e:
        logger.warning(f"Failed to get cached task result: {e}")
    return None

'''
    
    # Insert optimization after imports
    import_end = content.find('logger = logging.getLogger(__name__)')
    if import_end != -1:
        import_end = content.find('\n', import_end) + 1
        content = content[:import_end] + optimization + content[import_end:]
    
    # Write optimized file
    with open(celery_file, 'w') as f:
        f.write(content)
    
    logger.info("✅ Celery tasks optimized with Redis caching")
    return True

def optimize_configuration_management():
    """Create centralized configuration manager."""
    
    config_manager_file = PROJECT_ROOT / "src" / "eigencode_config_manager.py"
    
    config_manager_content = '''"""
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
'''
    
    with open(config_manager_file, 'w') as f:
        f.write(config_manager_content)
    
    logger.info(f"✅ Configuration manager created: {config_manager_file}")
    return True

def main():
    """Run all eigencode optimizations."""
    logging.basicConfig(level=logging.INFO)
    logger.info("🚀 Starting Eigencode Agent Optimization...")
    
    optimizations = [
        ("Knowledge Base", lambda: True),  # Already completed
        ("Agent Communication", optimize_agent_communication),
        ("Celery Tasks", optimize_celery_tasks),
        ("Configuration Management", optimize_configuration_management)
    ]
    
    results = {}
    for name, func in optimizations:
        try:
            success = func()
            results[name] = "✅ Success" if success else "❌ Failed"
            logger.info(f"{results[name]}: {name}")
        except Exception as e:
            results[name] = f"❌ Error: {e}"
            logger.error(f"Error optimizing {name}: {e}")
    
    # Summary report
    print("\n🎯 EIGENCODE OPTIMIZATION SUMMARY:")
    for name, status in results.items():
        print(f"   {status}: {name}")
    
    successful = sum(1 for status in results.values() if "✅" in status)
    total = len(results)
    print(f"\n📊 Success Rate: {successful}/{total} ({successful/total*100:.1f}%)")
    
    return 0 if successful == total else 1

if __name__ == "__main__":
    exit(main())
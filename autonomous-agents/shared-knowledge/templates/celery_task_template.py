"""
Template for creating new Celery tasks following Karen project patterns
Copy this template and modify for your specific agent/task needs
"""
import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from celery import Celery, signals

# Import the centralized agent communication system
from src.agent_communication import AgentCommunication

# Import any required clients or services
# from src.email_client import EmailClient
# from src.calendar_client import CalendarClient
# from src.llm_client import LLMClient

logger = logging.getLogger(__name__)

# For agent instances that need to be shared across tasks
_agent_instance = None

def get_agent_instance():
    """Singleton pattern for agent instance creation"""
    global _agent_instance
    if _agent_instance is None:
        logger.debug("Creating new AgentClass instance")
        try:
            # Initialize with required configuration
            _agent_instance = YourAgentClass(
                config_param1=os.getenv('CONFIG_PARAM1'),
                config_param2=os.getenv('CONFIG_PARAM2')
            )
            logger.info("AgentClass instance created successfully")
        except Exception as e:
            logger.error(f"Failed to create AgentClass instance: {e}", exc_info=True)
            raise
    return _agent_instance


class YourAgentClass:
    """Replace with your actual agent implementation"""
    def __init__(self, config_param1: str, config_param2: str):
        self.config1 = config_param1
        self.config2 = config_param2
        self.comm = AgentCommunication('your_agent_name')
        
        # Initialize any required clients
        try:
            # self.email_client = EmailClient(...)
            # self.calendar_client = CalendarClient(...)
            # self.llm_client = LLMClient()
            pass
        except ValueError as e:
            logger.error(f"Failed to initialize client: {e}")
            # Decide if this is fatal or if agent can work without it
            raise
    
    async def async_operation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Example async operation"""
        # Implement your async logic here
        await asyncio.sleep(1)  # Simulate work
        return {"status": "completed", "result": "processed"}
    
    def sync_operation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Example sync operation"""
        # Implement your sync logic here
        return {"status": "completed", "result": "processed"}


# Basic task pattern (synchronous)
@celery_app.task(name='your_basic_task', bind=True, ignore_result=True)
def your_basic_task(self, payload: Dict[str, Any] = None):
    """
    Basic task pattern for synchronous operations
    
    Args:
        payload: Optional dictionary with task parameters
    """
    task_logger = self.get_logger()
    comm = AgentCommunication('your_agent_name')
    
    task_logger.info(f"Starting your_basic_task with payload: {payload}")
    
    try:
        # Update status - starting
        comm.update_status('processing', 10, {
            'phase': 'initializing',
            'task_id': self.request.id,
            'started_at': datetime.now().isoformat()
        })
        
        # Read any pending messages
        messages = comm.read_messages()
        for msg in messages:
            task_logger.info(f"Received message: {msg.get('type')} from {msg.get('from')}")
            # Handle different message types
            if msg.get('type') == 'request':
                # Process request
                pass
        
        # Get agent instance if needed
        agent = get_agent_instance()
        
        # Update status - main processing
        comm.update_status('processing', 50, {
            'phase': 'main_processing',
            'task_id': self.request.id
        })
        
        # Perform main task work
        result = agent.sync_operation(payload or {})
        
        # Share knowledge/results
        comm.share_knowledge('task_results', {
            'task_type': 'your_basic_task',
            'completed_at': datetime.now().isoformat(),
            'result': result
        })
        
        # Send messages to other agents if needed
        comm.send_message('orchestrator', 'task_completed', {
            'task_id': self.request.id,
            'task_type': 'your_basic_task',
            'status': 'success',
            'result_summary': result
        })
        
        # Update status - completed
        comm.update_status('completed', 100, {
            'phase': 'done',
            'task_id': self.request.id,
            'completed_at': datetime.now().isoformat()
        })
        
        task_logger.info(f"Successfully completed your_basic_task: {result}")
        
    except Exception as e:
        task_logger.error(f"Error in your_basic_task: {e}", exc_info=True)
        
        # Update error status
        comm.update_status('error', 0, {
            'error': str(e),
            'task_id': self.request.id,
            'failed_at': datetime.now().isoformat(),
            'phase': 'failed'
        })
        
        # Optionally notify admin for critical errors
        if is_critical_error(e):
            notify_admin_of_error(e, self.request.id, payload)
        
        # Re-raise if Celery should retry
        # raise


# Async task pattern
@celery_app.task(name='your_async_task', ignore_result=True)
def your_async_task(payload: Dict[str, Any] = None):
    """
    Async task pattern for operations that use async/await
    
    Args:
        payload: Optional dictionary with task parameters
    """
    logger.info(f"Starting your_async_task with payload: {payload}")
    
    try:
        agent = get_agent_instance()
        
        # Run async method in sync context
        result = asyncio.run(
            agent.async_operation(payload or {})
        )
        
        logger.info(f"Successfully completed your_async_task: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in your_async_task: {e}", exc_info=True)
        raise


# Periodic task pattern
@celery_app.task(name='your_periodic_task', bind=True, ignore_result=True)
def your_periodic_task(self):
    """
    Periodic task pattern for scheduled operations
    No payload as this runs on a schedule
    """
    task_logger = self.get_logger()
    comm = AgentCommunication('your_agent_name')
    
    task_logger.info("Starting scheduled your_periodic_task")
    
    try:
        # Check for any configuration updates
        config_updates = check_for_config_updates()
        if config_updates:
            apply_config_updates(config_updates)
        
        # Perform periodic maintenance/checks
        comm.update_status('maintenance', 30, {
            'phase': 'checking_health',
            'task_id': self.request.id
        })
        
        # Example: Check system health
        health_status = perform_health_check()
        
        # Share health status
        comm.share_knowledge('system_health', {
            'timestamp': datetime.now().isoformat(),
            'status': health_status,
            'agent': 'your_agent_name'
        })
        
        # Perform periodic cleanup
        comm.update_status('maintenance', 70, {
            'phase': 'cleanup',
            'task_id': self.request.id
        })
        
        cleanup_results = perform_cleanup()
        
        comm.update_status('completed', 100, {
            'phase': 'done',
            'task_id': self.request.id,
            'health_status': health_status,
            'cleanup_results': cleanup_results
        })
        
        task_logger.info("Completed periodic maintenance task")
        
    except Exception as e:
        task_logger.error(f"Error in your_periodic_task: {e}", exc_info=True)
        comm.update_status('error', 0, {
            'error': str(e),
            'task_id': self.request.id
        })


# Helper functions
def is_critical_error(error: Exception) -> bool:
    """Determine if an error is critical enough to notify admin"""
    critical_errors = (
        ConnectionError,
        AuthenticationError,  # Custom error types
        ConfigurationError,
    )
    return isinstance(error, critical_errors)


def notify_admin_of_error(error: Exception, task_id: str, payload: Any):
    """Send admin notification for critical errors"""
    try:
        import traceback
        tb_str = traceback.format_exc()
        
        # Use the sending email client if available
        # Or implement your notification method
        admin_email = os.getenv('ADMIN_EMAIL_ADDRESS')
        if admin_email:
            # email_client.send_email(
            #     to=admin_email,
            #     subject=f"[URGENT] Task Error: {task_id}",
            #     body=f"Task failed with error:\n{str(error)}\n\nPayload:\n{payload}\n\nTraceback:\n{tb_str}"
            # )
            logger.info(f"Admin notification would be sent to {admin_email}")
    except Exception as e:
        logger.error(f"Failed to notify admin of error: {e}", exc_info=True)


def check_for_config_updates() -> Optional[Dict[str, Any]]:
    """Check if there are any configuration updates to apply"""
    # Implement your config check logic
    return None


def apply_config_updates(updates: Dict[str, Any]):
    """Apply configuration updates"""
    # Implement your config update logic
    pass


def perform_health_check() -> Dict[str, Any]:
    """Perform system health checks"""
    # Implement your health check logic
    return {
        'status': 'healthy',
        'checked_at': datetime.now().isoformat()
    }


def perform_cleanup() -> Dict[str, Any]:
    """Perform periodic cleanup tasks"""
    # Implement your cleanup logic
    return {
        'files_cleaned': 0,
        'memory_freed': 0
    }


# Beat schedule configuration (if this task needs to be scheduled)
# Add to celery_app.conf.beat_schedule in your main celery_app.py:
"""
'your-periodic-task-schedule': {
    'task': 'your_periodic_task',
    'schedule': crontab(minute='*/30'),  # Every 30 minutes
    # or
    'schedule': timedelta(hours=1),  # Every hour
    # or  
    'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
},
"""
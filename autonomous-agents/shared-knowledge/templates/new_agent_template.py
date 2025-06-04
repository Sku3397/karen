"""
New Agent Template for Karen AI System
==========================================

This template provides the standard structure for creating new agents
that integrate with Karen's Celery-based multi-agent architecture.

Usage:
1. Copy this template to src/agents/your_agent_name.py
2. Replace placeholders with your agent-specific implementation
3. Add Celery task in src/celery_app.py following the patterns
4. Test thoroughly before deploying

Follow Karen's established patterns for error handling, logging, and 
agent communication.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import time

# Import AgentCommunication when it's implemented
# from src.agent_communication import AgentCommunication

logger = logging.getLogger(__name__)

class YourAgentNameAgent:
    """
    [Agent Description] - Brief description of what this agent does
    
    Responsibilities:
    - List primary responsibilities
    - Follow single responsibility principle
    - Interface with other agents as needed
    
    Integration Points:
    - List what services this agent integrates with
    - Document any external APIs used
    - Note dependencies on other agents
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the agent with configuration.
        
        Args:
            config: Configuration dictionary containing agent settings
        """
        self.config = config
        self.agent_id = config.get('agent_id', 'your_agent_name')
        
        # Initialize agent communication (when implemented)
        # self.comm = AgentCommunication(self.agent_id)
        
        # Initialize any external service clients following Karen's patterns
        self._initialize_services()
        
        logger.info(f"{self.__class__.__name__} initialized successfully for agent {self.agent_id}")
    
    def _initialize_services(self):
        """Initialize external services and clients."""
        # Follow Karen's OAuth pattern for external services
        try:
            # Example: Initialize external service client
            # self.external_client = ExternalServiceClient(
            #     token_path=self.config.get('token_path'),
            #     credentials_path=self.config.get('credentials_path')
            # )
            logger.debug("External services initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize external services: {e}", exc_info=True)
            # Don't raise here - allow agent to operate in degraded mode
    
    async def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main task processing method - implement your agent logic here.
        
        Args:
            task_data: Task data from Celery or other agents
            
        Returns:
            Result dictionary with processing status and data
        """
        logger.info(f"Processing task for agent {self.agent_id}: {task_data.get('task_type', 'unknown')}")
        
        try:
            # Update status for monitoring
            # self.comm.update_status('processing', 10, {
            #     'phase': 'starting',
            #     'task_id': task_data.get('task_id')
            # })
            
            # Main processing logic here
            result = await self._perform_main_operation(task_data)
            
            # Share knowledge with other agents if applicable
            # self.comm.share_knowledge('discovery_type', {
            #     'agent': self.agent_id,
            #     'discovery': result,
            #     'timestamp': datetime.now().isoformat()
            # })
            
            # Update completion status
            # self.comm.update_status('completed', 100, {
            #     'phase': 'finished',
            #     'result_summary': 'success'
            # })
            
            logger.info(f"Successfully completed task processing for {self.agent_id}")
            return {
                'status': 'success',
                'result': result,
                'agent_id': self.agent_id,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing task in {self.agent_id}: {e}", exc_info=True)
            
            # Update error status
            # self.comm.update_status('error', 0, {
            #     'error': str(e),
            #     'phase': 'failed'
            # })
            
            return {
                'status': 'error',
                'error': str(e),
                'agent_id': self.agent_id,
                'timestamp': datetime.now().isoformat()
            }
    
    async def _perform_main_operation(self, task_data: Dict[str, Any]) -> Any:
        """
        Implement your main operation logic here.
        
        Args:
            task_data: Input data for processing
            
        Returns:
            Processing result
        """
        # Implement your agent's core functionality
        # Follow Karen's async patterns
        
        # Example: External API call with error handling
        try:
            # result = await asyncio.to_thread(
            #     self.external_client.blocking_method,
            #     task_data
            # )
            
            # Simulate work for template
            await asyncio.sleep(1)
            result = f"Processed {task_data.get('input', 'default_input')}"
            
            return result
            
        except Exception as e:
            logger.error(f"Error in main operation: {e}", exc_info=True)
            raise
    
    def handle_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Handle messages from other agents.
        
        Args:
            message: Message from another agent
            
        Returns:
            Response to send back (if any)
        """
        message_type = message.get('type')
        sender = message.get('from')
        content = message.get('content')
        
        logger.info(f"Agent {self.agent_id} received message '{message_type}' from {sender}")
        
        try:
            if message_type == 'request_info':
                return self._handle_info_request(content)
            elif message_type == 'task_assignment':
                return self._handle_task_assignment(content)
            elif message_type == 'status_update':
                return self._handle_status_update(content)
            else:
                logger.warning(f"Unknown message type '{message_type}' from {sender}")
                return None
                
        except Exception as e:
            logger.error(f"Error handling message from {sender}: {e}", exc_info=True)
            return {
                'type': 'error_response',
                'error': str(e),
                'original_message_type': message_type
            }
    
    def _handle_info_request(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Handle information requests from other agents."""
        requested_info = content.get('requested_info')
        
        # Implement info request handling
        return {
            'type': 'info_response',
            'requested_info': requested_info,
            'data': {'agent_status': 'operational', 'capabilities': ['example']},
            'agent_id': self.agent_id
        }
    
    def _handle_task_assignment(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Handle task assignments from orchestrator or other agents."""
        task_id = content.get('task_id')
        
        # Queue task for processing
        logger.info(f"Task {task_id} assigned to {self.agent_id}")
        
        return {
            'type': 'task_accepted',
            'task_id': task_id,
            'agent_id': self.agent_id
        }
    
    def _handle_status_update(self, content: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle status updates from other agents."""
        status = content.get('status')
        sender_agent = content.get('agent_id')
        
        logger.debug(f"Status update from {sender_agent}: {status}")
        
        # Process status update (no response needed)
        return None
    
    def get_agent_status(self) -> Dict[str, Any]:
        """
        Get current agent status for health checks.
        
        Returns:
            Dictionary containing agent status information
        """
        return {
            'agent_id': self.agent_id,
            'status': 'operational',
            'last_activity': datetime.now().isoformat(),
            'capabilities': self._get_capabilities(),
            'health': self._check_health()
        }
    
    def _get_capabilities(self) -> List[str]:
        """Return list of agent capabilities."""
        return [
            'task_processing',
            'message_handling',
            'status_reporting'
        ]
    
    def _check_health(self) -> Dict[str, Any]:
        """Perform health check on agent and its dependencies."""
        health_status = {
            'overall': 'healthy',
            'components': {}
        }
        
        # Check external service connectivity
        # try:
        #     if hasattr(self, 'external_client') and self.external_client:
        #         # Test connection
        #         health_status['components']['external_service'] = 'healthy'
        #     else:
        #         health_status['components']['external_service'] = 'unavailable'
        # except Exception as e:
        #     health_status['components']['external_service'] = f'error: {str(e)}'
        #     health_status['overall'] = 'degraded'
        
        return health_status


# Celery Task Integration Pattern
# Add this to src/celery_app.py:

"""
@celery_app.task(name='your_agent_task', bind=True, ignore_result=True)
def your_agent_task(self, task_data: Dict[str, Any]):
    '''Celery task for YourAgentNameAgent.'''
    task_logger = self.get_logger()
    comm = AgentCommunication('your_agent_name')
    task_logger.info(f"Executing your_agent_task with data: {task_data}")
    
    try:
        # Initialize agent with configuration
        agent_config = {
            'agent_id': 'your_agent_name',
            'token_path': os.getenv('YOUR_AGENT_TOKEN_PATH'),
            'credentials_path': os.getenv('GOOGLE_APP_CREDENTIALS_PATH')
        }
        
        agent = YourAgentNameAgent(agent_config)
        
        # Process the task
        result = asyncio.run(agent.process_task(task_data))
        
        # Handle the result
        if result['status'] == 'success':
            task_logger.info(f"Agent task completed successfully: {result}")
        else:
            task_logger.error(f"Agent task failed: {result}")
            
    except Exception as e:
        task_logger.error(f"Error in your_agent_task: {e}", exc_info=True)
        comm.update_status('error', 0, {'error': str(e), 'task_id': self.request.id})
        raise

# Add to beat_schedule in src/celery_app.py:
'your-agent-periodic-task': {
    'task': 'your_agent_task',
    'schedule': crontab(minute='*/30'),  # Every 30 minutes
    'args': [{'task_type': 'periodic_maintenance'}]
}
"""
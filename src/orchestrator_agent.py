"""
OrchestratorAgent - Central coordination and decision-making logic for the AI Handyman Secretary Assistant.
Routes requests to appropriate agents and manages overall workflow.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import re
from .agent_activity_logger import AgentActivityLogger

logger = logging.getLogger(__name__)
activity_logger = AgentActivityLogger()

class ContextManager:
    """Manages user context and conversation state."""
    
    def __init__(self):
        self.contexts: Dict[str, Dict[str, Any]] = {}
    
    def get_context(self, user_id: str) -> Dict[str, Any]:
        """Get context for a user."""
        return self.contexts.get(user_id, {})
    
    def update_context(self, user_id: str, updates: Dict[str, Any]) -> None:
        """Update context for a user."""
        if user_id not in self.contexts:
            self.contexts[user_id] = {}
        self.contexts[user_id].update(updates)

class OrchestratorAgent:
    """
    Central orchestrator that coordinates between different agents and manages workflow.
    """
    
    def __init__(self):
        """
        Initialize the OrchestratorAgent.
        """
        self.context_manager = ContextManager()
        
        # Log initialization
        activity_logger.log_activity(
            agent_name="orchestrator",
            activity_type="initialization",
            details={
                "context_manager": "initialized",
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Agent routing patterns
        self.agent_patterns = {
            'ScheduleAgent': [
                r'schedule.*meeting',
                r'book.*appointment',
                r'calendar',
                r'tomorrow.*meeting',
                r'next.*week',
                r'available.*time'
            ],
            'TaskManagerAgent': [
                r'create.*task',
                r'add.*todo',
                r'remind.*me',
                r'task.*list',
                r'complete.*task'
            ],
            'CommunicatorAgent': [
                r'send.*email',
                r'send.*sms',
                r'call.*client',
                r'message.*customer',
                r'contact.*client'
            ],
            'KnowledgeBaseAgent': [
                r'how.*to',
                r'what.*is',
                r'procedure.*for',
                r'help.*with',
                r'information.*about'
            ],
            'BillingAgent': [
                r'invoice',
                r'payment',
                r'bill.*client',
                r'charge.*for',
                r'cost.*of'
            ]
        }
        
        logger.info("OrchestratorAgent initialized successfully")
    
    def handle_input(self, user_id: str, input_text: str) -> List[Dict[str, Any]]:
        """
        Handle user input and route to appropriate agents.
        
        Args:
            user_id: ID of the user making the request
            input_text: The user's input text
            
        Returns:
            List of tasks assigned to various agents
        """
        try:
            # Get user context
            context = self.context_manager.get_context(user_id)
            
            # Analyze the input and determine which agent(s) should handle it
            assigned_agents = self._route_to_agents(input_text)
            
            # Create tasks for each assigned agent
            tasks = []
            for agent_name in assigned_agents:
                task = {
                    'id': str(uuid.uuid4()),
                    'user_id': user_id,
                    'input_text': input_text,
                    'assigned_to': agent_name,
                    'status': 'pending',
                    'created_at': datetime.now().isoformat(),
                    'priority': self._determine_priority(input_text),
                    'context': context
                }
                tasks.append(task)
            
            # Update context with new tasks
            last_tasks = context.get('last_tasks', [])
            last_tasks.extend([task['id'] for task in tasks])
            # Keep only last 10 tasks
            last_tasks = last_tasks[-10:]
            
            self.context_manager.update_context(user_id, {
                'last_input': input_text,
                'last_tasks': last_tasks,
                'last_interaction': datetime.now().isoformat()
            })
            
            logger.info(f"Routed input from user {user_id} to {len(tasks)} agents")
            return tasks
            
        except Exception as e:
            logger.error(f"Failed to handle input for user {user_id}: {str(e)}")
            return []
    
    def get_status(self, user_id: str) -> Dict[str, Any]:
        """
        Get the current status and context for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dictionary containing user context and status
        """
        try:
            context = self.context_manager.get_context(user_id)
            
            # Add some default values if not present
            if 'last_tasks' not in context:
                context['last_tasks'] = []
            
            status = {
                'user_id': user_id,
                'context': context,
                'active_tasks': len(context.get('last_tasks', [])),
                'last_interaction': context.get('last_interaction'),
                'status': 'active' if context.get('last_tasks') else 'idle'
            }
            
            logger.info(f"Retrieved status for user {user_id}")
            return context  # Return context directly as expected by tests
            
        except Exception as e:
            logger.error(f"Failed to get status for user {user_id}: {str(e)}")
            return {'last_tasks': []}
    
    def _route_to_agents(self, input_text: str) -> List[str]:
        """
        Determine which agents should handle the input based on pattern matching.
        
        Args:
            input_text: The user's input text
            
        Returns:
            List of agent names that should handle this input
        """
        input_lower = input_text.lower()
        assigned_agents = []
        
        for agent_name, patterns in self.agent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, input_lower):
                    if agent_name not in assigned_agents:
                        assigned_agents.append(agent_name)
                    break
        
        # If no specific agent is matched, default to TaskManagerAgent
        if not assigned_agents:
            assigned_agents.append('TaskManagerAgent')
        
        return assigned_agents
    
    def _determine_priority(self, input_text: str) -> str:
        """
        Determine the priority of a task based on input text.
        
        Args:
            input_text: The user's input text
            
        Returns:
            Priority level (high, medium, low)
        """
        input_lower = input_text.lower()
        
        # High priority keywords
        high_priority_keywords = ['urgent', 'emergency', 'asap', 'immediately', 'critical']
        if any(keyword in input_lower for keyword in high_priority_keywords):
            return 'high'
        
        # Medium priority keywords
        medium_priority_keywords = ['soon', 'today', 'tomorrow', 'this week']
        if any(keyword in input_lower for keyword in medium_priority_keywords):
            return 'medium'
        
        # Default to low priority
        return 'low'
    
    def update_task_status(self, task_id: str, status: str, result: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update the status of a task.
        
        Args:
            task_id: ID of the task to update
            status: New status (pending, in_progress, completed, failed)
            result: Optional result data from the agent
            
        Returns:
            bool: True if update was successful
        """
        try:
            # In a real implementation, this would update a database
            # For now, just log the update
            logger.info(f"Task {task_id} status updated to {status}")
            
            if result:
                logger.info(f"Task {task_id} result: {result}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update task {task_id} status: {str(e)}")
            return False
    
    def get_agent_capabilities(self) -> Dict[str, List[str]]:
        """
        Get the capabilities of all available agents.
        
        Returns:
            Dictionary mapping agent names to their capabilities
        """
        capabilities = {}
        for agent_name, patterns in self.agent_patterns.items():
            capabilities[agent_name] = [
                pattern.replace('.*', ' ').replace(r'\b', '').strip() 
                for pattern in patterns
            ]
        
        return capabilities
    
    def analyze_conversation_flow(self, user_id: str) -> Dict[str, Any]:
        """
        Analyze the conversation flow and patterns for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Analysis of conversation patterns
        """
        context = self.context_manager.get_context(user_id)
        
        analysis = {
            'total_interactions': len(context.get('last_tasks', [])),
            'most_used_agents': {},  # Would analyze task history
            'conversation_topics': [],  # Would analyze input patterns
            'user_preferences': {}  # Would learn from interaction patterns
        }
        
        return analysis
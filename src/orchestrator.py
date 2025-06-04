"""
Orchestrator Agent - Central coordinator for all agents
Uses AgentCommunication for inter-agent coordination
"""
import os
import time
import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import threading
from enum import Enum

# Import agent communication system
from .agent_communication import AgentCommunication

# Import for admin notifications
from .email_client import EmailClient
from .config import ADMIN_EMAIL_ADDRESS, SECRETARY_EMAIL_ADDRESS

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class WorkflowPhase(Enum):
    """Workflow execution phases"""
    ANALYSIS = "analysis"
    DEVELOPMENT = "development"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"

class OrchestratorAgent:
    """
    Central orchestrator that coordinates all other agents
    Routes requests and manages workflows between agents
    """
    
    def __init__(self):
        """Initialize the orchestrator with communication system"""
        logger.info("Initializing OrchestratorAgent")
        
        # Initialize communication
        self.comm = AgentCommunication('orchestrator')
        
        # Track agent registry
        self.registered_agents = [
            'archaeologist',
            'sms_engineer', 
            'phone_engineer',
            'memory_engineer',
            'test_engineer'
        ]
        
        # Workflow definitions
        self.workflows = {
            'full_system_scan': {
                'phases': [
                    WorkflowPhase.ANALYSIS,
                    WorkflowPhase.DEVELOPMENT,
                    WorkflowPhase.TESTING
                ],
                'agents': {
                    WorkflowPhase.ANALYSIS: ['archaeologist'],
                    WorkflowPhase.DEVELOPMENT: ['sms_engineer', 'phone_engineer', 'memory_engineer'],
                    WorkflowPhase.TESTING: ['test_engineer']
                }
            }
        }
        
        # Health check configuration
        self.health_check_interval = 300  # 5 minutes
        self.last_health_check = {}
        
        # Email client for admin notifications
        try:
            self.email_client = EmailClient(
                email_address=SECRETARY_EMAIL_ADDRESS,
                token_file_path=os.getenv('SECRETARY_TOKEN_PATH', 'gmail_token_karen.json')
            )
        except Exception as e:
            logger.error(f"Failed to initialize email client: {e}")
            self.email_client = None
        
        logger.info("OrchestratorAgent initialized successfully")
    
    def check_all_agent_health(self) -> Dict[str, Dict[str, Any]]:
        """Check health status of all registered agents"""
        logger.info("Performing health check on all agents")
        
        statuses = self.comm.get_all_agent_statuses()
        current_time = datetime.now()
        
        for agent in self.registered_agents:
            status = statuses.get(agent, {})
            
            if not status:
                logger.warning(f"Agent '{agent}' appears to be offline")
                continue
            
            # Check for error status
            if status.get('status') == 'error':
                logger.error(f"Agent '{agent}' is in error state")
                # Attempt recovery
                self.comm.send_message(agent, 'restart_request', {
                    'reason': 'error_detected',
                    'previous_error': status.get('details')
                })
        
        logger.info("Health check complete")
        return statuses
    
    def execute_workflow(self, workflow_name: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a predefined workflow"""
        logger.info(f"Starting workflow: {workflow_name}")
        
        if workflow_name not in self.workflows:
            logger.error(f"Unknown workflow: {workflow_name}")
            return {'success': False, 'error': f"Unknown workflow: {workflow_name}"}
        
        workflow = self.workflows[workflow_name]
        results = {
            'workflow': workflow_name,
            'started_at': datetime.now().isoformat(),
            'phases': {}
        }
        
        try:
            # Execute each phase
            for phase in workflow['phases']:
                logger.info(f"Starting phase: {phase.value}")
                phase_results = self._execute_phase(phase, workflow['agents'][phase], params)
                results['phases'][phase.value] = phase_results
                
                # Check if phase failed
                if not phase_results.get('success'):
                    logger.error(f"Phase {phase.value} failed")
                    results['success'] = False
                    results['error'] = f"Phase {phase.value} failed"
                    break
            else:
                results['success'] = True
            
            results['completed_at'] = datetime.now().isoformat()
            
        except Exception as e:
            logger.error(f"Workflow execution error: {e}", exc_info=True)
            results['success'] = False
            results['error'] = str(e)
        
        return results
    
    def _execute_phase(self, phase: WorkflowPhase, agents: List[str], 
                      params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a workflow phase with specified agents"""
        phase_results = {
            'phase': phase.value,
            'agents': {},
            'started_at': datetime.now().isoformat()
        }
        
        try:
            if phase == WorkflowPhase.ANALYSIS:
                # Start analysis phase
                for agent in agents:
                    self.comm.send_message(agent, 'start_analysis', {
                        'focus_areas': params.get('focus_areas', ['email_flow', 'celery_patterns']) if params else ['email_flow', 'celery_patterns'],
                        'phase_id': f"{phase.value}_{datetime.now().timestamp()}"
                    })
                
                # Wait for completion
                for agent in agents:
                    # Simple wait implementation
                    max_wait = 600  # 10 minutes
                    waited = 0
                    while waited < max_wait:
                        statuses = self.comm.get_all_agent_statuses()
                        agent_status = statuses.get(agent, {})
                        if agent_status.get('status') == 'completed':
                            phase_results['agents'][agent] = {'status': 'completed'}
                            break
                        time.sleep(30)
                        waited += 30
                    else:
                        phase_results['agents'][agent] = {'status': 'timeout'}
                        phase_results['success'] = False
                        return phase_results
            
            elif phase == WorkflowPhase.DEVELOPMENT:
                # Start development phase
                for agent in agents:
                    self.comm.send_message(agent, 'start_development', {
                        'knowledge_base': '/autonomous-agents/shared-knowledge/',
                        'preserve_features': params.get('preserve_features', ['email', 'calendar']) if params else ['email', 'calendar'],
                        'templates_path': '/autonomous-agents/shared-knowledge/templates/'
                    })
            
            elif phase == WorkflowPhase.TESTING:
                # Start testing phase
                for agent in agents:
                    self.comm.send_message(agent, 'start_testing', {
                        'test_suites': params.get('test_suites', ['unit', 'integration']) if params else ['unit', 'integration'],
                        'coverage_threshold': params.get('coverage_threshold', 80) if params else 80
                    })
            
            phase_results['success'] = all(
                agent_result.get('status') == 'completed' 
                for agent_result in phase_results['agents'].values()
            )
            phase_results['completed_at'] = datetime.now().isoformat()
            
        except Exception as e:
            logger.error(f"Phase execution error: {e}", exc_info=True)
            phase_results['success'] = False
            phase_results['error'] = str(e)
        
        return phase_results
    
    def coordinate_inter_agent_request(self, requesting_agent: str, target_agent: str,
                                     info_type: str, params: Optional[Dict[str, Any]] = None):
        """Coordinate information request between agents"""
        logger.info(f"Coordinating request from '{requesting_agent}' to '{target_agent}'")
        
        # Forward the request
        self.comm.send_message(target_agent, 'info_request', {
            'requesting_agent': requesting_agent,
            'needed_info': info_type,
            'params': params or {},
            'orchestrator_mediated': True
        })
    
    def get_system_overview(self) -> Dict[str, Any]:
        """Get complete system overview"""
        return {
            'orchestrator_status': 'active',
            'registered_agents': self.registered_agents,
            'agent_statuses': self.comm.get_all_agent_statuses(),
            'available_workflows': list(self.workflows.keys()),
            'timestamp': datetime.now().isoformat()
        }

# Singleton instance
_orchestrator_instance = None

def get_orchestrator_instance() -> OrchestratorAgent:
    """Get or create orchestrator instance"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = OrchestratorAgent()
    return _orchestrator_instance

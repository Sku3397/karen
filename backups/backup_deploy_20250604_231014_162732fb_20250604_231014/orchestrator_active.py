#!/usr/bin/env python3
"""
Active Orchestrator Agent - Coordinating all agents in the Karen system
Running as the central coordinator using AgentCommunication
"""
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import communication system
from agent_communication import AgentCommunication

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Orchestrator')

class ActiveOrchestrator:
    """Active Orchestrator coordinating all Karen agents"""
    
    def __init__(self):
        """Initialize the orchestrator with communication system"""
        logger.info("🎯 ORCHESTRATOR: Initializing Agent Communication System")
        
        # 1. Initialize communication
        self.comm = AgentCommunication('orchestrator')
        
        # Track registered agents
        self.registered_agents = [
            'archaeologist',
            'sms_engineer', 
            'phone_engineer',
            'memory_engineer',
            'test_engineer'
        ]
        
        # Workflow state tracking
        self.current_phase = None
        self.workflow_start_time = None
        self.agent_completion_status = {}
        
        # Health monitoring
        self.monitoring_active = True
        self.last_health_check = datetime.now()
        
        logger.info(f"✅ ORCHESTRATOR: Initialized with {len(self.registered_agents)} registered agents")
    
    def start_orchestration(self):
        """Start the orchestration process"""
        logger.info("🚀 ORCHESTRATOR: Starting system-wide coordination")
        
        # Update orchestrator status
        self.comm.update_status('active', 100, {
            'phase': 'coordinating',
            'registered_agents': len(self.registered_agents),
            'started_at': datetime.now().isoformat()
        })
        
        # Start monitoring thread
        self._start_monitoring_thread()
        
        # Begin workflow phases
        self._execute_analysis_phase()
    
    def _start_monitoring_thread(self):
        """Start background thread for agent monitoring"""
        def monitor_agents():
            while self.monitoring_active:
                try:
                    self._monitor_all_agent_statuses()
                    time.sleep(300)  # Check every 5 minutes
                except Exception as e:
                    logger.error(f"ORCHESTRATOR: Error in monitoring thread: {e}", exc_info=True)
                    time.sleep(60)  # Wait before retrying
        
        monitor_thread = threading.Thread(target=monitor_agents, daemon=True)
        monitor_thread.start()
        logger.info("🔍 ORCHESTRATOR: Started agent monitoring thread (5-minute intervals)")
    
    def _monitor_all_agent_statuses(self):
        """Monitor all agent statuses every 5 minutes"""
        logger.info("🔍 ORCHESTRATOR: Performing 5-minute health check")
        
        statuses = self.comm.get_all_agent_statuses()
        current_time = datetime.now()
        issues_found = []
        
        for agent in self.registered_agents:
            status = statuses.get(agent, {})
            
            if not status:
                logger.warning(f"⚠️  ORCHESTRATOR: Agent '{agent}' appears offline")
                issues_found.append(f"{agent}: offline")
                continue
            
            agent_status = status.get('status', 'unknown')
            timestamp = status.get('timestamp', '')
            
            # Check for error status
            if agent_status == 'error':
                logger.error(f"🚨 ORCHESTRATOR: Agent '{agent}' is in error state")
                details = status.get('details', {})
                error_msg = details.get('error', 'Unknown error')
                
                # Handle agent failure - send restart request
                self.comm.send_message(agent, 'restart_request', {
                    'reason': 'error_detected',
                    'previous_error': details,
                    'orchestrator_initiated': True,
                    'restart_timestamp': current_time.isoformat()
                })
                
                logger.info(f"🔄 ORCHESTRATOR: Sent restart request to '{agent}'")
                issues_found.append(f"{agent}: error - {error_msg}")
            
            # Check timestamp freshness
            elif timestamp:
                try:
                    status_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    age = current_time - status_time
                    
                    if age > timedelta(minutes=15):
                        logger.warning(f"⏰ ORCHESTRATOR: Agent '{agent}' status is stale ({age})")
                        issues_found.append(f"{agent}: stale status ({int(age.total_seconds()/60)}min)")
                except Exception as e:
                    logger.error(f"ORCHESTRATOR: Error parsing timestamp for '{agent}': {e}")
        
        # Log monitoring summary
        if issues_found:
            logger.warning(f"🔍 ORCHESTRATOR: Health check found {len(issues_found)} issues: {issues_found}")
        else:
            logger.info(f"✅ ORCHESTRATOR: All {len(statuses)} agents healthy")
        
        # Update our own status
        self.comm.update_status('monitoring', 100, {
            'last_health_check': current_time.isoformat(),
            'agents_monitored': len(self.registered_agents),
            'issues_found': len(issues_found),
            'issues': issues_found
        })
    
    def _execute_analysis_phase(self):
        """Phase 1: Start analysis with archaeologist"""
        logger.info("📋 ORCHESTRATOR: Starting Phase 1 - Analysis")
        
        self.current_phase = 'analysis'
        self.workflow_start_time = datetime.now()
        
        # Update status
        self.comm.update_status('coordinating', 25, {
            'phase': 'analysis',
            'workflow_phase': 1,
            'started_at': self.workflow_start_time.isoformat()
        })
        
        # 5. Start by sending message to archaeologist to begin analysis
        logger.info("🏛️  ORCHESTRATOR: Sending analysis task to archaeologist")
        
        self.comm.send_message('archaeologist', 'start_analysis', {
            'focus_areas': ['email_flow', 'celery_patterns', 'api_integrations'],
            'deliverables': [
                'system_architecture_documentation',
                'coding_patterns_analysis', 
                'integration_points_mapping',
                'do_not_modify_list'
            ],
            'orchestrator_initiated': True,
            'phase_id': f"analysis_{datetime.now().timestamp()}",
            'priority': 'high',
            'expected_completion': (datetime.now() + timedelta(minutes=30)).isoformat()
        })
        
        logger.info("✅ ORCHESTRATOR: Analysis task sent to archaeologist")
        
        # Share knowledge about workflow start
        self.comm.share_knowledge('workflow_coordination', {
            'event': 'analysis_phase_started',
            'coordinated_by': 'orchestrator',
            'target_agent': 'archaeologist',
            'expected_duration_minutes': 30,
            'next_phase': 'development'
        })
        
        # Wait for archaeologist completion
        self._wait_for_analysis_completion()
    
    def _wait_for_analysis_completion(self):
        """Wait for archaeologist to complete analysis"""
        logger.info("⏳ ORCHESTRATOR: Waiting for archaeologist to complete analysis...")
        
        max_wait_minutes = 45  # Allow extra time
        check_interval = 30    # Check every 30 seconds
        
        start_time = time.time()
        
        while time.time() - start_time < (max_wait_minutes * 60):
            # Check archaeologist status
            statuses = self.comm.get_all_agent_statuses()
            archaeologist_status = statuses.get('archaeologist', {})
            
            status = archaeologist_status.get('status', 'unknown')
            details = archaeologist_status.get('details', {})
            
            logger.info(f"🔍 ORCHESTRATOR: Archaeologist status: {status}")
            
            if status == 'completed':
                logger.info("✅ ORCHESTRATOR: Archaeologist completed analysis!")
                
                # Check if analysis delivered expected outputs
                if details.get('phase') == 'done':
                    self._handle_analysis_completion(details)
                    break
                
            elif status == 'error':
                logger.error(f"❌ ORCHESTRATOR: Archaeologist encountered error: {details}")
                self._handle_analysis_error(details)
                break
                
            # Wait before checking again
            time.sleep(check_interval)
            
            # Log progress if available
            progress = details.get('progress', 0)
            if progress > 0:
                logger.info(f"📊 ORCHESTRATOR: Archaeologist progress: {progress}%")
        
        else:
            logger.warning("⏰ ORCHESTRATOR: Archaeologist analysis timeout - proceeding to development phase")
            self._handle_analysis_timeout()
    
    def _handle_analysis_completion(self, details: Dict[str, Any]):
        """Handle successful analysis completion"""
        logger.info("🎉 ORCHESTRATOR: Analysis phase completed successfully")
        
        # Update workflow status
        analysis_duration = datetime.now() - self.workflow_start_time
        
        self.comm.update_status('coordinating', 50, {
            'phase': 'analysis_completed',
            'analysis_duration_minutes': int(analysis_duration.total_seconds() / 60),
            'moving_to': 'development_phase'
        })
        
        # Share completion knowledge
        self.comm.share_knowledge('workflow_coordination', {
            'event': 'analysis_phase_completed',
            'duration_minutes': int(analysis_duration.total_seconds() / 60),
            'deliverables_completed': details.get('deliverables', []),
            'knowledge_base_updated': True
        })
        
        # Proceed to development phase
        self._execute_development_phase()
    
    def _handle_analysis_error(self, details: Dict[str, Any]):
        """Handle analysis phase error"""
        logger.error("❌ ORCHESTRATOR: Analysis phase failed")
        
        error_msg = details.get('error', 'Unknown error')
        
        # Attempt recovery
        logger.info("🔄 ORCHESTRATOR: Attempting archaeologist recovery...")
        
        self.comm.send_message('archaeologist', 'restart_request', {
            'reason': 'analysis_phase_failure',
            'previous_error': details,
            'retry_analysis': True,
            'reduced_scope': ['email_flow', 'celery_patterns']  # Simplified scope for retry
        })
        
        # Wait briefly then proceed with limited scope
        time.sleep(60)
        logger.warning("⚠️  ORCHESTRATOR: Proceeding to development with limited analysis")
        self._execute_development_phase()
    
    def _handle_analysis_timeout(self):
        """Handle analysis phase timeout"""
        logger.warning("⏰ ORCHESTRATOR: Analysis phase timed out")
        
        # Check if partial results available
        statuses = self.comm.get_all_agent_statuses()
        archaeologist_status = statuses.get('archaeologist', {})
        progress = archaeologist_status.get('details', {}).get('progress', 0)
        
        if progress > 50:
            logger.info("📊 ORCHESTRATOR: Partial analysis available, proceeding to development")
        else:
            logger.warning("⚠️  ORCHESTRATOR: Limited analysis available, development may be constrained")
        
        # Proceed to development phase
        self._execute_development_phase()
    
    def _execute_development_phase(self):
        """Phase 2: Coordinate development with engineers"""
        logger.info("🛠️  ORCHESTRATOR: Starting Phase 2 - Development")
        
        self.current_phase = 'development'
        
        # Update status
        self.comm.update_status('coordinating', 75, {
            'phase': 'development',
            'workflow_phase': 2,
            'engineers_to_coordinate': 3
        })
        
        # Send development tasks to all engineers
        engineers = ['sms_engineer', 'phone_engineer', 'memory_engineer']
        
        for engineer in engineers:
            logger.info(f"🔧 ORCHESTRATOR: Sending development task to {engineer}")
            
            self.comm.send_message(engineer, 'start_development', {
                'knowledge_base': '/autonomous-agents/shared-knowledge/',
                'preserve_features': ['email', 'calendar'],
                'templates_path': '/autonomous-agents/shared-knowledge/templates/',
                'coding_patterns': 'use_karen_patterns',
                'integration_requirements': 'maintain_existing_apis',
                'orchestrator_initiated': True,
                'phase_id': f"development_{datetime.now().timestamp()}",
                'coordination_with': [e for e in engineers if e != engineer]  # Other engineers
            })
            
            # Initialize completion tracking
            self.agent_completion_status[engineer] = 'in_progress'
        
        logger.info("✅ ORCHESTRATOR: Development tasks sent to all engineers")
        
        # Handle inter-agent dependencies
        self._coordinate_development_dependencies()
    
    def _coordinate_development_dependencies(self):
        """Handle inter-agent dependencies during development"""
        logger.info("🔗 ORCHESTRATOR: Coordinating inter-agent dependencies")
        
        # SMS engineer needs patterns from archaeologist
        logger.info("📱 ORCHESTRATOR: SMS engineer requesting patterns from archaeologist")
        self._coordinate_inter_agent_request(
            requesting_agent='sms_engineer',
            target_agent='archaeologist', 
            info_type='celery_task_patterns',
            request_details={
                'needed_patterns': ['error_handling', 'async_operations', 'status_updates'],
                'format': 'implementation_examples',
                'urgency': 'high'
            }
        )
        
        # Phone engineer needs voice processing patterns
        logger.info("🎤 ORCHESTRATOR: Phone engineer requesting voice patterns from archaeologist")
        self._coordinate_inter_agent_request(
            requesting_agent='phone_engineer',
            target_agent='archaeologist',
            info_type='voice_processing_patterns',
            request_details={
                'needed_patterns': ['transcription_handling', 'async_voice_processing'],
                'integration_points': ['twilio', 'google_speech_api'],
                'urgency': 'medium'
            }
        )
        
        # Memory engineer needs data flow patterns
        logger.info("🧠 ORCHESTRATOR: Memory engineer requesting data patterns from archaeologist")
        self._coordinate_inter_agent_request(
            requesting_agent='memory_engineer',
            target_agent='archaeologist',
            info_type='data_flow_patterns', 
            request_details={
                'needed_patterns': ['conversation_storage', 'knowledge_indexing'],
                'integration_points': ['redis', 'filesystem'],
                'urgency': 'medium'
            }
        )
        
        # Start monitoring development progress
        self._monitor_development_progress()
    
    def _coordinate_inter_agent_request(self, requesting_agent: str, target_agent: str, 
                                      info_type: str, request_details: Dict[str, Any]):
        """Coordinate information request between agents"""
        logger.info(f"🔗 ORCHESTRATOR: Coordinating request from '{requesting_agent}' to '{target_agent}'")
        
        # Forward the request with orchestrator mediation
        self.comm.send_message(target_agent, 'info_request', {
            'requesting_agent': requesting_agent,
            'needed_info': info_type,
            'request_details': request_details,
            'orchestrator_mediated': True,
            'priority': request_details.get('urgency', 'medium'),
            'coordination_timestamp': datetime.now().isoformat()
        })
        
        # Log the coordination event
        self.comm.share_knowledge('coordination_log', {
            'event': 'inter_agent_request_coordinated',
            'from_agent': requesting_agent,
            'to_agent': target_agent,
            'info_type': info_type,
            'orchestrator': 'orchestrator',
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"✅ ORCHESTRATOR: Request coordinated between {requesting_agent} → {target_agent}")
    
    def _monitor_development_progress(self):
        """Monitor development progress across all engineers"""
        logger.info("📊 ORCHESTRATOR: Monitoring development progress")
        
        max_development_time = 60  # 60 minutes for development
        check_interval = 60       # Check every minute
        
        start_time = time.time()
        
        while time.time() - start_time < (max_development_time * 60):
            # Check all engineer statuses
            statuses = self.comm.get_all_agent_statuses()
            
            engineers = ['sms_engineer', 'phone_engineer', 'memory_engineer']
            completed_count = 0
            
            for engineer in engineers:
                status_data = statuses.get(engineer, {})
                status = status_data.get('status', 'unknown')
                details = status_data.get('details', {})
                
                if status == 'completed':
                    if self.agent_completion_status.get(engineer) != 'completed':
                        logger.info(f"✅ ORCHESTRATOR: {engineer} completed development")
                        self.agent_completion_status[engineer] = 'completed'
                    completed_count += 1
                elif status == 'error':
                    logger.error(f"❌ ORCHESTRATOR: {engineer} encountered error: {details}")
                    self.agent_completion_status[engineer] = 'error'
                else:
                    progress = details.get('progress', 0)
                    phase = details.get('phase', 'unknown')
                    logger.info(f"🔧 ORCHESTRATOR: {engineer} - {status} ({progress}%) - {phase}")
            
            # Check if all engineers completed
            if completed_count == len(engineers):
                logger.info("🎉 ORCHESTRATOR: All engineers completed development!")
                self._handle_development_completion()
                break
            
            # Wait before next check
            time.sleep(check_interval)
        
        else:
            logger.warning("⏰ ORCHESTRATOR: Development phase timeout")
            self._handle_development_timeout()
    
    def _handle_development_completion(self):
        """Handle successful development completion"""
        logger.info("🎉 ORCHESTRATOR: Development phase completed successfully")
        
        development_duration = datetime.now() - self.workflow_start_time
        
        self.comm.update_status('coordinating', 90, {
            'phase': 'development_completed',
            'total_duration_minutes': int(development_duration.total_seconds() / 60),
            'moving_to': 'testing_phase'
        })
        
        # Share completion knowledge
        self.comm.share_knowledge('workflow_coordination', {
            'event': 'development_phase_completed',
            'engineers_completed': list(self.agent_completion_status.keys()),
            'success_rate': len([s for s in self.agent_completion_status.values() if s == 'completed']) / len(self.agent_completion_status)
        })
        
        # Proceed to testing phase
        self._execute_testing_phase()
    
    def _handle_development_timeout(self):
        """Handle development phase timeout"""
        logger.warning("⏰ ORCHESTRATOR: Development phase timed out")
        
        # Check completion status
        completed = [k for k, v in self.agent_completion_status.items() if v == 'completed']
        in_progress = [k for k, v in self.agent_completion_status.items() if v == 'in_progress']
        
        logger.info(f"📊 ORCHESTRATOR: Development status - Completed: {completed}, In Progress: {in_progress}")
        
        if len(completed) >= 2:  # At least 2 engineers completed
            logger.info("✅ ORCHESTRATOR: Sufficient development completed, proceeding to testing")
            self._execute_testing_phase()
        else:
            logger.warning("⚠️  ORCHESTRATOR: Insufficient development completion, extending timeline")
            # Could implement extension logic here
            self._execute_testing_phase()  # Proceed anyway for demo
    
    def _execute_testing_phase(self):
        """Phase 3: Coordinate testing with test engineer"""
        logger.info("🧪 ORCHESTRATOR: Starting Phase 3 - Testing")
        
        self.current_phase = 'testing'
        
        # Update status
        self.comm.update_status('coordinating', 95, {
            'phase': 'testing',
            'workflow_phase': 3,
            'final_phase': True
        })
        
        # Send testing task to test engineer
        logger.info("🔬 ORCHESTRATOR: Sending testing task to test engineer")
        
        self.comm.send_message('test_engineer', 'start_testing', {
            'test_suites': ['unit', 'integration', 'system'],
            'coverage_threshold': 80,
            'test_focus_areas': [
                'email_processing_flow',
                'agent_communication',
                'celery_task_execution',
                'api_integrations'
            ],
            'orchestrator_initiated': True,
            'phase_id': f"testing_{datetime.now().timestamp()}",
            'include_performance_tests': True,
            'validate_against': '/autonomous-agents/shared-knowledge/karen-architecture.md'
        })
        
        logger.info("✅ ORCHESTRATOR: Testing task sent to test engineer")
        
        # Monitor testing progress
        self._monitor_testing_progress()
    
    def _monitor_testing_progress(self):
        """Monitor testing progress"""
        logger.info("🔍 ORCHESTRATOR: Monitoring testing progress")
        
        max_testing_time = 30  # 30 minutes for testing
        check_interval = 60    # Check every minute
        
        start_time = time.time()
        
        while time.time() - start_time < (max_testing_time * 60):
            statuses = self.comm.get_all_agent_statuses()
            test_status = statuses.get('test_engineer', {})
            
            status = test_status.get('status', 'unknown')
            details = test_status.get('details', {})
            
            if status == 'completed':
                logger.info("✅ ORCHESTRATOR: Testing completed!")
                self._handle_testing_completion(details)
                break
            elif status == 'error':
                logger.error(f"❌ ORCHESTRATOR: Testing failed: {details}")
                self._handle_testing_error(details)
                break
            else:
                progress = details.get('progress', 0)
                phase = details.get('phase', 'unknown')
                logger.info(f"🧪 ORCHESTRATOR: Testing - {status} ({progress}%) - {phase}")
            
            time.sleep(check_interval)
        
        else:
            logger.warning("⏰ ORCHESTRATOR: Testing phase timeout")
            self._handle_testing_timeout()
    
    def _handle_testing_completion(self, details: Dict[str, Any]):
        """Handle successful testing completion"""
        logger.info("🎉 ORCHESTRATOR: Testing phase completed successfully")
        
        total_duration = datetime.now() - self.workflow_start_time
        
        # Final status update
        self.comm.update_status('completed', 100, {
            'phase': 'workflow_completed',
            'total_duration_minutes': int(total_duration.total_seconds() / 60),
            'all_phases_completed': True,
            'test_results': details.get('results_summary', {})
        })
        
        # Share final knowledge
        self.comm.share_knowledge('workflow_coordination', {
            'event': 'full_workflow_completed',
            'total_duration_minutes': int(total_duration.total_seconds() / 60),
            'phases_completed': ['analysis', 'development', 'testing'],
            'success': True,
            'orchestrated_by': 'orchestrator'
        })
        
        logger.info("🏆 ORCHESTRATOR: Full workflow orchestration completed successfully!")
        self._generate_final_report()
    
    def _handle_testing_error(self, details: Dict[str, Any]):
        """Handle testing phase error"""
        logger.error("❌ ORCHESTRATOR: Testing phase failed")
        # Could implement retry logic or partial completion handling
        self._generate_final_report(success=False, error_details=details)
    
    def _handle_testing_timeout(self):
        """Handle testing phase timeout"""
        logger.warning("⏰ ORCHESTRATOR: Testing phase timed out")
        self._generate_final_report(success=False, timeout=True)
    
    def _generate_final_report(self, success: bool = True, **kwargs):
        """Generate final orchestration report"""
        total_duration = datetime.now() - self.workflow_start_time
        
        report = {
            'orchestration_summary': {
                'success': success,
                'total_duration_minutes': int(total_duration.total_seconds() / 60),
                'phases_executed': ['analysis', 'development', 'testing'],
                'agents_coordinated': self.registered_agents,
                'workflow_start': self.workflow_start_time.isoformat(),
                'workflow_end': datetime.now().isoformat()
            },
            'agent_completion_status': self.agent_completion_status,
            'issues_encountered': kwargs
        }
        
        logger.info("📋 ORCHESTRATOR: Final orchestration report:")
        logger.info(f"   Success: {success}")
        logger.info(f"   Duration: {int(total_duration.total_seconds() / 60)} minutes")
        logger.info(f"   Agents: {len(self.registered_agents)} coordinated")
        
        # Share final report
        self.comm.share_knowledge('orchestration_report', report)
        
        logger.info("🎯 ORCHESTRATOR: Orchestration session complete")

def main():
    """Main orchestrator execution"""
    print("🎯 ACTIVE ORCHESTRATOR STARTING")
    print("=" * 50)
    
    try:
        # Initialize orchestrator
        orchestrator = ActiveOrchestrator()
        
        # Start orchestration
        orchestrator.start_orchestration()
        
        # Keep running to monitor agents
        logger.info("🔄 ORCHESTRATOR: Entering monitoring mode...")
        
        try:
            while True:
                time.sleep(60)  # Keep alive
        except KeyboardInterrupt:
            logger.info("👋 ORCHESTRATOR: Shutdown requested")
            orchestrator.monitoring_active = False
            
    except Exception as e:
        logger.error(f"❌ ORCHESTRATOR: Fatal error: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
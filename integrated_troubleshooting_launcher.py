#!/usr/bin/env python3
"""
Integrated Troubleshooting System Launcher for Karen AI

Integrates with existing orchestrator_active.py workflow and launches
the collaborative troubleshooting ecosystem for multi-agent MCP development.
"""

import sys
import json
import time
import threading
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import logging

# Import our troubleshooting components
from troubleshooting_orchestrator import TroubleshootingOrchestrator
from agent_coordination_protocols import create_coordination_client
from enhanced_communication_system import create_communication_client
from testing_coordination_system import create_testing_coordinator
from knowledge_management_system import create_knowledge_manager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/workspace/logs/troubleshooting_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class IntegratedTroubleshootingSystem:
    """
    Main orchestrator for the collaborative troubleshooting system
    that integrates with Karen AI's existing orchestrator workflow.
    """
    
    def __init__(self):
        self.base_path = Path("/workspace/autonomous-agents")
        self.communication_path = self.base_path / "communication"
        self.orchestrator_inbox = self.communication_path / "inbox" / "orchestrator"
        
        # Core components
        self.troubleshooting_orchestrator = None
        self.coordination_clients = {}
        self.communication_clients = {}
        self.testing_coordinators = {}
        self.knowledge_managers = {}
        
        # Integration state
        self.running = False
        self.known_agents = {
            "mcp_codebase_tools": {
                "capabilities": ["mcp_tools", "python", "testing", "integration"],
                "specializations": ["tool_development", "api_integration"]
            },
            "business_intelligence": {
                "capabilities": ["metrics", "reporting", "data_analysis", "performance"],
                "specializations": ["roi_calculation", "dashboard_creation"]
            },
            "testing_agent": {
                "capabilities": ["test_automation", "validation", "integration_testing"],
                "specializations": ["pytest", "performance_testing"]
            },
            "troubleshooting_orchestrator": {
                "capabilities": ["coordination", "conflict_resolution", "workflow"],
                "specializations": ["agent_coordination", "issue_triage"]
            }
        }
        
        # Initialize communication infrastructure
        self._ensure_communication_infrastructure()
        
    def _ensure_communication_infrastructure(self):
        """Ensure communication infrastructure exists"""
        directories = [
            self.communication_path / "inbox" / "orchestrator",
            self.communication_path / "inbox" / "troubleshooting-orchestrator",
            self.communication_path / "outbox",
            self.base_path / "troubleshooting"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
    def start(self):
        """Start the integrated troubleshooting system"""
        logger.info("Starting Integrated Troubleshooting System")
        self.running = True
        
        try:
            # 1. Start core troubleshooting orchestrator
            self.troubleshooting_orchestrator = TroubleshootingOrchestrator()
            self.troubleshooting_orchestrator.start()
            
            # 2. Initialize components for each known agent
            for agent_id, agent_info in self.known_agents.items():
                self._initialize_agent_components(agent_id, agent_info)
                
            # 3. Start integration monitoring
            threading.Thread(target=self._monitor_orchestrator_integration, daemon=True).start()
            threading.Thread(target=self._monitor_agent_health, daemon=True).start()
            
            # 4. Register with main orchestrator
            self._register_with_orchestrator()
            
            # 5. Send initial status update
            self._send_startup_notification()
            
            logger.info("Integrated Troubleshooting System started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start troubleshooting system: {e}")
            self.stop()
            raise
            
    def _initialize_agent_components(self, agent_id: str, agent_info: Dict):
        """Initialize troubleshooting components for an agent"""
        try:
            # Create coordination client
            coordination_client = create_coordination_client(
                agent_id=agent_id,
                capabilities=agent_info["capabilities"],
                specializations=agent_info["specializations"]
            )
            self.coordination_clients[agent_id] = coordination_client
            
            # Create communication client
            communication_client = create_communication_client(
                agent_id=agent_id,
                subscribed_tags=["troubleshooting", "coordination", "testing"]
            )
            self.communication_clients[agent_id] = communication_client
            
            # Create testing coordinator
            testing_coordinator = create_testing_coordinator(agent_id)
            self.testing_coordinators[agent_id] = testing_coordinator
            
            # Create knowledge manager
            knowledge_manager = create_knowledge_manager(agent_id)
            self.knowledge_managers[agent_id] = knowledge_manager
            
            logger.info(f"Initialized troubleshooting components for {agent_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize components for {agent_id}: {e}")
            
    def _register_with_orchestrator(self):
        """Register troubleshooting system with main orchestrator"""
        registration_message = {
            "from": "troubleshooting_orchestrator",
            "to": "orchestrator",
            "type": "service_registration",
            "timestamp": datetime.now().isoformat(),
            "content": {
                "service_name": "integrated_troubleshooting_system",
                "capabilities": [
                    "multi_agent_coordination",
                    "conflict_resolution",
                    "testing_orchestration",
                    "knowledge_management",
                    "issue_triage",
                    "solution_sharing"
                ],
                "endpoints": {
                    "issue_reporting": "troubleshooting/issues/",
                    "solution_sharing": "troubleshooting/solutions/",
                    "testing_coordination": "troubleshooting/testing/",
                    "knowledge_base": "troubleshooting/knowledge-base/"
                },
                "status": "active",
                "version": "1.0.0"
            }
        }
        
        self._send_message_to_orchestrator(registration_message)
        
    def _send_startup_notification(self):
        """Send startup notification to all known agents"""
        notification = {
            "type": "troubleshooting_system_available",
            "timestamp": datetime.now().isoformat(),
            "content": {
                "services": [
                    "Issue coordination and triage",
                    "Multi-agent conflict resolution", 
                    "Testing environment management",
                    "Knowledge base and pattern matching",
                    "Solution sharing and validation"
                ],
                "how_to_use": {
                    "report_issue": "Send issue_report message to troubleshooting_orchestrator",
                    "request_help": "Send help_request message with problem description",
                    "share_solution": "Use solution_share message type",
                    "coordinate_testing": "Request test environment reservation"
                }
            }
        }
        
        # Broadcast to all agents
        for agent_id in self.known_agents.keys():
            if agent_id != "troubleshooting_orchestrator":
                self._send_message_to_agent(agent_id, {
                    **notification,
                    "from": "troubleshooting_orchestrator",
                    "to": agent_id
                })
                
    def _monitor_orchestrator_integration(self):
        """Monitor integration with main orchestrator"""
        while self.running:
            try:
                # Check for messages from main orchestrator
                if self.orchestrator_inbox.exists():
                    for message_file in self.orchestrator_inbox.glob("*.json"):
                        try:
                            with open(message_file, 'r') as f:
                                message = json.load(f)
                                
                            self._process_orchestrator_message(message)
                            
                            # Mark as processed
                            processed_file = self.orchestrator_inbox / f"processed_{message_file.name}"
                            message_file.rename(processed_file)
                            
                        except Exception as e:
                            logger.error(f"Error processing orchestrator message: {e}")
                            
                # Send periodic health updates
                self._send_health_update()
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring orchestrator integration: {e}")
                time.sleep(60)
                
    def _process_orchestrator_message(self, message: Dict):
        """Process messages from the main orchestrator"""
        message_type = message.get("type", "")
        
        if message_type == "health_check":
            self._respond_to_health_check(message)
        elif message_type == "agent_status_request":
            self._respond_with_agent_status(message)
        elif message_type == "coordination_request":
            self._handle_coordination_request(message)
        elif message_type == "priority_issue":
            self._handle_priority_issue(message)
        else:
            logger.info(f"Received orchestrator message: {message_type}")
            
    def _respond_to_health_check(self, message: Dict):
        """Respond to health check from main orchestrator"""
        response = {
            "from": "troubleshooting_orchestrator",
            "to": "orchestrator",
            "type": "health_check_response",
            "timestamp": datetime.now().isoformat(),
            "content": {
                "status": "healthy",
                "uptime_seconds": int(time.time() - getattr(self, 'start_time', time.time())),
                "components": {
                    "troubleshooting_orchestrator": "active",
                    "coordination_protocols": "active", 
                    "communication_system": "active",
                    "testing_coordination": "active",
                    "knowledge_management": "active"
                },
                "active_agents": len(self.coordination_clients),
                "active_issues": len(getattr(self.troubleshooting_orchestrator, 'active_issues', {})),
                "knowledge_entries": sum(len(km.knowledge_entries) for km in self.knowledge_managers.values())
            }
        }
        
        self._send_message_to_orchestrator(response)
        
    def _handle_coordination_request(self, message: Dict):
        """Handle coordination requests from main orchestrator"""
        request_type = message.get("content", {}).get("request_type", "")
        
        if request_type == "resolve_conflict":
            self._resolve_agent_conflict(message)
        elif request_type == "coordinate_testing":
            self._coordinate_testing_request(message)
        elif request_type == "share_knowledge":
            self._share_knowledge_request(message)
            
    def _resolve_agent_conflict(self, message: Dict):
        """Resolve conflicts between agents"""
        content = message.get("content", {})
        conflicting_agents = content.get("agents", [])
        conflict_resource = content.get("resource", "")
        
        logger.info(f"Resolving conflict between {conflicting_agents} over {conflict_resource}")
        
        # Use coordination protocol to resolve
        if len(conflicting_agents) >= 2:
            primary_agent = conflicting_agents[0]
            if primary_agent in self.coordination_clients:
                coord_client = self.coordination_clients[primary_agent]
                
                # Create coordination task for conflict resolution
                task_id = coord_client.create_coordination_task(
                    title=f"Resolve resource conflict: {conflict_resource}",
                    description=f"Coordinate access to {conflict_resource} between agents: {', '.join(conflicting_agents)}",
                    priority=coord_client.TaskPriority.HIGH,
                    required_resources=[conflict_resource],
                    tags=["conflict_resolution"],
                    estimated_duration=15
                )
                
                # Notify orchestrator of resolution attempt
                self._send_message_to_orchestrator({
                    "from": "troubleshooting_orchestrator",
                    "to": "orchestrator",
                    "type": "conflict_resolution_initiated",
                    "timestamp": datetime.now().isoformat(),
                    "content": {
                        "task_id": task_id,
                        "resource": conflict_resource,
                        "agents": conflicting_agents,
                        "estimated_resolution_minutes": 15
                    }
                })
                
    def _monitor_agent_health(self):
        """Monitor health of troubleshooting components"""
        while self.running:
            try:
                health_report = {}
                
                # Check coordination clients
                for agent_id, coord_client in self.coordination_clients.items():
                    status = coord_client.get_coordination_status()
                    health_report[f"{agent_id}_coordination"] = status
                    
                # Check communication clients
                for agent_id, comm_client in self.communication_clients.items():
                    stats = comm_client.get_communication_stats()
                    health_report[f"{agent_id}_communication"] = stats
                    
                # Check testing coordinators
                for agent_id, test_coord in self.testing_coordinators.items():
                    status = test_coord.get_testing_status()
                    health_report[f"{agent_id}_testing"] = status
                    
                # Check knowledge managers
                for agent_id, knowledge_mgr in self.knowledge_managers.items():
                    stats = knowledge_mgr.get_knowledge_stats()
                    health_report[f"{agent_id}_knowledge"] = stats
                    
                # Save health report
                health_file = self.base_path / "troubleshooting" / "health_report.json"
                with open(health_file, 'w') as f:
                    json.dump({
                        "timestamp": datetime.now().isoformat(),
                        "overall_status": "healthy",
                        "components": health_report
                    }, f, indent=2)
                    
                time.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error monitoring agent health: {e}")
                time.sleep(300)
                
    def _send_health_update(self):
        """Send periodic health update to orchestrator"""
        if hasattr(self, 'last_health_update'):
            time_since_last = time.time() - self.last_health_update
            if time_since_last < 300:  # Only send every 5 minutes
                return
                
        self.last_health_update = time.time()
        
        health_update = {
            "from": "troubleshooting_orchestrator",
            "to": "orchestrator", 
            "type": "health_update",
            "timestamp": datetime.now().isoformat(),
            "content": {
                "status": "operational",
                "active_components": len(self.coordination_clients),
                "recent_activity": {
                    "issues_processed": len(getattr(self.troubleshooting_orchestrator, 'active_issues', {})),
                    "tests_coordinated": sum(len(tc.active_executions) for tc in self.testing_coordinators.values()),
                    "knowledge_entries": sum(len(km.knowledge_entries) for km in self.knowledge_managers.values())
                }
            }
        }
        
        self._send_message_to_orchestrator(health_update)
        
    def _send_message_to_orchestrator(self, message: Dict):
        """Send message to main orchestrator"""
        orchestrator_inbox = self.communication_path / "inbox" / "orchestrator"
        orchestrator_inbox.mkdir(parents=True, exist_ok=True)
        
        message_file = orchestrator_inbox / f"troubleshooting_{int(time.time() * 1000)}.json"
        with open(message_file, 'w') as f:
            json.dump(message, f, indent=2)
            
    def _send_message_to_agent(self, agent_id: str, message: Dict):
        """Send message to specific agent"""
        agent_inbox = self.communication_path / "inbox" / agent_id
        agent_inbox.mkdir(parents=True, exist_ok=True)
        
        message_file = agent_inbox / f"troubleshooting_{int(time.time() * 1000)}.json"
        with open(message_file, 'w') as f:
            json.dump(message, f, indent=2)
            
    def discover_active_agents(self):
        """Discover active agents in the system"""
        inbox_path = self.communication_path / "inbox"
        if inbox_path.exists():
            discovered_agents = [d.name for d in inbox_path.iterdir() if d.is_dir()]
            
            for agent_id in discovered_agents:
                if agent_id not in self.known_agents and not agent_id.startswith("troubleshooting"):
                    # Add newly discovered agent
                    self.known_agents[agent_id] = {
                        "capabilities": ["general"],
                        "specializations": ["discovered"]
                    }
                    
                    # Initialize components for new agent
                    self._initialize_agent_components(agent_id, self.known_agents[agent_id])
                    
                    logger.info(f"Discovered new agent: {agent_id}")
                    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        return {
            "running": self.running,
            "components": {
                "troubleshooting_orchestrator": bool(self.troubleshooting_orchestrator),
                "coordination_clients": len(self.coordination_clients),
                "communication_clients": len(self.communication_clients),
                "testing_coordinators": len(self.testing_coordinators),
                "knowledge_managers": len(self.knowledge_managers)
            },
            "known_agents": list(self.known_agents.keys()),
            "integration_status": "active" if self.running else "inactive"
        }
        
    def stop(self):
        """Stop the integrated troubleshooting system"""
        logger.info("Stopping Integrated Troubleshooting System")
        self.running = False
        
        # Stop main orchestrator
        if self.troubleshooting_orchestrator:
            self.troubleshooting_orchestrator.stop()
            
        # Stop coordination clients
        for coord_client in self.coordination_clients.values():
            coord_client.stop_monitoring()
            
        # Stop communication clients
        for comm_client in self.communication_clients.values():
            comm_client.stop_monitoring()
            
        # Stop testing coordinators
        for test_coord in self.testing_coordinators.values():
            test_coord.stop()
            
        # Stop knowledge managers
        for knowledge_mgr in self.knowledge_managers.values():
            knowledge_mgr.stop()
            
        logger.info("Integrated Troubleshooting System stopped")

def main():
    """Main entry point for integrated troubleshooting system"""
    system = IntegratedTroubleshootingSystem()
    
    try:
        # Start the system
        system.start()
        
        # Discover any active agents
        system.discover_active_agents()
        
        # Keep running
        while system.running:
            time.sleep(10)
            
            # Periodically discover new agents
            system.discover_active_agents()
            
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"System error: {e}")
    finally:
        system.stop()

if __name__ == "__main__":
    main()
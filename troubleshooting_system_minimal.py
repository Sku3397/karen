#!/usr/bin/env python3
"""
Minimal Troubleshooting System - File-based only (no Redis dependency)

This version runs the core troubleshooting functionality using only 
file-based communication, perfect for environments without Redis.
"""

import json
import time
import threading
import logging
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass
from enum import Enum

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MessageType(Enum):
    ISSUE_REPORT = "issue_report"
    HELP_REQUEST = "help_request"
    SOLUTION_SHARE = "solution_share"
    STATUS_UPDATE = "status_update"
    COLLABORATION_INVITE = "collaboration_invite"

class IssueStatus(Enum):
    REPORTED = "reported"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"

@dataclass
class Issue:
    id: str
    title: str
    description: str
    reporter: str
    assigned_to: Optional[str]
    status: IssueStatus
    created_at: str
    updated_at: str
    tags: List[str]
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'reporter': self.reporter,
            'assigned_to': self.assigned_to,
            'status': self.status.value,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'tags': self.tags
        }

class MinimalTroubleshootingSystem:
    def __init__(self):
        self.base_path = Path("/workspace/autonomous-agents")
        self.communication_path = self.base_path / "communication"
        self.troubleshooting_path = self.base_path / "troubleshooting"
        self.inbox_path = self.communication_path / "inbox" / "troubleshooting-orchestrator"
        
        # State
        self.active_issues: Dict[str, Issue] = {}
        self.agent_capabilities = {
            "mcp_codebase_tools": ["mcp_tools", "python", "testing"],
            "business_intelligence": ["metrics", "reporting", "data_analysis"],
            "testing_agent": ["test_automation", "validation"]
        }
        self.running = False
        self.processed_messages = set()
        
        # Initialize directories
        self._setup_directories()
        
    def _setup_directories(self):
        """Setup required directory structure"""
        directories = [
            self.troubleshooting_path / "issues",
            self.troubleshooting_path / "solutions",
            self.troubleshooting_path / "coordination",
            self.troubleshooting_path / "knowledge-base",
            self.inbox_path,
            self.communication_path / "inbox" / "orchestrator"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            
    def start(self):
        """Start the minimal troubleshooting system"""
        logger.info("=" * 60)
        logger.info("KAREN AI COLLABORATIVE TROUBLESHOOTING SYSTEM")
        logger.info("=" * 60)
        logger.info("Starting file-based troubleshooting coordination...")
        
        self.running = True
        
        # Start monitoring thread
        threading.Thread(target=self._monitor_messages, daemon=True).start()
        
        # Send startup notification
        self._send_startup_notification()
        
        logger.info("✅ Troubleshooting system started successfully!")
        logger.info("")
        logger.info("Available Services:")
        logger.info("• Multi-agent issue coordination")
        logger.info("• Knowledge base and solution sharing")
        logger.info("• Agent communication facilitation")
        logger.info("• Problem assignment and tracking")
        logger.info("")
        logger.info("Agents can now:")
        logger.info("• Report issues → troubleshooting_orchestrator")
        logger.info("• Request help → send help_request message")
        logger.info("• Share solutions → use solution_share type")
        logger.info("• Collaborate on problems together")
        logger.info("")
        logger.info("System monitoring... Active and ready for issues!")
        
    def _monitor_messages(self):
        """Monitor for incoming messages"""
        while self.running:
            try:
                if self.inbox_path.exists():
                    for message_file in self.inbox_path.glob("*.json"):
                        if message_file.name in self.processed_messages:
                            continue
                            
                        try:
                            with open(message_file, 'r') as f:
                                message = json.load(f)
                                
                            self._process_message(message)
                            self.processed_messages.add(message_file.name)
                            
                            # Mark as processed
                            processed_file = self.inbox_path / f"processed_{message_file.name}"
                            message_file.rename(processed_file)
                            
                        except Exception as e:
                            logger.error(f"Error processing message {message_file}: {e}")
                            
                time.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring messages: {e}")
                time.sleep(5)
                
    def _process_message(self, message: Dict):
        """Process incoming message"""
        message_type = message.get("type", "")
        from_agent = message.get("from", "unknown")
        
        logger.info(f"📨 Received {message_type} from {from_agent}")
        
        if message_type == "issue_report":
            self._handle_issue_report(message)
        elif message_type == "help_request":
            self._handle_help_request(message)
        elif message_type == "solution_share":
            self._handle_solution_share(message)
        elif message_type == "status_update":
            self._handle_status_update(message)
            
    def _handle_issue_report(self, message: Dict):
        """Handle issue report from agent"""
        content = message.get("content", {})
        issue_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        issue = Issue(
            id=issue_id,
            title=content.get("title", message.get("subject", "Untitled Issue")),
            description=content.get("description", "No description provided"),
            reporter=message.get("from", "unknown"),
            assigned_to=None,
            status=IssueStatus.REPORTED,
            created_at=timestamp,
            updated_at=timestamp,
            tags=content.get("tags", [])
        )
        
        self.active_issues[issue_id] = issue
        self._save_issue(issue)
        
        # Try to assign the issue
        assigned_agent = self._find_best_agent(issue)
        if assigned_agent:
            issue.assigned_to = assigned_agent
            issue.status = IssueStatus.ASSIGNED
            issue.updated_at = datetime.now().isoformat()
            self._save_issue(issue)
            self._notify_agent_assignment(assigned_agent, issue)
            
        logger.info(f"🎯 Created issue {issue_id}: {issue.title}")
        if assigned_agent:
            logger.info(f"   Assigned to: {assigned_agent}")
        else:
            logger.info("   No suitable agent found, issue queued")
            
    def _handle_help_request(self, message: Dict):
        """Handle help request from agent"""
        logger.info(f"🆘 Help requested: {message.get('subject', 'No subject')}")
        
        # Create help issue
        help_message = {
            **message,
            "type": "issue_report",
            "content": {
                "title": f"Help Request: {message.get('subject', 'Assistance Needed')}",
                "description": message.get('content', {}).get('description', 'Agent requested help'),
                "tags": ["help_request"] + message.get('content', {}).get('tags', [])
            }
        }
        
        self._handle_issue_report(help_message)
        
    def _handle_solution_share(self, message: Dict):
        """Handle solution sharing from agent"""
        content = message.get("content", {})
        solution_id = str(uuid.uuid4())
        
        solution = {
            "id": solution_id,
            "title": content.get("title", "Shared Solution"),
            "description": content.get("description", ""),
            "author": message.get("from", "unknown"),
            "created_at": datetime.now().isoformat(),
            "problem_patterns": content.get("problem_patterns", []),
            "solution_steps": content.get("solution_steps", []),
            "tags": content.get("tags", [])
        }
        
        # Save solution
        solution_file = self.troubleshooting_path / "solutions" / f"{solution_id}.json"
        with open(solution_file, 'w') as f:
            json.dump(solution, f, indent=2)
            
        logger.info(f"💡 Solution shared: {solution['title']} by {solution['author']}")
        
        # Broadcast solution to other agents
        self._broadcast_solution(solution)
        
    def _handle_status_update(self, message: Dict):
        """Handle status updates from agents"""
        content = message.get("content", {})
        issue_id = content.get("issue_id")
        
        if issue_id and issue_id in self.active_issues:
            issue = self.active_issues[issue_id]
            status = content.get("status", "")
            
            if status == "resolved":
                issue.status = IssueStatus.RESOLVED
                issue.updated_at = datetime.now().isoformat()
                self._save_issue(issue)
                logger.info(f"✅ Issue {issue_id} marked as resolved")
                
    def _find_best_agent(self, issue: Issue) -> Optional[str]:
        """Find the best agent to handle an issue"""
        best_agent = None
        best_score = 0
        
        for agent, capabilities in self.agent_capabilities.items():
            score = 0
            
            # Check tag overlap
            for tag in issue.tags:
                if tag in capabilities:
                    score += 2
                    
            # Check description keywords
            description_lower = issue.description.lower()
            for capability in capabilities:
                if capability in description_lower:
                    score += 1
                    
            if score > best_score:
                best_score = score
                best_agent = agent
                
        return best_agent if best_score > 0 else None
        
    def _notify_agent_assignment(self, agent: str, issue: Issue):
        """Notify agent of issue assignment"""
        agent_inbox = self.communication_path / "inbox" / agent
        agent_inbox.mkdir(parents=True, exist_ok=True)
        
        message = {
            "from": "troubleshooting_orchestrator",
            "to": agent,
            "type": "issue_assignment",
            "timestamp": datetime.now().isoformat(),
            "subject": f"Issue Assigned: {issue.title}",
            "content": {
                "issue": issue.to_dict(),
                "assignment_reason": "Best capability match",
                "expected_response": "Please acknowledge and provide status updates"
            }
        }
        
        message_file = agent_inbox / f"assignment_{issue.id}.json"
        with open(message_file, 'w') as f:
            json.dump(message, f, indent=2)
            
    def _broadcast_solution(self, solution: Dict):
        """Broadcast solution to all agents"""
        for agent in self.agent_capabilities.keys():
            agent_inbox = self.communication_path / "inbox" / agent
            agent_inbox.mkdir(parents=True, exist_ok=True)
            
            message = {
                "from": "troubleshooting_orchestrator",
                "to": agent,
                "type": "solution_notification",
                "timestamp": datetime.now().isoformat(),
                "subject": f"New Solution Available: {solution['title']}",
                "content": {
                    "solution": solution,
                    "usage": "Available for reference in knowledge base"
                }
            }
            
            message_file = agent_inbox / f"solution_{solution['id']}.json"
            with open(message_file, 'w') as f:
                json.dump(message, f, indent=2)
                
    def _save_issue(self, issue: Issue):
        """Save issue to filesystem"""
        issue_file = self.troubleshooting_path / "issues" / f"{issue.id}.json"
        with open(issue_file, 'w') as f:
            json.dump(issue.to_dict(), f, indent=2)
            
    def _send_startup_notification(self):
        """Send startup notification to orchestrator"""
        orchestrator_inbox = self.communication_path / "inbox" / "orchestrator"
        orchestrator_inbox.mkdir(parents=True, exist_ok=True)
        
        message = {
            "from": "troubleshooting_orchestrator",
            "to": "orchestrator",
            "type": "service_started",
            "timestamp": datetime.now().isoformat(),
            "content": {
                "service": "collaborative_troubleshooting_system",
                "version": "1.0.0-minimal",
                "capabilities": [
                    "issue_coordination",
                    "agent_communication",
                    "solution_sharing",
                    "problem_assignment"
                ],
                "status": "active"
            }
        }
        
        message_file = orchestrator_inbox / f"troubleshooting_startup_{int(time.time())}.json"
        with open(message_file, 'w') as f:
            json.dump(message, f, indent=2)
            
    def get_status(self) -> Dict:
        """Get system status"""
        return {
            "running": self.running,
            "active_issues": len(self.active_issues),
            "resolved_issues": len([i for i in self.active_issues.values() if i.status == IssueStatus.RESOLVED]),
            "known_agents": list(self.agent_capabilities.keys()),
            "last_activity": datetime.now().isoformat()
        }
        
    def stop(self):
        """Stop the system"""
        self.running = False
        logger.info("Troubleshooting system stopped")

def main():
    """Main entry point"""
    system = MinimalTroubleshootingSystem()
    
    try:
        system.start()
        
        # Keep running and show periodic status
        while system.running:
            time.sleep(30)
            status = system.get_status()
            logger.info(f"📊 Status: {status['active_issues']} active issues, {status['resolved_issues']} resolved")
            
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        system.stop()

if __name__ == "__main__":
    main()
"""
AgentCommunication Implementation for Karen Orchestrator
=======================================================
Based on the template in shared-knowledge/templates/agent_communication_template.py
"""

import json
import os
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

class AgentCommunication:
    """
    Simplified file-based agent communication system.
    Uses the communication directory structure for message passing.
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.comm_dir = '/mnt/c/Users/Man/ultra/projects/karen/autonomous-agents/communication'
        self.status_dir = os.path.join(self.comm_dir, 'status')
        self.inbox_dir = os.path.join(self.comm_dir, 'inbox')
        self.outbox_dir = os.path.join(self.comm_dir, 'outbox')
        self.knowledge_dir = os.path.join(self.comm_dir, 'knowledge-base')
        
        # Ensure directories exist
        for dir_path in [self.status_dir, self.inbox_dir, self.outbox_dir, self.knowledge_dir]:
            os.makedirs(dir_path, exist_ok=True)
            
        print(f"AgentCommunication initialized for {agent_id}")
    
    def update_status(self, status: str, progress: int, details: Dict[str, Any] = None):
        """Update agent status in status directory."""
        status_data = {
            'agent': self.agent_id,
            'status': status,
            'progress': progress,
            'details': details or {},
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        status_file = os.path.join(self.status_dir, f'{self.agent_id}_status.json')
        with open(status_file, 'w') as f:
            json.dump(status_data, f, indent=2)
        
        print(f"Updated status for {self.agent_id}: {status} ({progress}%)")
    
    def send_message(self, recipient: str, message_type: str, content: Dict[str, Any]):
        """Send message to another agent's inbox."""
        timestamp = datetime.now(timezone.utc)
        message_id = f"{int(timestamp.timestamp() * 1000000)}"
        
        message_data = {
            'id': message_id,
            'sender': self.agent_id,
            'recipient': recipient,
            'message_type': message_type,
            'content': content,
            'timestamp': timestamp.isoformat()
        }
        
        # Create recipient inbox directory if needed
        recipient_inbox = os.path.join(self.inbox_dir, recipient)
        os.makedirs(recipient_inbox, exist_ok=True)
        
        # Save message to recipient's inbox
        filename = f"{self.agent_id}_to_{recipient}_{timestamp.strftime('%Y%m%d_%H%M%S')}_{message_id[-6:]}.json"
        message_file = os.path.join(recipient_inbox, filename)
        
        with open(message_file, 'w') as f:
            json.dump(message_data, f, indent=2)
        
        print(f"Sent '{message_type}' message from {self.agent_id} to {recipient}")
        return message_file
    
    def get_all_agent_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all agents."""
        statuses = {}
        
        if os.path.exists(self.status_dir):
            for filename in os.listdir(self.status_dir):
                if filename.endswith('_status.json'):
                    agent_name = filename.replace('_status.json', '')
                    status_file = os.path.join(self.status_dir, filename)
                    
                    try:
                        with open(status_file, 'r') as f:
                            statuses[agent_name] = json.load(f)
                    except Exception as e:
                        print(f"Error reading status for {agent_name}: {e}")
                        statuses[agent_name] = {
                            'status': 'unknown',
                            'progress': 0,
                            'error': str(e)
                        }
        
        return statuses
    
    def share_knowledge(self, knowledge_type: str, data: Dict[str, Any]):
        """Share knowledge in the knowledge base."""
        timestamp = datetime.now(timezone.utc)
        
        knowledge_data = {
            'contributor': self.agent_id,
            'type': knowledge_type,
            'content': data,
            'timestamp': timestamp.isoformat()
        }
        
        # Create filename with timestamp
        filename = f"{knowledge_type}_{self.agent_id}_{timestamp.strftime('%Y%m%d_%H%M%S_%f')[:-3]}.json"
        knowledge_file = os.path.join(self.knowledge_dir, filename)
        
        with open(knowledge_file, 'w') as f:
            json.dump(knowledge_data, f, indent=2)
        
        print(f"Shared knowledge '{knowledge_type}' from {self.agent_id}")
        return knowledge_file
    
    def check_archaeologist_complete(self) -> bool:
        """Check if archaeologist has been active by looking for knowledge base entries."""
        if not os.path.exists(self.knowledge_dir):
            return False
        
        # Look for recent knowledge base entries (within last hour)
        current_time = datetime.now(timezone.utc)
        recent_entries = []
        
        for filename in os.listdir(self.knowledge_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(self.knowledge_dir, filename)
                # Check file modification time
                mod_time = datetime.fromtimestamp(os.path.getmtime(file_path), tz=timezone.utc)
                time_diff = (current_time - mod_time).total_seconds()
                
                if time_diff < 3600:  # Within last hour
                    recent_entries.append(filename)
        
        # Consider archaeologist active if there are recent knowledge entries
        return len(recent_entries) > 10  # Arbitrary threshold
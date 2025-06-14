#!/usr/bin/env python3
"""
Infinite orchestrator loop using file-based agent communication
Coordinates all agents without Redis dependency
"""
import sys
import time
import json
import os
import glob
from datetime import datetime, timedelta
from pathlib import Path

# Setup paths
sys.path.append('.')

class FileBasedOrchestrator:
    """Orchestrator using file-based communication system"""
    
    def __init__(self):
        self.agent_name = "orchestrator"
        self.inbox_path = "autonomous-agents/communication/inbox/orchestrator"
        self.outbox_path = "autonomous-agents/communication/outbox"
        self.status_path = "autonomous-agents/communication/status"
        self.knowledge_path = "autonomous-agents/communication/knowledge-base"
        
        # Ensure directories exist
        Path(self.inbox_path).mkdir(parents=True, exist_ok=True)
        Path(self.outbox_path).mkdir(parents=True, exist_ok=True)
        Path(self.status_path).mkdir(parents=True, exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        
        self.registered_agents = [
            'archaeologist',
            'sms_engineer', 
            'phone_engineer',
            'memory_engineer',
            'test_engineer'
        ]
        
        self.cycle_count = 0
        
    def log(self, message):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] ORCHESTRATOR: {message}"
        print(log_message)
        
        # Also write to log file
        with open(f"logs/orchestrator_{datetime.now().strftime('%Y%m%d')}.log", "a") as f:
            f.write(log_message + "\n")
    
    def update_status(self, status, progress, details=None):
        """Update orchestrator status"""
        status_data = {
            "agent": "orchestrator",
            "status": status,
            "progress": progress,
            "details": details or {},
            "cycle_count": self.cycle_count,
            "timestamp": datetime.now().isoformat()
        }
        
        status_file = f"{self.status_path}/orchestrator_status.json"
        with open(status_file, "w") as f:
            json.dump(status_data, f, indent=2)
        
        self.log(f"Status updated: {status} ({progress}%)")
    
    def send_message(self, to_agent, msg_type, content):
        """Send message to agent inbox"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        message = {
            "from": "orchestrator",
            "to": to_agent,
            "type": msg_type,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to specific agent inbox
        agent_inbox = f"autonomous-agents/communication/inbox/{to_agent}"
        Path(agent_inbox).mkdir(parents=True, exist_ok=True)
        
        message_file = f"{agent_inbox}/orchestrator_to_{to_agent}_{timestamp}.json"
        with open(message_file, "w") as f:
            json.dump(message, f, indent=2)
        
        self.log(f"Message sent to {to_agent}: {msg_type}")
    
    def read_inbox_messages(self):
        """Read all messages from orchestrator inbox"""
        messages = []
        inbox_files = glob.glob(f"{self.inbox_path}/*.json")
        
        for file_path in inbox_files:
            try:
                with open(file_path, 'r') as f:
                    message = json.load(f)
                    messages.append((file_path, message))
            except Exception as e:
                self.log(f"Error reading message {file_path}: {e}")
        
        return messages
    
    def process_inbox_message(self, file_path, message):
        """Process a single inbox message"""
        try:
            from_agent = message.get("from")
            msg_type = message.get("type")
            content = message.get("content", {})
            
            self.log(f"Processing message from {from_agent}: {msg_type}")
            
            if msg_type == "analysis_complete":
                self.handle_analysis_complete(from_agent, content)
            elif msg_type == "implementation_complete":
                self.handle_implementation_complete(from_agent, content)
            elif msg_type == "test_results":
                self.handle_test_results(from_agent, content)
            elif msg_type == "help_request":
                self.handle_help_request(from_agent, content)
            elif msg_type == "status_update":
                self.handle_status_update(from_agent, content)
            
            # Move processed message
            processed_dir = f"{self.inbox_path}/processed"
            Path(processed_dir).mkdir(exist_ok=True)
            processed_path = f"{processed_dir}/{os.path.basename(file_path)}"
            os.rename(file_path, processed_path)
            
        except Exception as e:
            self.log(f"Error processing message {file_path}: {e}")
    
    def handle_analysis_complete(self, from_agent, content):
        """Handle analysis completion from agents"""
        if from_agent == "archaeologist":
            # Archaeologist completed - coordinate implementation
            self.log("Archaeologist analysis complete - coordinating implementation")
            
            # Send tasks to other agents
            self.send_message("memory_engineer", "high_priority_task", {
                "task": "implement_cross_medium_memory",
                "archaeological_findings": content.get("critical_findings", {}),
                "templates": content.get("templates_delivered", {})
            })
            
            self.send_message("sms_engineer", "implementation_ready", {
                "task": "finalize_sms_implementation", 
                "patterns_ready": True,
                "archaeological_findings": content.get("critical_findings", {})
            })
    
    def handle_implementation_complete(self, from_agent, content):
        """Handle implementation completion"""
        self.log(f"{from_agent} implementation complete")
        
        # Trigger testing
        self.send_message("test_engineer", "test_request", {
            "agent_to_test": from_agent,
            "test_types": ["unit", "integration"],
            "implementation_details": content
        })
    
    def handle_test_results(self, from_agent, content):
        """Handle test results"""
        test_status = content.get("status", "unknown")
        self.log(f"Test results from {from_agent}: {test_status}")
        
        if test_status == "failed":
            # Send back to implementation
            failed_agent = content.get("tested_agent")
            if failed_agent:
                self.send_message(failed_agent, "fix_required", {
                    "test_failures": content.get("failures", []),
                    "priority": "high"
                })
    
    def handle_help_request(self, from_agent, content):
        """Handle help requests between agents"""
        target_agent = content.get("target_agent")
        help_type = content.get("help_type")
        
        if target_agent and help_type:
            self.send_message(target_agent, "help_request_forwarded", {
                "requesting_agent": from_agent,
                "help_type": help_type,
                "details": content.get("details", {})
            })
    
    def handle_status_update(self, from_agent, content):
        """Handle status updates from agents"""
        status = content.get("status")
        self.log(f"{from_agent} status: {status}")
    
    def check_agent_health(self):
        """Check health of all registered agents"""
        for agent in self.registered_agents:
            status_file = f"{self.status_path}/{agent}_status.json"
            
            if os.path.exists(status_file):
                try:
                    with open(status_file, 'r') as f:
                        status_data = json.load(f)
                    
                    # Check if agent is stuck or failed
                    agent_status = status_data.get("status", "unknown")
                    if agent_status in ["error", "failed", "stuck"]:
                        self.log(f"Agent {agent} needs attention: {agent_status}")
                        self.send_message(agent, "recovery_request", {
                            "reason": agent_status,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                except Exception as e:
                    self.log(f"Error checking {agent} status: {e}")
            else:
                self.log(f"No status file for {agent}")
    
    def monitor_system_health(self):
        """Monitor overall system health"""
        # Check if email system is working
        email_test_file = "logs/email_agent_activity.log"
        if os.path.exists(email_test_file):
            # Check if recent activity (last 10 minutes)
            try:
                stat = os.stat(email_test_file)
                last_modified = datetime.fromtimestamp(stat.st_mtime)
                if datetime.now() - last_modified > timedelta(minutes=10):
                    self.log("WARNING: Email system may be down")
                    # Send alert to test engineer
                    self.send_message("test_engineer", "system_check", {
                        "priority": "urgent",
                        "system": "email",
                        "issue": "no_recent_activity"
                    })
            except Exception as e:
                self.log(f"Error checking email system: {e}")
    
    def execute_orchestration_cycle(self):
        """Execute one orchestration cycle"""
        self.cycle_count += 1
        self.log(f"Starting orchestration cycle #{self.cycle_count}")
        
        # Update status
        self.update_status("orchestrating", 
                          min(85 + (self.cycle_count % 10), 100), 
                          {
                              "cycle": self.cycle_count,
                              "agents_monitored": len(self.registered_agents),
                              "last_cycle": datetime.now().isoformat()
                          })
        
        # 1. Check agent health
        self.check_agent_health()
        
        # 2. Process inbox messages
        messages = self.read_inbox_messages()
        for file_path, message in messages:
            self.process_inbox_message(file_path, message)
        
        # 3. Monitor system health
        self.monitor_system_health()
        
        # 4. Periodic coordination tasks
        if self.cycle_count % 12 == 0:  # Every hour (5min * 12)
            self.log("Performing periodic system coordination")
            # Check if any agents need coordination
            for agent in self.registered_agents:
                self.send_message(agent, "health_check", {
                    "timestamp": datetime.now().isoformat(),
                    "orchestrator_cycle": self.cycle_count
                })
        
        self.log(f"Orchestration cycle #{self.cycle_count} complete")
    
    def run_infinite_loop(self):
        """Run the orchestrator in an infinite loop"""
        self.log("Starting infinite orchestration loop")
        
        try:
            while True:
                try:
                    self.execute_orchestration_cycle()
                    
                    # Sleep for 5 minutes between cycles
                    self.log("Sleeping for 5 minutes...")
                    time.sleep(300)
                    
                except KeyboardInterrupt:
                    self.log("Orchestrator interrupted by user")
                    break
                except Exception as e:
                    self.log(f"Error in orchestration cycle: {e}")
                    # Continue running even if there's an error
                    time.sleep(60)  # Wait 1 minute before retrying
                    
        except Exception as e:
            self.log(f"Fatal orchestrator error: {e}")
        finally:
            self.update_status("stopped", 0, {"reason": "orchestrator_stopped"})
            self.log("Orchestrator stopped")

def main():
    """Main entry point"""
    orchestrator = FileBasedOrchestrator()
    orchestrator.run_infinite_loop()

if __name__ == "__main__":
    main()
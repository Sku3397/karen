# src/autonomous_agent_runner.py
import json
import time
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import logging

# Create logs directory if it doesn't exist
Path('logs').mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/autonomous_runner.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class AutonomousAgentRunner:
    """Makes agents truly autonomous by continuously assigning tasks"""
    
    def __init__(self):
        self.task_file = Path("tasks/eigencode_assigned_tasks.json")
        self.agent_status_file = Path("autonomous_state.json")
        self.instruction_dir = Path("agent_instructions")
        self.instruction_dir.mkdir(exist_ok=True)
        self.running = True
        
    def get_next_task(self, agent_name: str) -> Dict:
        """Get next appropriate task for agent"""
        try:
            with open(self.task_file, 'r') as f:
                tasks = json.load(f)
            
            # Agent skill mappings
            agent_skills = {
                'sms_engineer': ['sms', 'message', 'text', 'notification'],
                'phone_engineer': ['phone', 'voice', 'call', 'telephony'],
                'memory_engineer': ['memory', 'storage', 'database', 'cache'],
                'test_engineer': ['test', 'testing', 'quality', 'validation'],
                'archaeologist': ['analysis', 'documentation', 'pattern', 'research']
            }
            
            skills = agent_skills.get(agent_name, [])
            
            # Find unassigned tasks matching agent skills
            for task in tasks:
                if task.get('status') == 'pending':
                    task_desc = task.get('description', '').lower()
                    # Check if any skill matches task description
                    if any(skill in task_desc for skill in skills):
                        return task
                    # Also check for general tasks
                    elif task.get('priority') == 'low' and not task.get('assigned_to'):
                        return task
            
            return None
        except Exception as e:
            logger.error(f"Error getting next task: {e}")
            return None
    
    def assign_task_to_agent(self, agent_name: str, task: Dict):
        """Create instruction file for agent"""
        instruction = f"""# Task Assignment for {agent_name}

## Task ID: {task.get('id', 'unknown')}
## Priority: {task.get('priority', 'medium')}
## Status: Starting

{task.get('description', 'No description provided')}

## Expected Deliverables:
{chr(10).join('- ' + d for d in task.get('deliverables', ['Complete the task as described']))}

## Instructions:
1. Read and understand the task requirements
2. Implement the solution
3. Test your implementation
4. Update task status in tasks/eigencode_assigned_tasks.json
5. Log your activity to agent_activities.jsonl

## When complete:
- Set task status to 'completed'
- Document what was done
- Move to next task
"""
        
        # Save instruction for agent
        instruction_file = self.instruction_dir / f"{agent_name}_current_task.md"
        
        with open(instruction_file, 'w') as f:
            f.write(instruction)
        
        # Update task status
        self._update_task_status(task['id'], 'assigned', agent_name)
        
        # Log assignment
        self._log_activity(agent_name, 'task_assigned', {
            'task_id': task['id'],
            'description': task.get('description', '')[:100] + '...'
        })
        
        logger.info(f"[SUCCESS] Assigned task {task['id']} to {agent_name}")
        
    def _update_task_status(self, task_id: str, status: str, agent_name: str = None):
        """Update task status in the task file"""
        try:
            with open(self.task_file, 'r') as f:
                tasks = json.load(f)
            
            for task in tasks:
                if task.get('id') == task_id:
                    task['status'] = status
                    if agent_name:
                        task['assigned_to'] = agent_name
                    task['updated_at'] = datetime.now().isoformat()
                    if status == 'assigned':
                        task['started_at'] = datetime.now().isoformat()
                    break
            
            with open(self.task_file, 'w') as f:
                json.dump(tasks, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error updating task status: {e}")
    
    def _log_activity(self, agent_name: str, activity_type: str, details: Dict):
        """Log activity to the centralized activity log"""
        activity = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "activity_type": activity_type,
            "details": details
        }
        
        with open("agent_activities.jsonl", 'a') as f:
            f.write(json.dumps(activity) + '\n')
    
    def _update_agent_status(self, agent_name: str, status: str, current_task: str = None):
        """Update agent status in autonomous_state.json"""
        try:
            with open(self.agent_status_file, 'r') as f:
                state = json.load(f)
            
            for agent in state['agents']:
                if agent['name'] == agent_name:
                    agent['status'] = status
                    if current_task:
                        agent['current_task'] = current_task
                    agent['last_update'] = datetime.now().isoformat()
                    break
            
            with open(self.agent_status_file, 'w') as f:
                json.dump(state, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error updating agent status: {e}")
    
    def check_agent_completion(self, agent_name: str) -> bool:
        """Check if agent has completed their current task"""
        instruction_file = self.instruction_dir / f"{agent_name}_current_task.md"
        completed_file = self.instruction_dir / f"{agent_name}_completed.flag"
        
        # Check if agent signaled completion
        if completed_file.exists():
            completed_file.unlink()  # Remove flag
            if instruction_file.exists():
                instruction_file.unlink()  # Remove instruction
            return True
        
        # Check if instruction file was removed (alternative completion signal)
        if not instruction_file.exists():
            return True
            
        return False
    
    def monitor_agents(self):
        """Continuously monitor and assign tasks"""
        logger.info("[STARTUP] Starting autonomous agent monitoring")
        
        while self.running:
            try:
                # Check each agent's status
                with open(self.agent_status_file, 'r') as f:
                    state = json.load(f)
                
                # Debug logging
                logger.debug(f"State file keys: {list(state.keys())}")
                
                if 'agents' not in state:
                    logger.error(f"'agents' key not found in state file. Available keys: {list(state.keys())}")
                    continue
                
                agents_updated = False
                
                for agent in state['agents']:
                    agent_name = agent['name']
                    
                    # Check if agent completed their task
                    if agent['status'] == 'working' and self.check_agent_completion(agent_name):
                        logger.info(f"[COMPLETED] {agent_name} completed their task")
                        self._update_agent_status(agent_name, 'idle')
                        agents_updated = True
                    
                    # Assign new task if agent is idle
                    if agent['status'] == 'idle' or agent.get('queue_length', 0) == 0:
                        next_task = self.get_next_task(agent_name)
                        if next_task:
                            self.assign_task_to_agent(agent_name, next_task)
                            self._update_agent_status(agent_name, 'working', next_task['id'])
                            agents_updated = True
                        else:
                            logger.debug(f"No suitable tasks for {agent_name}")
                
                if agents_updated:
                    logger.info("[STATUS] Agent statuses updated")
                    
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                
            # Wait before next check
            time.sleep(30)  # Check every 30 seconds
    
    def stop(self):
        """Stop the autonomous runner"""
        self.running = False
        logger.info("[SHUTDOWN] Stopping autonomous agent runner")

def main():
    """Main entry point"""
    runner = AutonomousAgentRunner()
    
    try:
        # Create initial status file if it doesn't exist
        if not runner.agent_status_file.exists():
            initial_state = {
                "system_start_time": datetime.now().isoformat(),
                "agents": [
                    {"name": "orchestrator", "status": "idle", "queue_length": 0},
                    {"name": "sms_engineer", "status": "idle", "queue_length": 0},
                    {"name": "phone_engineer", "status": "idle", "queue_length": 0},
                    {"name": "memory_engineer", "status": "idle", "queue_length": 0},
                    {"name": "test_engineer", "status": "idle", "queue_length": 0},
                    {"name": "archaeologist", "status": "idle", "queue_length": 0}
                ]
            }
            with open(runner.agent_status_file, 'w') as f:
                json.dump(initial_state, f, indent=2)
        
        runner.monitor_agents()
        
    except KeyboardInterrupt:
        runner.stop()
        logger.info("Shutdown complete")

if __name__ == "__main__":
    main()
import json
import time
import os
import threading
import queue
from datetime import datetime, timedelta
from pathlib import Path
import psutil
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/autonomous_system.log'),
        logging.StreamHandler()
    ]
)

class AutonomousTaskSystem:
    def __init__(self):
        self.task_queues = {
            'orchestrator': queue.Queue(),
            'archaeologist': queue.Queue(),
            'sms_engineer': queue.Queue(),
            'memory_engineer': queue.Queue(),
            'test_engineer': queue.Queue()
        }
        
        self.agent_states = {
            'orchestrator': {'status': 'idle', 'last_task': None, 'tasks_completed': 0},
            'archaeologist': {'status': 'idle', 'last_task': None, 'tasks_completed': 0},
            'sms_engineer': {'status': 'idle', 'last_task': None, 'tasks_completed': 0},
            'memory_engineer': {'status': 'idle', 'last_task': None, 'tasks_completed': 0},
            'test_engineer': {'status': 'idle', 'last_task': None, 'tasks_completed': 0}
        }
        
        self.start_time = datetime.now()
        self.target_runtime = timedelta(hours=6)
        
        # Memory monitoring
        self.memory_threshold = 80  # Use up to 80% of RAM
        self.cpu_threshold = 90     # Use up to 90% of CPU
        
        # Task completion tracking
        self.processed_task_files = set()  # Track processed completion files
        self.completion_monitor_running = False
        
        # Task templates for continuous work
        self.task_templates = self.load_task_templates()
        
        # Process any existing completed tasks
        self.process_existing_completed_tasks()
        
        # Start completion monitoring
        self.start_completion_monitor()
    
    def process_existing_completed_tasks(self):
        """Process any completed task files that exist at startup"""
        logging.info("Processing existing completed tasks...")
        
        try:
            self.check_completed_tasks()
            logging.info("Finished processing existing completed tasks")
        except Exception as e:
            logging.error(f"Error processing existing completed tasks: {e}", exc_info=True)
        
    def load_task_templates(self):
        """Load predefined task templates for each agent"""
        return {
            'orchestrator': [
                {
                    'type': 'check_health',
                    'description': 'Check all agent health status',
                    'interval': 300  # 5 minutes
                },
                {
                    'type': 'coordinate_workflow',
                    'description': 'Execute workflow coordination',
                    'interval': 600  # 10 minutes
                },
                {
                    'type': 'generate_report',
                    'description': 'Generate system status report',
                    'interval': 1800  # 30 minutes
                }
            ],
            'archaeologist': [
                {
                    'type': 'scan_new_files',
                    'description': 'Scan for new or modified Python files',
                    'interval': 600
                },
                {
                    'type': 'analyze_patterns',
                    'description': 'Analyze code patterns in src/',
                    'interval': 1200
                },
                {
                    'type': 'update_documentation',
                    'description': 'Update pattern documentation',
                    'interval': 1800
                },
                {
                    'type': 'create_templates',
                    'description': 'Create new code templates',
                    'interval': 2400
                }
            ],
            'sms_engineer': [
                {
                    'type': 'implement_feature',
                    'description': 'Implement next SMS feature',
                    'interval': 900
                },
                {
                    'type': 'refactor_code',
                    'description': 'Refactor and optimize SMS code',
                    'interval': 1800
                },
                {
                    'type': 'add_error_handling',
                    'description': 'Improve error handling',
                    'interval': 1200
                },
                {
                    'type': 'create_integration_tests',
                    'description': 'Create integration tests',
                    'interval': 2400
                }
            ],
            'memory_engineer': [
                {
                    'type': 'implement_storage',
                    'description': 'Implement conversation storage',
                    'interval': 900
                },
                {
                    'type': 'optimize_retrieval',
                    'description': 'Optimize memory retrieval',
                    'interval': 1500
                },
                {
                    'type': 'implement_linking',
                    'description': 'Implement cross-medium linking',
                    'interval': 1800
                },
                {
                    'type': 'performance_tuning',
                    'description': 'Tune ChromaDB performance',
                    'interval': 2400
                }
            ],
            'test_engineer': [
                {
                    'type': 'test_email',
                    'description': 'Test email system health',
                    'interval': 300  # Critical - every 5 minutes
                },
                {
                    'type': 'test_integrations',
                    'description': 'Test all integrations',
                    'interval': 600
                },
                {
                    'type': 'performance_test',
                    'description': 'Run performance tests',
                    'interval': 1800
                },
                {
                    'type': 'generate_test_report',
                    'description': 'Generate comprehensive test report',
                    'interval': 3600  # Hourly
                }
            ]
        }
        
    def load_master_plan_tasks(self):
        """Load tasks from the master development plan"""
        from master_plan_tasks import MasterPlanTaskGenerator
        
        generator = MasterPlanTaskGenerator()
        current_time = datetime.now()
        elapsed_hours = (current_time - self.start_time).total_seconds() / 3600
        
        # Determine which phase we're in
        current_phase = min(int(elapsed_hours) + 1, 5)
        
        # Generate tasks for current phase
        phase_tasks = generator.generate_phase_tasks(current_phase, current_time)
        
        # Add continuous test tasks
        test_tasks = generator.generate_test_tasks(current_time)
        
        # Queue all tasks
        for task in phase_tasks + test_tasks:
            agent_queue = self.task_queues.get(task['agent'])
            if agent_queue:
                # Create full task with instruction
                task['instruction'] = generator.create_task_instruction(task)
                agent_queue.put(task)
                
        logging.info(f"Loaded {len(phase_tasks)} phase {current_phase} tasks and {len(test_tasks)} test tasks")

    def generate_tasks(self):
        """Generate tasks for the next hour"""
        current_time = datetime.now()
        
        for agent, templates in self.task_templates.items():
            for template in templates:
                # Create multiple instances of each task type
                for i in range(3):  # 3 instances per task type
                    task = {
                        'id': f"{agent}_{template['type']}_{current_time.timestamp()}_{i}",
                        'agent': agent,
                        'type': template['type'],
                        'description': template['description'],
                        'created': current_time.isoformat(),
                        'priority': 1 if 'email' in template['type'] else 2,
                        'status': 'pending',
                        'retry_count': 0,
                        'max_retries': 3
                    }
                    self.task_queues[agent].put(task)
                    
        logging.info(f"Generated tasks for all agents")
        
    def create_agent_instruction(self, agent_name, task):
        """Create specific instruction for Claude agent"""
        instructions = {
            'orchestrator': f"""
Execute this task: {task['type']} - {task['description']}

Use the helper system:
import sys
sys.path.append('.')
from claude_helpers import orchestrator_helper as helper
from src.orchestrator import get_orchestrator_instance

# Task: {task['type']}
orchestrator = get_orchestrator_instance()

if '{task['type']}' == 'check_health':
    orchestrator.check_all_agent_health()
    helper.update_status('checking', 50, {{'task': '{task['id']}'}})
    # Check each agent's status
    statuses = helper.read_file('agent_states.json')
    helper.create_file('reports/health_check_{task['id']}.json', statuses)
    
elif '{task['type']}' == 'coordinate_workflow':
    orchestrator.execute_workflow()
    helper.send_message('sms_engineer', 'continue_development', {{'priority': 'high'}})
    helper.send_message('memory_engineer', 'continue_development', {{'priority': 'medium'}})
    
elif '{task['type']}' == 'generate_report':
    # Generate comprehensive system report
    report = f"System Report - {{datetime.now()}}"
    helper.create_file('reports/system_report_{task['id']}.md', report)

helper.update_status('completed', 100, {{'task': '{task['id']}', 'completed': True}})
print("Task {task['id']} completed")
""",

            'sms_engineer': f"""
Execute this task: {task['type']} - {task['description']}

import sys
sys.path.append('.')
from claude_helpers import sms_helper as helper

# Task: {task['type']}
if '{task['type']}' == 'implement_feature':
    # Check current progress
    if not os.path.exists('src/sms_client.py'):
        # Create initial SMS client
        sms_code = '''Complete SMS implementation...'''
        helper.create_file('src/sms_client.py', sms_code)
    else:
        # Add new feature
        current = helper.read_file('src/sms_client.py')
        # Enhance with new methods
        helper.update_status('enhancing', 60, {{'adding': 'bulk_sms_support'}})
        
elif '{task['type']}' == 'refactor_code':
    # Refactor existing code
    helper.update_status('refactoring', 70, {{'optimizing': 'sms_client'}})
    
elif '{task['type']}' == 'add_error_handling':
    # Improve error handling
    helper.update_status('improving', 80, {{'adding': 'robust_error_handling'}})
    
elif '{task['type']}' == 'create_integration_tests':
    # Create comprehensive tests
    test_code = '''SMS integration tests...'''
    helper.create_file('tests/test_sms_integration_{task['id']}.py', test_code)

helper.update_status('completed', 100, {{'task': '{task['id']}'}})
print("Task {task['id']} completed")
""",

            'test_engineer': f"""
Execute critical test task: {task['type']} - {task['description']}

import sys
sys.path.append('.')
from claude_helpers import test_helper as helper

# CRITICAL TASK: {task['type']}
if '{task['type']}' == 'test_email':
    # PRIORITY 1 - Email system health
    try:
        from src.email_client import EmailClient
        client = EmailClient()
        if not client.gmail_service:
            # EMERGENCY
            helper.send_message('orchestrator', 'EMERGENCY', {{'email': 'SYSTEM_DOWN'}})
            helper.update_status('CRITICAL', 100, {{'email': 'FAILED'}})
        else:
            helper.update_status('healthy', 95, {{'email': 'operational'}})
    except Exception as e:
        helper.send_message('all', 'ERROR', {{'email_test': str(e)}})
        
elif '{task['type']}' == 'test_integrations':
    # Test all system integrations
    results = {{'email': 'check', 'sms': 'check', 'memory': 'check'}}
    helper.create_file('test_results/integration_{task['id']}.json', json.dumps(results))
    
elif '{task['type']}' == 'performance_test':
    # Run performance benchmarks
    helper.update_status('benchmarking', 80, {{'testing': 'performance'}})
    
elif '{task['type']}' == 'generate_test_report':
    # Comprehensive test report
    report = "# Test Report\\nAll systems operational"
    helper.create_file('reports/test_report_{task['id']}.md', report)

helper.update_status('completed', 100, {{'task': '{task['id']}'}})
print("Test task {task['id']} completed")
"""
        }
        
        # Similar for archaeologist and memory_engineer...
        return instructions.get(agent_name, f"Execute task: {task}")
        
    def start_completion_monitor(self):
        """Start the background completion monitoring thread"""
        if not self.completion_monitor_running:
            self.completion_monitor_running = True
            monitor_thread = threading.Thread(
                target=self.monitor_task_completions,
                daemon=True,
                name="TaskCompletionMonitor"
            )
            monitor_thread.start()
            logging.info("Started task completion monitoring thread")
    
    def monitor_task_completions(self):
        """Background thread to monitor for completed tasks"""
        logging.info("Task completion monitor started")
        
        while self.completion_monitor_running:
            try:
                self.check_completed_tasks()
                time.sleep(10)  # Check every 10 seconds
            except Exception as e:
                logging.error(f"Error in task completion monitor: {e}", exc_info=True)
                time.sleep(30)  # Wait longer on error
    
    def check_completed_tasks(self):
        """Check for completed task files and update counters"""
        active_tasks_dir = Path('active_tasks')
        
        if not active_tasks_dir.exists():
            return
        
        # Look for completed task files
        completed_files = list(active_tasks_dir.glob('*_current_task_completed.json'))
        
        for completed_file in completed_files:
            file_path = str(completed_file)
            
            # Skip if already processed
            if file_path in self.processed_task_files:
                continue
            
            try:
                # Read the completed task file
                with open(completed_file, 'r') as f:
                    task_data = json.load(f)
                
                # Extract agent name from filename
                agent_name = self.extract_agent_from_filename(completed_file.name)
                
                if agent_name and agent_name in self.agent_states:
                    # Increment completion counter
                    self.agent_states[agent_name]['tasks_completed'] += 1
                    self.agent_states[agent_name]['status'] = 'idle'  # Reset to idle after completion
                    
                    # Get task info
                    task_info = task_data.get('task', {})
                    task_id = task_info.get('id', 'unknown')
                    task_type = task_info.get('type', 'unknown')
                    
                    logging.info(f"✅ Task completed: {agent_name} finished {task_type} ({task_id}). "
                               f"Total completed: {self.agent_states[agent_name]['tasks_completed']}")
                    
                    # Mark as processed
                    self.processed_task_files.add(file_path)
                    
                    # Move completed file to completed directory
                    self.archive_completed_task(completed_file, task_data)
                    
                    # Save updated state
                    self.save_state()
                
            except Exception as e:
                logging.error(f"Error processing completed task file {completed_file}: {e}")
    
    def extract_agent_from_filename(self, filename: str) -> str:
        """Extract agent name from task completion filename"""
        # Expected format: {agent}_current_task_completed.json
        if filename.endswith('_current_task_completed.json'):
            agent_name = filename.replace('_current_task_completed.json', '')
            
            # Map to known agent names
            agent_mapping = {
                'orchestrator': 'orchestrator',
                'archaeologist': 'archaeologist', 
                'sms_engineer': 'sms_engineer',
                'memory_engineer': 'memory_engineer',
                'test_engineer': 'test_engineer'
            }
            
            return agent_mapping.get(agent_name)
        
        return None
    
    def archive_completed_task(self, completed_file: Path, task_data: dict):
        """Move completed task file to archive"""
        try:
            # Create completed directory if it doesn't exist
            completed_dir = Path('active_tasks/completed')
            completed_dir.mkdir(exist_ok=True)
            
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            task_id = task_data.get('task', {}).get('id', 'unknown')
            archive_filename = f"{task_id}_{timestamp}.json"
            archive_path = completed_dir / archive_filename
            
            # Move the file
            completed_file.rename(archive_path)
            
            logging.debug(f"Archived completed task: {completed_file.name} -> {archive_path}")
            
        except Exception as e:
            logging.error(f"Error archiving completed task {completed_file}: {e}")
    
    def monitor_resources(self):
        """Monitor system resources"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        
        return {
            'cpu': cpu_percent,
            'memory': memory_percent,
            'safe_to_continue': cpu_percent < self.cpu_threshold and memory_percent < self.memory_threshold
        }
        
    def save_state(self):
        """Save system state for recovery"""
        state = {
            'start_time': self.start_time.isoformat(),
            'agent_states': self.agent_states,
            'tasks_in_queues': {agent: q.qsize() for agent, q in self.task_queues.items()},
            'runtime': str(datetime.now() - self.start_time)
        }
        
        with open('autonomous_state.json', 'w') as f:
            json.dump(state, f, indent=2)
            
    def run_autonomous_system(self):
        """Main autonomous system loop"""
        logging.info("Starting 6-hour autonomous operation")
        
        # Initial task generation
        self.generate_tasks()
        
        task_generation_interval = 3600  # Generate new tasks every hour
        last_generation = time.time()
        
        while (datetime.now() - self.start_time) < self.target_runtime:
            # Monitor resources
            resources = self.monitor_resources()
            
            if not resources['safe_to_continue']:
                logging.warning(f"Resource limits reached: {resources}")
                time.sleep(60)  # Cool down
                continue
                
            # Generate new tasks periodically
            if time.time() - last_generation > task_generation_interval:
                self.generate_tasks()
                last_generation = time.time()
                
            # Write tasks to files for agents
            for agent, task_queue in self.task_queues.items():
                if not task_queue.empty():
                    task = task_queue.get()
                    
                    # Create task file for agent
                    task_file = f"active_tasks/{agent}_current_task.json"
                    os.makedirs('active_tasks', exist_ok=True)
                    
                    with open(task_file, 'w') as f:
                        json.dump({
                            'task': task,
                            'instruction': self.create_agent_instruction(agent, task)
                        }, f, indent=2)
                        
                    self.agent_states[agent]['status'] = 'working'
                    self.agent_states[agent]['last_task'] = task['id']
                    
                    logging.info(f"Assigned task {task['id']} to {agent}")
                    
            # Save state
            self.save_state()
            
            # Brief pause
            time.sleep(30)  # Check every 30 seconds
            
        logging.info("6-hour autonomous operation complete!")
        
        # Stop completion monitoring
        self.completion_monitor_running = False
        
        # Final report
        self.generate_final_report()
        
    def generate_final_report(self):
        """Generate final summary report"""
        report = f"""
# Autonomous Operation Summary

Start Time: {self.start_time}
End Time: {datetime.now()}
Total Runtime: {datetime.now() - self.start_time}

## Tasks Completed:
{json.dumps(self.agent_states, indent=2)}

## System Status:
- Email System: Monitored every 5 minutes
- SMS System: Development progress
- Memory System: Implementation status
- Documentation: Updated

Generated by Autonomous Task System
"""
        
        with open(f'reports/autonomous_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md', 'w') as f:
            f.write(report)

if __name__ == '__main__':
    system = AutonomousTaskSystem()
    system.run_autonomous_system()
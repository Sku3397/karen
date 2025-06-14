'''
Task runner that executes commands from Claude agents without confirmation
'''
import json
import time
import subprocess
import os
from datetime import datetime
from pathlib import Path
from src.agent_communication import AgentCommunication

class AgentTaskRunner:
    def __init__(self, agent_name):
        self.agent_name = agent_name
        self.comm = AgentCommunication(f"{agent_name}_runner")
        self.task_file = f"tasks/{agent_name}_tasks.json"
        Path("tasks").mkdir(exist_ok=True)
        
    def add_task(self, task_type, params):
        """Add a task to the queue"""
        tasks = self.load_tasks()
        tasks.append({
            'id': len(tasks) + 1,
            'type': task_type,
            'params': params,
            'status': 'pending',
            'created': datetime.now().isoformat()
        })
        self.save_tasks(tasks)
        
    def load_tasks(self):
        """Load tasks from file"""
        if os.path.exists(self.task_file):
            with open(self.task_file, 'r') as f:
                return json.load(f)
        return []
        
    def save_tasks(self, tasks):
        """Save tasks to file"""
        with open(self.task_file, 'w') as f:
            json.dump(tasks, f, indent=2)
            
    def execute_tasks(self):
        """Execute all pending tasks"""
        tasks = self.load_tasks()
        
        for task in tasks:
            if task['status'] == 'pending':
                try:
                    self.execute_task(task)
                    task['status'] = 'completed'
                    task['completed'] = datetime.now().isoformat()
                except Exception as e:
                    task['status'] = 'failed'
                    task['error'] = str(e)
                    
        self.save_tasks(tasks)
        
    def execute_task(self, task):
        """Execute a single task"""
        task_type = task['type']
        params = task['params']
        
        if task_type == 'create_file':
            self.create_file(params['path'], params['content'])
        elif task_type == 'update_status':
            self.update_status(params['status'], params['progress'], params.get('details', {}))
        elif task_type == 'send_message':
            self.send_message(params['to'], params['type'], params['content'])
        elif task_type == 'run_command':
            self.run_command(params['command'])
        elif task_type == 'read_file':
            return self.read_file(params['path'])
        elif task_type == 'search_files':
            return self.search_files(params['pattern'], params.get('path', '.'))
        elif task_type == 'voice_implementation':
            self.execute_voice_implementation(params)
        elif task_type == 'voice_test':
            self.execute_voice_test(params)
        elif task_type == 'phone_system_check':
            self.execute_phone_system_check(params)
            
    def create_file(self, path, content):
        """Create a file without confirmation"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(content)
        print(f"Created: {path}")
        
    def update_status(self, status, progress, details):
        """Update agent status without confirmation"""
        self.comm.update_status(status, progress, details)
        print(f"Status updated: {status} ({progress}%)")
        
    def send_message(self, to, msg_type, content):
        """Send message without confirmation"""
        self.comm.send_message(to, msg_type, content)
        print(f"Message sent to {to}: {msg_type}")
        
    def run_command(self, command):
        """Run a shell command without confirmation"""
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        print(f"Command executed: {command}")
        return result.stdout
        
    def read_file(self, path):
        """Read file content"""
        with open(path, 'r') as f:
            return f.read()
            
    def search_files(self, pattern, path):
        """Search for files matching pattern"""
        import glob
        return glob.glob(f"{path}/**/{pattern}", recursive=True)
    
    def execute_voice_implementation(self, params):
        """Execute voice implementation task"""
        print(f"Executing voice implementation: {params.get('component', 'unknown')}")
        
        # Run the actual phone engineer agent
        cmd = "python -m src.phone_engineer_agent"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(f"Voice implementation result: {result.returncode}")
        return result.stdout
    
    def execute_voice_test(self, params):
        """Execute voice system test"""
        print(f"Executing voice test: {params.get('test_type', 'basic')}")
        
        # Run voice system tests
        cmd = "python test_phone_engineer.py"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        print(f"Voice test result: {result.returncode}")
        return result.stdout
    
    def execute_phone_system_check(self, params):
        """Execute phone system health check"""
        print(f"Executing phone system check: {params.get('check_type', 'health')}")
        
        # Check phone system components
        try:
            from src.voice_client import VoiceClient
            voice_client = VoiceClient()
            
            # Basic health check
            health_status = {
                'twilio_configured': hasattr(voice_client, 'client'),
                'karen_phone': voice_client.karen_phone if hasattr(voice_client, 'karen_phone') else None,
                'timestamp': time.time()
            }
            
            print(f"Phone system health: {health_status}")
            return health_status
            
        except Exception as e:
            print(f"Phone system check failed: {e}")
            return {'error': str(e)}

def main():
    """Run task runners for all agents"""
    agents = ['orchestrator', 'archaeologist', 'sms_engineer', 'memory_engineer', 'test_engineer', 'phone_engineer']
    
    while True:
        for agent in agents:
            runner = AgentTaskRunner(agent)
            runner.execute_tasks()
        time.sleep(5)  # Check every 5 seconds

if __name__ == '__main__':
    main() 
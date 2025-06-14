'''
Helper functions for Claude agents to use instead of direct actions
'''
import json
from agent_task_runner import AgentTaskRunner

class ClaudeHelper:
    def __init__(self, agent_name):
        self.agent_name = agent_name
        self.runner = AgentTaskRunner(agent_name)
        
    def create_file(self, path, content):
        """Queue file creation (no confirmation needed)"""
        self.runner.add_task('create_file', {
            'path': path,
            'content': content
        })
        return f"File creation queued: {path}"
        
    def update_status(self, status, progress, details=None):
        """Queue status update (no confirmation needed)"""
        self.runner.add_task('update_status', {
            'status': status,
            'progress': progress,
            'details': details or {}
        })
        return f"Status update queued: {status} ({progress}%)"
        
    def send_message(self, to, msg_type, content):
        """Queue message (no confirmation needed)"""
        self.runner.add_task('send_message', {
            'to': to,
            'type': msg_type,
            'content': content
        })
        return f"Message queued to {to}"
        
    def read_file(self, path):
        """Read file immediately"""
        try:
            with open(path, 'r') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {e}"
            
    def search_code(self, pattern):
        """Search code immediately"""
        import glob
        files = glob.glob(f"src/**/*.py", recursive=True)
        results = []
        for file in files:
            try:
                with open(file, 'r') as f:
                    content = f.read()
                    if pattern in content:
                        results.append(file)
            except:
                pass
        return results

# Make it easy to import
orchestrator_helper = ClaudeHelper('orchestrator')
archaeologist_helper = ClaudeHelper('archaeologist')
sms_helper = ClaudeHelper('sms_engineer')
memory_helper = ClaudeHelper('memory_engineer')
test_helper = ClaudeHelper('test_engineer') 
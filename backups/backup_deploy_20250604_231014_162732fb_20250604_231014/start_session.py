#!/usr/bin/env python3
"""
Start Session Script - Initializes the multi-agent development environment
Based on advanced multi-agent coordination patterns
"""
import json
import subprocess
import time
import os
import sys
from datetime import datetime
from pathlib import Path
import uuid
import re

# --- Configuration ---
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__))) # Should resolve to /c%3A/Users/Man/ultra/projects/karen
SESSION_ID = str(uuid.uuid4())
# RTH_SCRIPT_NAME = "robust_terminal_handler.py" # Removed as per user instruction
# CENTRAL_RTH_PATH = r"C:\\Users\\Man\\CursorAgentUtils\\robust_terminal_handler.py" # Removed as per user instruction

# --- Derived Paths ---
AUTONOMOUS_AGENTS_DIR = os.path.join(WORKSPACE_ROOT, "autonomous-agents")
SHARED_KNOWLEDGE_DIR = os.path.join(AUTONOMOUS_AGENTS_DIR, "shared-knowledge")
DAEMONS_DIR = os.path.join(AUTONOMOUS_AGENTS_DIR, "daemons")
LOGS_DIR = os.path.join(WORKSPACE_ROOT, "logs")
TEST_DAEMON_LOG_DIR = os.path.join(LOGS_DIR, "test_daemon")
CELERY_DAEMON_LOG_DIR = os.path.join(LOGS_DIR, "celery_daemon")
DAEMON_OUTPUT_DIR = os.path.join(LOGS_DIR, "daemon_output")
AGENT_OUTPUT_DIR = os.path.join(LOGS_DIR, "agent_out")

# --- File Paths ---
FILE_LOCKS_JSON_PATH = os.path.join(AUTONOMOUS_AGENTS_DIR, "file_locks.json")
FILE_LOCK_MANAGER_PATH = os.path.join(SHARED_KNOWLEDGE_DIR, "file_lock_manager.py")
INTELLIGENT_TODOS_JSON_PATH = os.path.join(SHARED_KNOWLEDGE_DIR, "intelligent_todos.json")
TODO_MANAGER_PATH = os.path.join(SHARED_KNOWLEDGE_DIR, "todo_manager.py")
NETWORK_STATUS_JSON_PATH = os.path.join(SHARED_KNOWLEDGE_DIR, "network_status.json")
PROJECT_OVERVIEW_MD_PATH = os.path.join(SHARED_KNOWLEDGE_DIR, "PROJECT_OVERVIEW.md")
AGENT_PROTOCOL_MD_PATH = os.path.join(SHARED_KNOWLEDGE_DIR, "AGENT_PROTOCOL.md")
TOOLS_AND_HELPERS_MD_PATH = os.path.join(SHARED_KNOWLEDGE_DIR, "TOOLS_AND_HELPERS.md")
MCP_BRIDGE_PATH = os.path.join(SHARED_KNOWLEDGE_DIR, "mcp_bridge.py")
LAUNCH_AGENTS_PY_PATH = os.path.join(WORKSPACE_ROOT, "launch_agents.py")

# --- Daemon Script Paths ---
TEST_DAEMON_PY_PATH = os.path.join(DAEMONS_DIR, "test_daemon.py")
CELERY_DAEMON_PY_PATH = os.path.join(DAEMONS_DIR, "celery_daemon.py")

# --- Placeholder Test/App File Paths ---
DUMMY_TEST_EMAIL_BASELINE_PATH = os.path.join(WORKSPACE_ROOT, "tests", "test_email_baseline.py")
DUMMY_TEST_SMS_INTEGRATION_PATH = os.path.join(WORKSPACE_ROOT, "tests", "test_sms_integration.py")
DUMMY_CELERY_APP_PATH = os.path.join(WORKSPACE_ROOT, "src", "celery_app.py")

# Corrected: Removed block of incorrectly placed global variables and function definition here.

def get_project_python_interpreter():
    """Detects and returns the path to the project's Python interpreter for start_session.py context."""
    # Prioritize .venv
    venv_python = os.path.join(WORKSPACE_ROOT, ".venv", "Scripts", "python.exe")
    if os.path.exists(venv_python):
        return venv_python
    # Fallback to venv
    venv_python_alt = os.path.join(WORKSPACE_ROOT, "venv", "Scripts", "python.exe")
    if os.path.exists(venv_python_alt):
        return venv_python_alt
    # Fallback to system python
    return sys.executable

PROJECT_PYTHON_INTERPRETER = get_project_python_interpreter()

def create_directories():
    """Creates the necessary directory structure for the session."""
    print("Creating directory structure...")
    os.makedirs(AUTONOMOUS_AGENTS_DIR, exist_ok=True)
    os.makedirs(SHARED_KNOWLEDGE_DIR, exist_ok=True)
    os.makedirs(DAEMONS_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)
    os.makedirs(TEST_DAEMON_LOG_DIR, exist_ok=True)
    os.makedirs(CELERY_DAEMON_LOG_DIR, exist_ok=True)
    os.makedirs(DAEMON_OUTPUT_DIR, exist_ok=True)
    os.makedirs(AGENT_OUTPUT_DIR, exist_ok=True)
    # Ensure parent dirs for placeholder files exist
    os.makedirs(os.path.dirname(DUMMY_TEST_EMAIL_BASELINE_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(DUMMY_TEST_SMS_INTEGRATION_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(DUMMY_CELERY_APP_PATH), exist_ok=True)
    print("Directory structure created.")

def initialize_file_locks():
    """Initializes the file_locks.json file."""
    print(f"Initializing file locks at {FILE_LOCKS_JSON_PATH}...")
    if not os.path.exists(FILE_LOCKS_JSON_PATH):
        with open(FILE_LOCKS_JSON_PATH, 'w') as f:
            json.dump({}, f, indent=4)
        print(f"{FILE_LOCKS_JSON_PATH} created.")
    else:
        print(f"{FILE_LOCKS_JSON_PATH} already exists.")

def generate_file_lock_manager():
    """Generates the file_lock_manager.py script."""
    print(f"Generating file lock manager at {FILE_LOCK_MANAGER_PATH}...")
    
    escaped_locks_file_path_for_script = repr(FILE_LOCKS_JSON_PATH)

    script_content = f'''
import json
import os
from filelock import FileLock, Timeout
from datetime import datetime

LOCKS_FILE = {escaped_locks_file_path_for_script}
METADATA_LOCK_FILE = LOCKS_FILE + '.lock'

class FileLockManager:
    def __init__(self, locks_file_path={escaped_locks_file_path_for_script}, lock_timeout=10):
        self.locks_file_path = locks_file_path
        self.metadata_lock = FileLock(self.locks_file_path + '.lock', timeout=lock_timeout)
        self._ensure_locks_file()

    def _ensure_locks_file(self):
        if not os.path.exists(self.locks_file_path):
            with self.metadata_lock:
                if not os.path.exists(self.locks_file_path): # Double check after acquiring lock
                    with open(self.locks_file_path, 'w') as f:
                        json.dump(dict(), f, indent=4)

    def _read_locks(self):
        try:
            with open(self.locks_file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return dict()

    def _write_locks(self, locks_data):
        with open(self.locks_file_path, 'w') as f:
            json.dump(locks_data, f, indent=4)

    def acquire_lock(self, file_path, agent_id, task_id, expires_in_seconds=3600):
        """Attempts to acquire a lock for a specific file."""
        absolute_file_path = os.path.abspath(file_path)
        with self.metadata_lock:
            locks = self._read_locks()
            current_time = datetime.utcnow().timestamp()

            if absolute_file_path in locks:
                lock_info = locks[absolute_file_path]
                if current_time < lock_info.get('expires_at', 0):
                    if lock_info['agent_id'] == agent_id and lock_info['task_id'] == task_id:
                        lock_info['expires_at'] = current_time + expires_in_seconds
                        lock_info['timestamp'] = datetime.utcnow().isoformat()
                        self._write_locks(locks)
                        return True, f"Lock for {{absolute_file_path}} refreshed by agent {{agent_id}} for task {{task_id}}."
                    return False, f"File {{absolute_file_path}} is already locked by agent {{lock_info['agent_id']}} for task {{lock_info['task_id']}}. Lock expires at {{datetime.fromtimestamp(lock_info['expires_at']).isoformat()}}."
                else:
                    pass # Expired lock, can be acquired
            
            locks[absolute_file_path] = {{
                'agent_id': agent_id,
                'task_id': task_id,
                'timestamp': datetime.utcnow().isoformat(),
                'expires_at': current_time + expires_in_seconds,
                'file_path': absolute_file_path
            }}
            self._write_locks(locks)
            return True, f"Lock acquired for {{absolute_file_path}} by agent {{agent_id}} for task {{task_id}}."

    def release_lock(self, file_path, agent_id, task_id):
        """Releases a lock for a specific file if held by the agent and task."""
        absolute_file_path = os.path.abspath(file_path)
        with self.metadata_lock:
            locks = self._read_locks()
            if absolute_file_path in locks:
                lock_info = locks[absolute_file_path]
                current_time = datetime.utcnow().timestamp()
                if current_time >= lock_info.get('expires_at', 0):
                    del locks[absolute_file_path]
                    self._write_locks(locks)
                    return True, f"Lock for {{absolute_file_path}} had already expired. Removed."

                if lock_info['agent_id'] == agent_id and lock_info['task_id'] == task_id:
                    del locks[absolute_file_path]
                    self._write_locks(locks)
                    return True, f"Lock for {{absolute_file_path}} released by agent {{agent_id}} for task {{task_id}}."
                else:
                    return False, f"Cannot release lock for {{absolute_file_path}}. Not held by agent {{agent_id}} for task {{task_id}} or lock expired. Current holder: {{lock_info.get('agent_id')}}."
            return True, f"No active lock found for {{absolute_file_path}} to release."

    def get_all_locked_files(self):
        """Returns a dictionary of all currently active locked files."""
        with self.metadata_lock:
            locks = self._read_locks()
            active_locks = dict()
            current_time = datetime.utcnow().timestamp()
            for file_path, lock_info in list(locks.items()):
                if current_time < lock_info.get('expires_at', 0):
                    active_locks[file_path] = lock_info
                else:
                    del locks[file_path]
            if len(active_locks) < len(locks):
                self._write_locks(locks)
            return active_locks

    def get_lock_status(self, file_path):
        """Returns the lock status for a specific file, or None if not locked or expired."""
        absolute_file_path = os.path.abspath(file_path)
        with self.metadata_lock:
            locks = self._read_locks()
            if absolute_file_path in locks:
                lock_info = locks[absolute_file_path]
                current_time = datetime.utcnow().timestamp()
                if current_time < lock_info.get('expires_at', 0):
                    return lock_info
                else:
                    del locks[absolute_file_path]
                    self._write_locks(locks)
                    return None
            return None

if __name__ == '__main__':
    current_script_dir = os.path.dirname(__file__)
    project_root_for_test = os.path.abspath(os.path.join(current_script_dir, '..', '..'))
    locks_json_path_for_test = os.path.join(project_root_for_test, 'autonomous-agents', 'file_locks.json')
    os.makedirs(os.path.dirname(locks_json_path_for_test), exist_ok=True)

    manager = FileLockManager(locks_file_path=locks_json_path_for_test)
    agent1 = "agent_alpha_tester"
    agent2 = "agent_beta_tester"
    task1 = "task_test_001"
    task2 = "task_test_002"
    
    dummy_file1_path = os.path.join(project_root_for_test, 'dummy_file1_test_lock.txt')
    dummy_file2_path = os.path.join(project_root_for_test, 'dummy_file2_test_lock.txt')

    os.makedirs(os.path.dirname(dummy_file1_path), exist_ok=True)
    if not os.path.exists(dummy_file1_path): open(dummy_file1_path, 'a').close()
    os.makedirs(os.path.dirname(dummy_file2_path), exist_ok=True)
    if not os.path.exists(dummy_file2_path): open(dummy_file2_path, 'a').close()

    print(f"--- Testing File Lock Manager from {{__file__}} ---")
    print(f"Using locks file: {{manager.locks_file_path}}")

    success, message = manager.acquire_lock(dummy_file1_path, agent1, task1, expires_in_seconds=5)
    print(f"Acquire {{dummy_file1_path}} by {{agent1}} for {{task1}}: {{success}} - {{message}}")
    success, message = manager.acquire_lock(dummy_file1_path, agent2, task2)
    print(f"Acquire {{dummy_file1_path}} by {{agent2}} for {{task2}}: {{success}} - {{message}}")
    success, message = manager.acquire_lock(dummy_file2_path, agent1, task1)
    print(f"Acquire {{dummy_file2_path}} by {{agent1}} for {{task1}}: {{success}} - {{message}}")
    
    print(f"All locked files initially: {{json.dumps(manager.get_all_locked_files(), indent=2)}}")
    print(f"Status of {{dummy_file1_path}}: {{manager.get_lock_status(dummy_file1_path)}}")
    
    success, message = manager.release_lock(dummy_file1_path, agent1, "fake_task_id_test")
    print(f"Release {{dummy_file1_path}} by {{agent1}} (using fake_task_id_test): {{success}} - {{message}}")
    success, message = manager.release_lock(dummy_file1_path, agent1, task1)
    print(f"Release {{dummy_file1_path}} by {{agent1}} for {{task1}}: {{success}} - {{message}}")
    
    print("Waiting for lock on file1 to potentially expire (set for 5s)...")
    import time
    time.sleep(5.1)
    
    success, message = manager.acquire_lock(dummy_file1_path, agent2, task2)
    print(f"Acquire {{dummy_file1_path}} by {{agent2}} for {{task2}} (after wait): {{success}} - {{message}}")
    print(f"All locked files after re-acquisition attempt: {{json.dumps(manager.get_all_locked_files(), indent=2)}}")
    
    if manager.get_lock_status(dummy_file1_path):
        success, message = manager.release_lock(dummy_file1_path, agent2, task2)
        print(f"Release {{dummy_file1_path}} by {{agent2}} for {{task2}} (cleanup): {{success}} - {{message}}")
    if manager.get_lock_status(dummy_file2_path):
        success, message = manager.release_lock(dummy_file2_path, agent1, task1)
        print(f"Release {{dummy_file2_path}} by {{agent1}} for {{task1}} (cleanup): {{success}} - {{message}}")
        
    print(f"All locked files after cleanup: {{json.dumps(manager.get_all_locked_files(), indent=2)}}")
    print("--- Test Complete ---")

'''
    with open(FILE_LOCK_MANAGER_PATH, 'w') as f:
        f.write(script_content)
    print(f"{FILE_LOCK_MANAGER_PATH} generated.")

# def main():
#     """Main function to set up the multi-agent session."""
#     print(f"Starting session {SESSION_ID} in workspace: {WORKSPACE_ROOT}")
#     
#     create_directories()
#     initialize_file_locks()
#     generate_file_lock_manager()
# 
#     # Future function calls will be added here:    
#     # initialize_intelligent_todos()
#     # generate_todo_manager()
#     # create_placeholder_files_for_daemons()
#     # generate_test_daemon_script()
#     # generate_celery_daemon_script()
#     # launch_background_daemons()
#     # generate_context_markdown_files()
#     # generate_mcp_bridge_script()
#     # initialize_network_status_and_agent_launcher()
# 
#     print("\\n--- Session Setup Partially Complete (File Lock System Ready) ---")
#     print(f"Session ID: {SESSION_ID}")
#     print(f"Shared Knowledge Dir: {SHARED_KNOWLEDGE_DIR}")
#     print(f"Logs Dir: {LOGS_DIR}")
#     print(f"Next steps involve setting up TODOs, Daemons, Context Files, MCP Bridge, and Agent Launcher.")
#     # print(f"To launch agents (once generated), run: python {LAUNCH_AGENTS_PY_PATH}")

if __name__ == "__main__":
    # main() # Call the old main function
    session_starter = KarenStartSession()
    session_starter.start()

class KarenStartSession:
    def __init__(self):
        self.project_root = Path.cwd().resolve()
        self.session_id = f"session_{int(time.time())}"
        self.autonomous_agents_dir = self.project_root / "autonomous-agents"
        self.context_dir = self.autonomous_agents_dir / "shared-knowledge"
        self.daemons_dir = self.autonomous_agents_dir / "daemons"
        self.logs_dir = self.project_root / "logs"
        
        self.context_dir.mkdir(parents=True, exist_ok=True)
        self.daemons_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
    def start(self):
        """Initialize the complete multi-agent session"""
        print(f"🚀 Starting Karen Multi-Agent Session: {self.session_id}")
        print(f"   Project Root: {self.project_root}")
        print("=" * 70)
        
        self.init_file_locking()
        self.create_intelligent_todos()
        self._ensure_dummy_files_for_daemons() # Create placeholders before daemons start
        self.start_daemons()
        self.init_eigencode_integration()
        self.generate_context_files()
        self.init_mcp_bridge()
        self.create_agent_launcher_and_status_file()
        
        print("\n✅ Session initialized successfully!")
        print(f"📁 Context directory: {self.context_dir.resolve()}")
        print(f"🔄 Daemons launched (check logs in {self.logs_dir / 'daemon_output'})")
        print(f"🤖 Ready for multi-agent development via launch_agents.py")
        print("=" * 70)
        self.print_next_steps()
        
    def _write_script(self, path: Path, content: str, make_executable: bool = False):
        path.write_text(content)
        if make_executable and os.name != 'nt':
            path.chmod(0o755)
        print(f"   Script created: {path.relative_to(self.project_root)}")

    def init_file_locking(self):
        print("🔒 Initializing file locking system...")
        lock_file_json_path = self.autonomous_agents_dir / "file_locks.json"
        if not lock_file_json_path.exists():
            lock_file_json_path.write_text(json.dumps({
                "locks": {}, "session_id": self.session_id, "created": datetime.now().isoformat()
            }, indent=2))
        
        script_content = '''
import json
import time
from datetime import datetime
from pathlib import Path
import filelock # pip install filelock

class FileLockManager:
    def __init__(self):
        # This script (file_lock_manager.py) is in autonomous-agents/shared-knowledge/
        # file_locks.json is in autonomous-agents/
        self.lock_file_json_path = Path(__file__).resolve().parent.parent / "file_locks.json"
        self.system_lock_path = self.lock_file_json_path.with_suffix(self.lock_file_json_path.suffix + ".lock")

    def _get_locks_data(self):
        try:
            return json.loads(self.lock_file_json_path.read_text(encoding='utf-8'))
        except (FileNotFoundError, json.JSONDecodeError): # Handle case where file might be temporarily missing or malformed
            return {"locks": {}, "session_id": "unknown_or_corrupt_lock_file"}

    def _save_locks_data(self, data):
        self.lock_file_json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    def acquire_lock(self, agent_name: str, file_path_project_relative: str, timeout: int = 300) -> tuple[bool, str]:
        file_path_key = str(Path(file_path_project_relative).as_posix()) # Normalize path for key
        with filelock.FileLock(str(self.system_lock_path)): # Lock the .lock file for atomicity
            locks_data = self._get_locks_data()
            current_locks = locks_data.get("locks", {})
            
            if file_path_key in current_locks:
                lock_info = current_locks[file_path_key]
                try:
                    lock_time = datetime.fromisoformat(lock_info["locked_at"])
                    if (datetime.now() - lock_time).total_seconds() < timeout:
                        return False, f"File '{file_path_key}' locked by {lock_info['agent']} at {lock_info['locked_at']}"
                except (ValueError, TypeError): 
                    pass # Stale/invalid lock, allow override
            
            current_locks[file_path_key] = {"agent": agent_name, "locked_at": datetime.now().isoformat()}
            locks_data["locks"] = current_locks
            self._save_locks_data(locks_data)
            return True, f"Lock acquired for '{file_path_key}'"

    def release_lock(self, agent_name: str, file_path_project_relative: str) -> bool:
        file_path_key = str(Path(file_path_project_relative).as_posix())
        with filelock.FileLock(str(self.system_lock_path)):
            locks_data = self._get_locks_data()
            current_locks = locks_data.get("locks", {})
            if file_path_key in current_locks and current_locks[file_path_key]["agent"] == agent_name:
                del current_locks[file_path_key]
                locks_data["locks"] = current_locks
                self._save_locks_data(locks_data)
                return True
            return False

    def get_all_locked_files(self) -> dict:
        with filelock.FileLock(str(self.system_lock_path)): # Read consistency
            return self._get_locks_data().get("locks", {})

# Global instance for agents to import
lock_manager = FileLockManager()
'''
        self._write_script(self.context_dir / "file_lock_manager.py", script_content)

    def create_intelligent_todos(self):
        print("📝 Creating intelligent TODO system...")
        todos_path = self.context_dir / "intelligent_todos.json"
        if not todos_path.exists():
            initial_todos = {"high_priority": [], "medium_priority": [], "low_priority": [], "claimed": {}, "completed": []}
            # Add some predefined dev tasks for demonstration
            dev_tasks = [
                {"id": "dev_hp_1", "task": "Implement core SMS sending feature", "agent_type_suggestion": "sms_engineer", "files_implicated": ["src/sms_service.py"], "description": "Basic SMS sending via Twilio."},
                {"id": "dev_mp_1", "task": "Setup basic project logging", "agent_type_suggestion": "orchestrator", "files_implicated": ["src/config.py", "src/main.py"], "description": "Configure logging for all modules."}
            ]
            initial_todos["high_priority"].append(dev_tasks[0])
            initial_todos["medium_priority"].append(dev_tasks[1])
            todos_path.write_text(json.dumps(initial_todos, indent=2))

        script_content = '''
import json
from pathlib import Path
from datetime import datetime
import filelock # pip install filelock

class TodoManager:
    def __init__(self):
        # This script (todo_manager.py) is in autonomous-agents/shared-knowledge/
        self.todo_file_path = Path(__file__).resolve().parent / "intelligent_todos.json"
        self.lock_path = self.todo_file_path.with_suffix(self.todo_file_path.suffix + ".lock")

    def _read_todos(self):
        try:
            return json.loads(self.todo_file_path.read_text(encoding='utf-8'))
        except (FileNotFoundError, json.JSONDecodeError):
            return {"high_priority": [], "medium_priority": [], "low_priority": [], "claimed": {}, "completed": []}

    def _write_todos(self, todos_data):
        self.todo_file_path.write_text(json.dumps(todos_data, indent=2, ensure_ascii=False))

    def claim_task(self, agent_name: str, task_id: str = None, preferred_priority: str = "high") -> dict | None:
        with filelock.FileLock(str(self.lock_path)):
            todos = self._read_todos()
            task_to_claim, original_list_key = None, None

            priority_order = [f"{preferred_priority}_priority"] + \
                             [f"{p}_priority" for p in ["high", "medium", "low"] if p != preferred_priority]

            if task_id: # Try to claim a specific task
                for p_key in priority_order: # Check all lists for the ID
                    current_list = todos.get(p_key, [])
                    for i, task_in_list in enumerate(current_list):
                        if task_in_list["id"] == task_id and task_id not in todos.get("claimed", {}):
                            task_to_claim, original_list_key = current_list.pop(i), p_key
                            break
                    if task_to_claim: break
            else: # Claim by priority
                for p_key in priority_order:
                    current_list = todos.get(p_key, [])
                    available = [t for t in current_list if t["id"] not in todos.get("claimed", {})]
                    if available:
                        task_to_claim = available[0]
                        # Remove claimed task from its list
                        todos[p_key] = [t for t in current_list if t["id"] != task_to_claim["id"]]
                        original_list_key = p_key
                        break
            
            if task_to_claim:
                claimed_map = todos.get("claimed", {})
                claimed_map[task_to_claim["id"]] = {
                    "agent": agent_name, "claimed_at": datetime.now().isoformat(),
                    "task_details": task_to_claim, "original_priority_key": original_list_key
                }
                todos["claimed"] = claimed_map
                self._write_todos(todos)
            return task_to_claim

    def release_task(self, agent_name: str, task_id: str) -> bool:
        with filelock.FileLock(str(self.lock_path)):
            todos = self._read_todos()
            claimed_map = todos.get("claimed", {})
            if task_id in claimed_map and claimed_map[task_id]["agent"] == agent_name:
                task_info = claimed_map.pop(task_id)
                original_task = task_info["task_details"]
                # Put back into its original priority list, or default
                priority_key = task_info.get("original_priority_key", "medium_priority") 
                if priority_key not in todos or not isinstance(todos[priority_key], list): 
                    todos[priority_key] = []
                todos[priority_key].insert(0, original_task) # Add to the front
                todos["claimed"] = claimed_map
                self._write_todos(todos)
                return True
            return False

    def complete_task(self, agent_name: str, task_id: str) -> bool:
        with filelock.FileLock(str(self.lock_path)):
            todos = self._read_todos()
            claimed_map = todos.get("claimed", {})
            if task_id in claimed_map and claimed_map[task_id]["agent"] == agent_name:
                task_info = claimed_map.pop(task_id)
                task_info["completed_at"] = datetime.now().isoformat()
                if "completed" not in todos or not isinstance(todos["completed"], list): 
                    todos["completed"] = []
                todos["completed"].append(task_info)
                todos["claimed"] = claimed_map
                self._write_todos(todos)
                return True
            return False

    def get_status_summary(self) -> dict:
        with filelock.FileLock(str(self.lock_path)): 
            todos = self._read_todos()
            summary = {}
            for p_key_suffix in ["high_priority", "medium_priority", "low_priority"]:
                summary[f"{p_key_suffix}_available"] = len([
                    t for t in todos.get(p_key_suffix, []) if t["id"] not in todos.get("claimed", {})
                ])
            summary["total_claimed"] = len(todos.get("claimed", {}))
            summary["total_completed"] = len(todos.get("completed", []))
            return summary

# Global instance for agents to import
todo_manager = TodoManager()
'''
        self._write_script(self.context_dir / "todo_manager.py", script_content)

    def _ensure_dummy_files_for_daemons(self):
        print("   Ensuring dummy files for daemons exist...")
        # Dummy test files
        test_files_dir = self.project_root / "tests"
        test_files_dir.mkdir(parents=True, exist_ok=True)
        dummy_test_content = "import pytest\n\ndef test_placeholder():\n    assert True\n"
        if not (test_files_dir / "test_email_baseline.py").exists():
            (test_files_dir / "test_email_baseline.py").write_text(dummy_test_content)
        if not (test_files_dir / "test_sms_integration.py").exists():
            (test_files_dir / "test_sms_integration.py").write_text(dummy_test_content)
        
        # Dummy Celery app
        src_dir = self.project_root / "src"
        src_dir.mkdir(parents=True, exist_ok=True)
        dummy_celery_content = ("from celery import Celery\n"
                                "redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')\n"
                                "app = Celery('karen_celery_app', broker=redis_url, backend=redis_url)\n"
                                "app.conf.update(task_serializer='json', accept_content=['json'], result_serializer='json')\n"
                                "@app.task\ndef dummy_task(x, y): return x + y\n")
        if not (src_dir / "celery_app.py").exists():
            (src_dir / "celery_app.py").write_text(f"import os\n{dummy_celery_content}")

    def start_daemons(self):
        print("🔄 Starting background daemons...")
        python_exe = sys.executable # Use the same python interpreter
        daemon_output_base = self.logs_dir / "daemon_output"
        daemon_output_base.mkdir(parents=True, exist_ok=True)

        # Test Daemon Script Content
        # Note: f-string escaping {{ and }} for literal braces in the generated script.
        test_daemon_script = f"""#!{python_exe}
# Test Daemon: Runs tests periodically
import time, subprocess, json, sys
from datetime import datetime
from pathlib import Path

# This script (test_daemon.py) is in autonomous-agents/daemons/
# PROJECT_ROOT is three levels up.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent 
LOG_DIR = PROJECT_ROOT / "logs" / "test_daemon"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Test files are relative to PROJECT_ROOT
TEST_FILES_TO_RUN = [
    "tests/test_email_baseline.py",
    "tests/test_sms_integration.py",
]

def run_tests():
    results = {{"timestamp": datetime.now().isoformat(), "test_outcomes": {{}} }}
    print(f"[TestDaemon {{datetime.now().strftime('%H:%M:%S')}}] Running tests...")
    for test_file_rel_path in TEST_FILES_TO_RUN:
        test_file_abs_path = PROJECT_ROOT / test_file_rel_path
        category_name = Path(test_file_rel_path).stem
        
        if not test_file_abs_path.exists():
            results["test_outcomes"][category_name] = {{"status": "file_not_found", "error": f"Test file {{test_file_abs_path}} not found."}}
            print(f"  - {{category_name}}: File not found")
            continue
        try:
            # Use sys.executable to ensure the correct python interpreter
            cmd = [sys.executable, "-m", "pytest", str(test_file_abs_path), "-v", "--tb=short"]
            process = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT, timeout=120)
            # Pytest exit code 0 for success, 1 for tests failed, 5 for no tests ran
            passed = process.returncode == 0 or (process.returncode == 5 and "no tests collected" in process.stdout)
            
            outcome = {{"status": "passed" if passed else "failed", 
                       "return_code": process.returncode, 
                       "output_snippet": process.stdout[-500:] + "\nSTDERR:\n" + process.stderr[-500:]}}
            results["test_outcomes"][category_name] = outcome
            print(f"  - {{category_name}}: {{outcome['status']}} (code: {{outcome['return_code']}})")

        except subprocess.TimeoutExpired:
            results["test_outcomes"][category_name] = {{"status": "timeout"}}
            print(f"  - {{category_name}}: Timeout")
        except Exception as e:
            results["test_outcomes"][category_name] = {{"status": "error", "details": str(e)}}
            print(f"  - {{category_name}}: Error - {{str(e)}}")
    
    report_path = LOG_DIR / "latest_test_results.json"
    report_path.write_text(json.dumps(results, indent=2))
    print(f"[TestDaemon {{datetime.now().strftime('%H:%M:%S')}}] Test run complete. Report: {{report_path}}")

if __name__ == "__main__":
    print(f"[TestDaemon {{datetime.now().strftime('%H:%M:%S')}}] Starting up. Project root: {{PROJECT_ROOT}}, Log dir: {{LOG_DIR}}")
    while True:
        run_tests()
        time.sleep(300) # 5 minutes
"""
        self._write_script(self.daemons_dir / "test_daemon.py", test_daemon_script, make_executable=True)

        # Celery Monitor Daemon Script Content
        celery_daemon_script = f"""#!{python_exe}
# Celery Monitor Daemon
import time, subprocess, json, sys, os
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LOG_DIR = PROJECT_ROOT / "logs" / "celery_daemon"
LOG_DIR.mkdir(parents=True, exist_ok=True)
# Assumes celery_app.py is in src/ relative to PROJECT_ROOT
CELERY_APP_MODULE = "src.celery_app" 

def get_celery_status():
    status = {{"timestamp": datetime.now().isoformat(), "services": {{}} }}
    current_env = {{**os.environ.copy()}}
    # Ensure src and project_root are in PYTHONPATH for Celery discovery
    python_path_parts = [str(PROJECT_ROOT / "src"), str(PROJECT_ROOT)]
    if "PYTHONPATH" in current_env:
        python_path_parts.append(current_env["PYTHONPATH"])
    current_env["PYTHONPATH"] = os.pathsep.join(python_path_parts)

    # Worker status
    try:
        # Use sys.executable for consistency
        worker_cmd = [sys.executable, "-m", "celery", "-A", CELERY_APP_MODULE, "inspect", "active"]
        proc = subprocess.run(worker_cmd, capture_output=True, text=True, cwd=PROJECT_ROOT, timeout=30, env=current_env)
        if proc.returncode == 0 and "->" in proc.stdout: # "->" indicates active workers
            status["services"]["celery_worker"] = {{"status": "running", "details": proc.stdout.strip()}}
        else:
            status["services"]["celery_worker"] = {{"status": "stopped_or_error", "code": proc.returncode, "details": (proc.stderr or proc.stdout).strip()}}
    except subprocess.TimeoutExpired:
        status["services"]["celery_worker"] = {{"status": "timeout", "details": "Celery inspect command timed out."}}
    except Exception as e: 
        status["services"]["celery_worker"] = {{"status": "error", "details": str(e)}}
    
    # Beat status (PID file)
    beat_pid_path = PROJECT_ROOT / "celerybeat.pid" # Standard location
    status["services"]["celery_beat"] = {{"status": "running" if beat_pid_path.exists() else "stopped", "pid_file_checked": str(beat_pid_path)}}
    
    # Redis status
    try:
        import redis # pip install redis
        # Use REDIS_URL from env if available, otherwise default
        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url, socket_connect_timeout=2, socket_timeout=2) # Short timeouts
        r.ping()
        status["services"]["redis"] = {{"status": "running", "url_used": redis_url}}
    except ImportError:
        status["services"]["redis"] = {{"status": "error", "details": "Python redis library not installed."}}
    except Exception as e: 
        status["services"]["redis"] = {{"status": "error_or_stopped", "details": str(e), "url_attempted": os.environ.get("REDIS_URL", "redis://localhost:6379/0")}}
    
    report_path = LOG_DIR / "celery_status.json"
    report_path.write_text(json.dumps(status, indent=2))
    print(f"[CeleryDaemon {{datetime.now().strftime('%H:%M:%S')}}] Status updated. Report: {{report_path}}")

if __name__ == "__main__":
    print(f"[CeleryDaemon {{datetime.now().strftime('%H:%M:%S')}}] Starting up. Project root: {{PROJECT_ROOT}}, Log dir: {{LOG_DIR}}")
    while True:
        get_celery_status()
        time.sleep(60) # 1 minute
"""
        self._write_script(self.daemons_dir / "celery_daemon.py", celery_daemon_script, make_executable=True)

        # Launch daemons
        daemon_scripts_to_launch = ["test_daemon.py", "celery_daemon.py"]
        for script_filename in daemon_scripts_to_launch:
            daemon_script_path = self.daemons_dir / script_filename
            log_subdir = daemon_output_base / daemon_script_path.stem
            log_subdir.mkdir(parents=True, exist_ok=True)
            
            # Open log files with line buffering (1) for text mode, or unbuffered (0) for binary.
            # Using "a" for append.
            stdout_log = open(log_subdir / "stdout.log", "a", buffering=1, encoding='utf-8')
            stderr_log = open(log_subdir / "stderr.log", "a", buffering=1, encoding='utf-8')
            
            cmd = [python_exe, str(daemon_script_path)]
            # Common Popen arguments
            popen_kwargs = {"stdout": stdout_log, "stderr": stderr_log, 
                            "cwd": self.project_root, # Run daemon from project root
                            "env": os.environ.copy()} # Pass current environment
            
            if os.name == 'nt': 
                popen_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW # Run hidden
            else: 
                popen_kwargs["start_new_session"] = True # Detach on Unix-like systems
            
            try:
                subprocess.Popen(cmd, **popen_kwargs)
                print(f"   Launched {script_filename}. Logs in: {log_subdir.relative_to(self.project_root)}")
            except Exception as e:
                print(f"   ERROR launching {script_filename}: {e}")
                # Close files if Popen failed, otherwise they are held by the daemon process
                stdout_log.close()
                stderr_log.close()

    def init_eigencode_integration(self):
        """Initialize Eigencode for enhanced code analysis"""
        print("🧬 Initializing Eigencode integration...")
        
        try:
            from eigencode_integration import EigencodeKarenBridge
            bridge = EigencodeKarenBridge()
            
            if bridge.eigencode_available:
                print("✅ Eigencode detected and configured by the bridge.")
                
                # Create quality monitoring daemon
                # Specification for the EigencodeQualityMonitor daemon
                quality_daemon_spec = {
                    'name': 'EigencodeQualityMonitor',
                    'description': 'AI-powered code quality monitoring using Eigencode or fallbacks. Regularly analyzes agent-generated code.',
                    'interval': 300, # Check every 5 minutes
                    'logic': '''
                        # This daemon will use the EigencodeKarenBridge to analyze code.
                        # For simplicity in this generated script, we assume the bridge is accessible
                        # or this logic would need to instantiate it / call an API.
                        # Placeholder logic:
                        try:
                            # In a real daemon, you might get a list of recently modified files
                            # from a shared queue or by scanning directories.
                            # bridge_instance = EigencodeKarenBridge() # If bridge is not globally accessible
                            # recent_code_files = get_recent_code_files_from_agents() # Placeholder function
                            # for file_path, agent_name in recent_code_files:
                            #     analysis = bridge_instance.analyze_agent_code(agent_name, file_path)
                            #     if analysis.get('issues'):
                            #         logger.warning(f"EigencodeQualityMonitor found issues in {file_path}: {analysis['issues']}")
                            #     else:
                            #         logger.info(f"EigencodeQualityMonitor: {file_path} looks good.")
                            pass # Replace with actual monitoring logic
                        except Exception as daemon_e:
                            logger.error(f"EigencodeQualityMonitor error during analysis: {daemon_e}")
                    '''
                }
                
                quality_daemon_code = bridge.create_enhanced_daemon(quality_daemon_spec)
                
                # Corrected daemon path to use self.daemons_dir
                daemon_path = self.daemons_dir / "eigencode_quality_monitor.py" # MODIFIED_LINE (used self.daemons_dir)
                self._write_script(daemon_path, quality_daemon_code, make_executable=True)
                print(f"   🤖 Eigencode Quality Monitor daemon script created at: {daemon_path.relative_to(self.project_root)}")
                
                # Attempt to start the daemon
                try:
                    python_exe = self.get_project_python_interpreter_for_subprocesses()
                    process = subprocess.Popen(
                        [python_exe, str(daemon_path)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
                        cwd=str(self.project_root) 
                    )
                    print(f"   🚀 Eigencode Quality Monitor daemon started (PID: {process.pid}).")
                except Exception as e_start:
                    print(f"   ⚠️ Failed to start Eigencode Quality Monitor daemon: {e_start}")
            else:
                print("⚠️  Eigencode not available via bridge, using fallback analysis methods within bridge if called.")
            
        except ImportError:
            print(f"⚠️  Failed to import EigencodeKarenBridge from eigencode_integration.py. Eigencode integration skipped.")
        except Exception as e:
            print(f"⚠️  Eigencode integration error: {e}")
            print("   Continuing without Eigencode enhancement.")

    def generate_context_files(self):
        print("📚 Generating comprehensive context files (OVERVIEW, PROTOCOL, TOOLS)...")
        
        overview_content = f"""# Karen AI Secretary - Project Overview
**Session ID**: {self.session_id}
**Generated**: {datetime.now().isoformat()}
**Project Root**: {self.project_root}

This project is a multi-agent system. 
- Shared knowledge modules (managers, bridge): `{self.context_dir.relative_to(self.project_root)}`
- Daemon scripts: `{self.daemons_dir.relative_to(self.project_root)}`
- Logs: `{self.logs_dir.relative_to(self.project_root)}` (includes daemon outputs and agent outputs)
"""
        project_overview_path = self.context_dir / "PROJECT_OVERVIEW.md"
        project_overview_path.write_text(overview_content)
        print(f"   Context file created: {project_overview_path.relative_to(self.project_root)}")
        
        protocol_content = f"""# Agent Protocol & Coordination
- **Tasking**: Claim tasks via `todo_manager` from `{self.context_dir.relative_to(self.project_root) / "intelligent_todos.json"}`.
- **File Edits**: MUST use `file_lock_manager` from `{self.context_dir.relative_to(self.project_root)}` before editing any project file. Lock status in `{self.autonomous_agents_dir.relative_to(self.project_root) / "file_locks.json"}`.
- **Tools**: Use `mcp_bridge` for file ops, git, and querying daemon reports.
- **Status**: Agent PIDs and basic status in `{self.context_dir.relative_to(self.project_root) / "network_status.json"}` (updated by `launch_agents.py` and potentially by agents themselves).
- **Logging**: Each agent's stdout/stderr logged to `{self.logs_dir.relative_to(self.project_root) / "agent_out" / "<agent_name>"}`.
"""
        agent_protocol_path = self.context_dir / "AGENT_PROTOCOL.md"
        agent_protocol_path.write_text(protocol_content)
        print(f"   Context file created: {agent_protocol_path.relative_to(self.project_root)}")
        
        tools_guide_content = f"""# Tools via MCP Bridge
Access: `from autonomous_agents.shared_knowledge.mcp_bridge import mcp_bridge_instance` (once `launch_agents.py` or agents instantiate it)
Call: `result = mcp_bridge_instance.execute_tool(category, operation, params={{...}})`
Always check `result` for an `'error'` key.

**Tool Categories & Operations (Example - to be implemented in mcp_bridge.py):**
- `file_operations`: `read`, `write`, `search` (glob), `list` (dir contents)
  - Params: `path` (project-relative), `content` (for write)
- `git_operations`: `status` (--short), `diff` (optional file), `commit` (-am)
  - Params: `file_path` (optional for diff), `message` (for commit)
- `test_operations`: `report` (reads test daemon output)
  - Output: Parsed JSON from `{self.logs_dir.relative_to(self.project_root) / "test_daemon/latest_test_results.json"}`
- `celery_operations`: `status` (reads celery daemon output)
  - Output: Parsed JSON from `{self.logs_dir.relative_to(self.project_root) / "celery_daemon/celery_status.json"}`

Refer to `autonomous_agents/shared_knowledge/mcp_bridge.py` for available tools and their detailed parameters.
"""
        tools_and_helpers_path = self.context_dir / "TOOLS_AND_HELPERS.md"
        tools_and_helpers_path.write_text(tools_guide_content)
        print(f"   Context file created: {tools_and_helpers_path.relative_to(self.project_root)}")

    def init_mcp_bridge(self):
        print("🌉 Initializing MCP Bridge (Master Control Program Bridge)...")
        mcp_bridge_path = self.context_dir / "mcp_bridge.py"
        
        if not mcp_bridge_path.exists():
            mcp_content = """#!/usr/bin/env python3
# MCP Bridge - Master Control Program
# Provides unified tool access for agents.
# Agents should import and use 'mcp_bridge_instance' which will be
# instantiated by launch_agents.py or individual agent init.

import json
from pathlib import Path
import subprocess
import os
import traceback # For detailed error reporting

class MCPBridge:
    def __init__(self, project_root_path: Path, logs_dir_path: Path):
        self.project_root = project_root_path.resolve()
        self.logs_dir = logs_dir_path.resolve()
        # One could also initialize shared components here, e.g.:
        # from .file_lock_manager import lock_manager # Assuming it's importable
        # self.file_locker = lock_manager
        print(f"[MCPBridge] Initialized. Project Root: {self.project_root}, Logs Dir: {self.logs_dir}")

    def execute_tool(self, category: str, operation: str, params: dict = None) -> dict:
        params = params if params is not None else {}
        print(f"[MCPBridge] Executing: Category='{category}', Operation='{operation}', Params='{params}'")
        try:
            if category == "file_operations":
                return self._handle_file_ops(operation, params)
            elif category == "git_operations":
                return self._handle_git_ops(operation, params)
            elif category == "test_operations":
                return self._handle_test_ops(operation, params)
            elif category == "celery_operations":
                return self._handle_celery_ops(operation, params)
            else:
                return {"error": f"Unknown tool category: {category}"}
        except Exception as e:
            return {"error": f"Exception in {category}.{operation}: {str(e)}", "details": traceback.format_exc()}

    def _resolve_path(self, relative_path_str: str) -> Path | None:
        # Helper to resolve and somewhat validate paths
        if not relative_path_str or not isinstance(relative_path_str, str):
            return None
        
        # Avoid absolute paths being passed directly in 'relative_path_str'
        if os.path.isabs(relative_path_str):
             # Check if it's a subpath of project_root if abs path given by mistake
            try:
                abs_p = Path(relative_path_str).resolve()
                abs_p.relative_to(self.project_root) # Will raise ValueError if not a subpath
                # If it's already an absolute path within the project, allow it.
                # This might happen if an agent constructs an absolute path correctly.
                return abs_p
            except ValueError:
                 return None # Not a subpath, reject.
            except Exception: # Other path errors
                 return None

        # Standard case: relative path
        resolved_path = (self.project_root / relative_path_str).resolve()
        
        # Security check: ensure the resolved path is within the project root
        try:
            resolved_path.relative_to(self.project_root)
        except ValueError:
            # Path is outside project root, potential security risk
            print(f"[MCPBridge] Path traversal attempt blocked: {relative_path_str} resolved to {resolved_path}")
            return None 
        return resolved_path

    def _handle_file_ops(self, operation: str, params: dict) -> dict:
        target_path_rel = params.get("path")
        abs_path = self._resolve_path(target_path_rel)

        if not abs_path:
            return {"error": f"Invalid or missing 'path': {target_path_rel}. Must be project-relative."}

        if operation == "read":
            if not abs_path.is_file():
                return {"error": f"File not found: {target_path_rel} (resolved: {abs_path})"}
            try:
                return {"content": abs_path.read_text(encoding='utf-8')}
            except Exception as e:
                return {"error": f"Could not read file {target_path_rel}: {str(e)}"}
        elif operation == "write":
            content = params.get("content")
            if content is None: # Allow empty string, but not None
                return {"error": "Missing 'content' for write operation"}
            try:
                abs_path.parent.mkdir(parents=True, exist_ok=True)
                abs_path.write_text(str(content), encoding='utf-8')
                return {"status": "success", "message": f"File '{target_path_rel}' written."}
            except Exception as e:
                return {"error": f"Could not write to file {target_path_rel}: {str(e)}"}
        elif operation == "list_dir":
            if not abs_path.is_dir():
                return {"error": f"Directory not found: {target_path_rel}"}
            try:
                items = [{"name": item.name, "type": "dir" if item.is_dir() else "file"} for item in abs_path.iterdir()]
                return {"items": items}
            except Exception as e:
                return {"error": f"Could not list directory {target_path_rel}: {str(e)}"}
        else:
            return {"error": f"Unknown file operation: {operation}"}

    def _run_subprocess(self, cmd_list: list, cwd_path: Path = None) -> dict:
        try:
            process = subprocess.run(cmd_list, capture_output=True, text=True, cwd=cwd_path or self.project_root, timeout=60, check=False)
            return {
                "stdout": process.stdout.strip(), 
                "stderr": process.stderr.strip(), 
                "return_code": process.returncode
            }
        except subprocess.TimeoutExpired:
            return {"error": "Command timed out", "command": " ".join(cmd_list)}
        except FileNotFoundError: # e.g. git not found
            return {"error": f"Command not found: {cmd_list[0]}", "command": " ".join(cmd_list)}
        except Exception as e:
            return {"error": f"Subprocess failed: {str(e)}", "command": " ".join(cmd_list)}

    def _handle_git_ops(self, operation: str, params: dict) -> dict:
        if operation == "status":
            return self._run_subprocess(["git", "status", "--short"])
        elif operation == "diff":
            file_to_diff = params.get("file_path")
            cmd = ["git", "diff"]
            if file_to_diff:
                abs_path = self._resolve_path(file_to_diff)
                if not abs_path:
                    return {"error": f"Invalid path for git diff: {file_to_diff}"}
                cmd.append(str(abs_path))
            return self._run_subprocess(cmd)
        elif operation == "commit":
            message = params.get("message")
            if not message:
                return {"error": "Commit message is required."}
            # Simplified: git commit -am "message"
            # For specific files, agents should `git add` first (another op?) or we enhance this.
            return self._run_subprocess(["git", "commit", "-am", message])
        else:
            return {"error": f"Unknown git operation: {operation}"}
            
    def _handle_test_ops(self, operation: str, params: dict) -> dict:
        if operation == "report":
            report_path = self.logs_dir / "test_daemon" / "latest_test_results.json"
            if report_path.exists():
                try:
                    return json.loads(report_path.read_text(encoding='utf-8'))
                except Exception as e:
                    return {"error": f"Error reading test report {report_path}: {str(e)}"}
            return {"error": f"Test report not found at {report_path}"}
        else:
            return {"error": f"Unknown test operation: {operation}"}

    def _handle_celery_ops(self, operation: str, params: dict) -> dict:
        if operation == "status":
            status_path = self.logs_dir / "celery_daemon" / "celery_status.json"
            if status_path.exists():
                try:
                    return json.loads(status_path.read_text(encoding='utf-8'))
                except Exception as e:
                    return {"error": f"Error reading Celery status {status_path}: {str(e)}"}
            return {"error": f"Celery status report not found at {status_path}"}
        else:
            return {"error": f"Unknown celery operation: {operation}"}

# Example of how an agent might get an instance.
# This instance would typically be created and passed by the agent manager (e.g. launch_agents.py)
# For direct use by agents if not passed:
# from pathlib import Path
# current_project_root = Path(__file__).resolve().parent.parent.parent # Adjust based on mcp_bridge.py location
# current_logs_dir = current_project_root / "logs"
# mcp_bridge_instance = MCPBridge(project_root_path=current_project_root, logs_dir_path=current_logs_dir)

# if __name__ == '__main__':
#     # Example usage for testing mcp_bridge.py directly
#     bridge = MCPBridge(Path.cwd(), Path.cwd() / 'logs')
#     print("--- Testing MCP Bridge ---")
#     # Ensure dummy files/dirs exist in a 'test_mcp_dir' for these examples
#     test_dir = Path.cwd() / "test_mcp_dir"
#     test_dir.mkdir(exist_ok=True)
#     (test_dir / "sample.txt").write_text("Hello from MCP Bridge test!")
#     (test_dir / "subdir").mkdir(exist_ok=True)
#     (test_dir / "subdir" / "another.txt").write_text("Another file.")

#     print("\nFile Read:")
#     print(bridge.execute_tool("file_operations", "read", {"path": "test_mcp_dir/sample.txt"}))
#     print(bridge.execute_tool("file_operations", "read", {"path": "test_mcp_dir/nonexistent.txt"}))
    
#     print("\nFile Write:")
#     print(bridge.execute_tool("file_operations", "write", {"path": "test_mcp_dir/new_file.txt", "content": "Written by MCP."}))
#     print(bridge.execute_tool("file_operations", "read", {"path": "test_mcp_dir/new_file.txt"}))

#     print("\nList Dir:")
#     print(bridge.execute_tool("file_operations", "list_dir", {"path": "test_mcp_dir"}))
#     print(bridge.execute_tool("file_operations", "list_dir", {"path": "test_mcp_dir/subdir"}))

#     # Git examples require a git repository.
#     # print("\nGit Status (run in a git repo):")
#     # print(bridge.execute_tool("git_operations", "status"))

#     # Assumes daemon reports are in logs/test_daemon/ and logs/celery_daemon/ relative to CWD
#     # print("\nTest Report:")
#     # print(bridge.execute_tool("test_operations", "report"))
#     # print("\nCelery Status:")
#     # print(bridge.execute_tool("celery_operations", "status"))
"""
            self._write_script(mcp_bridge_path, mcp_content)
        else:
            print(f"   MCP Bridge script already exists: {mcp_bridge_path.relative_to(self.project_root)}")

    def create_agent_launcher_and_status_file(self):
        print("🚀 Creating agent launcher (launch_agents.py) & network_status.json...")
        
        launch_agents_py_path = self.project_root / "launch_agents.py"
        network_status_json_path = self.context_dir / "network_status.json"
        agents_config_json_path = self.context_dir / "agents_config.json" # Centralized config

        if not network_status_json_path.exists():
            initial_status = {"agents": {}, "session_id": self.session_id, "last_updated": datetime.now().isoformat()}
            network_status_json_path.write_text(json.dumps(initial_status, indent=2))
            print(f"   Network status file created: {network_status_json_path.relative_to(self.project_root)}")

        if not agents_config_json_path.exists():
            dummy_config = {
                "agents": [
                    {
                        "name": "ExampleEmailAgent",
                        "script_path": "agents/email_processing_agent.py", # Relative to project root
                        "enabled": False,
                        "description": "Handles incoming emails for Karen. (Example - script needs to be created)",
                        "python_interpreter": "default", # 'default' or specific path
                        "args": ["--mode", "process"] 
                    },
                    {
                        "name": "ExampleTaskAgent",
                        "script_path": "agents/task_execution_agent.py",
                        "enabled": False,
                        "description": "Executes tasks from the TODO system. (Example - script needs to be created)",
                        "python_interpreter": "default",
                        "args": []
                    }
                ]
            }
            agents_config_json_path.write_text(json.dumps(dummy_config, indent=2))
            print(f"   Dummy agents_config.json created at: {agents_config_json_path.relative_to(self.project_root)}. Please review and update.")

            # Create a dummy agent script dir and one example agent if it doesn't exist
            agents_dir = self.project_root / "agents"
            agents_dir.mkdir(parents=True, exist_ok=True)
            dummy_agent_script_path = agents_dir / "email_processing_agent.py"
            if not dummy_agent_script_path.exists():
                dummy_agent_content = """#!/usr/bin/env python3
import time
import sys
import os
from pathlib import Path

# This is a dummy agent script. Replace with actual agent logic.
# It can access shared knowledge via relative paths or env vars.
# Example: Autonomous Agents dir is typically ../autonomous-agents from 'agents' dir

def main(args=None):
    agent_name = Path(__file__).stem
    print(f"[{agent_name}] Started. PID: {os.getpid()}. Args: {args}")
    
    # Example: Accessing shared knowledge (adjust path as needed)
    # shared_knowledge_dir = Path(__file__).resolve().parent.parent / "autonomous-agents" / "shared-knowledge"
    # print(f"[{agent_name}] Shared knowledge dir: {shared_knowledge_dir}")
    
    # todo_manager_path = shared_knowledge_dir / "todo_manager.py"
    # if todo_manager_path.exists():
    #     try:
    #         # This is a simplified import; proper packaging or PYTHONPATH management is better
    #         # sys.path.append(str(shared_knowledge_dir))
    #         # from todo_manager import todo_manager 
    #         # print(f"[{agent_name}] TODOs Status: {todo_manager.get_status_summary()}")
    #         pass # Actual usage would involve claiming/completing tasks
    #     except Exception as e:
    #         print(f"[{agent_name}] Error importing/using todo_manager: {e}")
            
    print(f"[{agent_name}] Running simple loop...")
    try:
        count = 0
        while True:
            print(f"[{agent_name}] Working... iteration {count}")
            count += 1
            time.sleep(30) # Simulate work
    except KeyboardInterrupt:
        print(f"[{agent_name}] Shutting down...")
    finally:
        print(f"[{agent_name}] Exited.")

if __name__ == "__main__":
    main(sys.argv[1:])
"""
                self._write_script(dummy_agent_script_path, dummy_agent_content, make_executable=True)
                print(f"   Dummy agent script created: {dummy_agent_script_path.relative_to(self.project_root)}")


        if not launch_agents_py_path.exists():
            launcher_content = f"""#!/usr/bin/env python3
# launch_agents.py - Manages and launches different AI agents based on agents_config.json
import subprocess
import json
import time
import os
import sys
from pathlib import Path
from datetime import datetime

# This script (launch_agents.py) is at the Project Root.
PROJECT_ROOT = Path(__file__).resolve().parent
AUTONOMOUS_AGENTS_DIR = PROJECT_ROOT / "autonomous-agents"
SHARED_KNOWLEDGE_DIR = AUTONOMOUS_AGENTS_DIR / "shared-knowledge"
LOGS_DIR = PROJECT_ROOT / "logs"
AGENT_LOG_BASE_DIR = LOGS_DIR / "agent_out" # Centralized log output for all agents

AGENTS_CONFIG_PATH = SHARED_KNOWLEDGE_DIR / "agents_config.json" 
NETWORK_STATUS_PATH = SHARED_KNOWLEDGE_DIR / "network_status.json"

# Robust Terminal Handler (RTH) is not used, as per user instruction.
# Agents are launched directly using the determined Python interpreter.

# Python interpreter detection (specific to launch_agents.py context)
def get_project_python_interpreter(config_preference="default"):
    if config_preference and config_preference != "default":
        p_path = Path(config_preference)
        if p_path.is_file() and os.access(p_path, os.X_OK):
            return str(p_path)
        print(f"[Launcher] Warning: Specified python interpreter '{config_preference}' not found or not executable. Falling back.")

    # Try project .venv
    venv_scripts = PROJECT_ROOT / ".venv" / ("Scripts" if os.name == 'nt' else "bin")
    venv_python = venv_scripts / ("python.exe" if os.name == 'nt' else "python")
    if venv_python.exists(): return str(venv_python)
    
    # Try project venv (alternative name)
    venv_alt_scripts = PROJECT_ROOT / "venv" / ("Scripts" if os.name == 'nt' else "bin")
    venv_alt_python = venv_alt_scripts / ("python.exe" if os.name == 'nt' else "python")
    if venv_alt_python.exists(): return str(venv_alt_python)
    
    return sys.executable # Fallback to current system Python

def update_network_status(agent_name, pid=None, status="stopped", script_path=None, error=None):
    # This needs file locking if multiple processes (e.g. agents themselves) update it.
    # For now, assuming only launch_agents.py writes to it primarily.
    try:
        data = json.loads(NETWORK_STATUS_PATH.read_text(encoding='utf-8')) if NETWORK_STATUS_PATH.exists() else {{"agents": {{}}, "last_updated": datetime.now().isoformat()}}
        
        agent_entry = data["agents"].get(agent_name, {{}})
        agent_entry["status"] = status
        if pid is not None: agent_entry["pid"] = pid
        if script_path is not None: agent_entry["script_path"] = script_path
        if status == "running":
            agent_entry["launched_at"] = datetime.now().isoformat()
            agent_entry.pop("stopped_at", None)
            agent_entry.pop("error", None)
        elif status == "stopped" or status == "error":
            agent_entry["stopped_at"] = datetime.now().isoformat()
            if error: agent_entry["error"] = str(error)
        
        data["agents"][agent_name] = agent_entry
        data["last_updated"] = datetime.now().isoformat()
        NETWORK_STATUS_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"[Launcher] Error updating network status for {agent_name}: {e}")

def launch_agent(agent_config):
    agent_name = agent_config.get("name", "UnnamedAgent")
    script_path_rel = agent_config.get("script_path")
    python_pref = agent_config.get("python_interpreter", "default")
    agent_args = agent_config.get("args", [])

    if not script_path_rel:
        print(f"[Launcher] Agent '{agent_name}' is missing 'script_path' in config. Skipping.")
        update_network_status(agent_name, status="config_error", error="Missing script_path")
        return None

    script_abs_path = (PROJECT_ROOT / script_path_rel).resolve()
    if not script_abs_path.exists():
        print(f"[Launcher] Agent script not found for '{agent_name}': {script_abs_path}. Skipping.")
        update_network_status(agent_name, status="script_not_found", script_path=str(script_abs_path), error="Script file missing")
        return None

    python_exe_to_use = get_project_python_interpreter(python_pref)
    print(f"[Launcher] Attempting to launch agent: '{agent_name}' using Python: {python_exe_to_use}")
    print(f"           Script: {script_abs_path}")
    if agent_args: print(f"           Args: {agent_args}")
    
    # Agent-specific log directory
    agent_log_dir = AGENT_LOG_BASE_DIR / agent_name
    agent_log_dir.mkdir(parents=True, exist_ok=True) # Ensure it exists
    
    stdout_log_path = agent_log_dir / "stdout.log"
    stderr_log_path = agent_log_dir / "stderr.log"
    
    # Open log files in append mode, line buffered
    try:
        stdout_log = open(stdout_log_path, "a", buffering=1, encoding='utf-8')
        stderr_log = open(stderr_log_path, "a", buffering=1, encoding='utf-8')
    except Exception as e:
        print(f"[Launcher] Error opening log files for {agent_name} in {agent_log_dir}: {e}")
        update_network_status(agent_name, status="log_error", script_path=str(script_abs_path), error=f"Log file open error: {e}")
        return None
        
    cmd = [python_exe_to_use, str(script_abs_path)] + agent_args
    
    popen_kwargs = {{
        "stdout": stdout_log, 
        "stderr": stderr_log, 
        "cwd": PROJECT_ROOT, # Run agent from project root by default
        "env": os.environ.copy() # Inherit environment
    }}
    
    # On Windows, CREATE_NEW_CONSOLE can be useful for debugging individual agents.
    # CREATE_NO_WINDOW runs them hidden. For daemons, hidden is typical.
    # On Unix, start_new_session=True detaches the agent process.
    if os.name == 'nt':
        popen_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW # subprocess.CREATE_NEW_CONSOLE
    else:
        popen_kwargs["start_new_session"] = True 
        
    try:
        process = subprocess.Popen(cmd, **popen_kwargs)
        print(f"[Launcher] Agent '{agent_name}' (PID: {process.pid}) launched. Logs: {agent_log_dir.relative_to(PROJECT_ROOT)}")
        update_network_status(agent_name, pid=process.pid, status="running", script_path=str(script_abs_path))
        return process
    except Exception as e:
        print(f"[Launcher] ERROR launching agent '{agent_name}': {e}")
        update_network_status(agent_name, status="launch_error", script_path=str(script_abs_path), error=f"Launch exception: {e}")
        # Ensure log files are closed if Popen failed early
        stdout_log.close()
        stderr_log.close()
        return None

def main():
    print(f"[Launcher] Session Started: {datetime.now().isoformat()}")
    print(f"[Launcher] Project Root: {PROJECT_ROOT}")
    print(f"[Launcher] Agent Config: {AGENTS_CONFIG_PATH}")
    print(f"[Launcher] Network Status: {NETWORK_STATUS_PATH}")
    print(f"[Launcher] Agent Logs Base: {AGENT_LOG_BASE_DIR}")
    AGENT_LOG_BASE_DIR.mkdir(parents=True, exist_ok=True)


    if not AGENTS_CONFIG_PATH.exists():
        print(f"[Launcher] CRITICAL: Agent configuration file not found: {AGENTS_CONFIG_PATH}")
        print(f"[Launcher] Please create it (a dummy was generated by start_session.py if this is the first run).")
        return

    try:
        config_data = json.loads(AGENTS_CONFIG_PATH.read_text(encoding='utf-8'))
    except Exception as e:
        print(f"[Launcher] CRITICAL: Error reading agent config {AGENTS_CONFIG_PATH}: {e}")
        return
        
    launched_processes = []
    for agent_conf in config_data.get("agents", []):
        if agent_conf.get("enabled", False):
            proc = launch_agent(agent_conf)
            if proc:
                launched_processes.append({"name": agent_conf.get("name", "UnnamedAgent"), "process": proc})
            time.sleep(0.5) # Stagger launches slightly
            
    if launched_processes:
        print(f"\n[Launcher] {len(launched_processes)} agent(s) have been launched.")
        print(f"[Launcher] Monitor their status in {NETWORK_STATUS_PATH.relative_to(PROJECT_ROOT)} and logs in {AGENT_LOG_BASE_DIR.relative_to(PROJECT_ROOT)}")
        print("[Launcher] This script will now exit. Launched agents run in the background.")
    else:
        print("\n[Launcher] No agents were enabled or launched from the configuration.")
        print("[Launcher] Edit agents_config.json to enable and define agents.")

if __name__ == "__main__":
    main()
"""
            self._write_script(launch_agents_py_path, launcher_content, make_executable=True)
        else:
            print(f"   Agent launcher script already exists: {launch_agents_py_path.relative_to(self.project_root)}")

    def print_next_steps(self):
        print("\n" + "=" * 70)
        print("🎉 SESSION INITIALIZATION COMPLETE 🎉")
        print("=" * 70)
        print("\n📋 Next Steps & Key Locations:")
        print(f"  1. Shared Knowledge & Config: {self.context_dir.relative_to(self.project_root)}")
        print(f"     - Agent Configuration: {(self.context_dir / 'agents_config.json').relative_to(self.project_root)}")
        print(f"     - TODOs: {(self.context_dir / 'intelligent_todos.json').relative_to(self.project_root)}")
        print(f"     - File Locks: {(self.autonomous_agents_dir / 'file_locks.json').relative_to(self.project_root)}")
        print(f"     - Network Status: {(self.context_dir / 'network_status.json').relative_to(self.project_root)}")
        print(f"     - Context Docs: PROJECT_OVERVIEW.md, AGENT_PROTOCOL.md, TOOLS_AND_HELPERS.md")

        agents_dir_rel = (self.project_root / 'agents').relative_to(self.project_root)
        print(f"\n  2. Develop Agent Logic in: ./{agents_dir_rel}")
        print(f"     (An example agent 'email_processing_agent.py' may have been created there)")
        
        launch_script_rel = (self.project_root / 'launch_agents.py').relative_to(self.project_root)
        print(f"\n  3. Launch Enabled Agents using: python {launch_script_rel}")
        
        daemon_logs_rel = (self.logs_dir / 'daemon_output').relative_to(self.project_root)
        print(f"\n  4. Monitor Daemon Logs in: ./{daemon_logs_rel}")
        print(f"     (For 'test_daemon' and 'celery_daemon')")
        
        agent_logs_rel = (self.logs_dir / 'agent_out').relative_to(self.project_root)
        print(f"\n  5. Monitor Individual Agent Logs in: ./{agent_logs_rel}/<AGENT_NAME>/")
        print("=" * 70)

# The main execution block was already updated to use KarenStartSession.
# if __name__ == "__main__":
#    session_starter = KarenStartSession()
#    session_starter.start()
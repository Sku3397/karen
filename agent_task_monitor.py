import sys
import os
print(f"sys.path for agent_task_monitor.py: {sys.path}")
print(f"PYTHONPATH: {os.environ.get('PYTHONPATH')}")
print(f"PYTHONHOME: {os.environ.get('PYTHONHOME')}")
sys.exit()

"""
Monitors task files and updates agent instructions dynamically
"""
import json
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class TaskFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.src_path.endswith('_current_task.json'):
            print(f"New task file: {event.src_path}")
            # Agents will read these files
            
    def on_modified(self, event):
        if event.src_path.endswith('_current_task.json'):
            print(f"Task updated: {event.src_path}")

def monitor_tasks():
    """Monitor task files for changes"""
    event_handler = TaskFileHandler()
    observer = Observer()
    observer.schedule(event_handler, 'active_tasks', recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == '__main__':
    monitor_tasks()
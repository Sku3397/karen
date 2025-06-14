#!/usr/bin/env python3
"""
Fix missing 'id' fields in eigencode_assigned_tasks.json
"""

import json
import uuid
from pathlib import Path

def fix_missing_ids():
    """Add missing 'id' fields to tasks that don't have them"""
    task_file = Path("tasks/eigencode_assigned_tasks.json")
    
    if not task_file.exists():
        print(f"Task file not found: {task_file}")
        return
    
    print("Loading tasks from file...")
    with open(task_file, 'r') as f:
        tasks = json.load(f)
    
    fixed_count = 0
    
    for task in tasks:
        if isinstance(task, dict) and 'task_id' in task and 'id' not in task:
            # Generate a new ID for this task
            task['id'] = f"task_{uuid.uuid4().hex[:8]}"
            fixed_count += 1
            print(f"Added id '{task['id']}' to task '{task['task_id']}'")
    
    if fixed_count > 0:
        print(f"\nFixed {fixed_count} tasks. Saving to file...")
        with open(task_file, 'w') as f:
            json.dump(tasks, f, indent=2)
        print("Tasks file updated successfully!")
    else:
        print("No tasks needed fixing.")

if __name__ == "__main__":
    fix_missing_ids()
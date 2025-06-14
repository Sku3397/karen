"""
Force generation of next phase tasks
"""
import json
from datetime import datetime
from master_plan_tasks import MasterPlanTaskGenerator
import os

# Clear completed tasks
completed_dir = 'active_tasks/completed'
os.makedirs(completed_dir, exist_ok=True)

# Move completed tasks
import glob
for f in glob.glob('active_tasks/*_completed.json'):
    os.rename(f, f.replace('active_tasks/', 'active_tasks/completed/'))

# Generate new tasks
generator = MasterPlanTaskGenerator()
current_time = datetime.now()

# Check what phase we should be in (based on time or completed tasks)
completed_count = len(glob.glob('active_tasks/completed/*.json'))
phase = min((completed_count // 20) + 1, 5)  # 20 tasks per phase

print(f"Generating Phase {phase} tasks...")

# Generate tasks
tasks = generator.generate_phase_tasks(phase, current_time)
test_tasks = generator.generate_test_tasks(current_time)

# Save tasks to files
for task in tasks + test_tasks:
    agent = task['agent']
    task['instruction'] = generator.create_task_instruction(task)
    
    filename = f"active_tasks/{agent}_current_task_{task['id']}.json"
    with open(filename, 'w') as f:
        json.dump({'task': task, 'instruction': task['instruction']}, f, indent=2)
    
    print(f"Created: {filename}")

print(f"\nGenerated {len(tasks)} phase tasks and {len(test_tasks)} test tasks")
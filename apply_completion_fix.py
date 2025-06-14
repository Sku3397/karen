#!/usr/bin/env python3
"""
Apply the completion tracking fix to update autonomous_state.json immediately
"""
import json
import os
from pathlib import Path
from datetime import datetime

def apply_completion_fix():
    """Apply the completion tracking fix immediately"""
    
    print("🔧 Applying Agent Completion Tracking Fix")
    print("=" * 50)
    
    # Load current state
    try:
        with open('autonomous_state.json', 'r') as f:
            current_state = json.load(f)
        print("📖 Loaded current autonomous_state.json")
    except FileNotFoundError:
        print("❌ autonomous_state.json not found")
        return
    
    agent_states = current_state.get('agent_states', {})
    
    print("📊 Current completion counts:")
    for agent, data in agent_states.items():
        completed = data.get('tasks_completed', 0)
        print(f"  {agent}: {completed} completed")
    
    # Check for completed task files
    active_tasks_dir = Path('active_tasks')
    if not active_tasks_dir.exists():
        print("❌ No active_tasks directory found")
        return
    
    completed_files = list(active_tasks_dir.glob('*_current_task_completed.json'))
    print(f"\n🔍 Found {len(completed_files)} completed task files to process...")
    
    processed_count = 0
    for completed_file in completed_files:
        try:
            # Read the task file
            with open(completed_file, 'r') as f:
                task_data = json.load(f)
            
            # Extract agent name from filename  
            filename = completed_file.name
            if filename.endswith('_current_task_completed.json'):
                agent_name = filename.replace('_current_task_completed.json', '')
                
                if agent_name in agent_states:
                    # Increment the counter
                    agent_states[agent_name]['tasks_completed'] += 1
                    agent_states[agent_name]['status'] = 'idle'  # Reset to idle after completion
                    
                    # Get task info
                    task_info = task_data.get('task', {})
                    task_id = task_info.get('id', 'unknown')
                    task_type = task_info.get('type', 'unknown')
                    
                    print(f"✅ {agent_name}: credited for {task_type} ({task_id})")
                    processed_count += 1
                    
                    # Archive the completed file
                    completed_dir = active_tasks_dir / 'completed'
                    completed_dir.mkdir(exist_ok=True)
                    
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    archive_name = f"{task_id}_{timestamp}.json"
                    archive_path = completed_dir / archive_name
                    
                    completed_file.rename(archive_path)
                    print(f"📁 Archived: {completed_file.name} -> {archive_path.name}")
                    
        except Exception as e:
            print(f"❌ Error processing {completed_file}: {e}")
    
    if processed_count > 0:
        # Update the state file
        current_state['agent_states'] = agent_states
        
        with open('autonomous_state.json', 'w') as f:
            json.dump(current_state, f, indent=2)
        
        print(f"\n💾 Updated autonomous_state.json with {processed_count} task completions")
        
        print("\n📊 New completion counts:")
        total_completed = 0
        for agent, data in agent_states.items():
            completed = data.get('tasks_completed', 0)
            total_completed += completed
            status = data.get('status', 'unknown')
            print(f"  {agent}: {completed} completed, status: {status}")
        
        print(f"\n🎯 Total tasks completed across all agents: {total_completed}")
        print("✅ SUCCESS: Agent completion tracking has been fixed!")
        print("🎉 All agents are now properly credited for their completed work!")
        
    else:
        print("\n⚠️  No completed tasks found to process")

if __name__ == '__main__':
    apply_completion_fix()
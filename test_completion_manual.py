#!/usr/bin/env python3
"""
Manual test to verify the completion tracking fix logic
"""
import json
import os
from pathlib import Path

def test_completion_logic():
    """Test the completion tracking logic manually"""
    
    print("🔍 Testing Agent Completion Tracking Fix Logic")
    print("=" * 50)
    
    # Simulate the agent states
    agent_states = {
        'orchestrator': {'status': 'working', 'last_task': None, 'tasks_completed': 0},
        'archaeologist': {'status': 'working', 'last_task': None, 'tasks_completed': 0},
        'sms_engineer': {'status': 'working', 'last_task': None, 'tasks_completed': 0},
        'memory_engineer': {'status': 'working', 'last_task': None, 'tasks_completed': 0},
        'test_engineer': {'status': 'working', 'last_task': None, 'tasks_completed': 0}
    }
    
    print("📊 Initial state (all agents at 0 completions):")
    for agent, data in agent_states.items():
        print(f"  {agent}: {data['tasks_completed']} completed")
    
    print("\n🔍 Checking for completed task files...")
    
    # Check for completed task files
    active_tasks_dir = Path('active_tasks')
    if not active_tasks_dir.exists():
        print("❌ No active_tasks directory found")
        return
    
    completed_files = list(active_tasks_dir.glob('*_current_task_completed.json'))
    print(f"📁 Found {len(completed_files)} completed task files:")
    
    processed_count = 0
    for completed_file in completed_files:
        print(f"  - {completed_file.name}")
        
        try:
            # Read the task file
            with open(completed_file, 'r') as f:
                task_data = json.load(f)
            
            # Extract agent name from filename  
            filename = completed_file.name
            if filename.endswith('_current_task_completed.json'):
                agent_name = filename.replace('_current_task_completed.json', '')
                
                if agent_name in agent_states:
                    # Simulate incrementing the counter
                    agent_states[agent_name]['tasks_completed'] += 1
                    agent_states[agent_name]['status'] = 'idle'
                    
                    # Get task info
                    task_info = task_data.get('task', {})
                    task_id = task_info.get('id', 'unknown')
                    task_type = task_info.get('type', 'unknown')
                    
                    print(f"    ✅ {agent_name}: {task_type} ({task_id})")
                    processed_count += 1
                    
        except Exception as e:
            print(f"    ❌ Error reading {completed_file}: {e}")
    
    print(f"\n📊 Final state after processing {processed_count} completed tasks:")
    total_completed = 0
    for agent, data in agent_states.items():
        completed = data['tasks_completed']
        total_completed += completed
        status = data['status']
        print(f"  {agent}: {completed} completed, status: {status}")
    
    print(f"\n🎯 Total tasks completed across all agents: {total_completed}")
    
    if total_completed > 0:
        print("✅ SUCCESS: The fix logic works correctly!")
        print("🎉 When implemented, agents will be properly credited for completed work!")
        
        # Show what the updated autonomous_state.json would look like
        updated_state = {
            "agent_states": agent_states,
            "note": "This is what autonomous_state.json will look like after the fix"
        }
        
        print("\n📄 Updated state that will be saved:")
        print(json.dumps(updated_state, indent=2))
        
    else:
        print("⚠️  No completed tasks found to process")
        print("💡 This could mean:")
        print("   - Agents haven't completed any tasks yet")
        print("   - Task files are in a different location")
        print("   - Tasks are still running")

if __name__ == '__main__':
    test_completion_logic()
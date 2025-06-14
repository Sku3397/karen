#!/usr/bin/env python3
"""
Test script to verify the agent completion tracking fix
"""
import json
from autonomous_task_system import AutonomousTaskSystem

def test_completion_tracking():
    """Test that existing completed tasks are properly tracked"""
    
    print("🔍 Testing Agent Completion Tracking Fix")
    print("=" * 50)
    
    # Check current state before fix
    try:
        with open('autonomous_state.json', 'r') as f:
            state_before = json.load(f)
        
        print("📊 State BEFORE fix:")
        for agent, data in state_before.get('agent_states', {}).items():
            completed = data.get('tasks_completed', 0)
            status = data.get('status', 'unknown')
            last_task = data.get('last_task', 'none')
            print(f"  {agent}: {completed} completed, status: {status}, last: {last_task}")
    
    except FileNotFoundError:
        print("⚠️  No existing autonomous_state.json found")
        state_before = None
    
    print("\n🚀 Initializing AutonomousTaskSystem with fix...")
    
    # Initialize the system (this will process existing completed tasks)
    system = AutonomousTaskSystem()
    
    # Give it a moment to process
    import time
    time.sleep(2)
    
    # Check state after fix
    try:
        with open('autonomous_state.json', 'r') as f:
            state_after = json.load(f)
        
        print("\n📊 State AFTER fix:")
        total_completed = 0
        for agent, data in state_after.get('agent_states', {}).items():
            completed = data.get('tasks_completed', 0)
            status = data.get('status', 'unknown')
            last_task = data.get('last_task', 'none')
            total_completed += completed
            print(f"  {agent}: {completed} completed, status: {status}, last: {last_task}")
        
        print(f"\n🎯 Total tasks completed across all agents: {total_completed}")
        
        if total_completed > 0:
            print("✅ SUCCESS: Task completion tracking is working!")
            print("🎉 Agents are now properly credited for their completed work!")
        else:
            print("⚠️  No completed tasks detected - agents may still be working or no tasks completed yet")
            
    except FileNotFoundError:
        print("❌ Error: autonomous_state.json not found after fix")
    
    # Stop the monitoring
    system.completion_monitor_running = False
    print("\n🛑 Stopped completion monitoring")

if __name__ == '__main__':
    test_completion_tracking()
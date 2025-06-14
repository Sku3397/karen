#!/usr/bin/env python3
# monitor.py
import json

# Load data
with open('autonomous_state.json') as f:
    state = json.load(f)

with open('tasks/eigencode_assigned_tasks.json') as f:
    tasks = json.load(f)

# Calculate stats
agents_working = len([a for a in state['agents'] if a['status'] == 'working'])
total_agents = len(state['agents'])

total_tasks = len(tasks)
completed_tasks = len([t for t in tasks if t.get('status') in ['completed', 'done']])
in_progress = len([t for t in tasks if t.get('status') == 'in_progress'])

# Display
print("🎯 KAREN AI STATUS")
print("=" * 40)
print(f"Agents: {agents_working}/{total_agents} working")
print(f"Tasks: {completed_tasks}/{total_tasks} ({completed_tasks/total_tasks*100:.1f}%) complete")
print(f"In Progress: {in_progress} tasks")
print("=" * 40)

# Show what each agent is doing
print("\nAgent Details:")
for agent in state['agents']:
    status_emoji = "🟢" if agent['status'] == 'working' else "⚪"
    print(f"{status_emoji} {agent['name']}: {agent['status']}")
#!/usr/bin/env python3
"""
Autonomous Eigencode Completion Report Generator
"""
import json
from datetime import datetime
from pathlib import Path

def generate_completion_report():
    """Generate comprehensive completion report"""
    
    # Read the task file
    with open('tasks/eigencode_assigned_tasks.json', 'r') as f:
        tasks = json.load(f)

    # Generate completion report
    completed_tasks = [t for t in tasks if t.get('status') == 'completed']
    total_tasks = len(tasks)
    completed_count = len(completed_tasks)

    categories = {}
    priorities = {'high': 0, 'medium': 0, 'low': 0}

    for task in completed_tasks:
        cat = task.get('category', 'Unknown')
        categories[cat] = categories.get(cat, 0) + 1
        
        pri = task.get('priority', 'medium')
        priorities[pri] += 1

    report = {
        'timestamp': datetime.now().isoformat(),
        'total_tasks': total_tasks,
        'completed_tasks': completed_count,
        'completion_rate': f'{(completed_count/total_tasks)*100:.1f}%',
        'categories_completed': categories,
        'priorities_completed': priorities,
        'target_achieved': completed_count >= 50,
        'worker_id': 'eigencode_autonomous_worker'
    }

    # Save report
    Path('reports').mkdir(exist_ok=True)
    with open('reports/eigencode_completion_report.json', 'w') as f:
        json.dump(report, f, indent=2)

    print(f'✅ AUTONOMOUS EIGENCODE COMPLETION REPORT')
    print(f'==========================================')
    print(f'Tasks Completed: {completed_count}/{total_tasks} ({report["completion_rate"]})')
    target_status = "EXCEEDED" if completed_count >= 50 else "NOT MET"
    print(f'Target: 50 tasks - {target_status}')
    print(f'')
    print(f'Categories Completed:')
    for cat, count in sorted(categories.items()):
        print(f'  {cat}: {count} tasks')
    print(f'')
    print(f'Priority Distribution:')
    for pri, count in priorities.items():
        print(f'  {pri.upper()}: {count} tasks')
    print(f'')
    print(f'Report saved to: reports/eigencode_completion_report.json')
    
    return report

if __name__ == "__main__":
    generate_completion_report()
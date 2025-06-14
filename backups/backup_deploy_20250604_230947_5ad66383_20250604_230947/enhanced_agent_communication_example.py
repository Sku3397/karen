#!/usr/bin/env python3
"""
Enhanced Agent Communication System - Usage Examples
Demonstrates skill-based routing, load balancing, and dynamic priority adjustment
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import json

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from src.agent_communication import (
    AgentCommunication, 
    TaskRequest, 
    TaskPriority, 
    AgentSkill,
    AgentPerformanceMetrics
)

def demonstrate_skill_based_routing():
    """Demonstrate skill-based task routing capabilities"""
    print("🎯 === SKILL-BASED ROUTING DEMONSTRATION ===")
    
    # Initialize orchestrator communication
    orchestrator = AgentCommunication('orchestrator')
    
    # Example 1: SMS Integration Task
    sms_task = TaskRequest(
        task_id="SMS_INTEGRATION_001",
        task_type="implement_sms_features",
        description="Implement SMS conversation threading and template system",
        priority=TaskPriority.HIGH,
        required_skills=[
            AgentSkill.SMS_INTEGRATION,
            AgentSkill.NLP_PROCESSING,
            AgentSkill.PYTHON_DEVELOPMENT
        ],
        estimated_duration=120,  # 2 hours
        deadline=datetime.now() + timedelta(hours=6),
        skill_weights={
            AgentSkill.SMS_INTEGRATION: 2.0,  # Higher importance
            AgentSkill.NLP_PROCESSING: 1.5,
            AgentSkill.PYTHON_DEVELOPMENT: 1.0
        }
    )
    
    best_agent = orchestrator.find_best_agent_for_task(sms_task)
    print(f"✅ SMS Task routed to: {best_agent}")
    
    # Example 2: Memory Optimization Task
    memory_task = TaskRequest(
        task_id="MEM_OPT_001",
        task_type="optimize_memory_performance",
        description="Optimize ChromaDB queries and improve memory retrieval speed",
        priority=TaskPriority.MEDIUM,
        required_skills=[
            AgentSkill.MEMORY_MANAGEMENT,
            AgentSkill.DATABASE_OPERATIONS,
            AgentSkill.PERFORMANCE_OPTIMIZATION
        ],
        estimated_duration=90,
        skill_weights={
            AgentSkill.MEMORY_MANAGEMENT: 2.0,
            AgentSkill.PERFORMANCE_OPTIMIZATION: 1.8,
            AgentSkill.DATABASE_OPERATIONS: 1.2
        }
    )
    
    best_agent = orchestrator.find_best_agent_for_task(memory_task)
    print(f"✅ Memory Task routed to: {best_agent}")
    
    # Example 3: Critical Emergency Task
    emergency_task = TaskRequest(
        task_id="EMERGENCY_001",
        task_type="fix_critical_bug",
        description="Fix critical email processing failure causing system downtime",
        priority=TaskPriority.CRITICAL,
        required_skills=[
            AgentSkill.EMAIL_PROCESSING,
            AgentSkill.ERROR_HANDLING,
            AgentSkill.PYTHON_DEVELOPMENT
        ],
        estimated_duration=30,
        deadline=datetime.now() + timedelta(minutes=30)
    )
    
    best_agent = orchestrator.find_best_agent_for_task(emergency_task)
    print(f"🚨 Emergency Task routed to: {best_agent}")

def demonstrate_load_balancing():
    """Demonstrate advanced load balancing capabilities"""
    print("\n⚖️ === LOAD BALANCING DEMONSTRATION ===")
    
    orchestrator = AgentCommunication('orchestrator')
    
    # Simulate different agent loads
    print("📊 Current Agent Workload:")
    workload_report = orchestrator.get_agent_workload_report()
    
    for agent, data in workload_report['agents'].items():
        print(f"  {agent}: {data['utilization_percent']}% utilization ({data['availability']})")
    
    print(f"\n🖥️ System Load: {workload_report['system_load_percent']}%")
    
    # Demonstrate routing multiple tasks with load balancing
    tasks = [
        TaskRequest(
            task_id=f"BATCH_TASK_{i:03d}",
            task_type="process_data",
            description=f"Process data batch {i}",
            priority=TaskPriority.MEDIUM,
            required_skills=[AgentSkill.PYTHON_DEVELOPMENT],
            estimated_duration=45
        ) for i in range(5)
    ]
    
    print("\n🔄 Routing batch tasks with load balancing:")
    for task in tasks:
        selected_agent = orchestrator.route_task_with_load_balancing(task)
        if selected_agent:
            print(f"  Task {task.task_id} → {selected_agent}")
        else:
            print(f"  Task {task.task_id} → No available agent")

def demonstrate_dynamic_priority_adjustment():
    """Demonstrate dynamic priority adjustment based on various factors"""
    print("\n🎚️ === DYNAMIC PRIORITY ADJUSTMENT DEMONSTRATION ===")
    
    orchestrator = AgentCommunication('orchestrator')
    
    # Example 1: Age-based priority escalation
    old_task = TaskRequest(
        task_id="OLD_TASK_001",
        task_type="routine_maintenance",
        description="Routine system maintenance task",
        priority=TaskPriority.LOW,
        required_skills=[AgentSkill.MONITORING],
        estimated_duration=60,
        created_at=datetime.now() - timedelta(hours=25)  # 25 hours old
    )
    
    print(f"📅 Old task original priority: {old_task.priority.name}")
    adjusted_task = orchestrator._adjust_task_priority(old_task)
    print(f"📈 After age adjustment: {adjusted_task.priority.name}")
    
    # Example 2: Deadline-based priority escalation
    urgent_task = TaskRequest(
        task_id="URGENT_TASK_001",
        task_type="client_report",
        description="Generate client report for meeting",
        priority=TaskPriority.MEDIUM,
        required_skills=[AgentSkill.DOCUMENTATION],
        estimated_duration=30,
        deadline=datetime.now() + timedelta(minutes=45)  # 45 minutes deadline
    )
    
    print(f"\n⏰ Urgent task original priority: {urgent_task.priority.name}")
    adjusted_urgent = orchestrator._adjust_task_priority(urgent_task)
    print(f"🔥 After deadline adjustment: {adjusted_urgent.priority.name}")

def demonstrate_performance_tracking():
    """Demonstrate agent performance tracking and skill rating updates"""
    print("\n📈 === PERFORMANCE TRACKING DEMONSTRATION ===")
    
    orchestrator = AgentCommunication('orchestrator')
    
    # Simulate task completion for different agents
    test_scenarios = [
        {
            'agent': 'sms_engineer',
            'task_id': 'SMS_TASK_001',
            'success': True,
            'completion_time': 75.0,  # 1.25 hours
            'skills_used': [AgentSkill.SMS_INTEGRATION, AgentSkill.PYTHON_DEVELOPMENT]
        },
        {
            'agent': 'memory_engineer',
            'task_id': 'MEM_TASK_001',
            'success': True,
            'completion_time': 45.0,  # 45 minutes
            'skills_used': [AgentSkill.MEMORY_MANAGEMENT, AgentSkill.DATABASE_OPERATIONS]
        },
        {
            'agent': 'test_engineer',
            'task_id': 'TEST_TASK_001',
            'success': False,
            'completion_time': 120.0,  # Failed after 2 hours
            'skills_used': [AgentSkill.TESTING_AUTOMATION]
        }
    ]
    
    print("🔄 Updating agent performance metrics:")
    for scenario in test_scenarios:
        orchestrator.update_agent_performance(
            agent=scenario['agent'],
            task_id=scenario['task_id'],
            success=scenario['success'],
            completion_time=scenario['completion_time'],
            skill_used=scenario['skills_used']
        )
        
        status = "✅ SUCCESS" if scenario['success'] else "❌ FAILED"
        print(f"  {scenario['agent']}: {status} ({scenario['completion_time']:.1f}min)")
    
    # Show updated performance metrics
    print("\n📊 Updated Performance Metrics:")
    for agent, metrics in orchestrator.performance_metrics.items():
        if metrics.tasks_completed > 0 or metrics.tasks_failed > 0:
            print(f"  {agent}:")
            print(f"    Success Rate: {metrics.success_rate:.2%}")
            print(f"    Avg Completion: {metrics.average_completion_time:.1f}min")
            print(f"    Current Load: {metrics.current_load}/{metrics.max_concurrent_tasks}")
            
            # Show top skills
            top_skills = orchestrator._get_top_skills(metrics)
            if top_skills:
                print(f"    Top Skills: {', '.join([f'{s['skill']}({s['rating']:.2f})' for s in top_skills])}")

def demonstrate_optimization_recommendations():
    """Demonstrate system optimization recommendations"""
    print("\n🔧 === OPTIMIZATION RECOMMENDATIONS ===")
    
    orchestrator = AgentCommunication('orchestrator')
    
    # Generate optimization recommendations
    recommendations = orchestrator.optimize_task_distribution()
    
    print("📋 System Analysis Results:")
    
    if recommendations['overloaded_agents']:
        print(f"⚠️  Overloaded Agents: {', '.join(recommendations['overloaded_agents'])}")
    
    if recommendations['underutilized_agents']:
        print(f"💤 Underutilized Agents: {', '.join(recommendations['underutilized_agents'])}")
    
    if recommendations['skill_gaps']:
        print("\n🎯 Skill Gap Analysis:")
        for gap in recommendations['skill_gaps']:
            print(f"  ⚠️  {gap['skill']}: {gap['reason']}")
    
    print("\n🗺️ Skill Coverage Map:")
    for skill, agents in recommendations['skill_coverage'].items():
        agent_count = len(agents)
        max_rating = max([a['rating'] for a in agents]) if agents else 0.0
        coverage_status = "🟢" if agent_count >= 2 and max_rating >= 0.7 else "🟡" if agent_count >= 1 else "🔴"
        print(f"  {coverage_status} {skill}: {agent_count} agents (max rating: {max_rating:.2f})")

def create_sample_task_routing_scenario():
    """Create a comprehensive task routing scenario"""
    print("\n🎬 === COMPREHENSIVE TASK ROUTING SCENARIO ===")
    
    orchestrator = AgentCommunication('orchestrator')
    
    # Create a mix of tasks with different priorities and skill requirements
    task_scenarios = [
        {
            'task_id': 'EMAIL_BUG_FIX',
            'type': 'bug_fix',
            'description': 'Fix email authentication timeout issues',
            'priority': TaskPriority.CRITICAL,
            'skills': [AgentSkill.EMAIL_PROCESSING, AgentSkill.ERROR_HANDLING],
            'duration': 60,
            'deadline_hours': 2
        },
        {
            'task_id': 'SMS_FEATURE_DEV',
            'type': 'feature_development',
            'description': 'Implement SMS quick reply suggestions',
            'priority': TaskPriority.HIGH,
            'skills': [AgentSkill.SMS_INTEGRATION, AgentSkill.NLP_PROCESSING],
            'duration': 180,
            'deadline_hours': 24
        },
        {
            'task_id': 'VOICE_TESTING',
            'type': 'testing',
            'description': 'Create integration tests for voice transcription',
            'priority': TaskPriority.MEDIUM,
            'skills': [AgentSkill.VOICE_PROCESSING, AgentSkill.TESTING_AUTOMATION],
            'duration': 90,
            'deadline_hours': 48
        },
        {
            'task_id': 'DOC_UPDATE',
            'type': 'documentation',
            'description': 'Update API documentation for new endpoints',
            'priority': TaskPriority.LOW,
            'skills': [AgentSkill.DOCUMENTATION, AgentSkill.API_INTEGRATION],
            'duration': 120,
            'deadline_hours': 72
        },
        {
            'task_id': 'MEMORY_ANALYSIS',
            'type': 'analysis',
            'description': 'Analyze memory usage patterns and optimize queries',
            'priority': TaskPriority.MEDIUM,
            'skills': [AgentSkill.MEMORY_MANAGEMENT, AgentSkill.PERFORMANCE_OPTIMIZATION],
            'duration': 150,
            'deadline_hours': 36
        }
    ]
    
    print("📋 Task Routing Results:")
    print("-" * 80)
    
    for scenario in task_scenarios:
        task = TaskRequest(
            task_id=scenario['task_id'],
            task_type=scenario['type'],
            description=scenario['description'],
            priority=scenario['priority'],
            required_skills=scenario['skills'],
            estimated_duration=scenario['duration'],
            deadline=datetime.now() + timedelta(hours=scenario['deadline_hours'])
        )
        
        # Route the task
        selected_agent = orchestrator.route_task_with_load_balancing(task)
        
        # Display routing result
        priority_icon = {
            TaskPriority.CRITICAL: "🚨",
            TaskPriority.HIGH: "🔴",
            TaskPriority.MEDIUM: "🟡",
            TaskPriority.LOW: "🟢"
        }
        
        print(f"{priority_icon[task.priority]} {task.task_id}")
        print(f"   → Assigned to: {selected_agent or 'NO AGENT AVAILABLE'}")
        print(f"   → Skills: {', '.join([s.value for s in task.required_skills])}")
        print(f"   → Duration: {task.estimated_duration}min | Deadline: {scenario['deadline_hours']}h")
        print()

def main():
    """Run all demonstration scenarios"""
    print("🤖 ENHANCED AGENT COMMUNICATION SYSTEM DEMONSTRATION")
    print("=" * 60)
    
    try:
        demonstrate_skill_based_routing()
        demonstrate_load_balancing()
        demonstrate_dynamic_priority_adjustment()
        demonstrate_performance_tracking()
        demonstrate_optimization_recommendations()
        create_sample_task_routing_scenario()
        
        print("\n✅ === DEMONSTRATION COMPLETE ===")
        print("All enhanced features have been successfully demonstrated!")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Learning System Integration with Agent Communication
Shows how the learning system integrates with the enhanced agent communication system
"""

import sys
import json
import random
import time
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / 'src'))

from src.learning_system import get_learning_system_instance, ArchitectureImprovement
from src.agent_communication import (
    AgentCommunication, 
    TaskRequest, 
    TaskPriority, 
    AgentSkill,
    get_agent_communication_instance
)

def simulate_integrated_task_flow():
    """Demonstrate integration between learning system and agent communication"""
    print("🔗 LEARNING SYSTEM + AGENT COMMUNICATION INTEGRATION")
    print("=" * 60)
    
    # Initialize systems
    learning_system = get_learning_system_instance()
    agent_comm = get_agent_communication_instance()
    
    print("✅ Both systems initialized successfully")
    
    # Simulate task routing and learning
    tasks = [
        TaskRequest(
            task_id="integrated_001",
            task_type="sms_response",
            description="Handle customer SMS inquiry",
            priority=TaskPriority.MEDIUM,
            required_skills=[AgentSkill.SMS_MANAGEMENT, AgentSkill.CUSTOMER_SERVICE],
            deadline=datetime.now(),
            metadata={
                'customer_id': 'cust_001',
                'message_length': 150,
                'urgency': 'normal'
            }
        ),
        TaskRequest(
            task_id="integrated_002", 
            task_type="memory_update",
            description="Update customer profile information",
            priority=TaskPriority.HIGH,
            required_skills=[AgentSkill.MEMORY_OPERATIONS, AgentSkill.DATA_PROCESSING],
            deadline=datetime.now(),
            metadata={
                'data_size': 'large',
                'update_type': 'profile_enhancement'
            }
        ),
        TaskRequest(
            task_id="integrated_003",
            task_type="test_execution", 
            description="Run system integration tests",
            priority=TaskPriority.LOW,
            required_skills=[AgentSkill.TESTING, AgentSkill.SYSTEM_MONITORING],
            deadline=datetime.now(),
            metadata={
                'test_suite': 'integration',
                'expected_duration': 300
            }
        )
    ]
    
    print(f"\n📋 Processing {len(tasks)} integrated tasks...")
    
    for task in tasks:
        print(f"\n🎯 Processing task: {task.task_id}")
        
        # 1. Agent communication system routes the task
        best_agent = agent_comm.find_best_agent_for_task(
            required_skills=task.required_skills,
            priority=task.priority,
            estimated_duration=task.metadata.get('expected_duration', 120)
        )
        
        if best_agent:
            print(f"   ✅ Routed to agent: {best_agent}")
            
            # 2. Simulate task execution
            start_time = time.time()
            
            # Simulate different outcomes based on agent capabilities
            agent_skills = agent_comm.agent_skills.get(best_agent, [])
            skill_match = all(skill in agent_skills for skill in task.required_skills)
            
            # Higher success rate for good skill matches
            success_probability = 0.9 if skill_match else 0.6
            success = random.random() < success_probability
            
            # Simulate completion time
            base_time = task.metadata.get('expected_duration', 120)
            if success:
                completion_time = base_time * random.uniform(0.8, 1.2)
            else:
                completion_time = base_time * random.uniform(1.5, 3.0)
            
            print(f"   ⏱️  Execution: {success} in {completion_time:.1f}s")
            
            # 3. Update agent communication system
            agent_comm.record_task_completion(
                agent=best_agent,
                task_id=task.task_id,
                success=success,
                completion_time=completion_time
            )
            
            # 4. Learning system analyzes the outcome
            task_data = {
                'task_type': task.task_type,
                'required_skills': [skill.value for skill in task.required_skills],
                'priority': task.priority.value,
                'routing_score': agent_comm._calculate_routing_score(
                    best_agent, task.required_skills, task.priority, base_time
                ),
                'skill_match': skill_match,
                'metadata': task.metadata
            }
            
            learning_system.analyze_task_completion(
                task_id=task.task_id,
                agent=best_agent,
                success=success,
                completion_time=completion_time,
                task_data=task_data
            )
            
            print(f"   📊 Learning system updated with results")
            
        else:
            print(f"   ❌ No suitable agent found for task")
            
            # Record failed routing for learning system
            learning_system.analyze_task_completion(
                task_id=task.task_id,
                agent="system",
                success=False,
                completion_time=0,
                task_data={
                    'task_type': task.task_type,
                    'required_skills': [skill.value for skill in task.required_skills],
                    'priority': task.priority.value,
                    'failure_reason': 'no_suitable_agent'
                }
            )
        
        time.sleep(0.5)  # Brief pause between tasks
    
    return learning_system, agent_comm

def analyze_integrated_performance(learning_system, agent_comm):
    """Analyze performance using both systems"""
    print(f"\n📈 INTEGRATED PERFORMANCE ANALYSIS")
    print("=" * 50)
    
    # Get workload report from agent communication
    workload_report = agent_comm.get_agent_workload_report()
    print(f"📊 Agent Communication System Report:")
    print(f"   Active Agents: {workload_report['summary']['active_agents']}")
    print(f"   Total Capacity: {workload_report['summary']['total_capacity']}")
    print(f"   Current Load: {workload_report['summary']['current_load']}")
    print(f"   System Utilization: {workload_report['summary']['utilization_percent']:.1f}%")
    
    # Get learning insights
    learning_insights = learning_system.get_learning_insights()
    print(f"\n🧠 Learning System Insights:")
    print(f"   System Health: {learning_insights['system_health']['status']}")
    print(f"   Success Rate: {learning_insights['system_health']['success_rate']:.1%}")
    print(f"   Patterns Learned: {learning_insights['learning_progress']['total_patterns_learned']}")
    
    # Cross-system analysis
    print(f"\n🔗 Cross-System Correlation:")
    
    # Check if low utilization correlates with patterns
    if workload_report['summary']['utilization_percent'] < 50:
        print("   📉 Low system utilization detected")
        if learning_insights['learning_progress']['total_patterns_learned'] > 10:
            print("   💡 Learning system has sufficient data for optimization suggestions")
        else:
            print("   ⚠️  More data needed for optimization recommendations")
    
    # Check skill coverage vs success rate
    optimization_recs = agent_comm.optimize_task_distribution()
    skill_gaps = len(optimization_recs.get('skill_gaps', []))
    success_rate = learning_insights['system_health']['success_rate']
    
    if skill_gaps > 5 and success_rate < 0.8:
        print("   🚨 Skill gaps may be impacting success rate")
    elif skill_gaps == 0 and success_rate > 0.9:
        print("   ✅ Good skill coverage correlates with high success rate")
    
    return workload_report, learning_insights

def generate_integrated_improvements(learning_system, agent_comm, workload_report):
    """Generate improvements using both systems"""
    print(f"\n🏗️  INTEGRATED IMPROVEMENT RECOMMENDATIONS")
    print("=" * 50)
    
    # Get improvements from learning system
    learning_improvements = learning_system.generate_architecture_improvements()
    
    # Get optimization recommendations from agent communication
    comm_optimizations = agent_comm.optimize_task_distribution()
    
    print(f"🎯 Learning System Improvements: {len(learning_improvements)}")
    for improvement in learning_improvements[:3]:
        print(f"   • {improvement.title} ({improvement.priority} priority)")
        print(f"     {improvement.description}")
        print()
    
    print(f"🔧 Agent Communication Optimizations:")
    
    # Skill gaps
    if 'skill_gaps' in comm_optimizations:
        print(f"   📚 Skill Gaps ({len(comm_optimizations['skill_gaps'])}):")
        for gap in comm_optimizations['skill_gaps'][:3]:
            print(f"     • {gap['skill']}: {gap['reason']}")
    
    # Underutilized agents
    if 'underutilized_agents' in comm_optimizations:
        print(f"   💤 Underutilized Agents ({len(comm_optimizations['underutilized_agents'])}):")
        for agent in comm_optimizations['underutilized_agents'][:3]:
            print(f"     • {agent}: {workload_report['agents'][agent]['utilization_percent']:.1f}% utilization")
    
    # Create integrated recommendations
    print(f"\n🤝 INTEGRATED RECOMMENDATIONS:")
    
    integrated_recommendations = []
    
    # Combine skill gap analysis
    skill_related_improvements = [imp for imp in learning_improvements 
                                if 'skill' in imp.category.lower()]
    
    if skill_related_improvements and 'skill_gaps' in comm_optimizations:
        integrated_recommendations.append({
            'title': 'Comprehensive Skill Enhancement Program',
            'description': f'Address {len(comm_optimizations["skill_gaps"])} skill gaps identified by agent communication and {len(skill_related_improvements)} skill-related patterns from learning system',
            'priority': 'high',
            'source': 'integrated_analysis'
        })
    
    # Combine load balancing analysis
    load_improvements = [imp for imp in learning_improvements 
                        if 'load' in imp.category.lower() or 'capacity' in imp.category.lower()]
    
    if load_improvements and workload_report['summary']['utilization_percent'] < 60:
        integrated_recommendations.append({
            'title': 'Dynamic Load Balancing Optimization',
            'description': f'Current utilization is {workload_report["summary"]["utilization_percent"]:.1f}% with load balancing issues identified by learning system',
            'priority': 'medium',
            'source': 'integrated_analysis'
        })
    
    # Performance correlation recommendations
    success_rate = learning_system.get_learning_insights()['system_health']['success_rate']
    if success_rate < 0.85 and workload_report['summary']['utilization_percent'] > 80:
        integrated_recommendations.append({
            'title': 'Capacity Expansion for Quality Improvement',
            'description': f'High utilization ({workload_report["summary"]["utilization_percent"]:.1f}%) correlating with reduced success rate ({success_rate:.1%})',
            'priority': 'critical',
            'source': 'integrated_analysis'
        })
    
    for i, rec in enumerate(integrated_recommendations, 1):
        print(f"   {i}. {rec['title']} ({rec['priority']} priority)")
        print(f"      {rec['description']}")
        print()
    
    return integrated_recommendations

def save_integrated_analysis(learning_system, agent_comm, workload_report, learning_insights, integrated_recommendations):
    """Save comprehensive integrated analysis"""
    print(f"\n💾 SAVING INTEGRATED ANALYSIS")
    print("=" * 40)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create comprehensive report
    integrated_report = {
        'timestamp': datetime.now().isoformat(),
        'integration_demo': True,
        'agent_communication_data': {
            'workload_report': workload_report,
            'optimization_recommendations': agent_comm.optimize_task_distribution()
        },
        'learning_system_data': {
            'insights': learning_insights,
            'improvements': [
                {
                    'improvement_id': imp.improvement_id,
                    'title': imp.title,
                    'category': imp.category,
                    'priority': imp.priority,
                    'confidence': imp.confidence
                }
                for imp in learning_system.generate_architecture_improvements()
            ]
        },
        'integrated_recommendations': integrated_recommendations,
        'performance_correlation': {
            'utilization_vs_success_rate': {
                'utilization': workload_report['summary']['utilization_percent'],
                'success_rate': learning_insights['system_health']['success_rate'],
                'correlation_strength': 'moderate' if abs(workload_report['summary']['utilization_percent'] - learning_insights['system_health']['success_rate'] * 100) < 20 else 'weak'
            }
        }
    }
    
    # Save to learning system analysis directory
    report_path = Path('autonomous-agents/learning/analysis') / f'integrated_analysis_{timestamp}.json'
    
    with open(report_path, 'w') as f:
        json.dump(integrated_report, f, indent=2, default=str)
    
    print(f"✅ Integrated analysis saved to: {report_path}")
    
    # Also save a summary
    summary_path = Path('autonomous-agents/learning/analysis') / f'integration_summary_{timestamp}.json'
    
    summary = {
        'integration_timestamp': datetime.now().isoformat(),
        'key_findings': {
            'system_health': learning_insights['system_health']['status'],
            'success_rate': learning_insights['system_health']['success_rate'],
            'utilization': workload_report['summary']['utilization_percent'],
            'patterns_learned': learning_insights['learning_progress']['total_patterns_learned'],
            'improvements_suggested': len(integrated_recommendations)
        },
        'top_recommendations': [rec['title'] for rec in integrated_recommendations[:3]]
    }
    
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"📄 Integration summary saved to: {summary_path}")

def main():
    """Main integration demonstration"""
    print("🚀 KAREN AI INTEGRATED LEARNING DEMONSTRATION")
    print("=" * 60)
    print("This demo shows integration between:")
    print("• Learning System (pattern analysis & improvements)")
    print("• Agent Communication (task routing & optimization)")
    print()
    
    # Run integrated task flow
    learning_system, agent_comm = simulate_integrated_task_flow()
    
    # Analyze performance using both systems
    workload_report, learning_insights = analyze_integrated_performance(learning_system, agent_comm)
    
    # Generate integrated improvements
    integrated_recommendations = generate_integrated_improvements(learning_system, agent_comm, workload_report)
    
    # Save comprehensive analysis
    save_integrated_analysis(learning_system, agent_comm, workload_report, learning_insights, integrated_recommendations)
    
    print("\n🎉 INTEGRATION DEMONSTRATION COMPLETE!")
    print("The learning system and agent communication system work together to:")
    print("• Route tasks optimally")
    print("• Learn from outcomes")
    print("• Generate integrated improvement recommendations")
    print("• Provide comprehensive system insights")

if __name__ == "__main__":
    main() 
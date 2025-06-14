#!/usr/bin/env python3
"""
Learning System Demonstration Script
Shows how the learning system tracks patterns and suggests improvements
"""

import sys
import json
import random
import time
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / 'src'))

from src.learning_system import (
    LearningSystem,
    get_learning_system_instance,
    analyze_agent_task_completion,
    generate_system_improvements,
    get_system_learning_report,
    AgentSkill,
    FailureCategory
)

def generate_sample_task_data():
    """Generate sample task data for demonstration"""
    task_types = ["sms_response", "email_processing", "memory_storage", "phone_call", "test_execution"]
    skills = ["SMS_MANAGEMENT", "EMAIL_HANDLING", "MEMORY_OPERATIONS", "PHONE_SYSTEM", "TESTING"]
    priorities = ["low", "medium", "high", "critical"]
    
    return {
        'task_type': random.choice(task_types),
        'required_skills': random.sample(skills, k=random.randint(1, 3)),
        'priority': random.choice(priorities),
        'complexity': random.choice(['simple', 'moderate', 'complex']),
        'estimated_duration': random.randint(30, 600)  # 30 seconds to 10 minutes
    }

def simulate_task_completions(learning_system: LearningSystem, num_tasks: int = 50):
    """Simulate various task completions for learning"""
    print(f"\n📊 Simulating {num_tasks} task completions...")
    
    agents = ["sms_engineer", "memory_engineer", "test_engineer", "orchestrator", "phone_engineer"]
    
    for i in range(num_tasks):
        task_id = f"demo_task_{i+1:03d}"
        agent = random.choice(agents)
        task_data = generate_sample_task_data()
        
        # Simulate different success rates for different agents
        agent_success_rates = {
            "sms_engineer": 0.9,
            "memory_engineer": 0.85,
            "test_engineer": 0.7,  # Lower success rate for demo
            "orchestrator": 0.95,
            "phone_engineer": 0.8
        }
        
        success = random.random() < agent_success_rates.get(agent, 0.8)
        
        # Simulate completion times (failures tend to take longer)
        if success:
            base_time = task_data['estimated_duration']
            completion_time = base_time + random.uniform(-base_time*0.3, base_time*0.5)
        else:
            # Failed tasks often timeout or take much longer
            completion_time = task_data['estimated_duration'] * random.uniform(1.5, 4.0)
        
        # Add some realistic variance
        completion_time = max(10, completion_time + random.uniform(-30, 60))
        
        # Analyze the task completion
        learning_system.analyze_task_completion(
            task_id=task_id,
            agent=agent,
            success=success,
            completion_time=completion_time,
            task_data=task_data
        )
        
        if i % 10 == 0:
            print(f"  Processed {i+1}/{num_tasks} tasks...")
        
        # Small delay to simulate real-time processing
        time.sleep(0.1)
    
    print(f"✅ Completed simulation of {num_tasks} tasks")

def demonstrate_pattern_analysis(learning_system: LearningSystem):
    """Demonstrate pattern analysis capabilities"""
    print("\n🔍 PATTERN ANALYSIS RESULTS")
    print("=" * 50)
    
    # Get success patterns report
    success_report = learning_system.get_success_patterns_report()
    print(f"\n📈 Success Patterns Discovered: {success_report['total_patterns']}")
    
    if success_report['high_confidence_patterns']:
        print("\n🏆 High Confidence Success Patterns:")
        for pattern in success_report['high_confidence_patterns'][:3]:
            print(f"  • {pattern['description']}")
            print(f"    Success Rate: {pattern['success_rate']:.1%}")
            print(f"    Avg Time: {pattern['avg_completion_time']:.1f}s")
            print(f"    Confidence: {pattern['confidence']:.1%}")
            print(f"    Sample Size: {pattern['sample_size']}")
            print()
    
    # Agent performance analysis
    if success_report['agent_performance_analysis']:
        print("👥 Agent Performance Analysis:")
        for agent, stats in success_report['agent_performance_analysis'].items():
            print(f"  • {agent}:")
            print(f"    Avg Success Rate: {stats['avg_success_rate']:.1%}")
            print(f"    Avg Completion Time: {stats['avg_completion_time']:.1f}s")
            print(f"    Tasks Analyzed: {stats['total_tasks_analyzed']}")
            print()

def demonstrate_failure_analysis(learning_system: LearningSystem):
    """Demonstrate failure analysis capabilities"""
    print("\n⚠️  FAILURE ANALYSIS RESULTS")
    print("=" * 50)
    
    failure_report = learning_system.get_failure_analysis_report()
    print(f"\n📊 Failure Patterns Identified: {failure_report['total_failure_patterns']}")
    
    if failure_report['failure_breakdown']:
        print("\n🔍 Failure Breakdown by Category:")
        for category, stats in failure_report['failure_breakdown'].items():
            print(f"  • {category.replace('_', ' ').title()}:")
            print(f"    Pattern Count: {stats['pattern_count']}")
            print(f"    Total Frequency: {stats['total_frequency']}")
            print(f"    Avg Impact Score: {stats['avg_impact_score']:.1%}")
            print(f"    Affected Agents: {stats['affected_agents']}")
            print()
    
    if failure_report['most_affected_agents']:
        print("🎯 Most Affected Agents:")
        for agent, failure_count in list(failure_report['most_affected_agents'].items())[:3]:
            print(f"  • {agent}: {failure_count} failures")
        print()
    
    if failure_report['critical_issues']:
        print("🚨 Critical Issues Identified:")
        for issue in failure_report['critical_issues'][:2]:
            print(f"  • {issue['description']}")
            print(f"    Frequency: {issue['frequency']}")
            print(f"    Impact Score: {issue['impact_score']:.1%}")
            print(f"    Mitigation: {issue['mitigation_suggestions'][0] if issue['mitigation_suggestions'] else 'None'}")
            print()

def demonstrate_architecture_improvements(learning_system: LearningSystem):
    """Demonstrate architecture improvement suggestions"""
    print("\n🏗️  ARCHITECTURE IMPROVEMENT SUGGESTIONS")
    print("=" * 50)
    
    improvements = learning_system.generate_architecture_improvements()
    print(f"\n💡 Generated {len(improvements)} improvement suggestions")
    
    if improvements:
        # Group by priority
        priority_groups = {}
        for improvement in improvements:
            priority = improvement.priority
            if priority not in priority_groups:
                priority_groups[priority] = []
            priority_groups[priority].append(improvement)
        
        for priority in ['critical', 'high', 'medium', 'low']:
            if priority in priority_groups:
                print(f"\n🎯 {priority.upper()} Priority Improvements:")
                for improvement in priority_groups[priority]:
                    print(f"  • {improvement.title}")
                    print(f"    Category: {improvement.category}")
                    print(f"    Description: {improvement.description}")
                    print(f"    Effort: {improvement.implementation_effort}")
                    print(f"    Timeline: {improvement.suggested_timeline}")
                    print(f"    Confidence: {improvement.confidence:.1%}")
                    print(f"    Benefits: {', '.join(improvement.expected_benefits[:2])}")
                    print()

def demonstrate_learning_insights(learning_system: LearningSystem):
    """Demonstrate comprehensive learning insights"""
    print("\n🧠 COMPREHENSIVE LEARNING INSIGHTS")
    print("=" * 50)
    
    insights = learning_system.get_learning_insights()
    
    # System health
    health = insights['system_health']
    print(f"\n🏥 System Health: {health['status'].upper()}")
    print(f"   Health Score: {health['score']:.1%}")
    print(f"   Success Rate: {health['success_rate']:.1%}")
    print(f"   Total Tasks: {health['total_tasks_analyzed']}")
    
    # Learning progress
    progress = insights['learning_progress']
    print(f"\n📚 Learning Progress:")
    print(f"   Patterns Learned: {progress['total_patterns_learned']}")
    print(f"   Failure Patterns: {progress['failure_patterns_identified']}")
    print(f"   Improvements Suggested: {progress['architecture_improvements_suggested']}")
    print(f"   Data Points Analyzed: {progress['data_points_analyzed']}")
    
    # Top insights
    if insights['top_insights']:
        print(f"\n🔍 Top Insights:")
        for insight in insights['top_insights']:
            print(f"   • {insight}")
    
    # Recommended actions
    if insights['recommended_actions']:
        print(f"\n🎯 Recommended Actions:")
        for action in insights['recommended_actions']:
            print(f"   • {action}")

def save_demonstration_report(learning_system: LearningSystem):
    """Save a comprehensive demonstration report"""
    print("\n💾 Saving demonstration report...")
    
    report_path = learning_system.save_analysis_report("comprehensive")
    
    if report_path:
        print(f"✅ Report saved to: {report_path}")
        
        # Also create a summary file
        summary = {
            'demonstration_timestamp': datetime.now().isoformat(),
            'learning_insights': learning_system.get_learning_insights(),
            'patterns_discovered': len(learning_system.task_patterns),
            'failures_analyzed': len(learning_system.failure_patterns),
            'improvements_suggested': len(learning_system.architecture_improvements)
        }
        
        summary_path = Path(report_path).parent / f"demo_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"📄 Summary saved to: {summary_path}")
    else:
        print("❌ Failed to save report")

def main():
    """Main demonstration function"""
    print("🚀 KAREN AI LEARNING SYSTEM DEMONSTRATION")
    print("=" * 50)
    print("This demo shows how the learning system:")
    print("• Tracks successful task patterns")
    print("• Identifies common failures")
    print("• Suggests architecture improvements")
    print()
    
    # Initialize learning system
    print("🔧 Initializing Learning System...")
    learning_system = get_learning_system_instance()
    
    # Simulate task completions
    simulate_task_completions(learning_system, num_tasks=75)
    
    # Demonstrate all analysis capabilities
    demonstrate_pattern_analysis(learning_system)
    demonstrate_failure_analysis(learning_system)
    demonstrate_architecture_improvements(learning_system)
    demonstrate_learning_insights(learning_system)
    
    # Save demonstration report
    save_demonstration_report(learning_system)
    
    print("\n🎉 DEMONSTRATION COMPLETE!")
    print("The learning system has analyzed task patterns and generated insights.")
    print("Check the autonomous-agents/learning/ directory for saved reports and data.")

if __name__ == "__main__":
    main() 
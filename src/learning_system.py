#!/usr/bin/env python3
"""
Learning System for Karen AI Multi-Agent Architecture
Analyzes patterns, identifies failures, and suggests improvements
"""

import json
import os
import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from pathlib import Path
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import numpy as np
from enum import Enum
import pickle
import hashlib

# Import enhanced agent communication components
from .agent_communication import (
    AgentCommunication, 
    TaskRequest, 
    TaskPriority, 
    AgentSkill,
    AgentPerformanceMetrics
)

# Set up logging
logger = logging.getLogger(__name__)

class PatternType(Enum):
    """Types of patterns the learning system can identify"""
    SUCCESS_PATTERN = "success_pattern"
    FAILURE_PATTERN = "failure_pattern"
    PERFORMANCE_PATTERN = "performance_pattern"
    SKILL_PATTERN = "skill_pattern"
    LOAD_PATTERN = "load_pattern"
    TIMING_PATTERN = "timing_pattern"

class FailureCategory(Enum):
    """Categories of task failures"""
    SKILL_MISMATCH = "skill_mismatch"
    OVERLOAD = "agent_overload"
    TIMEOUT = "task_timeout"
    QUALITY_ISSUE = "quality_issue"
    DEPENDENCY_FAILURE = "dependency_failure"
    RESOURCE_CONSTRAINT = "resource_constraint"
    COORDINATION_FAILURE = "coordination_failure"

@dataclass
class TaskPattern:
    """Represents a learned pattern from task execution"""
    pattern_id: str
    pattern_type: PatternType
    description: str
    conditions: Dict[str, Any]  # Conditions that trigger this pattern
    outcomes: Dict[str, Any]    # Expected outcomes
    confidence: float           # 0.0-1.0 confidence in this pattern
    sample_size: int           # Number of tasks this pattern is based on
    success_rate: float        # Success rate for this pattern
    avg_completion_time: float # Average completion time
    discovered_at: datetime
    last_updated: datetime
    examples: List[str]        # Task IDs that match this pattern

@dataclass
class FailurePattern:
    """Represents a pattern of task failures"""
    pattern_id: str
    failure_category: FailureCategory
    description: str
    triggers: Dict[str, Any]   # What causes this failure
    frequency: int             # How often this failure occurs
    impact_score: float        # 0.0-1.0 severity of this failure type
    affected_agents: List[str] # Agents most affected by this failure
    affected_skills: List[AgentSkill] # Skills most affected
    mitigation_suggestions: List[str] # How to prevent this failure
    discovered_at: datetime
    examples: List[str]        # Task IDs that failed with this pattern

@dataclass
class ArchitectureImprovement:
    """Represents a suggested architecture improvement"""
    improvement_id: str
    category: str              # e.g., "skill_distribution", "load_balancing", "agent_capacity"
    title: str
    description: str
    rationale: str            # Why this improvement is suggested
    expected_benefits: List[str] # Expected outcomes
    implementation_effort: str # "low", "medium", "high"
    priority: str             # "critical", "high", "medium", "low"
    affected_components: List[str] # Which parts of the system would change
    metrics_to_track: List[str] # How to measure success
    suggested_timeline: str   # Implementation timeframe
    confidence: float         # 0.0-1.0 confidence in this suggestion

class LearningSystem:
    """
    Advanced learning system that analyzes agent performance and suggests improvements
    """
    
    def __init__(self, agent_name: str = "learning_system"):
        self.agent_name = agent_name
        self.comm = AgentCommunication(agent_name)
        
        # Initialize directories
        project_root = Path(__file__).parent.parent
        self.learning_dir = project_root / 'autonomous-agents' / 'learning'
        self.analysis_dir = self.learning_dir / 'analysis'
        self.patterns_dir = self.learning_dir / 'patterns'
        self.improvements_dir = self.learning_dir / 'improvements'
        self.models_dir = self.learning_dir / 'models'
        
        self._ensure_directories()
        
        # Learning data storage
        self.task_patterns: Dict[str, TaskPattern] = {}
        self.failure_patterns: Dict[str, FailurePattern] = {}
        self.architecture_improvements: Dict[str, ArchitectureImprovement] = {}
        
        # Analysis caches
        self.performance_history = []
        self.routing_history = []
        self.failure_history = []
        
        # Load existing patterns and data
        self._load_learning_data()
        
        logger.info(f"LearningSystem initialized with {len(self.task_patterns)} patterns")

    def _ensure_directories(self):
        """Create learning system directories"""
        for directory in [self.learning_dir, self.analysis_dir, self.patterns_dir, 
                         self.improvements_dir, self.models_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def _load_learning_data(self):
        """Load existing learning data from files"""
        try:
            # Load task patterns
            patterns_file = self.patterns_dir / 'task_patterns.json'
            if patterns_file.exists():
                with open(patterns_file, 'r') as f:
                    data = json.load(f)
                    for pattern_id, pattern_data in data.items():
                        # Handle datetime deserialization
                        pattern_data['discovered_at'] = datetime.fromisoformat(pattern_data['discovered_at'])
                        pattern_data['last_updated'] = datetime.fromisoformat(pattern_data['last_updated'])
                        pattern_data['pattern_type'] = PatternType(pattern_data['pattern_type'])
                        self.task_patterns[pattern_id] = TaskPattern(**pattern_data)
            
            # Load failure patterns
            failures_file = self.patterns_dir / 'failure_patterns.json'
            if failures_file.exists():
                with open(failures_file, 'r') as f:
                    data = json.load(f)
                    for pattern_id, pattern_data in data.items():
                        pattern_data['discovered_at'] = datetime.fromisoformat(pattern_data['discovered_at'])
                        pattern_data['failure_category'] = FailureCategory(pattern_data['failure_category'])
                        pattern_data['affected_skills'] = [AgentSkill(skill) for skill in pattern_data['affected_skills']]
                        self.failure_patterns[pattern_id] = FailurePattern(**pattern_data)
            
            # Load architecture improvements
            improvements_file = self.improvements_dir / 'suggestions.json'
            if improvements_file.exists():
                with open(improvements_file, 'r') as f:
                    data = json.load(f)
                    for improvement_id, improvement_data in data.items():
                        self.architecture_improvements[improvement_id] = ArchitectureImprovement(**improvement_data)
                        
        except Exception as e:
            logger.error(f"Error loading learning data: {e}")

    def _save_learning_data(self):
        """Save learning data to files"""
        try:
            # Save task patterns
            patterns_file = self.patterns_dir / 'task_patterns.json'
            patterns_data = {}
            for pattern_id, pattern in self.task_patterns.items():
                pattern_dict = asdict(pattern)
                pattern_dict['discovered_at'] = pattern.discovered_at.isoformat()
                pattern_dict['last_updated'] = pattern.last_updated.isoformat()
                pattern_dict['pattern_type'] = pattern.pattern_type.value
                patterns_data[pattern_id] = pattern_dict
            
            with open(patterns_file, 'w') as f:
                json.dump(patterns_data, f, indent=2)
            
            # Save failure patterns
            failures_file = self.patterns_dir / 'failure_patterns.json'
            failures_data = {}
            for pattern_id, pattern in self.failure_patterns.items():
                pattern_dict = asdict(pattern)
                pattern_dict['discovered_at'] = pattern.discovered_at.isoformat()
                pattern_dict['failure_category'] = pattern.failure_category.value
                pattern_dict['affected_skills'] = [skill.value for skill in pattern.affected_skills]
                failures_data[pattern_id] = pattern_dict
            
            with open(failures_file, 'w') as f:
                json.dump(failures_data, f, indent=2)
            
            # Save architecture improvements
            improvements_file = self.improvements_dir / 'suggestions.json'
            improvements_data = {}
            for improvement_id, improvement in self.architecture_improvements.items():
                improvements_data[improvement_id] = asdict(improvement)
            
            with open(improvements_file, 'w') as f:
                json.dump(improvements_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving learning data: {e}")

    def analyze_task_completion(self, task_id: str, agent: str, success: bool, 
                              completion_time: float, task_data: Dict[str, Any]):
        """
        Analyze a completed task and update learning patterns
        """
        logger.info(f"Analyzing task completion: {task_id} by {agent} (success: {success})")
        
        # Record the task completion
        completion_record = {
            'task_id': task_id,
            'agent': agent,
            'success': success,
            'completion_time': completion_time,
            'task_data': task_data,
            'timestamp': datetime.now().isoformat()
        }
        
        if success:
            self.performance_history.append(completion_record)
            self._analyze_success_patterns(completion_record)
        else:
            self.failure_history.append(completion_record)
            self._analyze_failure_patterns(completion_record)
        
        # Limit history size to prevent memory issues
        self.performance_history = self.performance_history[-1000:]
        self.failure_history = self.failure_history[-500:]
        
        # Update patterns and save
        self._update_patterns()
        self._save_learning_data()

    def _analyze_success_patterns(self, completion_record: Dict[str, Any]):
        """Identify patterns in successful task completions"""
        task_data = completion_record['task_data']
        agent = completion_record['agent']
        completion_time = completion_record['completion_time']
        
        # Analyze skill-success patterns
        if 'required_skills' in task_data:
            skills = task_data['required_skills']
            skill_pattern_id = f"skill_success_{hash(tuple(sorted(skills)))}"
            
            if skill_pattern_id not in self.task_patterns:
                self.task_patterns[skill_pattern_id] = TaskPattern(
                    pattern_id=skill_pattern_id,
                    pattern_type=PatternType.SKILL_PATTERN,
                    description=f"Successful completion with skills: {', '.join(skills)}",
                    conditions={'required_skills': skills},
                    outcomes={'success_rate': 1.0, 'avg_completion_time': completion_time},
                    confidence=0.1,  # Low initial confidence
                    sample_size=1,
                    success_rate=1.0,
                    avg_completion_time=completion_time,
                    discovered_at=datetime.now(),
                    last_updated=datetime.now(),
                    examples=[completion_record['task_id']]
                )
            else:
                # Update existing pattern
                pattern = self.task_patterns[skill_pattern_id]
                pattern.sample_size += 1
                pattern.avg_completion_time = (
                    (pattern.avg_completion_time * (pattern.sample_size - 1) + completion_time) 
                    / pattern.sample_size
                )
                pattern.confidence = min(1.0, pattern.sample_size / 10.0)  # Max confidence at 10 samples
                pattern.last_updated = datetime.now()
                pattern.examples.append(completion_record['task_id'])
                
                # Limit examples to last 10
                pattern.examples = pattern.examples[-10:]
        
        # Analyze agent-task type patterns
        if 'task_type' in task_data:
            agent_task_pattern_id = f"agent_task_{agent}_{task_data['task_type']}"
            
            if agent_task_pattern_id not in self.task_patterns:
                self.task_patterns[agent_task_pattern_id] = TaskPattern(
                    pattern_id=agent_task_pattern_id,
                    pattern_type=PatternType.SUCCESS_PATTERN,
                    description=f"Agent {agent} successfully handles {task_data['task_type']} tasks",
                    conditions={'agent': agent, 'task_type': task_data['task_type']},
                    outcomes={'success_rate': 1.0, 'avg_completion_time': completion_time},
                    confidence=0.1,
                    sample_size=1,
                    success_rate=1.0,
                    avg_completion_time=completion_time,
                    discovered_at=datetime.now(),
                    last_updated=datetime.now(),
                    examples=[completion_record['task_id']]
                )
            else:
                # Update existing pattern
                pattern = self.task_patterns[agent_task_pattern_id]
                pattern.sample_size += 1
                pattern.avg_completion_time = (
                    (pattern.avg_completion_time * (pattern.sample_size - 1) + completion_time) 
                    / pattern.sample_size
                )
                pattern.confidence = min(1.0, pattern.sample_size / 10.0)
                pattern.last_updated = datetime.now()
                pattern.examples.append(completion_record['task_id'])
                pattern.examples = pattern.examples[-10:]

    def _analyze_failure_patterns(self, completion_record: Dict[str, Any]):
        """Identify patterns in task failures"""
        task_data = completion_record['task_data']
        agent = completion_record['agent']
        
        # Determine failure category based on available data
        failure_category = self._categorize_failure(completion_record)
        
        # Create or update failure pattern
        failure_pattern_id = f"failure_{failure_category.value}_{agent}"
        
        if failure_pattern_id not in self.failure_patterns:
            self.failure_patterns[failure_pattern_id] = FailurePattern(
                pattern_id=failure_pattern_id,
                failure_category=failure_category,
                description=f"Agent {agent} experiencing {failure_category.value} failures",
                triggers={'agent': agent, 'category': failure_category.value},
                frequency=1,
                impact_score=0.5,  # Default impact
                affected_agents=[agent],
                affected_skills=self._extract_skills_from_task(task_data),
                mitigation_suggestions=self._generate_mitigation_suggestions(failure_category),
                discovered_at=datetime.now(),
                examples=[completion_record['task_id']]
            )
        else:
            # Update existing failure pattern
            pattern = self.failure_patterns[failure_pattern_id]
            pattern.frequency += 1
            pattern.examples.append(completion_record['task_id'])
            pattern.examples = pattern.examples[-10:]
            
            # Increase impact score based on frequency
            pattern.impact_score = min(1.0, pattern.frequency / 20.0)

    def _categorize_failure(self, completion_record: Dict[str, Any]) -> FailureCategory:
        """Categorize the type of failure based on available data"""
        task_data = completion_record['task_data']
        agent = completion_record['agent']
        completion_time = completion_record['completion_time']
        
        # Get agent performance metrics
        agent_metrics = self.comm.performance_metrics.get(agent)
        
        # Check for skill mismatch
        if 'required_skills' in task_data and agent_metrics:
            required_skills = set(task_data['required_skills'])
            agent_skills = set(self.comm.agent_skills.get(agent, []))
            
            if not required_skills.issubset({skill.value for skill in agent_skills}):
                return FailureCategory.SKILL_MISMATCH
        
        # Check for agent overload
        if agent_metrics and agent_metrics.current_load >= agent_metrics.max_concurrent_tasks:
            return FailureCategory.OVERLOAD
        
        # Check for timeout (if completion time is very high)
        if completion_time > 240:  # 4 hours
            return FailureCategory.TIMEOUT
        
        # Default to quality issue
        return FailureCategory.QUALITY_ISSUE

    def _extract_skills_from_task(self, task_data: Dict[str, Any]) -> List[AgentSkill]:
        """Extract skills from task data"""
        if 'required_skills' in task_data:
            try:
                return [AgentSkill(skill) for skill in task_data['required_skills']]
            except ValueError:
                # Handle case where skill string doesn't match enum
                return []
        return []

    def _generate_mitigation_suggestions(self, failure_category: FailureCategory) -> List[str]:
        """Generate suggestions to mitigate specific failure types"""
        suggestions = {
            FailureCategory.SKILL_MISMATCH: [
                "Review and update agent skill definitions",
                "Implement cross-training between agents",
                "Add skill validation before task assignment"
            ],
            FailureCategory.OVERLOAD: [
                "Increase agent capacity limits",
                "Implement better load balancing",
                "Add more agents with similar skills"
            ],
            FailureCategory.TIMEOUT: [
                "Break down large tasks into smaller chunks",
                "Implement timeout warnings and checkpoints",
                "Review task complexity estimation"
            ],
            FailureCategory.QUALITY_ISSUE: [
                "Implement code review processes",
                "Add automated quality checks",
                "Provide additional training materials"
            ],
            FailureCategory.DEPENDENCY_FAILURE: [
                "Implement retry mechanisms with exponential backoff",
                "Add health checks for external dependencies",
                "Create fallback mechanisms"
            ],
            FailureCategory.RESOURCE_CONSTRAINT: [
                "Monitor resource usage and set alerts",
                "Implement resource throttling",
                "Scale system resources"
            ],
            FailureCategory.COORDINATION_FAILURE: [
                "Improve inter-agent communication protocols",
                "Add coordination timeouts and retries",
                "Implement conflict resolution mechanisms"
            ]
        }
        
        return suggestions.get(failure_category, ["Review task execution process"])

    def _update_patterns(self):
        """Update pattern confidence and cleanup old patterns"""
        current_time = datetime.now()
        
        # Update confidence scores based on recent performance
        for pattern in self.task_patterns.values():
            # Decay confidence for old patterns
            days_since_update = (current_time - pattern.last_updated).days
            if days_since_update > 30:
                pattern.confidence *= 0.9  # Decay confidence by 10%
        
        # Remove patterns with very low confidence
        low_confidence_patterns = [
            pattern_id for pattern_id, pattern in self.task_patterns.items()
            if pattern.confidence < 0.1 and pattern.sample_size < 3
        ]
        
        for pattern_id in low_confidence_patterns:
            del self.task_patterns[pattern_id]
        
        logger.debug(f"Updated patterns, removed {len(low_confidence_patterns)} low-confidence patterns")

    def generate_architecture_improvements(self) -> List[ArchitectureImprovement]:
        """
        Analyze patterns and generate architecture improvement suggestions
        """
        logger.info("Generating architecture improvement suggestions")
        
        improvements = []
        
        # Analyze skill distribution
        improvements.extend(self._analyze_skill_distribution())
        
        # Analyze load balancing effectiveness
        improvements.extend(self._analyze_load_balancing())
        
        # Analyze failure patterns for systemic issues
        improvements.extend(self._analyze_systemic_failures())
        
        # Analyze performance trends
        improvements.extend(self._analyze_performance_trends())
        
        # Update stored improvements
        for improvement in improvements:
            self.architecture_improvements[improvement.improvement_id] = improvement
        
        self._save_learning_data()
        
        return improvements

    def _analyze_skill_distribution(self) -> List[ArchitectureImprovement]:
        """Analyze skill distribution and suggest improvements"""
        improvements = []
        
        # Get current skill coverage
        workload_report = self.comm.get_agent_workload_report()
        optimization_recommendations = self.comm.optimize_task_distribution()
        
        # Check for critical skill gaps
        critical_gaps = [
            gap for gap in optimization_recommendations.get('skill_gaps', [])
            if gap['reason'] == 'low_coverage'
        ]
        
        if critical_gaps:
            improvements.append(ArchitectureImprovement(
                improvement_id="skill_coverage_enhancement",
                category="skill_distribution",
                title="Address Critical Skill Coverage Gaps",
                description=f"System has {len(critical_gaps)} skills with insufficient coverage",
                rationale="Multiple skills have fewer than 2 agents, creating single points of failure",
                expected_benefits=[
                    "Improved system resilience",
                    "Better task distribution",
                    "Reduced bottlenecks"
                ],
                implementation_effort="medium",
                priority="high",
                affected_components=["agent_skills", "task_routing"],
                metrics_to_track=["skill_coverage_percentage", "task_assignment_success_rate"],
                suggested_timeline="2-3 weeks",
                confidence=0.8
            ))
        
        # Check for expertise issues
        low_expertise_skills = [
            gap for gap in optimization_recommendations.get('skill_gaps', [])
            if gap['reason'] == 'low_expertise'
        ]
        
        if low_expertise_skills:
            improvements.append(ArchitectureImprovement(
                improvement_id="skill_expertise_improvement",
                category="skill_development",
                title="Improve Agent Skill Expertise",
                description=f"System has {len(low_expertise_skills)} skills with low expertise ratings",
                rationale="Low skill ratings indicate agents need additional training or experience",
                expected_benefits=[
                    "Higher task success rates",
                    "Faster completion times",
                    "Better quality outcomes"
                ],
                implementation_effort="high",
                priority="medium",
                affected_components=["agent_training", "skill_ratings"],
                metrics_to_track=["average_skill_rating", "task_success_rate"],
                suggested_timeline="4-6 weeks",
                confidence=0.7
            ))
        
        return improvements

    def _analyze_load_balancing(self) -> List[ArchitectureImprovement]:
        """Analyze load balancing effectiveness"""
        improvements = []
        
        workload_report = self.comm.get_agent_workload_report()
        agents = workload_report.get('agents', {})
        
        # Check for load imbalances
        utilizations = [data['utilization_percent'] for data in agents.values()]
        
        if utilizations:
            avg_utilization = statistics.mean(utilizations)
            utilization_variance = statistics.variance(utilizations) if len(utilizations) > 1 else 0
            
            # High variance indicates poor load balancing
            if utilization_variance > 400:  # Standard deviation > 20%
                improvements.append(ArchitectureImprovement(
                    improvement_id="load_balancing_optimization",
                    category="load_balancing",
                    title="Optimize Load Distribution",
                    description=f"High variance in agent utilization (variance: {utilization_variance:.1f})",
                    rationale="Uneven load distribution leads to bottlenecks and inefficient resource usage",
                    expected_benefits=[
                        "More even resource utilization",
                        "Reduced system bottlenecks",
                        "Improved overall throughput"
                    ],
                    implementation_effort="medium",
                    priority="high",
                    affected_components=["task_routing", "load_balancer"],
                    metrics_to_track=["utilization_variance", "average_response_time"],
                    suggested_timeline="2-3 weeks",
                    confidence=0.8
                ))
            
            # Check for overall low utilization
            if avg_utilization < 30:
                improvements.append(ArchitectureImprovement(
                    improvement_id="capacity_optimization",
                    category="capacity_management",
                    title="Optimize System Capacity",
                    description=f"Low average utilization ({avg_utilization:.1f}%) suggests over-provisioning",
                    rationale="Low utilization indicates potential for capacity reduction or increased workload",
                    expected_benefits=[
                        "Better resource efficiency",
                        "Cost optimization",
                        "Right-sized system capacity"
                    ],
                    implementation_effort="low",
                    priority="medium",
                    affected_components=["agent_capacity", "system_scaling"],
                    metrics_to_track=["average_utilization", "cost_per_task"],
                    suggested_timeline="1-2 weeks",
                    confidence=0.6
                ))
        
        return improvements

    def _analyze_systemic_failures(self) -> List[ArchitectureImprovement]:
        """Analyze failure patterns for systemic issues"""
        improvements = []
        
        # Group failures by category
        failure_counts = Counter()
        for pattern in self.failure_patterns.values():
            failure_counts[pattern.failure_category] += pattern.frequency
        
        # Identify most common failure types
        if failure_counts:
            most_common_failure = failure_counts.most_common(1)[0]
            failure_type, count = most_common_failure
            
            if count > 5:  # Significant number of failures
                improvements.append(ArchitectureImprovement(
                    improvement_id=f"address_{failure_type.value}_failures",
                    category="reliability",
                    title=f"Address {failure_type.value.replace('_', ' ').title()} Issues",
                    description=f"System experiencing {count} instances of {failure_type.value} failures",
                    rationale=f"{failure_type.value} is the most common failure type, indicating systemic issues",
                    expected_benefits=[
                        "Reduced failure rate",
                        "Improved system reliability",
                        "Better user experience"
                    ],
                    implementation_effort="high",
                    priority="critical",
                    affected_components=self._get_components_for_failure_type(failure_type),
                    metrics_to_track=["failure_rate", "system_uptime", "task_success_rate"],
                    suggested_timeline="3-4 weeks",
                    confidence=0.9
                ))
        
        return improvements

    def _analyze_performance_trends(self) -> List[ArchitectureImprovement]:
        """Analyze performance trends and suggest improvements"""
        improvements = []
        
        if len(self.performance_history) < 10:
            return improvements  # Need more data for trend analysis
        
        # Analyze completion time trends
        recent_times = [record['completion_time'] for record in self.performance_history[-20:]]
        older_times = [record['completion_time'] for record in self.performance_history[-40:-20]]
        
        if older_times:
            recent_avg = statistics.mean(recent_times)
            older_avg = statistics.mean(older_times)
            
            # Check if performance is degrading
            if recent_avg > older_avg * 1.2:  # 20% increase in completion time
                improvements.append(ArchitectureImprovement(
                    improvement_id="performance_degradation_investigation",
                    category="performance",
                    title="Investigate Performance Degradation",
                    description=f"Average completion time increased by {((recent_avg/older_avg - 1) * 100):.1f}%",
                    rationale="Increasing completion times indicate potential performance bottlenecks",
                    expected_benefits=[
                        "Restored system performance",
                        "Better user experience",
                        "Increased throughput"
                    ],
                    implementation_effort="medium",
                    priority="high",
                    affected_components=["performance_monitoring", "bottleneck_analysis"],
                    metrics_to_track=["average_completion_time", "system_throughput"],
                    suggested_timeline="2-3 weeks",
                    confidence=0.7
                ))
        
        return improvements

    def _get_components_for_failure_type(self, failure_type: FailureCategory) -> List[str]:
        """Get system components most relevant to a failure type"""
        component_mapping = {
            FailureCategory.SKILL_MISMATCH: ["skill_system", "task_routing", "agent_capabilities"],
            FailureCategory.OVERLOAD: ["load_balancer", "capacity_management", "scaling_system"],
            FailureCategory.TIMEOUT: ["task_management", "timeout_handling", "progress_monitoring"],
            FailureCategory.QUALITY_ISSUE: ["quality_assurance", "testing_system", "code_review"],
            FailureCategory.DEPENDENCY_FAILURE: ["dependency_management", "external_integrations"],
            FailureCategory.RESOURCE_CONSTRAINT: ["resource_management", "system_monitoring"],
            FailureCategory.COORDINATION_FAILURE: ["agent_communication", "coordination_protocols"]
        }
        
        return component_mapping.get(failure_type, ["system_core"])

    def get_success_patterns_report(self) -> Dict[str, Any]:
        """Generate a comprehensive report of successful task patterns"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_patterns': len(self.task_patterns),
            'high_confidence_patterns': [],
            'skill_success_analysis': {},
            'agent_performance_analysis': {},
            'recommendations': []
        }
        
        # High confidence patterns
        high_confidence = [
            pattern for pattern in self.task_patterns.values()
            if pattern.confidence > 0.7 and pattern.sample_size >= 5
        ]
        
        for pattern in high_confidence:
            report['high_confidence_patterns'].append({
                'pattern_id': pattern.pattern_id,
                'description': pattern.description,
                'success_rate': pattern.success_rate,
                'avg_completion_time': pattern.avg_completion_time,
                'confidence': pattern.confidence,
                'sample_size': pattern.sample_size
            })
        
        # Skill success analysis
        skill_patterns = [p for p in self.task_patterns.values() if p.pattern_type == PatternType.SKILL_PATTERN]
        for pattern in skill_patterns:
            if 'required_skills' in pattern.conditions:
                skills_key = ', '.join(sorted(pattern.conditions['required_skills']))
                report['skill_success_analysis'][skills_key] = {
                    'success_rate': pattern.success_rate,
                    'avg_completion_time': pattern.avg_completion_time,
                    'sample_size': pattern.sample_size,
                    'confidence': pattern.confidence
                }
        
        # Agent performance analysis
        agent_patterns = [p for p in self.task_patterns.values() if p.pattern_type == PatternType.SUCCESS_PATTERN]
        agent_stats = defaultdict(list)
        
        for pattern in agent_patterns:
            if 'agent' in pattern.conditions:
                agent = pattern.conditions['agent']
                agent_stats[agent].append(pattern)
        
        for agent, patterns in agent_stats.items():
            avg_success_rate = statistics.mean([p.success_rate for p in patterns])
            avg_completion_time = statistics.mean([p.avg_completion_time for p in patterns])
            total_samples = sum([p.sample_size for p in patterns])
            
            report['agent_performance_analysis'][agent] = {
                'avg_success_rate': avg_success_rate,
                'avg_completion_time': avg_completion_time,
                'total_tasks_analyzed': total_samples,
                'pattern_count': len(patterns)
            }
        
        return report

    def get_failure_analysis_report(self) -> Dict[str, Any]:
        """Generate a comprehensive failure analysis report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_failure_patterns': len(self.failure_patterns),
            'failure_breakdown': {},
            'most_affected_agents': {},
            'critical_issues': [],
            'mitigation_summary': {}
        }
        
        # Failure breakdown by category
        category_stats = defaultdict(list)
        for pattern in self.failure_patterns.values():
            category_stats[pattern.failure_category.value].append(pattern)
        
        for category, patterns in category_stats.items():
            total_frequency = sum([p.frequency for p in patterns])
            avg_impact = statistics.mean([p.impact_score for p in patterns])
            
            report['failure_breakdown'][category] = {
                'pattern_count': len(patterns),
                'total_frequency': total_frequency,
                'avg_impact_score': avg_impact,
                'affected_agents': len(set().union(*[p.affected_agents for p in patterns]))
            }
        
        # Most affected agents
        agent_failure_counts = defaultdict(int)
        for pattern in self.failure_patterns.values():
            for agent in pattern.affected_agents:
                agent_failure_counts[agent] += pattern.frequency
        
        report['most_affected_agents'] = dict(
            sorted(agent_failure_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        )
        
        # Critical issues (high impact, high frequency)
        critical_patterns = [
            p for p in self.failure_patterns.values()
            if p.impact_score > 0.7 and p.frequency > 3
        ]
        
        for pattern in critical_patterns:
            report['critical_issues'].append({
                'pattern_id': pattern.pattern_id,
                'description': pattern.description,
                'frequency': pattern.frequency,
                'impact_score': pattern.impact_score,
                'affected_agents': pattern.affected_agents,
                'mitigation_suggestions': pattern.mitigation_suggestions
            })
        
        # Mitigation summary
        all_suggestions = []
        for pattern in self.failure_patterns.values():
            all_suggestions.extend(pattern.mitigation_suggestions)
        
        suggestion_counts = Counter(all_suggestions)
        report['mitigation_summary'] = dict(suggestion_counts.most_common(10))
        
        return report

    def get_learning_insights(self) -> Dict[str, Any]:
        """Get comprehensive learning insights and recommendations"""
        return {
            'timestamp': datetime.now().isoformat(),
            'system_health': self._calculate_system_health(),
            'learning_progress': {
                'total_patterns_learned': len(self.task_patterns),
                'failure_patterns_identified': len(self.failure_patterns),
                'architecture_improvements_suggested': len(self.architecture_improvements),
                'data_points_analyzed': len(self.performance_history) + len(self.failure_history)
            },
            'top_insights': self._get_top_insights(),
            'recommended_actions': self._get_recommended_actions(),
            'confidence_metrics': self._calculate_confidence_metrics()
        }

    def _calculate_system_health(self) -> Dict[str, Any]:
        """Calculate overall system health metrics"""
        if not self.performance_history and not self.failure_history:
            return {'status': 'insufficient_data', 'score': 0.5}
        
        total_tasks = len(self.performance_history) + len(self.failure_history)
        success_rate = len(self.performance_history) / total_tasks if total_tasks > 0 else 0
        
        # Calculate average completion time for successful tasks
        avg_completion_time = (
            statistics.mean([record['completion_time'] for record in self.performance_history])
            if self.performance_history else 0
        )
        
        # Health score based on success rate and completion time
        health_score = success_rate * 0.7 + (1.0 / (1.0 + avg_completion_time / 60.0)) * 0.3
        
        status = 'excellent' if health_score > 0.8 else \
                'good' if health_score > 0.6 else \
                'fair' if health_score > 0.4 else 'poor'
        
        return {
            'status': status,
            'score': health_score,
            'success_rate': success_rate,
            'avg_completion_time_minutes': avg_completion_time,
            'total_tasks_analyzed': total_tasks
        }

    def _get_top_insights(self) -> List[str]:
        """Get the most important insights discovered"""
        insights = []
        
        # Top performing patterns
        top_patterns = sorted(
            [p for p in self.task_patterns.values() if p.confidence > 0.5],
            key=lambda x: x.success_rate * x.confidence,
            reverse=True
        )[:3]
        
        for pattern in top_patterns:
            insights.append(f"High-performing pattern: {pattern.description} "
                          f"(success rate: {pattern.success_rate:.1%}, confidence: {pattern.confidence:.1%})")
        
        # Most critical failures
        critical_failures = sorted(
            self.failure_patterns.values(),
            key=lambda x: x.impact_score * x.frequency,
            reverse=True
        )[:2]
        
        for failure in critical_failures:
            insights.append(f"Critical issue: {failure.description} "
                          f"(frequency: {failure.frequency}, impact: {failure.impact_score:.1%})")
        
        return insights

    def _get_recommended_actions(self) -> List[str]:
        """Get recommended actions based on analysis"""
        actions = []
        
        # Based on architecture improvements
        high_priority_improvements = [
            improvement for improvement in self.architecture_improvements.values()
            if improvement.priority in ['critical', 'high']
        ]
        
        for improvement in high_priority_improvements[:3]:
            actions.append(f"{improvement.title}: {improvement.description}")
        
        # Based on failure patterns
        if self.failure_patterns:
            most_common_failure = max(self.failure_patterns.values(), key=lambda x: x.frequency)
            actions.append(f"Address {most_common_failure.failure_category.value}: "
                         f"{most_common_failure.mitigation_suggestions[0] if most_common_failure.mitigation_suggestions else 'Investigate further'}")
        
        return actions[:5]  # Limit to top 5 actions

    def _calculate_confidence_metrics(self) -> Dict[str, float]:
        """Calculate confidence metrics for the learning system"""
        if not self.task_patterns:
            return {'overall_confidence': 0.0}
        
        pattern_confidences = [pattern.confidence for pattern in self.task_patterns.values()]
        sample_sizes = [pattern.sample_size for pattern in self.task_patterns.values()]
        
        return {
            'overall_confidence': statistics.mean(pattern_confidences),
            'avg_pattern_confidence': statistics.mean(pattern_confidences),
            'max_pattern_confidence': max(pattern_confidences),
            'avg_sample_size': statistics.mean(sample_sizes),
            'total_data_points': sum(sample_sizes)
        }

    def save_analysis_report(self, report_type: str = "comprehensive") -> str:
        """Save a comprehensive analysis report to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.analysis_dir / f"learning_analysis_{report_type}_{timestamp}.json"
        
        if report_type == "comprehensive":
            report = {
                'learning_insights': self.get_learning_insights(),
                'success_patterns': self.get_success_patterns_report(),
                'failure_analysis': self.get_failure_analysis_report(),
                'architecture_improvements': [
                    asdict(improvement) for improvement in self.architecture_improvements.values()
                ]
            }
        elif report_type == "success":
            report = self.get_success_patterns_report()
        elif report_type == "failures":
            report = self.get_failure_analysis_report()
        else:
            report = self.get_learning_insights()
        
        try:
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Analysis report saved to {report_file}")
            return str(report_file)
        except Exception as e:
            logger.error(f"Error saving analysis report: {e}")
            return ""


def get_learning_system_instance() -> LearningSystem:
    """Get a singleton instance of the learning system"""
    if not hasattr(get_learning_system_instance, '_instance'):
        get_learning_system_instance._instance = LearningSystem()
    return get_learning_system_instance._instance


# Example usage functions
def analyze_agent_task_completion(task_id: str, agent: str, success: bool, 
                                completion_time: float, task_data: Dict[str, Any]):
    """Convenience function to analyze task completion"""
    learning_system = get_learning_system_instance()
    learning_system.analyze_task_completion(task_id, agent, success, completion_time, task_data)


def generate_system_improvements() -> List[ArchitectureImprovement]:
    """Convenience function to generate architecture improvements"""
    learning_system = get_learning_system_instance()
    return learning_system.generate_architecture_improvements()


def get_system_learning_report() -> Dict[str, Any]:
    """Convenience function to get comprehensive learning report"""
    learning_system = get_learning_system_instance()
    return learning_system.get_learning_insights() 
# Enhanced Agent Communication System

## Overview

The Karen AI Agent Communication system has been significantly enhanced with advanced capabilities for **skill-based task routing**, **intelligent load balancing**, and **dynamic priority adjustment**. These enhancements enable the multi-agent system to operate more efficiently, distribute work optimally, and adapt to changing conditions automatically.

## 🎯 Key Features

### 1. Skill-Based Task Routing
- **Agent Skill Mapping**: Each agent has defined skills and ratings
- **Task Skill Requirements**: Tasks specify required skills and importance weights
- **Intelligent Matching**: Advanced algorithms match tasks to best-suited agents
- **Skill Rating Evolution**: Agent skills improve/decline based on performance

### 2. Load Balancing
- **Real-time Load Monitoring**: Track current workload for each agent
- **Capacity Management**: Respect agent capacity limits
- **Performance-Based Routing**: Consider agent performance history
- **System Load Awareness**: Adjust routing based on overall system load

### 3. Dynamic Priority Adjustment
- **Age-Based Escalation**: Old tasks automatically get higher priority
- **Deadline Urgency**: Tasks near deadline get priority boost
- **System Load Adaptation**: Adjust priorities based on system capacity
- **Smart Retry Logic**: Failed tasks get escalated appropriately

## 🏗️ Architecture Components

### Core Classes

#### `TaskPriority` Enum
```python
class TaskPriority(Enum):
    CRITICAL = 1  # Urgent system issues, deadlines < 1 hour
    HIGH = 2      # Important features, deadlines < 24 hours  
    MEDIUM = 3    # Standard development tasks
    LOW = 4       # Documentation, cleanup tasks
```

#### `AgentSkill` Enum
```python
class AgentSkill(Enum):
    # Technical Skills
    NLP_PROCESSING = "nlp_processing"
    SMS_INTEGRATION = "sms_integration"
    EMAIL_PROCESSING = "email_processing"
    VOICE_PROCESSING = "voice_processing"
    CALENDAR_MANAGEMENT = "calendar_management"
    MEMORY_MANAGEMENT = "memory_management"
    
    # Development Skills
    PYTHON_DEVELOPMENT = "python_development"
    API_INTEGRATION = "api_integration"
    DATABASE_OPERATIONS = "database_operations"
    TESTING_AUTOMATION = "testing_automation"
    CODE_ANALYSIS = "code_analysis"
    DOCUMENTATION = "documentation"
    
    # System Skills
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    ERROR_HANDLING = "error_handling"
    SECURITY_AUDIT = "security_audit"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"
    
    # Coordination Skills
    TASK_ORCHESTRATION = "task_orchestration"
    INTER_AGENT_COORDINATION = "inter_agent_coordination"
    WORKFLOW_MANAGEMENT = "workflow_management"
```

#### `AgentPerformanceMetrics` Dataclass
```python
@dataclass
class AgentPerformanceMetrics:
    agent_name: str
    tasks_completed: int = 0
    tasks_failed: int = 0
    average_completion_time: float = 0.0
    last_activity: Optional[datetime] = None
    success_rate: float = 1.0
    current_load: int = 0
    max_concurrent_tasks: int = 3
    response_time_avg: float = 0.0
    skill_ratings: Dict[str, float] = None  # skill -> rating (0.0-1.0)
```

#### `TaskRequest` Dataclass
```python
@dataclass
class TaskRequest:
    task_id: str
    task_type: str
    description: str
    priority: TaskPriority
    required_skills: List[AgentSkill]
    estimated_duration: int  # minutes
    deadline: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = None
    skill_weights: Dict[AgentSkill, float] = None  # skill importance weighting
```

## 🎮 Usage Examples

### Basic Task Routing

```python
from src.agent_communication import (
    AgentCommunication, TaskRequest, TaskPriority, AgentSkill
)
from datetime import datetime, timedelta

# Initialize communication system
orchestrator = AgentCommunication('orchestrator')

# Create a task with skill requirements
task = TaskRequest(
    task_id="SMS_FEATURE_001",
    task_type="implement_sms_threading",
    description="Implement SMS conversation threading system",
    priority=TaskPriority.HIGH,
    required_skills=[
        AgentSkill.SMS_INTEGRATION,
        AgentSkill.NLP_PROCESSING,
        AgentSkill.PYTHON_DEVELOPMENT
    ],
    estimated_duration=120,  # 2 hours
    deadline=datetime.now() + timedelta(hours=6),
    skill_weights={
        AgentSkill.SMS_INTEGRATION: 2.0,    # Most important
        AgentSkill.NLP_PROCESSING: 1.5,     # Important
        AgentSkill.PYTHON_DEVELOPMENT: 1.0  # Standard
    }
)

# Route task to best available agent
selected_agent = orchestrator.find_best_agent_for_task(task)
print(f"Task routed to: {selected_agent}")
```

### Advanced Load Balancing

```python
# Route task with automatic load balancing and priority adjustment
selected_agent = orchestrator.route_task_with_load_balancing(task)

# Get comprehensive workload report
workload_report = orchestrator.get_agent_workload_report()
print(f"System Load: {workload_report['system_load_percent']}%")

for agent, data in workload_report['agents'].items():
    print(f"{agent}: {data['utilization_percent']}% ({data['availability']})")
```

### Performance Tracking

```python
# Update agent performance after task completion
orchestrator.update_agent_performance(
    agent='sms_engineer',
    task_id='SMS_FEATURE_001',
    success=True,
    completion_time=95.0,  # minutes
    skill_used=[AgentSkill.SMS_INTEGRATION, AgentSkill.PYTHON_DEVELOPMENT]
)

# Get optimization recommendations
recommendations = orchestrator.optimize_task_distribution()
print("Overloaded agents:", recommendations['overloaded_agents'])
print("Skill gaps:", recommendations['skill_gaps'])
```

## 🧮 Routing Algorithm

### Agent Selection Process

The system uses a sophisticated scoring algorithm to select the best agent for each task:

```python
def _calculate_agent_score(self, agent: str, task_request: TaskRequest) -> float:
    """
    Score components:
    1. Skill match quality (40%)
    2. Load balancing factor (25%) 
    3. Performance history (20%)
    4. Response time factor (15%)
    Plus priority and deadline boost multipliers
    """
    
    # 1. Skill match score based on overlap and ratings
    skill_score = self._calculate_skill_match_score(agent, task_request)
    
    # 2. Load balancing (prefer less loaded agents)
    load_factor = 1.0 - (current_load / max_capacity)
    
    # 3. Performance score (success rate + completion time)
    performance_score = (success_rate + time_efficiency) / 2
    
    # 4. Response time score (faster is better)
    response_score = baseline_time / actual_response_time
    
    # 5. Priority boost for urgent tasks
    priority_boost = 1.3 if CRITICAL else 1.1 if HIGH else 1.0
    
    # 6. Deadline urgency boost
    deadline_boost = 1.4 if <2h else 1.2 if <24h else 1.0
    
    # Final weighted score
    final_score = (
        skill_score * 0.40 +
        load_factor * 0.25 +
        performance_score * 0.20 +
        response_score * 0.15
    ) * priority_boost * deadline_boost
    
    return final_score
```

### Skill Matching Algorithm

```python
def _calculate_skill_match_score(self, agent: str, task_request: TaskRequest) -> float:
    """Calculate skill match quality"""
    
    # Base score: percentage of required skills the agent has
    skill_overlap = len(agent_skills ∩ required_skills)
    base_score = skill_overlap / len(required_skills)
    
    # Enhanced score: weighted by skill ratings and task importance
    weighted_score = 0.0
    total_weight = 0.0
    
    for skill in required_skills:
        skill_rating = agent.skill_ratings.get(skill, 0.5)  # 0.0-1.0
        skill_weight = task.skill_weights.get(skill, 1.0)   # task importance
        
        weighted_score += skill_rating * skill_weight
        total_weight += skill_weight
    
    enhanced_score = weighted_score / total_weight
    
    # Combine base and enhanced scores
    return (base_score + enhanced_score) / 2
```

## 🔄 Dynamic Priority Adjustment

### Age-Based Escalation
```python
def _adjust_task_priority(self, task_request: TaskRequest) -> TaskRequest:
    """Automatically escalate priority for old tasks"""
    
    task_age_hours = (now - task.created_at).total_seconds() / 3600
    
    if task_age_hours > 24 and priority != CRITICAL:
        if priority == LOW:
            task.priority = MEDIUM
        elif priority == MEDIUM:
            task.priority = HIGH  
        elif priority == HIGH:
            task.priority = CRITICAL
        
        log(f"Escalated task {task.id} priority due to age")
    
    return task_request
```

### Deadline-Based Escalation
```python
# Escalate to CRITICAL if deadline < 1 hour
if task.deadline:
    time_until_deadline = (task.deadline - now).total_seconds() / 3600
    if time_until_deadline < 1 and priority != CRITICAL:
        task.priority = CRITICAL
        log(f"Escalated task {task.id} to CRITICAL due to imminent deadline")
```

### System Load Adaptation
```python
def _calculate_system_load(self) -> float:
    """Calculate overall system utilization"""
    total_load = sum(agent.current_load for agent in all_agents)
    total_capacity = sum(agent.max_concurrent_tasks for agent in all_agents)
    return total_load / total_capacity
```

## 📊 Performance Tracking & Analytics

### Skill Rating Evolution

Agent skill ratings evolve based on task performance:

```python
def update_agent_performance(self, agent: str, task_id: str, success: bool, 
                            completion_time: float, skills_used: List[AgentSkill]):
    """Update performance metrics and skill ratings"""
    
    # Update basic metrics
    if success:
        metrics.tasks_completed += 1
        # Improve skill ratings on successful completion
        for skill in skills_used:
            current_rating = metrics.skill_ratings.get(skill.value, 0.5)
            improvement = 0.05 if fast_completion else 0.02
            new_rating = min(1.0, current_rating + improvement)
            metrics.skill_ratings[skill.value] = new_rating
    else:
        metrics.tasks_failed += 1
        # Slightly decrease ratings on failure
        for skill in skills_used:
            current_rating = metrics.skill_ratings.get(skill.value, 0.5)
            new_rating = max(0.1, current_rating - 0.03)
            metrics.skill_ratings[skill.value] = new_rating
    
    # Update success rate and completion time
    metrics.success_rate = tasks_completed / (tasks_completed + tasks_failed)
    metrics.average_completion_time = exponential_moving_average(completion_time)
```

### Workload Analytics

```python
def get_agent_workload_report(self) -> Dict[str, Dict]:
    """Generate comprehensive workload analytics"""
    
    for agent, metrics in self.performance_metrics.items():
        utilization = metrics.current_load / metrics.max_concurrent_tasks
        
        report[agent] = {
            'utilization_percent': round(utilization * 100, 1),
            'success_rate': round(metrics.success_rate, 3),
            'avg_completion_time_min': round(metrics.average_completion_time, 1),
            'performance_trend': 'excellent' if success_rate > 0.9 else
                               'good' if success_rate > 0.7 else
                               'fair' if success_rate > 0.5 else 'poor',
            'availability': 'available' if utilization < 0.8 else
                          'busy' if utilization < 1.0 else 'overloaded',
            'top_skills': get_top_rated_skills(metrics, top_n=3)
        }
    
    return report
```

## 🔧 System Optimization

### Automatic Optimization Recommendations

```python
def optimize_task_distribution(self) -> Dict[str, List[str]]:
    """Analyze system and provide optimization recommendations"""
    
    recommendations = {
        'overloaded_agents': [],      # Agents with >90% utilization
        'underutilized_agents': [],   # Agents with <30% utilization  
        'skill_gaps': [],             # Skills with low coverage/ratings
        'skill_coverage': {}          # Coverage analysis per skill
    }
    
    # Identify workload imbalances
    for agent, data in workload_report['agents'].items():
        if data['utilization_percent'] > 90:
            recommendations['overloaded_agents'].append(agent)
        elif data['utilization_percent'] < 30:
            recommendations['underutilized_agents'].append(agent)
    
    # Analyze skill coverage
    for skill in AgentSkill:
        agents_with_skill = [agent for agent, skills in agent_skills.items() 
                           if skill in skills]
        
        if len(agents_with_skill) < 2:  # Low coverage
            recommendations['skill_gaps'].append({
                'skill': skill.value,
                'reason': 'low_coverage',
                'agents': len(agents_with_skill)
            })
        elif max_skill_rating < 0.6:  # Low expertise
            recommendations['skill_gaps'].append({
                'skill': skill.value, 
                'reason': 'low_expertise',
                'max_rating': max_skill_rating
            })
    
    return recommendations
```

## 📁 File System Organization

The enhanced system creates the following directory structure:

```
autonomous-agents/communication/
├── inbox/                    # Agent message inboxes
│   ├── orchestrator/
│   ├── sms_engineer/
│   └── ...
├── status/                   # Agent status files
├── knowledge-base/           # Shared knowledge
├── skills/                   # 🆕 Agent skill definitions
│   └── agent_skills.json
├── performance/              # 🆕 Performance metrics
│   └── agent_metrics.json
└── routing/                  # 🆕 Routing decisions & analysis
    ├── routing_20241204.json
    └── optimization_recommendations_*.json
```

## 🚀 Getting Started

### 1. Initialize Enhanced Communication

```python
from src.agent_communication import AgentCommunication

# Each agent initializes with enhanced features
comm = AgentCommunication('your_agent_name')

# The system automatically:
# - Loads/creates agent skill mappings
# - Initializes performance tracking
# - Sets up routing cache
# - Creates required directories
```

### 2. Define Agent Skills

```python
# Skills are automatically initialized from defaults, or you can customize:
custom_skills = {
    'my_new_agent': [
        AgentSkill.API_INTEGRATION,
        AgentSkill.PYTHON_DEVELOPMENT,
        AgentSkill.TESTING_AUTOMATION
    ]
}

# Skills are automatically saved and loaded from files
```

### 3. Route Tasks

```python
# Create task with skill requirements
task = TaskRequest(
    task_id="UNIQUE_TASK_ID",
    task_type="implementation",
    description="Task description",
    priority=TaskPriority.HIGH,
    required_skills=[AgentSkill.SMS_INTEGRATION],
    estimated_duration=60
)

# Route with full optimization
selected_agent = comm.route_task_with_load_balancing(task)
```

### 4. Track Performance

```python
# After task completion, update metrics
comm.update_agent_performance(
    agent='sms_engineer',
    task_id='TASK_001', 
    success=True,
    completion_time=45.0,
    skill_used=[AgentSkill.SMS_INTEGRATION]
)

# Get system insights
report = comm.get_agent_workload_report()
recommendations = comm.optimize_task_distribution()
```

## 🔍 Monitoring & Analytics

### Real-Time Monitoring

The system provides multiple levels of monitoring:

1. **Agent Status**: Real-time load and availability
2. **Task Routing**: Decision logging and analysis
3. **Performance Metrics**: Success rates, completion times
4. **Skill Evolution**: How agent capabilities change over time
5. **System Optimization**: Bottlenecks and improvement suggestions

### Analytics Dashboard Data

```python
# Get comprehensive system overview
workload_report = comm.get_agent_workload_report()

{
    'timestamp': '2024-12-04T10:30:00',
    'system_load_percent': 65.2,
    'agents': {
        'sms_engineer': {
            'utilization_percent': 75.0,
            'success_rate': 0.94,
            'avg_completion_time_min': 67.3,
            'performance_trend': 'excellent',
            'availability': 'busy',
            'top_skills': [
                {'skill': 'sms_integration', 'rating': 0.87},
                {'skill': 'python_development', 'rating': 0.82}
            ]
        }
    }
}
```

## 🎯 Best Practices

### 1. Task Definition
- **Be Specific**: Define clear skill requirements
- **Weight Appropriately**: Use skill_weights for task-specific importance
- **Set Realistic Deadlines**: Consider agent capacity and system load
- **Estimate Duration**: Help with load balancing decisions

### 2. Agent Configuration  
- **Define Skills Accurately**: Ensure agent skills match actual capabilities
- **Set Appropriate Capacity**: Configure max_concurrent_tasks realistically
- **Monitor Performance**: Regularly check agent metrics and optimization recommendations

### 3. System Optimization
- **Review Skill Gaps**: Address underrepresented skills
- **Balance Workloads**: Monitor for overloaded/underutilized agents
- **Track Trends**: Use performance analytics to identify improvement opportunities
- **Adjust Priorities**: Use dynamic priority adjustment for better responsiveness

## 🛠️ Advanced Configuration

### Custom Skill Weights

```python
task = TaskRequest(
    # ... other parameters ...
    skill_weights={
        AgentSkill.SMS_INTEGRATION: 3.0,    # Critical for this task
        AgentSkill.NLP_PROCESSING: 2.0,     # Important
        AgentSkill.PYTHON_DEVELOPMENT: 1.0  # Standard requirement
    }
)
```

### Performance Tuning

```python
# Adjust agent capacity based on performance
if agent_metrics.success_rate > 0.95 and avg_completion_time < 30:
    agent_metrics.max_concurrent_tasks = min(5, current_max + 1)
elif agent_metrics.success_rate < 0.7:
    agent_metrics.max_concurrent_tasks = max(1, current_max - 1)
```

### Custom Priority Adjustment Rules

```python
def custom_priority_adjustment(task):
    """Custom rules for specific task types"""
    if task.task_type == 'security_patch':
        task.priority = TaskPriority.CRITICAL
    elif task.task_type == 'client_request' and task.deadline:
        hours_until_deadline = (task.deadline - datetime.now()).total_seconds() / 3600
        if hours_until_deadline < 4:
            task.priority = TaskPriority.HIGH
    
    return task
```

## 📈 Future Enhancements

The enhanced agent communication system provides a solid foundation for future improvements:

1. **Machine Learning Integration**: Use ML to predict optimal agent assignments
2. **Cross-Agent Learning**: Share successful patterns between agents  
3. **Predictive Load Balancing**: Forecast system load and proactively adjust
4. **Advanced Analytics**: Deeper insights into system performance patterns
5. **Auto-Scaling**: Dynamically adjust agent capacity based on demand

---

## 📞 Support

For questions about the enhanced agent communication system:

1. **Check the examples**: `enhanced_agent_communication_example.py`
2. **Review the implementation**: `src/agent_communication.py`
3. **Run the demonstration**: `python enhanced_agent_communication_example.py`
4. **Monitor the logs**: Check routing and performance files in `autonomous-agents/communication/`

The enhanced system is designed to be self-optimizing and provides extensive logging and analytics to help understand and improve agent coordination. 
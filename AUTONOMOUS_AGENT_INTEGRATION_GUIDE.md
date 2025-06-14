# Autonomous Agent Integration Guide

## 🎯 Overview

The autonomous wrapper system transforms Claude Code agents into fully autonomous workers that can:
- Monitor for new tasks automatically
- Execute tasks without human intervention  
- Integrate with Karen's agent communication system
- Handle errors and recovery gracefully
- Provide comprehensive logging and monitoring

## 🚀 Quick Start

### 1. Basic Agent Launch
```bash
# Start any agent autonomously
./agent_autonomous_wrapper.sh test_engineer
./agent_autonomous_wrapper.sh memory_engineer  
./agent_autonomous_wrapper.sh sms_engineer
./agent_autonomous_wrapper.sh orchestrator
```

### 2. Advanced Configuration
```bash
# Enable debug logging
LOG_LEVEL=DEBUG ./agent_autonomous_wrapper.sh test_engineer

# Set custom timeout (2 hours)
MAX_TASK_RUNTIME=7200 ./agent_autonomous_wrapper.sh memory_engineer

# Faster health checks (every 10 seconds)
HEALTH_CHECK_INTERVAL=10 ./agent_autonomous_wrapper.sh orchestrator
```

## 📋 Task Management

### Creating Agent Tasks

Create instruction files in `agent_instructions/`:

```markdown
# agent_instructions/test_engineer_current_task.md
# Agent Task: test_engineer
**Priority:** high
**Deadline:** 2025-06-05T12:00:00Z
**Source:** Manual Assignment
**Timestamp:** 2025-06-05T00:30:00Z

## Task Description
Create comprehensive tests for the enhanced NLP system.

Test components:
1. Service entity extraction
2. Price detection algorithms
3. Multi-language support
4. Customer preference learning

## Instructions
Create test files in tests/ directory and ensure >95% pass rate.

## Success Criteria
- All tests pass
- Coverage report generated
- Results shared with orchestrator
```

### Task Lifecycle

1. **Detection**: Agent wrapper monitors `agent_instructions/` directory
2. **Processing**: Task moved to `.processing` state during execution
3. **Completion**: Task moved to `agent_progress/completed_*` with timestamp
4. **Logging**: Results logged to multiple files for tracking

## 🔄 Agent Communication Integration

### Inbox Message Processing

The wrapper automatically processes messages from other agents:

```json
{
  "from": "orchestrator",
  "to": "test_engineer", 
  "type": "high_priority_task_assignment",
  "content": {
    "task_assignment": {
      "description": "Run integration tests for new features",
      "priority": "high",
      "deadline": "2025-06-05T18:00:00Z"
    }
  },
  "timestamp": "2025-06-05T00:30:00Z"
}
```

Messages are automatically converted to task instructions when appropriate.

### Status Notifications

Agents automatically notify the orchestrator upon task completion:

```json
{
  "from": "test_engineer",
  "to": "orchestrator",
  "type": "task_completion",
  "content": {
    "completion_details": {
      "agent": "test_engineer",
      "duration_seconds": 1847,
      "status": "completed"
    },
    "agent_status": "available",
    "next_task_ready": true
  }
}
```

## 📊 Monitoring and Health Checks

### Real-time Status

Check agent health at any time:
```bash
# View current status
cat agent_progress/test_engineer_health.json

# Monitor live logs
tail -f logs/agents/test_engineer_health.log

# Check completion history
cat agent_progress/completions.log
```

### Health Monitoring Features

- **Memory Usage**: Alerts when >90% memory used
- **Disk Space**: Monitors available storage  
- **Task Duration**: Detects stuck tasks (>2 hours)
- **Error Tracking**: Logs all failures with context
- **Uptime Tracking**: Records agent operational time

### Health Report Example
```json
{
  "agent": "test_engineer",
  "status": "healthy",
  "timestamp": "2025-06-05T00:30:15Z",
  "memory_usage": "34.2%",
  "disk_usage": "67%", 
  "issues": [],
  "uptime_seconds": 3847
}
```

## 🛠️ Integration with Existing Systems

### Celery Integration
```python
# Add to existing celery tasks
from agent_communication import notify_agent

@celery_app.task
def process_email_with_nlp(email_data):
    # Process email
    result = enhanced_nlp.process_email_content(email_data)
    
    # Notify test engineer if needed
    if result['confidence'] < 0.8:
        notify_agent('test_engineer', {
            'type': 'validation_request',
            'content': {
                'email_data': email_data,
                'nlp_result': result,
                'reason': 'low_confidence_score'
            }
        })
```

### NLP System Integration
```python
# Enhanced NLP can trigger agent tasks
def process_customer_message(message, customer_id):
    result = nlp_processor.process_enhanced_message(message, customer_id)
    
    # High-value customer needs special attention
    if result['customer_value'] == 'high':
        create_agent_task('memory_engineer', {
            'task': 'update_vip_customer_profile',
            'customer_id': customer_id,
            'interaction_data': result
        })
```

## 🔧 Production Deployment

### Multi-Agent Startup Script
```bash
#!/bin/bash
# production_startup.sh

echo "🚀 Starting Karen AI Autonomous Agent System"

# Start core agents in background
./agent_autonomous_wrapper.sh orchestrator &
./agent_autonomous_wrapper.sh memory_engineer &  
./agent_autonomous_wrapper.sh sms_engineer &
./agent_autonomous_wrapper.sh test_engineer &

echo "✅ All agents started autonomously"
echo "📊 Monitor with: tail -f logs/agents/*.log"
```

### Process Management
```bash
# Check all running agents
ps aux | grep agent_autonomous_wrapper

# Stop specific agent
pkill -f "agent_autonomous_wrapper.sh test_engineer"

# Stop all agents
pkill -f agent_autonomous_wrapper

# Restart with health checks
for agent in orchestrator memory_engineer sms_engineer test_engineer; do
    echo "Starting $agent..."
    ./agent_autonomous_wrapper.sh $agent &
    sleep 2
done
```

## 📈 Performance Optimization

### Best Practices

1. **Resource Management**
   - Set appropriate `MAX_TASK_RUNTIME` for your tasks
   - Monitor memory usage in production
   - Use `HEALTH_CHECK_INTERVAL` based on criticality

2. **Task Design**
   - Break large tasks into smaller chunks
   - Include clear success criteria
   - Set realistic deadlines

3. **Error Handling**
   - Monitor error logs regularly
   - Implement retry logic for critical tasks
   - Use agent communication for coordination

### Scaling Considerations

- **Multiple Instances**: Run multiple agents of same type for load balancing
- **Priority Queues**: Use task priorities to handle urgent work first
- **Resource Limits**: Set memory and CPU limits in production
- **Monitoring**: Implement centralized logging for large deployments

## 🐛 Troubleshooting

### Common Issues

**Agent not starting:**
```bash
# Check permissions
chmod +x agent_autonomous_wrapper.sh

# Verify directories exist
mkdir -p agent_instructions agent_progress logs/agents
```

**Tasks not being detected:**
```bash
# Check file naming
ls agent_instructions/*_current_task.md

# Verify file permissions
chmod 644 agent_instructions/*.md
```

**Agent stuck on task:**
```bash
# Check processing files
ls agent_instructions/*.processing

# Force cleanup (careful!)
rm agent_instructions/*.processing
```

### Debug Mode

Enable detailed logging:
```bash
LOG_LEVEL=DEBUG ./agent_autonomous_wrapper.sh test_engineer
```

This provides:
- Detailed message processing logs
- Health check details  
- Task execution step-by-step
- Error context and stack traces

## 🎉 Success Stories

With the autonomous wrapper system, you can achieve:

- **24/7 Operation**: Agents work continuously without supervision
- **Automatic Scaling**: Add more agents as workload increases
- **Fault Tolerance**: Agents recover from errors and continue working
- **Integration**: Seamless connection with existing Karen AI systems
- **Monitoring**: Complete visibility into agent performance and health

The system is now ready for production deployment with your enhanced NLP capabilities!
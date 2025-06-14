# Eigencode Integration for Karen AI Multi-Agent System

This document describes the Eigencode integration setup for the Karen AI multi-agent system, providing comprehensive code analysis and monitoring capabilities.

## Overview

The Eigencode integration provides:
- **Code Analysis**: Comprehensive static analysis of Python code
- **Agent Monitoring**: Specialized monitoring for multi-agent patterns
- **Quality Metrics**: Code quality, complexity, and documentation metrics
- **Continuous Monitoring**: Background daemon for ongoing code health
- **Report Generation**: Human-readable analysis reports

## Files Structure

```
eigencode_setup.sh              # Main setup script
eigencode.config.json           # Main configuration file
eigencode_karen.sh              # Wrapper script for commands
eigencode_alternative.py        # Alternative implementation (when official Eigencode unavailable)

autonomous-agents/communication/
├── eigencode_sms.json          # SMS Engineer monitoring config
├── eigencode_phone.json        # Phone Engineer monitoring config
└── eigencode_memory.json       # Memory Engineer monitoring config

reports/
├── eigencode_analysis.json     # Detailed JSON analysis results
└── eigencode_report.md         # Human-readable analysis report
```

## Quick Start

### 1. Setup Eigencode Integration

```bash
# Run the setup script
bash eigencode_setup.sh

# Check status
bash eigencode_karen.sh status
```

### 2. Run Analysis

```bash
# Run one-time analysis
bash eigencode_karen.sh analyze

# Generate comprehensive report
bash eigencode_karen.sh report
```

### 3. Start Continuous Monitoring

```bash
# Start daemon for continuous monitoring
bash eigencode_karen.sh start

# Check daemon status
bash eigencode_karen.sh status

# Stop daemon
bash eigencode_karen.sh stop
```

## Configuration

### Main Configuration (eigencode.config.json)

```json
{
  "project": {
    "name": "karen-ai",
    "description": "Multi-agent AI assistant system for handyman services"
  },
  "language": "python",
  "frameworks": ["fastapi", "celery", "redis"],
  "analysis": {
    "depth": "comprehensive",
    "check_patterns": ["security", "performance", "maintainability"]
  },
  "agents": {
    "monitor": [
      "src/orchestrator_agent.py",
      "src/communication_agent.py",
      "src/sms_engineer_agent.py"
    ]
  }
}
```

### Agent-Specific Configurations

Each agent has specialized monitoring:

- **SMS Engineer**: Focuses on conversation threading, template rendering
- **Phone Engineer**: Monitors voice transcription, call handling
- **Memory Engineer**: Tracks context retrieval, memory persistence

## Features

### Code Analysis Metrics

- **Lines of Code**: Total lines, blank lines, comment lines
- **Complexity**: Cyclomatic complexity analysis
- **Documentation**: Docstring coverage percentage
- **Quality Issues**: Style violations, missing documentation
- **Agent Patterns**: Multi-agent specific pattern detection

### Multi-Agent System Analysis

- **Agent Detection**: Identifies agent files and patterns
- **Communication Patterns**: Analyzes inter-agent communication
- **State Management**: Monitors state handling patterns
- **Error Handling**: Checks for proper exception handling
- **Consistency**: Validates consistent agent interfaces

### Sample Analysis Output

```
## Project Summary
- **Files Analyzed**: 185
- **Total Lines**: 36,119
- **Functions**: 1,049
- **Classes**: 244
- **Issues Found**: 1,810

## Agent System Analysis
- **Agent Files**: 64
- **Communication Files**: 18
- **State Management Files**: 12

## Recommendations
- Multi-agent system detected. Ensure consistent communication patterns.
- Some agents lack proper error handling. Consider adding try-catch blocks.
```

## Commands Reference

### eigencode_karen.sh Commands

```bash
# Analysis commands
bash eigencode_karen.sh analyze    # Run full project analysis
bash eigencode_karen.sh report     # Generate human-readable report

# Daemon commands
bash eigencode_karen.sh start      # Start monitoring daemon
bash eigencode_karen.sh stop       # Stop monitoring daemon
bash eigencode_karen.sh restart    # Restart daemon
bash eigencode_karen.sh status     # Show current status
```

### Alternative Implementation Commands

When official Eigencode is not available, use the alternative implementation:

```bash
# Direct usage
python3 eigencode_alternative.py analyze
python3 eigencode_alternative.py report
python3 eigencode_alternative.py daemon
python3 eigencode_alternative.py status
```

## Integration with Development Workflow

### 1. Pre-commit Analysis

Add to your pre-commit hooks:

```bash
#!/bin/bash
# Run quick analysis before commit
bash eigencode_karen.sh analyze
```

### 2. Continuous Integration

Add to CI/CD pipeline:

```yaml
- name: Code Analysis
  run: |
    bash eigencode_setup.sh
    bash eigencode_karen.sh analyze
    bash eigencode_karen.sh report
```

### 3. Daily Monitoring

Set up cron job for daily analysis:

```bash
# Add to crontab
0 6 * * * cd /path/to/karen && bash eigencode_karen.sh analyze
```

## Monitoring Agent Health

### Agent-Specific Monitoring

Each agent type has specialized monitoring rules:

#### SMS Engineer Monitoring
- **Focus**: Conversation threading, template accuracy
- **Metrics**: Response time, template rendering success rate
- **Files**: `sms_conversation_manager.py`, `sms_templates.py`

#### Phone Engineer Monitoring  
- **Focus**: Voice transcription quality, call stability
- **Metrics**: Transcription accuracy, call success rate
- **Files**: `phone_engineer_agent.py`, `voice_client.py`

#### Memory Engineer Monitoring
- **Focus**: Context retrieval, memory persistence
- **Metrics**: Retrieval accuracy, memory utilization
- **Files**: `memory_client.py`, `context_manager.py`

### System Health Indicators

- **Green**: All agents operational, no critical issues
- **Yellow**: Minor issues detected, non-critical
- **Red**: Critical issues found, immediate attention needed

## Troubleshooting

### Common Issues

1. **Eigencode Not Found**
   ```bash
   # Solution: Use alternative implementation
   python3 eigencode_alternative.py status
   ```

2. **Permission Errors**
   ```bash
   # Fix script permissions
   chmod +x eigencode_setup.sh
   chmod +x eigencode_karen.sh
   ```

3. **Analysis Errors**
   ```bash
   # Check Python syntax in problematic files
   python3 -m py_compile src/problematic_file.py
   ```

### Log Files

- **Daemon Logs**: `logs/eigencode.log`
- **Analysis Results**: `reports/eigencode_analysis.json`
- **Error Reports**: Check stderr output during analysis

## Best Practices

### 1. Regular Analysis

- Run analysis before major commits
- Schedule daily automated analysis
- Monitor trends in code quality metrics

### 2. Agent Pattern Consistency

- Ensure all agents follow consistent interfaces
- Implement proper error handling in all agents
- Maintain documentation standards

### 3. Performance Monitoring

- Track complexity trends over time
- Monitor agent communication patterns
- Optimize high-complexity functions

## Future Enhancements

### Planned Features

1. **Real-time Monitoring**: Live code quality dashboard
2. **Agent Performance Metrics**: Runtime performance tracking
3. **Automated Fixes**: Auto-correction of common issues
4. **Integration Alerts**: Slack/email notifications for critical issues
5. **Historical Trending**: Long-term code quality trends

### Custom Rules

Add project-specific rules to `eigencode.config.json`:

```json
{
  "rules": {
    "max_function_length": 50,
    "max_class_length": 300,
    "complexity_threshold": 10,
    "test_coverage_min": 80
  }
}
```

## Contributing

When adding new agents or modifying existing ones:

1. Update relevant `eigencode_*.json` configuration
2. Run analysis to ensure code quality
3. Check agent pattern consistency
4. Update documentation as needed

## Support

For issues with Eigencode integration:

1. Check configuration files for syntax errors
2. Review log files for detailed error messages
3. Run analysis in verbose mode for debugging
4. Use alternative implementation if official Eigencode unavailable

---

**Last Updated**: 2025-06-04  
**Version**: 1.0.0  
**Maintainer**: Karen AI Development Team
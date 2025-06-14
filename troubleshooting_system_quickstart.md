# Troubleshooting System Quick Start Guide

## 🚀 Starting the System

### Option 1: Launch Script (Recommended)
```bash
cd /workspace
python launch_troubleshooting_system.py
```

### Option 2: Manual Start
```bash
cd /workspace
python troubleshooting_orchestrator.py
```

## 📨 For Agent Developers: How to Integrate

### 1. Import the Communication Client
```python
from enhanced_communication_system import create_communication_client, MessageType, MessagePriority

# Initialize in your agent
comm_client = create_communication_client(
    agent_id="your_agent_name",
    subscribed_tags=["troubleshooting", "mcp_tools", "testing"]
)
```

### 2. Report Issues
```python
# When your agent encounters a problem
comm_client.send_message(
    to_agent="troubleshooting_orchestrator",
    message_type=MessageType.ISSUE_REPORT,
    subject="MCP Server Connection Failed",
    content={
        "description": "Cannot connect to MCP server on port 8080",
        "error_details": "ConnectionRefusedError: [Errno 111] Connection refused",
        "affected_resources": ["mcp-server-config.json", "claude_desktop_config.json"],
        "tags": ["mcp_integration", "connection_error"],
        "context": {
            "current_task": "testing new MCP tool",
            "last_working_state": "5 minutes ago",
            "environment": "development"
        }
    },
    priority=MessagePriority.HIGH,
    requires_response=True,
    response_deadline_minutes=30
)
```

### 3. Request Help
```python
# When you need assistance from other agents
help_id = comm_client.request_help(
    subject="Need Redis Configuration Help",
    description="Setting up Redis for MCP tool testing but getting authentication errors",
    tags=["redis", "configuration", "testing"],
    preferred_agents=["mcp_codebase_tools", "testing_agent"],
    urgency=MessagePriority.MEDIUM
)
```

### 4. Share Solutions
```python
from enhanced_communication_system import SolutionCategory

# When you solve a problem, share it
solution_id = comm_client.share_solution(
    category=SolutionCategory.MCP_INTEGRATION,
    title="Fix MCP Server Port Conflicts",
    description="How to resolve port conflicts when running multiple MCP servers",
    problem_patterns=[
        "port already in use",
        "address already in use",
        "bind: address already in use"
    ],
    solution_steps=[
        "Check running processes: `lsof -i :8080`",
        "Kill conflicting process: `kill -9 <PID>`",
        "Update port in config: change to unused port",
        "Restart MCP server with new port",
        "Update Claude Desktop config with new port"
    ],
    code_snippets={
        "check_port": "lsof -i :8080",
        "config_update": '{"command": "node", "args": ["server.js", "--port", "8081"]}'
    },
    validation_steps=[
        "Test MCP server connection",
        "Verify Claude Desktop integration",
        "Run basic tool test"
    ],
    tags=["mcp", "port_conflict", "server_config"]
)
```

## 🔧 For Testing: Coordination Usage

### 1. Register Test Suites
```python
from testing_coordination_system import create_testing_coordinator, TestType, TestEnvironment

# Initialize testing coordinator
test_coord = create_testing_coordinator("your_agent_name")

# Register a test suite
suite_id = test_coord.register_test_suite(
    name="MCP Integration Tests",
    test_type=TestType.INTEGRATION,
    environment=TestEnvironment.ISOLATED,
    test_files=["tests/test_mcp_integration.py", "tests/test_tool_execution.py"],
    dependencies=["mcp_server_running"],
    required_resources=["mcp-server-config.json", "test_database"],
    estimated_duration=45,  # minutes
    max_parallel=1
)
```

### 2. Schedule Test Execution
```python
# Schedule the test to run
execution_id = test_coord.schedule_test_execution(
    suite_id=suite_id,
    priority=5  # 1-10 scale, 10 = highest
)

# The system will automatically:
# - Reserve test environment
# - Claim required resources
# - Execute tests in isolation
# - Generate reports
# - Clean up afterwards
```

## 📚 Knowledge Base Usage

### 1. Search for Solutions
```python
from knowledge_management_system import create_knowledge_manager, KnowledgeType

knowledge_mgr = create_knowledge_manager("your_agent_name")

# Search for existing solutions
results = knowledge_mgr.search_knowledge(
    query="MCP server timeout error",
    entry_type=KnowledgeType.TROUBLESHOOTING_PATTERN,
    tags=["mcp", "timeout"]
)

for entry, relevance_score in results:
    print(f"Solution: {entry.title} (Score: {relevance_score:.2f})")
    print(f"Steps: {entry.content.get('steps', [])}")
```

### 2. Find Matching Patterns
```python
# Get automated suggestions for an issue
issue = "MCP tool execution fails with 'schema validation error'"
matches = knowledge_mgr.find_matching_patterns(
    issue_description=issue,
    context={"tool_name": "file_operations", "mcp_version": "1.0.0"}
)

for match in matches:
    print(f"Pattern: {match.pattern_id}")
    print(f"Confidence: {match.confidence_score:.2f}")
    print(f"Suggested actions: {match.suggested_actions}")
```

## 🎯 Real-World Usage Examples

### Example 1: MCP Tool Development Issue

**Scenario**: Agent developing MCP tools hits a schema validation error

```python
# 1. Agent reports the issue
comm_client.send_message(
    to_agent="troubleshooting_orchestrator",
    message_type=MessageType.ISSUE_REPORT,
    subject="MCP Tool Schema Validation Failing",
    content={
        "description": "New file_operations tool failing schema validation",
        "error_details": "Invalid schema: missing required property 'inputSchema'",
        "affected_resources": ["src/tools/file_operations.py"],
        "context": {
            "tool_name": "file_operations", 
            "mcp_version": "1.0.0",
            "test_command": "python -m pytest tests/test_file_operations.py"
        }
    }
)

# 2. System automatically:
# - Assigns to agent with MCP expertise
# - Finds similar patterns in knowledge base
# - Suggests proven solutions
# - Coordinates if multiple agents needed

# 3. Agent gets response with:
# - Step-by-step fix instructions
# - Code examples
# - Testing recommendations
# - Prevention tips
```

### Example 2: Testing Coordination

**Scenario**: Multiple agents need to run tests without conflicts

```python
# Agent A registers integration tests
test_coord_a.register_test_suite(
    name="MCP Server Integration",
    test_type=TestType.INTEGRATION,
    environment=TestEnvironment.INTEGRATION,
    required_resources=["mcp_server", "test_database"]
)

# Agent B registers performance tests  
test_coord_b.register_test_suite(
    name="Business Intelligence Performance",
    test_type=TestType.PERFORMANCE,
    environment=TestEnvironment.ISOLATED,
    required_resources=["redis_server", "test_metrics_db"]
)

# System automatically:
# - Schedules tests to avoid resource conflicts
# - Uses different environments when needed
# - Aggregates results for comparison
# - Shares performance insights
```

### Example 3: Knowledge Sharing

**Scenario**: Agent solves a tricky configuration issue

```python
# After solving Redis connection issue
comm_client.share_solution(
    category=SolutionCategory.CONFIGURATION,
    title="Fix Redis Authentication for MCP Tools",
    description="Resolve Redis AUTH errors in MCP tool development",
    problem_patterns=["NOAUTH Authentication required", "Redis connection denied"],
    solution_steps=[
        "Check Redis configuration: `redis-cli CONFIG GET requirepass`",
        "Set password in environment: `export REDIS_PASSWORD=your_password`",
        "Update MCP tool Redis client with auth",
        "Test connection: `redis-cli -a your_password ping`"
    ],
    code_snippets={
        "redis_client": """
import redis
client = redis.Redis(
    host='localhost',
    port=6379,
    password=os.getenv('REDIS_PASSWORD'),
    decode_responses=True
)
""",
        "env_setup": "export REDIS_PASSWORD=karen_ai_redis_2024"
    }
)

# System automatically:
# - Stores solution in knowledge base
# - Notifies other agents of new solution
# - Indexes keywords for future searches
# - Tracks solution effectiveness
```

## 🔍 Monitoring and Status

### Check System Status
```python
# Get overall system health
from integrated_troubleshooting_launcher import IntegratedTroubleshootingSystem

system = IntegratedTroubleshootingSystem()
status = system.get_system_status()
print(f"System running: {status['running']}")
print(f"Active agents: {status['known_agents']}")
```

### View Knowledge Base Stats
```python
stats = knowledge_mgr.get_knowledge_stats()
print(f"Total solutions: {stats['total_entries']}")
print(f"Average success rate: {stats['average_success_rate']:.2%}")
```

### Check Testing Status
```python
test_status = test_coord.get_testing_status()
print(f"Active tests: {test_status['active_executions']}")
print(f"Environment availability: {test_status['environment_reservations']}")
```

## 📁 File Locations

**Configuration**: `/workspace/autonomous-agents/troubleshooting/`
**Knowledge Base**: `/workspace/autonomous-agents/troubleshooting/knowledge-base/`
**Test Results**: `/workspace/autonomous-agents/troubleshooting/testing-results/`
**Communication**: `/workspace/autonomous-agents/communication/inbox/`
**Logs**: `/workspace/logs/troubleshooting_*.log`

## 🆘 Getting Help

### Built-in Help System
```python
# Request help from the troubleshooting system itself
comm_client.request_help(
    subject="How to use troubleshooting system",
    description="Need guidance on integrating with troubleshooting orchestrator",
    tags=["help", "documentation", "integration"]
)
```

### Emergency Broadcast
```python
# For critical issues affecting multiple agents
comm_client.broadcast_message(
    title="CRITICAL: Redis Server Down",
    content="Redis server is unresponsive, all dependent services affected",
    priority=MessagePriority.CRITICAL,
    tags=["critical", "redis", "infrastructure"]
)
```

The system is designed to be intuitive - just start using it and it will learn and improve from every interaction!
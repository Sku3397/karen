#!/bin/bash
# Demo of Autonomous Agent System for Karen AI
# Shows complete workflow: task creation → agent execution → completion

set -e

echo "🎯 Karen AI Autonomous Agent System Demo"
echo "========================================="

# Setup
DEMO_DIR="/tmp/karen_agent_demo"
mkdir -p "$DEMO_DIR"/{agent_instructions,agent_progress,logs}

echo "📁 Created demo environment: $DEMO_DIR"

# Create sample task
cat > "$DEMO_DIR/agent_instructions/demo_agent_current_task.md" << 'EOF'
# Agent Task: demo_agent
**Priority:** high
**Deadline:** none
**Source:** Demo System
**Timestamp:** 2025-06-05T00:30:00Z

## Task Description
Demonstrate autonomous agent task processing:
1. Detect this instruction file
2. Process the task automatically  
3. Log completion and notify other agents
4. Clean up and wait for next task

## Instructions
This is a demo task to show the autonomous wrapper system.

## Success Criteria
- Task detected and processed automatically
- Completion logged with timestamp
- Status updated properly
EOF

echo "📝 Created demo task instruction"

# Create simplified wrapper for demo
cat > "$DEMO_DIR/demo_wrapper.sh" << 'EOF'
#!/bin/bash
AGENT_NAME="$1"
INSTRUCTION_FILE="agent_instructions/${AGENT_NAME}_current_task.md"

echo "🤖 Starting autonomous agent: $AGENT_NAME"
echo "📋 Watching for: $INSTRUCTION_FILE"

for i in {1..10}; do
    if [ -f "$INSTRUCTION_FILE" ]; then
        echo "📧 Task found! Processing..."
        
        # Show task
        echo "📄 Task content:"
        cat "$INSTRUCTION_FILE" | head -5
        
        # Simulate processing
        echo "⚙️  Agent working..."
        sleep 2
        
        # Complete task
        echo "✅ Task completed!"
        echo "$(date): Task completed by $AGENT_NAME" >> agent_progress/completions.log
        
        # Move to completed
        mv "$INSTRUCTION_FILE" "agent_progress/completed_$(basename "$INSTRUCTION_FILE")"
        
        echo "🎉 Demo complete!"
        exit 0
    fi
    
    echo "⏳ Waiting for task... ($i/10)"
    sleep 1
done

echo "❌ No task found in 10 seconds"
EOF

chmod +x "$DEMO_DIR/demo_wrapper.sh"

# Run demo
echo ""
echo "🚀 Starting autonomous agent demo..."
cd "$DEMO_DIR"
./demo_wrapper.sh demo_agent

echo ""
echo "📊 Demo Results:"
echo "================"

if [ -f "agent_progress/completions.log" ]; then
    echo "✅ Completion log:"
    cat agent_progress/completions.log
else
    echo "❌ No completion log found"
fi

if [ -f "agent_progress/completed_demo_agent_current_task.md" ]; then
    echo "✅ Task file moved to completed"
    ls -la agent_progress/completed_*
else
    echo "❌ Task file not moved"
fi

echo ""
echo "🎯 Autonomous Agent System Features Demonstrated:"
echo "================================================="
echo "✅ Task Detection - Agent found instruction file automatically"
echo "✅ Task Processing - Agent executed task workflow"  
echo "✅ Completion Logging - Results logged with timestamp"
echo "✅ File Management - Task moved to completed status"
echo "✅ Status Reporting - Clear progress and completion feedback"

echo ""
echo "🚀 Ready for Production Agent Deployment!"

# Cleanup
rm -rf "$DEMO_DIR"
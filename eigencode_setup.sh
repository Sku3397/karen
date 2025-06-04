#!/bin/bash
# Eigencode Setup Script for Karen AI Multi-Agent System

# Note: Not using set -e to allow script to continue even if installation fails

echo "🔧 Setting up Eigencode integration for Karen AI..."
echo "================================================="

# Function to check command availability
check_command() {
    if command -v "$1" &> /dev/null; then
        echo "✓ $1 is available"
        return 0
    else
        echo "✗ $1 is not available"
        return 1
    fi
}

# Function to install eigencode via different methods
install_eigencode() {
    echo "📦 Attempting to install Eigencode..."
    
    # Try npm first
    if check_command npm; then
        echo "Trying npm installation..."
        if npm install -g eigencode 2>/dev/null; then
            echo "✓ Eigencode installed via npm"
            return 0
        else
            echo "✗ npm installation failed"
        fi
    fi
    
    # Try pip3
    if check_command pip3; then
        echo "Trying pip3 installation..."
        if pip3 install eigencode 2>/dev/null; then
            echo "✓ Eigencode installed via pip3"
            return 0
        else
            echo "✗ pip3 installation failed"
        fi
    fi
    
    # Try pip
    if check_command pip; then
        echo "Trying pip installation..."
        if pip install eigencode 2>/dev/null; then
            echo "✓ Eigencode installed via pip"
            return 0
        else
            echo "✗ pip installation failed"
        fi
    fi
    
    # If all methods fail, provide manual installation instructions
    echo "❌ Automatic installation failed"
    echo "📋 Manual installation options:"
    echo "   1. Visit https://eigencode.ai for official installation"
    echo "   2. Check GitHub: https://github.com/eigencode/eigencode"
    echo "   3. Try: curl -sSL https://install.eigencode.ai | bash"
    echo "   4. Or download from releases: https://releases.eigencode.ai"
    echo "⚠️ Continuing with configuration setup..."
    return 0  # Don't fail the script
}

# Check if eigencode is already installed
if check_command eigencode; then
    echo "✓ Eigencode is already installed"
    eigencode --version 2>/dev/null || echo "✓ Eigencode binary found"
else
    echo "📥 Eigencode not found, attempting installation..."
    install_eigencode
fi

# Create eigencode configuration for Karen AI
echo "📝 Creating Eigencode configuration..."

cat > eigencode.config.json << 'EOF'
{
  "project": {
    "name": "karen-ai",
    "description": "Multi-agent AI assistant system for handyman services",
    "version": "1.0.0"
  },
  "language": "python",
  "frameworks": [
    "fastapi",
    "celery",
    "redis",
    "google-api-python-client",
    "openai"
  ],
  "structure": {
    "src_dir": "src/",
    "test_dir": "tests/",
    "config_dir": "config/",
    "docs_dir": "docs/"
  },
  "style": {
    "indent": 4,
    "line_length": 100,
    "quotes": "double",
    "trailing_comma": true,
    "sort_imports": true
  },
  "analysis": {
    "depth": "comprehensive",
    "include_suggestions": true,
    "auto_fix": false,
    "check_patterns": [
      "security",
      "performance",
      "maintainability",
      "documentation"
    ]
  },
  "agents": {
    "monitor": [
      "src/orchestrator_agent.py",
      "src/communication_agent.py",
      "src/sms_engineer_agent.py",
      "src/phone_engineer_agent.py",
      "src/memory_client.py"
    ],
    "patterns": {
      "agent_communication": "autonomous-agents/shared-knowledge/templates/",
      "celery_tasks": "src/celery_*.py",
      "api_endpoints": "src/api/",
      "test_files": "tests/"
    }
  },
  "daemons": {
    "interval": 300,
    "background": true,
    "log_file": "logs/eigencode.log",
    "watch_files": [
      "src/**/*.py",
      "tests/**/*.py",
      "autonomous-agents/**/*.py"
    ]
  },
  "integrations": {
    "github": {
      "enabled": true,
      "auto_pr": false,
      "branch_prefix": "eigencode/"
    },
    "slack": {
      "enabled": false,
      "webhook_url": null
    },
    "email": {
      "enabled": false,
      "smtp_server": null
    }
  },
  "rules": {
    "max_function_length": 50,
    "max_class_length": 300,
    "max_file_length": 1000,
    "complexity_threshold": 10,
    "test_coverage_min": 80
  },
  "exclude": [
    "node_modules/",
    ".venv/",
    "__pycache__/",
    "*.pyc",
    ".git/",
    "dist/",
    "build/",
    "logs/",
    "temp_scripts/"
  ]
}
EOF

echo "✓ Eigencode configuration created: eigencode.config.json"

# Create agent-specific eigencode configurations
echo "📝 Creating agent-specific configurations..."

# SMS Engineer configuration
cat > autonomous-agents/communication/eigencode_sms.json << 'EOF'
{
  "agent": "sms_engineer",
  "focus": [
    "conversation_threading",
    "template_rendering",
    "state_management"
  ],
  "monitor_files": [
    "../../src/sms_conversation_manager.py",
    "../../src/sms_templates.py",
    "../../src/sms_engineer_agent.py"
  ],
  "metrics": [
    "response_time",
    "template_accuracy",
    "conversation_completion_rate"
  ]
}
EOF

# Phone Engineer configuration  
cat > autonomous-agents/communication/eigencode_phone.json << 'EOF'
{
  "agent": "phone_engineer",
  "focus": [
    "voice_transcription",
    "call_handling",
    "integration_stability"
  ],
  "monitor_files": [
    "../../src/phone_engineer_agent.py",
    "../../src/voice_client.py",
    "../../src/integrations/transcription.py"
  ],
  "metrics": [
    "transcription_accuracy",
    "call_success_rate",
    "response_latency"
  ]
}
EOF

# Memory Engineer configuration
cat > autonomous-agents/communication/eigencode_memory.json << 'EOF'
{
  "agent": "memory_engineer", 
  "focus": [
    "context_retrieval",
    "memory_persistence",
    "cross_medium_integration"
  ],
  "monitor_files": [
    "../../src/memory_client.py",
    "../../src/context_manager.py"
  ],
  "metrics": [
    "retrieval_accuracy",
    "memory_utilization",
    "context_relevance"
  ]
}
EOF

echo "✓ Agent-specific configurations created"

# Create eigencode wrapper script for Karen AI
cat > eigencode_karen.sh << 'EOF'
#!/bin/bash
# Eigencode wrapper for Karen AI multi-agent system

EIGENCODE_CONFIG="eigencode.config.json"
LOG_FILE="logs/eigencode.log"

# Ensure logs directory exists
mkdir -p logs

# Function to run eigencode analysis
run_analysis() {
    echo "🔍 Running Eigencode analysis..."
    if command -v eigencode &> /dev/null; then
        eigencode analyze --config "$EIGENCODE_CONFIG" --output "reports/eigencode_analysis.json"
        echo "✓ Analysis complete. Report saved to reports/eigencode_analysis.json"
    elif [ -f "eigencode_alternative.py" ]; then
        echo "Using alternative Eigencode implementation..."
        python3 eigencode_alternative.py analyze --config "$EIGENCODE_CONFIG"
        echo "✓ Analysis complete using alternative implementation"
    else
        echo "❌ Eigencode not available. Please run eigencode_setup.sh first."
        exit 1
    fi
}

# Function to start eigencode daemon
start_daemon() {
    echo "🔄 Starting Eigencode daemon..."
    if command -v eigencode &> /dev/null; then
        eigencode daemon start --config "$EIGENCODE_CONFIG" --log "$LOG_FILE"
        echo "✓ Daemon started. Logs: $LOG_FILE"
    elif [ -f "eigencode_alternative.py" ]; then
        echo "Starting alternative Eigencode daemon..."
        python3 eigencode_alternative.py daemon --config "$EIGENCODE_CONFIG" &
        echo $! > eigencode_daemon.pid
        echo "✓ Alternative daemon started. PID: $(cat eigencode_daemon.pid)"
    else
        echo "❌ Eigencode not available. Please run eigencode_setup.sh first."
        exit 1
    fi
}

# Function to stop eigencode daemon
stop_daemon() {
    echo "⏹️  Stopping Eigencode daemon..."
    if command -v eigencode &> /dev/null; then
        eigencode daemon stop
        echo "✓ Daemon stopped"
    elif [ -f "eigencode_daemon.pid" ]; then
        PID=$(cat eigencode_daemon.pid)
        if kill "$PID" 2>/dev/null; then
            echo "✓ Alternative daemon stopped (PID: $PID)"
            rm -f eigencode_daemon.pid
        else
            echo "⚠️ Daemon PID $PID not found or already stopped"
            rm -f eigencode_daemon.pid
        fi
    else
        echo "❌ No daemon running"
    fi
}

# Function to show eigencode status
show_status() {
    echo "📊 Eigencode Status:"
    if command -v eigencode &> /dev/null; then
        eigencode daemon status || echo "Daemon not running"
        echo "Configuration: $EIGENCODE_CONFIG"
        echo "Log file: $LOG_FILE"
    elif [ -f "eigencode_alternative.py" ]; then
        echo "✓ Alternative Eigencode implementation available"
        echo "Configuration: $EIGENCODE_CONFIG"
        if [ -f "eigencode_daemon.pid" ]; then
            PID=$(cat eigencode_daemon.pid)
            if kill -0 "$PID" 2>/dev/null; then
                echo "✓ Alternative daemon running (PID: $PID)"
            else
                echo "⚠️ Daemon PID file exists but process not running"
                rm -f eigencode_daemon.pid
            fi
        else
            echo "○ Daemon not running"
        fi
        echo "Reports: reports/"
        echo "Last analysis: $(ls -la reports/eigencode_analysis.json 2>/dev/null | awk '{print $6" "$7" "$8}' || echo 'None')"
    else
        echo "❌ Eigencode not installed"
    fi
}

# Main command handling
case "$1" in
    "analyze"|"analysis")
        run_analysis
        ;;
    "start"|"daemon")
        start_daemon
        ;;
    "stop")
        stop_daemon
        ;;
    "status")
        show_status
        ;;
    "restart")
        stop_daemon
        sleep 2
        start_daemon
        ;;
    "report")
        echo "📊 Generating comprehensive report..."
        if [ -f "eigencode_alternative.py" ]; then
            python3 eigencode_alternative.py report
        else
            echo "❌ Report generation requires alternative implementation"
        fi
        ;;
    *)
        echo "Karen AI Eigencode Integration"
        echo "Usage: $0 {analyze|start|stop|status|restart|report}"
        echo ""
        echo "Commands:"
        echo "  analyze  - Run code analysis"
        echo "  start    - Start monitoring daemon"
        echo "  stop     - Stop monitoring daemon" 
        echo "  status   - Show current status"
        echo "  restart  - Restart daemon"
        echo "  report   - Generate comprehensive report"
        ;;
esac
EOF

chmod +x eigencode_karen.sh
echo "✓ Eigencode wrapper script created: eigencode_karen.sh"

# Create reports directory
mkdir -p reports
echo "✓ Reports directory created"

# Verify installation
echo ""
echo "🔍 Verifying Eigencode setup..."
if command -v eigencode &> /dev/null; then
    echo "✅ Eigencode is ready!"
    eigencode --version 2>/dev/null || echo "✅ Eigencode binary available"
    echo ""
    echo "🚀 Quick start:"
    echo "   ./eigencode_karen.sh analyze   # Run analysis"
    echo "   ./eigencode_karen.sh start     # Start monitoring" 
    echo "   ./eigencode_karen.sh status    # Check status"
else
    echo "⚠️ Eigencode not detected. Manual installation may be required."
    echo "📋 Next steps:"
    echo "   1. Install Eigencode manually from https://eigencode.ai"
    echo "   2. Re-run this script to complete setup"
    echo "   3. Use ./eigencode_karen.sh once Eigencode is installed"
fi

echo ""
echo "📁 Files created:"
echo "   - eigencode.config.json (main configuration)"
echo "   - autonomous-agents/communication/eigencode_*.json (agent configs)"
echo "   - eigencode_karen.sh (wrapper script)"
echo "   - reports/ (analysis output directory)"
echo ""
echo "✅ Eigencode integration setup complete!"
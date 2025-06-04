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

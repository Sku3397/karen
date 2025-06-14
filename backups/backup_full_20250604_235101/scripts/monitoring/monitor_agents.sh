#!/bin/bash
# Karen AI Secretary - Agent Monitor Script
# Usage: ./scripts/monitoring/monitor_agents.sh [--continuous] [--interval SECONDS]

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
CONTINUOUS=false
INTERVAL=30

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --continuous)
            CONTINUOUS=true
            shift
            ;;
        --interval)
            INTERVAL="$2"
            shift 2
            ;;
        *)
            echo "Usage: $0 [--continuous] [--interval SECONDS]"
            exit 1
            ;;
    esac
done

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Get agent status from autonomous_state.json
get_agent_status() {
    local state_file="$PROJECT_ROOT/autonomous_state.json"
    
    if [[ ! -f "$state_file" ]]; then
        echo "State file not found"
        return 1
    fi
    
    python3 -c "
import json
import sys

try:
    with open('$state_file', 'r') as f:
        data = json.load(f)
    
    agent_states = data.get('agent_states', {})
    tasks_in_queues = data.get('tasks_in_queues', {})
    runtime = data.get('runtime', 'unknown')
    start_time = data.get('start_time', 'unknown')
    
    print(f'Runtime: {runtime}')
    print(f'Start Time: {start_time}')
    print()
    
    total_completed = 0
    total_queued = 0
    
    for agent, state in agent_states.items():
        status = state.get('status', 'unknown')
        completed = state.get('tasks_completed', 0)
        last_task = state.get('last_task', 'none')
        queued = tasks_in_queues.get(agent, 0)
        
        total_completed += completed
        total_queued += queued
        
        # Status emoji
        status_emoji = '🟢' if status == 'idle' else '🔵' if status == 'working' else '🔴'
        
        print(f'{status_emoji} {agent.upper()}:')
        print(f'  Status: {status}')
        print(f'  Completed: {completed} tasks')
        print(f'  Queued: {queued} tasks')
        print(f'  Last Task: {last_task}')
        print()
    
    print(f'TOTALS:')
    print(f'  Completed: {total_completed} tasks')
    print(f'  Queued: {total_queued} tasks')
    
except Exception as e:
    print(f'Error reading state file: {e}')
    sys.exit(1)
"
}

# Check for recent agent activity
check_agent_activity() {
    local inbox_dir="$PROJECT_ROOT/autonomous-agents/communication/inbox"
    
    if [[ ! -d "$inbox_dir" ]]; then
        warning "Agent inbox directory not found"
        return 1
    fi
    
    echo -e "${CYAN}Recent Agent Activity:${NC}"
    echo "====================="
    
    # Check for recent messages
    local recent_messages=0
    for agent_dir in "$inbox_dir"/*; do
        if [[ -d "$agent_dir" ]]; then
            local agent_name
            agent_name=$(basename "$agent_dir")
            local message_count
            message_count=$(find "$agent_dir" -name "*.json" -mmin -60 2>/dev/null | wc -l)
            
            if [[ $message_count -gt 0 ]]; then
                echo "📨 $agent_name: $message_count messages in last hour"
                recent_messages=$((recent_messages + message_count))
            fi
        fi
    done
    
    if [[ $recent_messages -eq 0 ]]; then
        info "No recent agent messages in the last hour"
    fi
    echo ""
}

# Check knowledge base updates
check_knowledge_base() {
    local kb_dir="$PROJECT_ROOT/autonomous-agents/communication/knowledge-base"
    
    if [[ ! -d "$kb_dir" ]]; then
        warning "Knowledge base directory not found"
        return 1
    fi
    
    echo -e "${CYAN}Knowledge Base Activity:${NC}"
    echo "======================="
    
    # Find recent knowledge base entries
    local recent_kb
    recent_kb=$(find "$kb_dir" -name "*.json" -mmin -1440 2>/dev/null | wc -l) # Last 24 hours
    
    if [[ $recent_kb -gt 0 ]]; then
        echo "📚 $recent_kb new knowledge entries in last 24 hours"
        
        # Show latest entries
        echo ""
        echo "Latest entries:"
        find "$kb_dir" -name "*.json" -mmin -1440 -printf "%T@ %f\n" 2>/dev/null | \
            sort -nr | head -5 | while read -r timestamp filename; do
            local date_str
            date_str=$(date -d "@${timestamp%.*}" "+%Y-%m-%d %H:%M")
            echo "  📄 $filename ($date_str)"
        done
    else
        info "No recent knowledge base updates"
    fi
    echo ""
}

# Check log file growth
check_log_growth() {
    echo -e "${CYAN}Log File Status:${NC}"
    echo "==============="
    
    # Check main log files
    local log_files=(
        "autonomous_system.log"
        "celery_worker.log"
        "celery_beat.log"
        "orchestrator_20250603.log"
    )
    
    for log_file in "${log_files[@]}"; do
        local full_path="$LOG_DIR/$log_file"
        if [[ -f "$full_path" ]]; then
            local size age lines
            size=$(du -h "$full_path" | cut -f1)
            age=$(stat -c %Y "$full_path" 2>/dev/null || echo 0)
            lines=$(wc -l < "$full_path" 2>/dev/null || echo 0)
            
            local last_modified
            last_modified=$(date -d "@$age" "+%Y-%m-%d %H:%M" 2>/dev/null || echo "unknown")
            
            echo "📝 $log_file: $size ($lines lines, modified: $last_modified)"
        else
            echo "❓ $log_file: Not found"
        fi
    done
    echo ""
}

# Monitor performance metrics
check_performance() {
    echo -e "${CYAN}Performance Metrics:${NC}"
    echo "==================="
    
    # Memory usage
    local memory_info
    memory_info=$(free -h | grep Mem)
    local total_mem used_mem available_mem
    total_mem=$(echo "$memory_info" | awk '{print $2}')
    used_mem=$(echo "$memory_info" | awk '{print $3}')
    available_mem=$(echo "$memory_info" | awk '{print $7}')
    
    echo "💾 Memory: $used_mem / $total_mem used, $available_mem available"
    
    # CPU load
    local load_avg
    load_avg=$(uptime | awk -F'load average:' '{print $2}')
    echo "⚡ CPU Load:$load_avg"
    
    # Disk usage
    local disk_usage
    disk_usage=$(df -h "$PROJECT_ROOT" | tail -1)
    local disk_used disk_available disk_percent
    disk_used=$(echo "$disk_usage" | awk '{print $3}')
    disk_available=$(echo "$disk_usage" | awk '{print $4}')
    disk_percent=$(echo "$disk_usage" | awk '{print $5}')
    
    echo "💿 Disk: $disk_used used, $disk_available available ($disk_percent)"
    
    # Process count
    local python_processes
    python_processes=$(pgrep -f python | wc -l)
    echo "🐍 Python processes: $python_processes"
    
    echo ""
}

# Check for errors in logs
check_recent_errors() {
    echo -e "${CYAN}Recent Errors:${NC}"
    echo "============="
    
    local error_count=0
    
    # Check for errors in recent logs
    if [[ -f "$LOG_DIR/autonomous_system.log" ]]; then
        local recent_errors
        recent_errors=$(tail -1000 "$LOG_DIR/autonomous_system.log" 2>/dev/null | grep -i "error\|exception\|failed" | tail -5 || echo "")
        
        if [[ -n "$recent_errors" ]]; then
            echo "🚨 Recent errors in autonomous_system.log:"
            echo "$recent_errors" | while read -r line; do
                echo "  ❌ $line"
                ((error_count++))
            done
            echo ""
        fi
    fi
    
    if [[ $error_count -eq 0 ]]; then
        echo "✅ No recent errors found in logs"
        echo ""
    fi
}

# Generate monitoring report
generate_report() {
    clear
    echo "════════════════════════════════════════════════════════════════"
    echo "🤖 KAREN AI SECRETARY - AGENT MONITORING DASHBOARD"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    
    get_agent_status
    echo ""
    
    check_agent_activity
    check_knowledge_base
    check_log_growth
    check_performance
    check_recent_errors
    
    echo "════════════════════════════════════════════════════════════════"
    echo "Last Updated: $(date)"
    if [[ "$CONTINUOUS" == "true" ]]; then
        echo "Press Ctrl+C to stop monitoring"
    fi
    echo "════════════════════════════════════════════════════════════════"
}

# Main monitoring loop
main() {
    if [[ "$CONTINUOUS" == "true" ]]; then
        log "Starting continuous agent monitoring (interval: ${INTERVAL}s)"
        log "Press Ctrl+C to stop"
        
        # Set up signal handler
        trap 'echo ""; log "Monitoring stopped"; exit 0' INT TERM
        
        while true; do
            generate_report
            sleep "$INTERVAL"
        done
    else
        generate_report
    fi
}

main
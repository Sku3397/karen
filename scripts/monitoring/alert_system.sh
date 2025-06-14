#!/bin/bash
# Karen AI Secretary - Alert System
# Usage: ./scripts/monitoring/alert_system.sh [--check-only] [--email RECIPIENT]

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
ALERT_LOG="$LOG_DIR/alerts.log"
CHECK_ONLY=false
EMAIL_RECIPIENT=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --check-only)
            CHECK_ONLY=true
            shift
            ;;
        --email)
            EMAIL_RECIPIENT="$2"
            shift 2
            ;;
        *)
            echo "Usage: $0 [--check-only] [--email RECIPIENT]"
            exit 1
            ;;
    esac
done

# Alert thresholds
MEMORY_THRESHOLD=85
DISK_THRESHOLD=90
LOAD_THRESHOLD=3.0
ERROR_THRESHOLD=10
SERVICE_DOWN_CRITICAL=true

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Alert levels
declare -A ALERTS
ALERT_LEVEL="none"  # none, warning, critical

log_alert() {
    local level="$1"
    local message="$2"
    local timestamp
    timestamp=$(date -Iseconds)
    
    # Log to alert file
    mkdir -p "$(dirname "$ALERT_LOG")"
    echo "$timestamp [$level] $message" >> "$ALERT_LOG"
    
    # Display alert
    case "$level" in
        "CRITICAL")
            echo -e "${RED}🚨 CRITICAL ALERT:${NC} $message"
            ALERT_LEVEL="critical"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠️  WARNING:${NC} $message"
            if [[ "$ALERT_LEVEL" != "critical" ]]; then
                ALERT_LEVEL="warning"
            fi
            ;;
        "INFO")
            echo -e "${BLUE}ℹ️  INFO:${NC} $message"
            ;;
    esac
}

# Check system resources
check_system_resources() {
    # Memory check
    local memory_info
    memory_info=$(free | grep Mem)
    local total_mem used_mem
    total_mem=$(echo "$memory_info" | awk '{print $2}')
    used_mem=$(echo "$memory_info" | awk '{print $3}')
    local memory_percent=$((used_mem * 100 / total_mem))
    
    if [[ $memory_percent -gt $MEMORY_THRESHOLD ]]; then
        log_alert "CRITICAL" "Memory usage critical: ${memory_percent}% (threshold: ${MEMORY_THRESHOLD}%)"
        ALERTS["memory"]="critical"
    elif [[ $memory_percent -gt $((MEMORY_THRESHOLD - 10)) ]]; then
        log_alert "WARNING" "Memory usage high: ${memory_percent}%"
        ALERTS["memory"]="warning"
    fi
    
    # Disk space check
    local disk_usage
    disk_usage=$(df "$PROJECT_ROOT" | tail -1 | awk '{print $5}' | sed 's/%//')
    
    if [[ $disk_usage -gt $DISK_THRESHOLD ]]; then
        log_alert "CRITICAL" "Disk space critical: ${disk_usage}% (threshold: ${DISK_THRESHOLD}%)"
        ALERTS["disk"]="critical"
    elif [[ $disk_usage -gt $((DISK_THRESHOLD - 10)) ]]; then
        log_alert "WARNING" "Disk space low: ${disk_usage}%"
        ALERTS["disk"]="warning"
    fi
    
    # CPU load check
    local load_avg
    load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    
    if command -v bc &> /dev/null; then
        if [[ $(echo "$load_avg > $LOAD_THRESHOLD" | bc -l) -eq 1 ]]; then
            log_alert "WARNING" "CPU load high: $load_avg (threshold: $LOAD_THRESHOLD)"
            ALERTS["cpu"]="warning"
        fi
    fi
}

# Check service health
check_services() {
    local pid_dir="$PROJECT_ROOT/pids"
    local services=("celery_worker" "celery_beat" "autonomous")
    
    for service in "${services[@]}"; do
        local pid_file="$pid_dir/${service}.pid"
        
        if [[ ! -f "$pid_file" ]]; then
            log_alert "CRITICAL" "Service $service: PID file missing"
            ALERTS["service_$service"]="critical"
            continue
        fi
        
        local pid
        pid=$(cat "$pid_file")
        
        if ! kill -0 "$pid" 2>/dev/null; then
            log_alert "CRITICAL" "Service $service: Process not running (PID: $pid)"
            ALERTS["service_$service"]="critical"
        fi
    done
    
    # Check Redis
    if ! redis-cli ping > /dev/null 2>&1; then
        log_alert "CRITICAL" "Redis service not responding"
        ALERTS["redis"]="critical"
    fi
}

# Check for errors in logs
check_log_errors() {
    local error_count=0
    local log_files=(
        "$LOG_DIR/autonomous_system.log"
        "$LOG_DIR/celery_worker.log"
        "$LOG_DIR/celery_beat.log"
    )
    
    for log_file in "${log_files[@]}"; do
        if [[ -f "$log_file" ]]; then
            # Count errors in the last hour
            local recent_errors
            recent_errors=$(find "$log_file" -mmin -60 -exec grep -c -i "error\|exception\|critical" {} \; 2>/dev/null || echo 0)
            error_count=$((error_count + recent_errors))
        fi
    done
    
    if [[ $error_count -gt $ERROR_THRESHOLD ]]; then
        log_alert "WARNING" "High error rate: $error_count errors in last hour (threshold: $ERROR_THRESHOLD)"
        ALERTS["errors"]="warning"
    fi
}

# Check agent performance
check_agent_performance() {
    local state_file="$PROJECT_ROOT/autonomous_state.json"
    
    if [[ ! -f "$state_file" ]]; then
        log_alert "WARNING" "Autonomous state file not found"
        ALERTS["agents"]="warning"
        return
    fi
    
    # Check if agents are stuck
    local agent_status
    agent_status=$(python3 -c "
import json
from datetime import datetime, timedelta

try:
    with open('$state_file', 'r') as f:
        data = json.load(f)
    
    start_time_str = data.get('start_time', '')
    if start_time_str:
        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        runtime_hours = (datetime.now().astimezone() - start_time).total_seconds() / 3600
        
        # Check if system has been running for more than 6 hours with no completed tasks
        agent_states = data.get('agent_states', {})
        total_completed = sum(agent.get('tasks_completed', 0) for agent in agent_states.values())
        
        if runtime_hours > 1 and total_completed == 0:
            print('STUCK')
        elif runtime_hours > 6:
            print('LONG_RUNNING')
        else:
            print('OK')
    else:
        print('NO_START_TIME')
        
except Exception as e:
    print('ERROR')
" 2>/dev/null)
    
    case "$agent_status" in
        "STUCK")
            log_alert "WARNING" "Agents may be stuck - no tasks completed after 1+ hours"
            ALERTS["agents"]="warning"
            ;;
        "LONG_RUNNING")
            log_alert "INFO" "System has been running for 6+ hours"
            ;;
        "ERROR"|"NO_START_TIME")
            log_alert "WARNING" "Cannot determine agent status"
            ALERTS["agents"]="warning"
            ;;
    esac
}

# Check file system issues
check_filesystem() {
    # Check for large log files
    local large_logs
    large_logs=$(find "$LOG_DIR" -type f -size +500M 2>/dev/null | wc -l)
    
    if [[ $large_logs -gt 0 ]]; then
        log_alert "WARNING" "Found $large_logs log files larger than 500MB"
        ALERTS["filesystem"]="warning"
    fi
    
    # Check for old files that might need cleanup
    local old_files
    old_files=$(find "$PROJECT_ROOT" -name "*.log" -mtime +30 2>/dev/null | wc -l)
    
    if [[ $old_files -gt 100 ]]; then
        log_alert "INFO" "Found $old_files log files older than 30 days - consider cleanup"
    fi
}

# Send email alert (if configured)
send_email_alert() {
    local recipient="$1"
    local subject="$2"
    local body="$3"
    
    if command -v mail &> /dev/null; then
        echo "$body" | mail -s "$subject" "$recipient"
        log_alert "INFO" "Email alert sent to $recipient"
    elif command -v sendmail &> /dev/null; then
        {
            echo "To: $recipient"
            echo "Subject: $subject"
            echo ""
            echo "$body"
        } | sendmail "$recipient"
        log_alert "INFO" "Email alert sent to $recipient via sendmail"
    else
        log_alert "WARNING" "Cannot send email - no mail command available"
    fi
}

# Generate alert summary
generate_alert_summary() {
    local summary=""
    local critical_count=0
    local warning_count=0
    
    for alert_key in "${!ALERTS[@]}"; do
        local alert_level="${ALERTS[$alert_key]}"
        if [[ "$alert_level" == "critical" ]]; then
            ((critical_count++))
        elif [[ "$alert_level" == "warning" ]]; then
            ((warning_count++))
        fi
        summary="${summary}\n- ${alert_key}: ${alert_level}"
    done
    
    if [[ $critical_count -gt 0 ]]; then
        echo -e "CRITICAL ALERTS DETECTED!\n\nSummary:$summary"
    elif [[ $warning_count -gt 0 ]]; then
        echo -e "Warning alerts detected.\n\nSummary:$summary"
    else
        echo "All systems operating normally."
    fi
}

# Main alert check function
main() {
    echo "🚨 Karen AI Secretary - Alert System Check"
    echo "=========================================="
    echo "Timestamp: $(date)"
    echo ""
    
    # Perform all checks
    check_system_resources
    check_services
    check_log_errors
    check_agent_performance
    check_filesystem
    
    # Generate summary
    local summary
    summary=$(generate_alert_summary)
    echo ""
    echo "$summary"
    
    # Send email if needed and not in check-only mode
    if [[ "$CHECK_ONLY" == "false" && -n "$EMAIL_RECIPIENT" && "$ALERT_LEVEL" != "none" ]]; then
        local subject="Karen AI Alert - $ALERT_LEVEL"
        send_email_alert "$EMAIL_RECIPIENT" "$subject" "$summary"
    fi
    
    # Exit with appropriate code
    case "$ALERT_LEVEL" in
        "critical") exit 2 ;;
        "warning") exit 1 ;;
        *) exit 0 ;;
    esac
}

main
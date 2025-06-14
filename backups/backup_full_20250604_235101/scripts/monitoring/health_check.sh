#!/bin/bash
# Karen AI Secretary - Health Check Script
# Usage: ./scripts/monitoring/health_check.sh [--json|--brief|--detailed]

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PID_DIR="$PROJECT_ROOT/pids"
LOG_DIR="$PROJECT_ROOT/logs"
OUTPUT_FORMAT="${1:-detailed}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Health check results
declare -A HEALTH_STATUS
declare -A HEALTH_DETAILS
OVERALL_HEALTH="healthy"

log() {
    if [[ "$OUTPUT_FORMAT" != "--json" ]]; then
        echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
    fi
}

error() {
    if [[ "$OUTPUT_FORMAT" != "--json" ]]; then
        echo -e "${RED}[ERROR]${NC} $1" >&2
    fi
}

warning() {
    if [[ "$OUTPUT_FORMAT" != "--json" ]]; then
        echo -e "${YELLOW}[WARNING]${NC} $1"
    fi
}

info() {
    if [[ "$OUTPUT_FORMAT" != "--json" ]]; then
        echo -e "${BLUE}[INFO]${NC} $1"
    fi
}

# Check if a process is running by PID file
check_process() {
    local service_name="$1"
    local pid_file="$PID_DIR/${service_name}.pid"
    
    if [[ ! -f "$pid_file" ]]; then
        HEALTH_STATUS["$service_name"]="down"
        HEALTH_DETAILS["$service_name"]="PID file not found"
        OVERALL_HEALTH="unhealthy"
        return 1
    fi
    
    local pid
    pid=$(cat "$pid_file")
    
    if ! kill -0 "$pid" 2>/dev/null; then
        HEALTH_STATUS["$service_name"]="down"
        HEALTH_DETAILS["$service_name"]="Process not running (PID: $pid)"
        OVERALL_HEALTH="unhealthy"
        return 1
    fi
    
    # Check process age and memory usage
    local process_info
    process_info=$(ps -p "$pid" -o pid,ppid,etime,pcpu,pmem,cmd --no-headers 2>/dev/null || echo "")
    
    if [[ -n "$process_info" ]]; then
        local cpu_usage memory_usage elapsed_time
        cpu_usage=$(echo "$process_info" | awk '{print $4}')
        memory_usage=$(echo "$process_info" | awk '{print $5}')
        elapsed_time=$(echo "$process_info" | awk '{print $3}')
        
        HEALTH_STATUS["$service_name"]="running"
        HEALTH_DETAILS["$service_name"]="PID: $pid, CPU: ${cpu_usage}%, MEM: ${memory_usage}%, Uptime: $elapsed_time"
    else
        HEALTH_STATUS["$service_name"]="unknown"
        HEALTH_DETAILS["$service_name"]="Process info unavailable"
    fi
}

# Check Redis health
check_redis() {
    local service_name="redis"
    
    if ! command -v redis-cli &> /dev/null; then
        HEALTH_STATUS["$service_name"]="unavailable"
        HEALTH_DETAILS["$service_name"]="Redis CLI not found"
        return 1
    fi
    
    local redis_response
    redis_response=$(redis-cli ping 2>/dev/null || echo "ERROR")
    
    if [[ "$redis_response" == "PONG" ]]; then
        # Get Redis info
        local memory_used connections_received
        memory_used=$(redis-cli info memory 2>/dev/null | grep "used_memory_human:" | cut -d: -f2 | tr -d '\r' || echo "unknown")
        connections_received=$(redis-cli info stats 2>/dev/null | grep "total_connections_received:" | cut -d: -f2 | tr -d '\r' || echo "unknown")
        
        HEALTH_STATUS["$service_name"]="running"
        HEALTH_DETAILS["$service_name"]="Memory: $memory_used, Connections: $connections_received"
    else
        HEALTH_STATUS["$service_name"]="down"
        HEALTH_DETAILS["$service_name"]="Not responding to ping"
        OVERALL_HEALTH="unhealthy"
    fi
}

# Check disk space
check_disk_space() {
    local service_name="disk_space"
    local usage
    usage=$(df "$PROJECT_ROOT" | tail -1 | awk '{print $5}' | sed 's/%//')
    
    if [[ $usage -gt 90 ]]; then
        HEALTH_STATUS["$service_name"]="critical"
        HEALTH_DETAILS["$service_name"]="${usage}% used - critically low"
        OVERALL_HEALTH="unhealthy"
    elif [[ $usage -gt 80 ]]; then
        HEALTH_STATUS["$service_name"]="warning"
        HEALTH_DETAILS["$service_name"]="${usage}% used - getting low"
        if [[ "$OVERALL_HEALTH" == "healthy" ]]; then
            OVERALL_HEALTH="degraded"
        fi
    else
        HEALTH_STATUS["$service_name"]="good"
        HEALTH_DETAILS["$service_name"]="${usage}% used"
    fi
}

# Check log file sizes
check_log_sizes() {
    local service_name="log_files"
    local total_size large_files
    
    if [[ ! -d "$LOG_DIR" ]]; then
        HEALTH_STATUS["$service_name"]="unknown"
        HEALTH_DETAILS["$service_name"]="Log directory not found"
        return 1
    fi
    
    total_size=$(du -sh "$LOG_DIR" 2>/dev/null | cut -f1 || echo "unknown")
    large_files=$(find "$LOG_DIR" -type f -size +100M 2>/dev/null | wc -l)
    
    if [[ $large_files -gt 0 ]]; then
        HEALTH_STATUS["$service_name"]="warning"
        HEALTH_DETAILS["$service_name"]="Total: $total_size, Large files: $large_files"
        if [[ "$OVERALL_HEALTH" == "healthy" ]]; then
            OVERALL_HEALTH="degraded"
        fi
    else
        HEALTH_STATUS["$service_name"]="good"
        HEALTH_DETAILS["$service_name"]="Total: $total_size"
    fi
}

# Check autonomous system status
check_autonomous_status() {
    local service_name="autonomous_system"
    local state_file="$PROJECT_ROOT/autonomous_state.json"
    
    if [[ ! -f "$state_file" ]]; then
        HEALTH_STATUS["$service_name"]="unknown"
        HEALTH_DETAILS["$service_name"]="State file not found"
        return 1
    fi
    
    # Parse the state file
    local total_completed runtime
    total_completed=$(python3 -c "
import json
try:
    with open('$state_file', 'r') as f:
        data = json.load(f)
    total = sum(agent.get('tasks_completed', 0) for agent in data.get('agent_states', {}).values())
    print(total)
except:
    print('0')
" 2>/dev/null)
    
    runtime=$(python3 -c "
import json
try:
    with open('$state_file', 'r') as f:
        data = json.load(f)
    print(data.get('runtime', 'unknown'))
except:
    print('unknown')
" 2>/dev/null)
    
    HEALTH_STATUS["$service_name"]="running"
    HEALTH_DETAILS["$service_name"]="Tasks completed: $total_completed, Runtime: $runtime"
}

# Check email processing
check_email_processing() {
    local service_name="email_processing"
    local last_activity
    
    # Check for recent email activity in logs
    if [[ -f "$LOG_DIR/email_agent_activity.log" ]]; then
        last_activity=$(tail -1 "$LOG_DIR/email_agent_activity.log" 2>/dev/null | head -c 19 || echo "")
        
        if [[ -n "$last_activity" ]]; then
            HEALTH_STATUS["$service_name"]="active"
            HEALTH_DETAILS["$service_name"]="Last activity: $last_activity"
        else
            HEALTH_STATUS["$service_name"]="unknown"
            HEALTH_DETAILS["$service_name"]="No recent activity found"
        fi
    else
        HEALTH_STATUS["$service_name"]="unknown"
        HEALTH_DETAILS["$service_name"]="Email activity log not found"
    fi
}

# Check system resources
check_system_resources() {
    local service_name="system_resources"
    
    # Memory usage
    local memory_info
    memory_info=$(free | grep Mem)
    local total_mem used_mem
    total_mem=$(echo "$memory_info" | awk '{print $2}')
    used_mem=$(echo "$memory_info" | awk '{print $3}')
    local memory_percent=$((used_mem * 100 / total_mem))
    
    # CPU load
    local load_avg
    load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    
    # Check thresholds
    if [[ $memory_percent -gt 90 ]] || [[ $(echo "$load_avg > 4.0" | bc -l 2>/dev/null || echo 0) -eq 1 ]]; then
        HEALTH_STATUS["$service_name"]="critical"
        HEALTH_DETAILS["$service_name"]="Memory: ${memory_percent}%, Load: $load_avg"
        OVERALL_HEALTH="unhealthy"
    elif [[ $memory_percent -gt 80 ]] || [[ $(echo "$load_avg > 2.0" | bc -l 2>/dev/null || echo 0) -eq 1 ]]; then
        HEALTH_STATUS["$service_name"]="warning"
        HEALTH_DETAILS["$service_name"]="Memory: ${memory_percent}%, Load: $load_avg"
        if [[ "$OVERALL_HEALTH" == "healthy" ]]; then
            OVERALL_HEALTH="degraded"
        fi
    else
        HEALTH_STATUS["$service_name"]="good"
        HEALTH_DETAILS["$service_name"]="Memory: ${memory_percent}%, Load: $load_avg"
    fi
}

# Generate JSON output
output_json() {
    local timestamp
    timestamp=$(date -Iseconds)
    
    echo "{"
    echo "  \"timestamp\": \"$timestamp\","
    echo "  \"overall_health\": \"$OVERALL_HEALTH\","
    echo "  \"services\": {"
    
    local first=true
    for service in "${!HEALTH_STATUS[@]}"; do
        if [[ "$first" == "true" ]]; then
            first=false
        else
            echo ","
        fi
        echo -n "    \"$service\": {\"status\": \"${HEALTH_STATUS[$service]}\", \"details\": \"${HEALTH_DETAILS[$service]}\"}"
    done
    
    echo ""
    echo "  }"
    echo "}"
}

# Generate brief output
output_brief() {
    echo "Karen AI Secretary Health: $OVERALL_HEALTH"
    for service in "${!HEALTH_STATUS[@]}"; do
        local status_icon
        case "${HEALTH_STATUS[$service]}" in
            "running"|"good"|"active") status_icon="✅" ;;
            "warning"|"degraded") status_icon="⚠️" ;;
            "down"|"critical") status_icon="❌" ;;
            *) status_icon="❓" ;;
        esac
        echo "$status_icon $service: ${HEALTH_STATUS[$service]}"
    done
}

# Generate detailed output
output_detailed() {
    log "🏥 Karen AI Secretary Health Check"
    log "Overall Status: $OVERALL_HEALTH"
    echo ""
    
    for service in "${!HEALTH_STATUS[@]}"; do
        local status_color
        case "${HEALTH_STATUS[$service]}" in
            "running"|"good"|"active") status_color="$GREEN" ;;
            "warning"|"degraded") status_color="$YELLOW" ;;
            "down"|"critical") status_color="$RED" ;;
            *) status_color="$BLUE" ;;
        esac
        
        echo -e "${status_color}$service${NC}: ${HEALTH_STATUS[$service]}"
        echo "  └─ ${HEALTH_DETAILS[$service]}"
        echo ""
    done
}

# Main health check function
main() {
    # Initialize health checks
    check_process "celery_worker"
    check_process "celery_beat"
    check_process "autonomous"
    check_redis
    check_disk_space
    check_log_sizes
    check_autonomous_status
    check_email_processing
    check_system_resources
    
    # Generate output based on format
    case "$OUTPUT_FORMAT" in
        "--json")
            output_json
            ;;
        "--brief")
            output_brief
            ;;
        "--detailed"|*)
            output_detailed
            ;;
    esac
    
    # Save health check to file
    local health_file="$LOG_DIR/system/health_check_$(date +%Y%m%d_%H%M%S).json"
    mkdir -p "$(dirname "$health_file")"
    output_json > "$health_file"
    
    # Exit with appropriate code
    case "$OVERALL_HEALTH" in
        "healthy") exit 0 ;;
        "degraded") exit 1 ;;
        "unhealthy") exit 2 ;;
        *) exit 3 ;;
    esac
}

main
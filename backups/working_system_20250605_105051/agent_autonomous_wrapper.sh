#!/bin/bash
# Agent Autonomous Wrapper Script for Karen AI
# 
# This script makes Claude Code agents fully autonomous by:
# 1. Monitoring for new task instructions
# 2. Executing agent workflows automatically
# 3. Handling completion detection and logging
# 4. Integrating with Karen's agent communication system
# 5. Providing error handling and recovery

set -uo pipefail  # Temporarily removed -e for debugging

# Script Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
AGENT_NAME="${1:-}"
LOG_LEVEL="DEBUG"  # Forced DEBUG for testing
MAX_TASK_RUNTIME="${MAX_TASK_RUNTIME:-3600}"  # 1 hour max per task
HEALTH_CHECK_INTERVAL="${HEALTH_CHECK_INTERVAL:-30}"  # 30 seconds

# Directories
AGENT_INSTRUCTIONS_DIR="$PROJECT_ROOT/agent_instructions"
AGENT_PROGRESS_DIR="$PROJECT_ROOT/agent_progress"
COMMUNICATION_DIR="$PROJECT_ROOT/autonomous-agents/communication"
INBOX_DIR="$COMMUNICATION_DIR/inbox"
LOGS_DIR="$PROJECT_ROOT/logs/agents"

# Files
INSTRUCTION_FILE="$AGENT_INSTRUCTIONS_DIR/${AGENT_NAME}_current_task.md"
COMPLETION_LOG="$AGENT_PROGRESS_DIR/completions.log"
ERROR_LOG="$LOGS_DIR/${AGENT_NAME}_errors.log"
HEALTH_LOG="$LOGS_DIR/${AGENT_NAME}_health.log"
PID_FILE="$AGENT_PROGRESS_DIR/${AGENT_NAME}.pid"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case "$level" in
        ERROR)   echo -e "${RED}[$timestamp] [$AGENT_NAME] ERROR: $message${NC}" ;;
        WARN)    echo -e "${YELLOW}[$timestamp] [$AGENT_NAME] WARN: $message${NC}" ;;
        INFO)    echo -e "${GREEN}[$timestamp] [$AGENT_NAME] INFO: $message${NC}" ;;
        DEBUG)   echo -e "${BLUE}[$timestamp] [$AGENT_NAME] DEBUG: $message${NC}" ;;
        SUCCESS) echo -e "${PURPLE}[$timestamp] [$AGENT_NAME] SUCCESS: $message${NC}" ;;
        TASK)    echo -e "${CYAN}[$timestamp] [$AGENT_NAME] TASK: $message${NC}" ;;
    esac
    
    # Also log to file
    echo "[$timestamp] [$AGENT_NAME] [$level] $message" >> "$HEALTH_LOG"
}

# --- START JQ COMMAND SETUP ---
# Determine the jq command to use
JQ_CMD=""
# Project root is defined as SCRIPT_DIR
LOCAL_JQ_PATH="$PROJECT_ROOT/scripts/jq.exe"

if [ -x "$LOCAL_JQ_PATH" ]; then
    JQ_CMD="$LOCAL_JQ_PATH"
    log INFO "Using local jq executable at $JQ_CMD"
elif command -v jq >/dev/null 2>&1; then
    JQ_CMD="jq"
    log INFO "Using jq found in PATH"
else
    log ERROR "jq command not found. Checked local path: $LOCAL_JQ_PATH and system PATH. Please ensure jq.exe is in scripts/ or jq is in PATH."
    exit 1
fi
# --- END JQ COMMAND SETUP ---

# Error handling
error_handler() {
    local line_number="$1"
    local error_code="$2"
    local command="$BASH_COMMAND"
    
    log ERROR "Script failed at line $line_number with exit code $error_code"
    log ERROR "Failed command: $command"
    
    # Log to error file
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Line $line_number: $command (exit $error_code)" >> "$ERROR_LOG"
    
    # Cleanup
    cleanup_handler
    exit "$error_code"
}

# Cleanup handler
cleanup_handler() {
    log INFO "Cleaning up agent wrapper..."
    
    # Remove PID file
    [ -f "$PID_FILE" ] && rm -f "$PID_FILE"
    
    # Signal any child processes to stop
    if [ -n "${AGENT_PID:-}" ]; then
        kill -TERM "$AGENT_PID" 2>/dev/null || true
    fi
}

# Setup signal handlers
trap 'error_handler ${LINENO} $?' ERR
trap 'cleanup_handler; exit 0' SIGINT SIGTERM

# Validate input
validate_setup() {
    if [ -z "$AGENT_NAME" ]; then
        echo "Usage: $0 <agent_name>"
        echo "Available agents: orchestrator, memory_engineer, sms_engineer, test_engineer, archaeologist"
        exit 1
    fi
    
    # Create required directories
    mkdir -p "$AGENT_INSTRUCTIONS_DIR" "$AGENT_PROGRESS_DIR" "$LOGS_DIR"
    mkdir -p "$INBOX_DIR/$AGENT_NAME"
    
    # Initialize log files
    touch "$COMPLETION_LOG" "$ERROR_LOG" "$HEALTH_LOG"
    
    log INFO "Agent wrapper initialized for $AGENT_NAME"
    log INFO "Project root: $PROJECT_ROOT"
    log INFO "Instruction file: $INSTRUCTION_FILE"
}

# Check if another instance is running
check_existing_instance() {
    if [ -f "$PID_FILE" ]; then
        local existing_pid=$(cat "$PID_FILE")
        # More robust check: verify if the PID exists and its command line matches the current script and agent
        # This requires knowing how the script is named/called, $0 might be ./agent_autonomous_wrapper.sh
        # Using ps and grepping for the script name and agent name is a common approach.
        # The exact ps options and grep pattern might need tuning based on the OS/environment.
        if ps -p "$existing_pid" -o args= | grep -q "agent_autonomous_wrapper.sh.*$AGENT_NAME" 2>/dev/null; then
            log ERROR "Agent wrapper for $AGENT_NAME appears to be already running with PID $existing_pid. Command: $(ps -p "$existing_pid" -o args=)"
            log ERROR "If this is incorrect, please remove the PID file: $PID_FILE"
            exit 1
        else
            log WARN "Stale PID file found for $AGENT_NAME (PID $existing_pid not a running instance of this agent or not found), removing..."
            rm -f "$PID_FILE"
        fi
    fi
    
    # Store current PID
    echo $$ > "$PID_FILE"
}

# Check agent health
check_agent_health() {
    local health_status="healthy"
    local issues=()
    
    # Check memory usage
    if command -v free >/dev/null 2>&1; then
        local memory_usage=$(free | awk '/^Mem:/{printf "%.1f", $3/$2 * 100}')
        if (( $(echo "$memory_usage > 90" | bc -l) )); then
            issues+=("High memory usage: ${memory_usage}%")
            health_status="degraded"
        fi
    fi
    
    # Check disk space
    local disk_usage=$(df "$PROJECT_ROOT" | awk 'NR==2{print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 90 ]; then
        issues+=("High disk usage: ${disk_usage}%")
        health_status="degraded"
    fi
    
    # Check if instruction file is stuck (older than 2 hours)
    if [ -f "${INSTRUCTION_FILE}.processing" ]; then
        local file_age=$(($(date +%s) - $(stat -c %Y "${INSTRUCTION_FILE}.processing")))
        if [ "$file_age" -gt 7200 ]; then
            issues+=("Task stuck for $(($file_age / 3600)) hours")
            health_status="unhealthy"
        fi
    fi
    
    # Log health status
    if [ "$health_status" = "healthy" ]; then
        log DEBUG "Health check passed"
    else
        log WARN "Health issues detected: ${issues[*]}"
    fi
    
    # Create health report
    cat > "$AGENT_PROGRESS_DIR/${AGENT_NAME}_health.json" << EOF
{
    "agent": "$AGENT_NAME",
    "status": "$health_status",
    "timestamp": "$(date -Iseconds)",
    "memory_usage": "${memory_usage:-unknown}%",
    "disk_usage": "${disk_usage}%",
    "issues": [$(printf '"%s",' "${issues[@]}" | sed 's/,$//')],
    "uptime_seconds": $(($SECONDS))
}
EOF
}

# Process agent communication inbox
process_inbox_messages() {
    local inbox_path="$INBOX_DIR/$AGENT_NAME"
    
    # Process any new messages
    for message_file in "$inbox_path"/*.json; do
        [ -f "$message_file" ] || continue
        
        local filename=$(basename "$message_file")
        
        # Skip processed messages
        [[ "$filename" == processed_* ]] && continue
        
        log INFO "Processing inbox message: $filename"
        
        # Extract message content
        local message_type=$($JQ_CMD -r '.type // "unknown"' "$message_file" 2>/dev/null || echo "unknown")
        local from_agent=$($JQ_CMD -r '.from // "unknown"' "$message_file" 2>/dev/null || echo "unknown")
        local content=$($JQ_CMD -r '.content // {}' "$message_file" 2>/dev/null || echo "{}")
        
        log INFO "Message from $from_agent: $message_type"
        
        # Convert message to task instruction if applicable
        if [[ "$message_type" == *"task_assignment"* ]] || [[ "$message_type" == *"priority"* ]]; then
            convert_message_to_task "$message_file"
        fi
        
        # Mark as processed
        mv "$message_file" "$inbox_path/processed_$filename"
        log DEBUG "Message processed and archived"
    done
}

# Convert communication message to task instruction
convert_message_to_task() {
    local message_file="$1"
    
    # Extract task details from message
    local task_content=$($JQ_CMD -r '.content.task_assignment.description // .content // "No description"' "$message_file" 2>/dev/null)
    local priority=$($JQ_CMD -r '.content.task_assignment.priority // "medium"' "$message_file" 2>/dev/null)
    local deadline=$($JQ_CMD -r '.content.task_assignment.deadline // "none"' "$message_file" 2>/dev/null)
    
    # Only create task if no current task exists
    if [ ! -f "$INSTRUCTION_FILE" ] && [ ! -f "${INSTRUCTION_FILE}.processing" ]; then
        cat > "$INSTRUCTION_FILE" << EOF
# Agent Task: $AGENT_NAME
**Priority:** $priority
**Deadline:** $deadline
**Source:** Agent Communication System
**Timestamp:** $(date -Iseconds)

## Task Description
$task_content

## Instructions
Please complete this task and update the agent communication system with results.

## Success Criteria
- Task completion logged to agent communication system
- Results shared with requesting agent
- Status updated in task tracking system
EOF
        
        log TASK "Created new task from communication message"
    else
        log WARN "Cannot create task - agent is already busy"
    fi
}

# Execute task with Claude Code agent
execute_task() {
    local instruction_file="$1"
    local processing_file="${instruction_file}.processing"
    
    log TASK "Starting task execution"
    log INFO "Instruction file: $instruction_file"
    
    # Move to processing
    mv "$instruction_file" "$processing_file"
    rm -f "$instruction_file" # Explicitly remove the original source file
    
    # Show task to agent (in practice, this would integrate with Claude Code)
    log INFO "Task content:"
    echo "$(cat "$processing_file")" | sed 's/^/  │ /'
    
    # Simulate agent work (replace with actual Claude Code integration)
    local task_start_time=$(date +%s)
    local timeout_time=$((task_start_time + MAX_TASK_RUNTIME))
    
    # In a real implementation, you would:
    # 1. Launch Claude Code with the instruction file
    # 2. Monitor for completion signals
    # 3. Handle timeouts and errors
    
    # For demonstration, we'll simulate work
    log INFO "Agent is working on task..."
    
    # Simulate some work time (replace with actual agent monitoring)
    local work_duration=$((RANDOM % 60 + 30))  # 30-90 seconds
    log DEBUG "Simulating work for $work_duration seconds..."
    
    for ((i=1; i<=work_duration; i++)); do
        sleep 1
        
        # Check for timeout
        if [ "$(date +%s)" -gt "$timeout_time" ]; then
            log ERROR "Task timed out after $MAX_TASK_RUNTIME seconds"
            return 1
        fi
        
        # Show progress
        if (( i % 10 == 0 )); then
            log DEBUG "Task progress: $i/$work_duration seconds"
        fi
    done
    
    # Simulate successful completion
    local completion_time=$(date +%s)
    local duration=$((completion_time - task_start_time))
    
    # Log completion
    log SUCCESS "Task completed in $duration seconds"
    
    # Create completion record
    local completion_record="{
        \"agent\": \"$AGENT_NAME\",
        \"task_file\": \"$(basename "$processing_file")\",
        \"start_time\": \"$(date -d @$task_start_time -Iseconds)\",
        \"completion_time\": \"$(date -d @$completion_time -Iseconds)\",
        \"duration_seconds\": $duration,
        \"status\": \"completed\"
    }"
    
    # Log to completion file
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Task completed by $AGENT_NAME in ${duration}s" >> "$COMPLETION_LOG"
    echo "$completion_record" >> "$AGENT_PROGRESS_DIR/${AGENT_NAME}_completions.jsonl"
    
    # Notify other agents if needed
    notify_task_completion "$completion_record"
    
    # Clean up processing file
    mv "$processing_file" "$AGENT_PROGRESS_DIR/completed_$(basename "$processing_file")_$(date +%Y%m%d_%H%M%S)"
    
    return 0
}

# Notify other agents of task completion
notify_task_completion() {
    local completion_record="$1"
    
    # Create notification for orchestrator
    local notification_file="$INBOX_DIR/orchestrator/${AGENT_NAME}_completion_$(date +%Y%m%d_%H%M%S).json"
    
    cat > "$notification_file" << EOF
{
    "from": "$AGENT_NAME",
    "to": "orchestrator",
    "type": "task_completion",
    "timestamp": "$(date -Iseconds)",
    "content": {
        "completion_details": $completion_record,
        "agent_status": "available",
        "next_task_ready": true
    }
}
EOF
    
    log INFO "Notified orchestrator of task completion"
}

# Main monitoring loop
main_loop() {
    log INFO "Starting autonomous agent wrapper for $AGENT_NAME"
    log INFO "Process ID: $$"
    
    local iteration=0
    
    while true; do
        iteration=$((iteration + 1))
        
        # Health check every N iterations
        if (( iteration % (HEALTH_CHECK_INTERVAL / 10) == 0 )); then
            check_agent_health
        fi
        
        # Process inbox messages
        process_inbox_messages
        
        # Check for new task instructions
        if [ -f "$INSTRUCTION_FILE" ]; then
            log TASK "New task instruction found"
            
            if execute_task "$INSTRUCTION_FILE"; then
                log SUCCESS "Task execution completed successfully"
            else
                log ERROR "Task execution failed"
                # Move failed task to error directory
                mkdir -p "$AGENT_PROGRESS_DIR/failed"
                mv "${INSTRUCTION_FILE}.processing" "$AGENT_PROGRESS_DIR/failed/failed_$(basename "$INSTRUCTION_FILE")_$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true
            fi
            
            log INFO "DIAGNOSTIC: Exiting after one task processing cycle."
            exit 0 # DIAGNOSTIC: Exit after one task cycle
        fi
        
        # Check if we're currently processing a task
        if [ -f "${INSTRUCTION_FILE}.processing" ]; then
            log DEBUG "Agent busy processing task..."
        else
            log DEBUG "Agent available for new tasks (iteration $iteration)"
        fi
        
        # Sleep before next iteration
        sleep 10
    done
}

# Print usage information
print_usage() {
    cat << EOF
Agent Autonomous Wrapper for Karen AI

Usage: $0 <agent_name>

Available agents:
  - orchestrator     : Main coordination agent
  - memory_engineer  : Memory and context management
  - sms_engineer     : SMS system implementation
  - test_engineer    : Testing and quality assurance  
  - archaeologist    : System analysis and discovery

Environment variables:
  LOG_LEVEL              : Logging level (DEBUG, INFO, WARN, ERROR)
  MAX_TASK_RUNTIME       : Maximum seconds per task (default: 3600)
  HEALTH_CHECK_INTERVAL  : Health check frequency in seconds (default: 30)

Examples:
  $0 orchestrator        # Start orchestrator agent wrapper
  $0 memory_engineer     # Start memory engineer agent wrapper
  
  LOG_LEVEL=DEBUG $0 sms_engineer     # Start with debug logging
EOF
}

# Main script execution
main() {
    # LOG_LEVEL is already forced to DEBUG at the top of the script.
    # Show usage if no arguments
    if [ $# -eq 0 ]; then
        print_usage
        exit 1
    fi
    
    # Handle help flag
    if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
        print_usage
        exit 0
    fi
    
    # Setup and validation
    validate_setup
    check_existing_instance
    
    # Start main loop
    main_loop
}

# Execute main function with all arguments
main "$@"
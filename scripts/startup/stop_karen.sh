#!/bin/bash
# Karen AI Secretary - Shutdown Script
# Usage: ./scripts/startup/stop_karen.sh [graceful|force]

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PID_DIR="$PROJECT_ROOT/pids"
LOG_DIR="$PROJECT_ROOT/logs"
SHUTDOWN_MODE="${1:-graceful}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
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

# Stop a service by PID file
stop_service() {
    local service_name="$1"
    local pid_file="$PID_DIR/${service_name}.pid"
    local timeout="${2:-30}"
    
    if [[ ! -f "$pid_file" ]]; then
        info "$service_name: No PID file found, assuming not running"
        return 0
    fi
    
    local pid
    pid=$(cat "$pid_file")
    
    if ! kill -0 "$pid" 2>/dev/null; then
        warning "$service_name: Process $pid not running, cleaning up PID file"
        rm -f "$pid_file"
        return 0
    fi
    
    log "Stopping $service_name (PID: $pid)..."
    
    if [[ "$SHUTDOWN_MODE" == "force" ]]; then
        kill -KILL "$pid" 2>/dev/null || true
        rm -f "$pid_file"
        log "$service_name stopped forcefully"
        return 0
    fi
    
    # Graceful shutdown
    kill -TERM "$pid" 2>/dev/null || true
    
    # Wait for graceful shutdown
    local count=0
    while kill -0 "$pid" 2>/dev/null && [[ $count -lt $timeout ]]; do
        sleep 1
        ((count++))
    done
    
    if kill -0 "$pid" 2>/dev/null; then
        warning "$service_name didn't stop gracefully, forcing..."
        kill -KILL "$pid" 2>/dev/null || true
    fi
    
    rm -f "$pid_file"
    log "$service_name stopped"
}

# Stop Autonomous Agents
stop_autonomous_agents() {
    log "Stopping Autonomous Agent System..."
    stop_service "autonomous" 45
}

# Stop Frontend
stop_frontend() {
    log "Stopping Frontend..."
    stop_service "frontend" 15
}

# Stop FastAPI
stop_fastapi() {
    log "Stopping FastAPI..."
    stop_service "fastapi" 30
}

# Stop Celery Beat
stop_celery_beat() {
    log "Stopping Celery Beat..."
    stop_service "celery_beat" 30
}

# Stop Celery Worker
stop_celery_worker() {
    log "Stopping Celery Worker..."
    stop_service "celery_worker" 45
}

# Stop Redis (if managed by us)
stop_redis() {
    if [[ "${STOP_REDIS:-false}" == "true" ]]; then
        log "Stopping Redis..."
        
        # Check if Redis is running in Docker
        if docker ps --format "{{.Names}}" | grep -q "karen-redis"; then
            docker stop karen-redis 2>/dev/null || true
            docker rm karen-redis 2>/dev/null || true
            log "Redis Docker container stopped"
        elif pgrep redis-server > /dev/null; then
            if [[ "$SHUTDOWN_MODE" == "force" ]]; then
                pkill -KILL redis-server 2>/dev/null || true
            else
                redis-cli shutdown 2>/dev/null || true
            fi
            log "Redis server stopped"
        else
            info "Redis not running or not managed by Karen"
        fi
    else
        info "Redis shutdown skipped (set STOP_REDIS=true to enable)"
    fi
}

# Clean up any orphaned processes
cleanup_orphans() {
    if [[ "$SHUTDOWN_MODE" == "force" ]]; then
        log "Cleaning up orphaned processes..."
        
        # Kill any remaining celery processes
        pkill -f "celery.*karen" 2>/dev/null || true
        
        # Kill any remaining Python processes related to Karen
        pkill -f "python.*orchestrator" 2>/dev/null || true
        pkill -f "python.*autonomous" 2>/dev/null || true
        
        log "Orphaned processes cleaned up"
    fi
}

# Save shutdown information
save_shutdown_info() {
    local shutdown_time
    shutdown_time=$(date -Iseconds)
    
    cat > "$PROJECT_ROOT/last_shutdown.json" << EOF
{
  "shutdown_at": "$shutdown_time",
  "shutdown_mode": "$SHUTDOWN_MODE",
  "shutdown_by": "$(whoami)",
  "graceful": $([ "$SHUTDOWN_MODE" = "graceful" ] && echo "true" || echo "false")
}
EOF
    
    log "Shutdown information saved"
}

# Generate shutdown report
generate_shutdown_report() {
    local report_file="$LOG_DIR/shutdown_$(date +%Y%m%d_%H%M%S).log"
    
    {
        echo "Karen AI Secretary - Shutdown Report"
        echo "===================================="
        echo "Shutdown Time: $(date)"
        echo "Shutdown Mode: $SHUTDOWN_MODE"
        echo "User: $(whoami)"
        echo ""
        echo "Services Status After Shutdown:"
        echo "------------------------------"
        
        for service in celery_worker celery_beat fastapi frontend autonomous; do
            local pid_file="$PID_DIR/${service}.pid"
            if [[ -f "$pid_file" ]]; then
                echo "⚠️  $service: PID file still exists"
            else
                echo "✅ $service: Clean shutdown"
            fi
        done
        
        echo ""
        echo "System Status:"
        echo "-------------"
        echo "Redis: $(redis-cli ping 2>/dev/null || echo 'Not responding')"
        echo "Disk Space: $(df -h "$PROJECT_ROOT" | tail -1 | awk '{print $4}') available"
        echo "Memory: $(free -h | grep Mem | awk '{print $7}') available"
        
    } > "$report_file"
    
    log "Shutdown report saved to: $report_file"
}

# Main shutdown sequence
main() {
    log "🛑 Stopping Karen AI Secretary System"
    log "Shutdown mode: $SHUTDOWN_MODE"
    
    # Stop services in reverse order of startup
    stop_autonomous_agents
    stop_frontend
    stop_fastapi
    stop_celery_beat
    stop_celery_worker
    stop_redis
    
    cleanup_orphans
    save_shutdown_info
    generate_shutdown_report
    
    # Clean up startup info
    rm -f "$PROJECT_ROOT/startup_info.json"
    
    log "✅ Karen AI Secretary System stopped successfully"
    
    if [[ "$SHUTDOWN_MODE" == "graceful" ]]; then
        info "All services have been gracefully stopped"
    else
        warning "Services were forcefully terminated"
    fi
}

# Handle script arguments
case "${SHUTDOWN_MODE}" in
    graceful|force)
        main
        ;;
    *)
        echo "Usage: $0 [graceful|force]"
        echo "  graceful: Wait for services to stop gracefully (default)"
        echo "  force: Immediately terminate all services"
        exit 1
        ;;
esac
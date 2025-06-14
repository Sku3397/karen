#!/bin/bash
# Karen AI Secretary - Main Startup Script
# Usage: ./scripts/startup/start_karen.sh [environment]

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENVIRONMENT="${1:-development}"
LOG_DIR="$PROJECT_ROOT/logs"
PID_DIR="$PROJECT_ROOT/pids"

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

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is not installed"
        exit 1
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        warning "Node.js not found - frontend will not be available"
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        warning "Docker not found - using local services only"
    fi
    
    # Check Redis
    if ! command -v redis-cli &> /dev/null; then
        warning "Redis CLI not found - may need to start Redis manually"
    fi
    
    log "Prerequisites check completed"
}

# Create necessary directories
create_directories() {
    log "Creating necessary directories..."
    
    mkdir -p "$LOG_DIR"/{agents,system,tasks,workflows}
    mkdir -p "$PID_DIR"
    mkdir -p "$PROJECT_ROOT"/{active_tasks/completed,reports,backups}
    mkdir -p "$PROJECT_ROOT/autonomous-agents/communication/inbox"/{orchestrator,archaeologist,sms_engineer,memory_engineer,test_engineer,phone_engineer}
    mkdir -p "$PROJECT_ROOT/autonomous-agents/communication/inbox"/{orchestrator,archaeologist,sms_engineer,memory_engineer,test_engineer,phone_engineer}/processed
    
    log "Directories created successfully"
}

# Load environment variables
load_environment() {
    log "Loading environment configuration for: $ENVIRONMENT"
    
    ENV_FILE="$PROJECT_ROOT/.env"
    if [[ "$ENVIRONMENT" != "development" ]]; then
        ENV_FILE="$PROJECT_ROOT/.env.$ENVIRONMENT"
    fi
    
    if [[ -f "$ENV_FILE" ]]; then
        source "$ENV_FILE"
        log "Environment loaded from $ENV_FILE"
    else
        warning "Environment file $ENV_FILE not found"
    fi
}

# Start Redis if needed
start_redis() {
    log "Starting Redis..."
    
    if pgrep redis-server > /dev/null; then
        info "Redis is already running"
        return 0
    fi
    
    if command -v docker &> /dev/null; then
        log "Starting Redis with Docker..."
        docker run -d --name karen-redis -p 6379:6379 --restart unless-stopped redis:alpine
        sleep 3
    elif command -v redis-server &> /dev/null; then
        log "Starting Redis locally..."
        redis-server --daemonize yes --port 6379
        sleep 2
    else
        error "Redis not available - please install Redis or Docker"
        exit 1
    fi
    
    # Test Redis connection
    if redis-cli ping > /dev/null 2>&1; then
        log "Redis started successfully"
    else
        error "Failed to start Redis"
        exit 1
    fi
}

# Start Celery Worker
start_celery_worker() {
    log "Starting Celery Worker..."
    
    cd "$PROJECT_ROOT"
    
    if [[ -f "$PID_DIR/celery_worker.pid" ]]; then
        if kill -0 "$(cat "$PID_DIR/celery_worker.pid")" 2>/dev/null; then
            info "Celery Worker is already running"
            return 0
        fi
    fi
    
    nohup python3 -m celery -A src.celery_app:celery_app worker \
        -l INFO \
        --pool=solo \
        --pidfile="$PID_DIR/celery_worker.pid" \
        > "$LOG_DIR/celery_worker.log" 2>&1 &
    
    sleep 3
    
    if [[ -f "$PID_DIR/celery_worker.pid" ]] && kill -0 "$(cat "$PID_DIR/celery_worker.pid")" 2>/dev/null; then
        log "Celery Worker started successfully (PID: $(cat "$PID_DIR/celery_worker.pid"))"
    else
        error "Failed to start Celery Worker"
        exit 1
    fi
}

# Start Celery Beat
start_celery_beat() {
    log "Starting Celery Beat..."
    
    cd "$PROJECT_ROOT"
    
    if [[ -f "$PID_DIR/celery_beat.pid" ]]; then
        if kill -0 "$(cat "$PID_DIR/celery_beat.pid")" 2>/dev/null; then
            info "Celery Beat is already running"
            return 0
        fi
    fi
    
    nohup python3 -m celery -A src.celery_app:celery_app beat \
        -l INFO \
        --scheduler django_celery_beat.schedulers:DatabaseScheduler \
        --pidfile="$PID_DIR/celery_beat.pid" \
        > "$LOG_DIR/celery_beat.log" 2>&1 &
    
    sleep 3
    
    if [[ -f "$PID_DIR/celery_beat.pid" ]] && kill -0 "$(cat "$PID_DIR/celery_beat.pid")" 2>/dev/null; then
        log "Celery Beat started successfully (PID: $(cat "$PID_DIR/celery_beat.pid"))"
    else
        error "Failed to start Celery Beat"
        exit 1
    fi
}

# Start FastAPI (optional)
start_fastapi() {
    if [[ "${START_FASTAPI:-false}" == "true" ]]; then
        log "Starting FastAPI server..."
        
        cd "$PROJECT_ROOT"
        
        if [[ -f "$PID_DIR/fastapi.pid" ]]; then
            if kill -0 "$(cat "$PID_DIR/fastapi.pid")" 2>/dev/null; then
                info "FastAPI is already running"
                return 0
            fi
        fi
        
        nohup python3 -m src.main \
            > "$LOG_DIR/fastapi.log" 2>&1 &
        
        echo $! > "$PID_DIR/fastapi.pid"
        sleep 3
        
        if kill -0 "$(cat "$PID_DIR/fastapi.pid")" 2>/dev/null; then
            log "FastAPI started successfully (PID: $(cat "$PID_DIR/fastapi.pid"))"
        else
            error "Failed to start FastAPI"
            rm -f "$PID_DIR/fastapi.pid"
        fi
    else
        info "FastAPI startup skipped (set START_FASTAPI=true to enable)"
    fi
}

# Start Frontend (optional)
start_frontend() {
    if [[ "${START_FRONTEND:-false}" == "true" ]] && command -v npm &> /dev/null; then
        log "Starting Frontend development server..."
        
        cd "$PROJECT_ROOT"
        
        if [[ -f "$PID_DIR/frontend.pid" ]]; then
            if kill -0 "$(cat "$PID_DIR/frontend.pid")" 2>/dev/null; then
                info "Frontend is already running"
                return 0
            fi
        fi
        
        nohup npm start > "$LOG_DIR/frontend.log" 2>&1 &
        echo $! > "$PID_DIR/frontend.pid"
        sleep 5
        
        if kill -0 "$(cat "$PID_DIR/frontend.pid")" 2>/dev/null; then
            log "Frontend started successfully (PID: $(cat "$PID_DIR/frontend.pid"))"
        else
            error "Failed to start Frontend"
            rm -f "$PID_DIR/frontend.pid"
        fi
    else
        info "Frontend startup skipped (set START_FRONTEND=true to enable)"
    fi
}

# Start Autonomous Agents
start_autonomous_agents() {
    if [[ "${START_AUTONOMOUS:-true}" == "true" ]]; then
        log "Starting Autonomous Agent System..."
        
        cd "$PROJECT_ROOT"
        
        if [[ -f "$PID_DIR/autonomous.pid" ]]; then
            if kill -0 "$(cat "$PID_DIR/autonomous.pid")" 2>/dev/null; then
                info "Autonomous system is already running"
                return 0
            fi
        fi
        
        nohup python3 orchestrator_active.py \
            > "$LOG_DIR/autonomous_system.log" 2>&1 &
        
        echo $! > "$PID_DIR/autonomous.pid"
        sleep 5
        
        if kill -0 "$(cat "$PID_DIR/autonomous.pid")" 2>/dev/null; then
            log "Autonomous Agent System started successfully (PID: $(cat "$PID_DIR/autonomous.pid"))"
        else
            error "Failed to start Autonomous Agent System"
            rm -f "$PID_DIR/autonomous.pid"
        fi
    else
        info "Autonomous agents startup skipped (set START_AUTONOMOUS=true to enable)"
    fi
}

# Health check
health_check() {
    log "Performing health check..."
    
    local issues=0
    
    # Check Redis
    if ! redis-cli ping > /dev/null 2>&1; then
        error "Redis health check failed"
        ((issues++))
    fi
    
    # Check Celery Worker
    if [[ -f "$PID_DIR/celery_worker.pid" ]]; then
        if ! kill -0 "$(cat "$PID_DIR/celery_worker.pid")" 2>/dev/null; then
            error "Celery Worker health check failed"
            ((issues++))
        fi
    else
        error "Celery Worker PID file not found"
        ((issues++))
    fi
    
    # Check Celery Beat
    if [[ -f "$PID_DIR/celery_beat.pid" ]]; then
        if ! kill -0 "$(cat "$PID_DIR/celery_beat.pid")" 2>/dev/null; then
            error "Celery Beat health check failed"
            ((issues++))
        fi
    else
        error "Celery Beat PID file not found"
        ((issues++))
    fi
    
    if [[ $issues -eq 0 ]]; then
        log "All health checks passed!"
        return 0
    else
        error "Health check found $issues issues"
        return 1
    fi
}

# Main startup sequence
main() {
    log "🚀 Starting Karen AI Secretary System"
    log "Environment: $ENVIRONMENT"
    log "Project Root: $PROJECT_ROOT"
    
    check_prerequisites
    create_directories
    load_environment
    start_redis
    start_celery_worker
    start_celery_beat
    start_fastapi
    start_frontend
    start_autonomous_agents
    
    log "⏳ Waiting for services to stabilize..."
    sleep 10
    
    if health_check; then
        log "✅ Karen AI Secretary System started successfully!"
        log "📊 Status Dashboard: http://localhost:8000 (if FastAPI enabled)"
        log "🖥️  Frontend: http://localhost:8082 (if Frontend enabled)"
        log "📁 Logs: $LOG_DIR"
        log "🔧 PIDs: $PID_DIR"
        
        # Save startup info
        cat > "$PROJECT_ROOT/startup_info.json" << EOF
{
  "started_at": "$(date -Iseconds)",
  "environment": "$ENVIRONMENT",
  "pids": {
    "celery_worker": "$(cat "$PID_DIR/celery_worker.pid" 2>/dev/null || echo 'null')",
    "celery_beat": "$(cat "$PID_DIR/celery_beat.pid" 2>/dev/null || echo 'null')",
    "fastapi": "$(cat "$PID_DIR/fastapi.pid" 2>/dev/null || echo 'null')",
    "frontend": "$(cat "$PID_DIR/frontend.pid" 2>/dev/null || echo 'null')",
    "autonomous": "$(cat "$PID_DIR/autonomous.pid" 2>/dev/null || echo 'null')"
  }
}
EOF
        
    else
        error "❌ Startup completed with issues - check logs for details"
        exit 1
    fi
}

# Handle script arguments
case "${1:-start}" in
    start)
        main
        ;;
    check)
        health_check
        ;;
    *)
        echo "Usage: $0 [start|check] [environment]"
        echo "  start: Start all Karen services (default)"
        echo "  check: Perform health check only"
        echo "  environment: development (default), staging, production"
        exit 1
        ;;
esac
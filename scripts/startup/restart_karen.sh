#!/bin/bash
# Karen AI Secretary - Restart Script
# Usage: ./scripts/startup/restart_karen.sh [environment] [graceful|force]

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENVIRONMENT="${1:-development}"
SHUTDOWN_MODE="${2:-graceful}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

main() {
    log "🔄 Restarting Karen AI Secretary System"
    log "Environment: $ENVIRONMENT"
    log "Shutdown mode: $SHUTDOWN_MODE"
    
    # Stop the system
    log "⏹️  Stopping current system..."
    if ! "$SCRIPT_DIR/stop_karen.sh" "$SHUTDOWN_MODE"; then
        error "Failed to stop system cleanly"
        if [[ "$SHUTDOWN_MODE" != "force" ]]; then
            log "Retrying with force..."
            "$SCRIPT_DIR/stop_karen.sh" force
        else
            exit 1
        fi
    fi
    
    # Wait a moment for cleanup
    log "⏳ Waiting for system cleanup..."
    sleep 5
    
    # Start the system
    log "▶️  Starting system..."
    if ! "$SCRIPT_DIR/start_karen.sh" "$ENVIRONMENT"; then
        error "Failed to start system"
        exit 1
    fi
    
    log "✅ Karen AI Secretary System restarted successfully!"
}

# Validate arguments
if [[ ! "$SHUTDOWN_MODE" =~ ^(graceful|force)$ ]]; then
    echo "Usage: $0 [environment] [graceful|force]"
    echo "  environment: development (default), staging, production"
    echo "  shutdown_mode: graceful (default) or force"
    exit 1
fi

main
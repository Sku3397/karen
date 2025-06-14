#!/bin/bash
# Karen AI Secretary - System Backup Script
# Usage: ./scripts/backup/backup_system.sh [--full|--incremental] [--destination PATH]

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKUP_TYPE="incremental"
BACKUP_DESTINATION="$PROJECT_ROOT/backups"
BACKUP_NAME="backup_$(date +%Y%m%d_%H%M%S)"
RETENTION_DAYS=30

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --full)
            BACKUP_TYPE="full"
            shift
            ;;
        --incremental)
            BACKUP_TYPE="incremental"
            shift
            ;;
        --destination)
            BACKUP_DESTINATION="$2"
            shift 2
            ;;
        *)
            echo "Usage: $0 [--full|--incremental] [--destination PATH]"
            echo "  --full: Complete system backup (default: incremental)"
            echo "  --incremental: Only changed files since last backup"
            echo "  --destination: Backup destination directory"
            exit 1
            ;;
    esac
done

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

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Create backup directory
create_backup_directory() {
    local backup_path="$BACKUP_DESTINATION/$BACKUP_NAME"
    
    log "Creating backup directory: $backup_path"
    mkdir -p "$backup_path"
    
    echo "$backup_path"
}

# Backup configuration files
backup_config() {
    local backup_path="$1"
    
    log "Backing up configuration files..."
    
    local config_backup="$backup_path/config"
    mkdir -p "$config_backup"
    
    # Environment files
    if [[ -f "$PROJECT_ROOT/.env" ]]; then
        cp "$PROJECT_ROOT/.env" "$config_backup/.env.backup"
    fi
    
    # Copy other environment files
    find "$PROJECT_ROOT" -maxdepth 1 -name ".env.*" -type f -exec cp {} "$config_backup/" \;
    
    # Configuration directories
    if [[ -d "$PROJECT_ROOT/config" ]]; then
        cp -r "$PROJECT_ROOT/config" "$config_backup/"
    fi
    
    # OAuth tokens (sensitive but necessary for recovery)
    find "$PROJECT_ROOT" -name "*token*.json" -type f -exec cp {} "$config_backup/" \;
    
    # Docker and infrastructure configs
    local infra_files=(
        "docker-compose.yml"
        "docker-compose.prod.yml"
        "Dockerfile"
        "package.json"
        "requirements.txt"
        "pytest.ini"
        "firebase.json"
        "firestore.rules"
    )
    
    for file in "${infra_files[@]}"; do
        if [[ -f "$PROJECT_ROOT/$file" ]]; then
            cp "$PROJECT_ROOT/$file" "$config_backup/"
        fi
    done
    
    log "Configuration backup completed"
}

# Backup source code
backup_source() {
    local backup_path="$1"
    
    log "Backing up source code..."
    
    local source_backup="$backup_path/source"
    mkdir -p "$source_backup"
    
    # Copy source directories
    local source_dirs=(
        "src"
        "scripts"
        "docs"
        "functions"
        "infra"
        "infrastructure"
        "monitoring"
        "iac"
        "gcp"
        "deploy"
        "migrations"
    )
    
    for dir in "${source_dirs[@]}"; do
        if [[ -d "$PROJECT_ROOT/$dir" ]]; then
            cp -r "$PROJECT_ROOT/$dir" "$source_backup/"
        fi
    done
    
    # Copy important root files
    local root_files=(
        "*.py"
        "*.md"
        "*.sh"
        "*.toml"
        "*.yaml"
        "*.yml"
        "*.js"
        "*.json"
        "*.txt"
    )
    
    for pattern in "${root_files[@]}"; do
        find "$PROJECT_ROOT" -maxdepth 1 -name "$pattern" -type f -exec cp {} "$source_backup/" \; 2>/dev/null || true
    done
    
    log "Source code backup completed"
}

# Backup agent data
backup_agent_data() {
    local backup_path="$1"
    
    log "Backing up agent data..."
    
    local agent_backup="$backup_path/agent_data"
    mkdir -p "$agent_backup"
    
    # Autonomous agents data
    if [[ -d "$PROJECT_ROOT/autonomous-agents" ]]; then
        cp -r "$PROJECT_ROOT/autonomous-agents" "$agent_backup/"
    fi
    
    # Active tasks
    if [[ -d "$PROJECT_ROOT/active_tasks" ]]; then
        cp -r "$PROJECT_ROOT/active_tasks" "$agent_backup/"
    fi
    
    # Task definitions
    if [[ -d "$PROJECT_ROOT/tasks" ]]; then
        cp -r "$PROJECT_ROOT/tasks" "$agent_backup/"
    fi
    
    # Agent state files
    local state_files=(
        "autonomous_state.json"
        "startup_info.json"
        "last_shutdown.json"
    )
    
    for file in "${state_files[@]}"; do
        if [[ -f "$PROJECT_ROOT/$file" ]]; then
            cp "$PROJECT_ROOT/$file" "$agent_backup/"
        fi
    done
    
    log "Agent data backup completed"
}

# Backup logs
backup_logs() {
    local backup_path="$1"
    
    log "Backing up logs..."
    
    local log_backup="$backup_path/logs"
    
    if [[ -d "$PROJECT_ROOT/logs" ]]; then
        # For incremental backup, only copy recent logs
        if [[ "$BACKUP_TYPE" == "incremental" ]]; then
            mkdir -p "$log_backup"
            find "$PROJECT_ROOT/logs" -type f -mtime -7 -exec cp --parents {} "$log_backup/" \; 2>/dev/null || true
        else
            cp -r "$PROJECT_ROOT/logs" "$log_backup"
        fi
    fi
    
    log "Logs backup completed"
}

# Backup reports and generated data
backup_reports() {
    local backup_path="$1"
    
    log "Backing up reports and generated data..."
    
    local reports_backup="$backup_path/reports"
    mkdir -p "$reports_backup"
    
    # Reports directory
    if [[ -d "$PROJECT_ROOT/reports" ]]; then
        cp -r "$PROJECT_ROOT/reports" "$reports_backup/"
    fi
    
    # Test results
    if [[ -d "$PROJECT_ROOT/test_results" ]]; then
        cp -r "$PROJECT_ROOT/test_results" "$reports_backup/"
    fi
    
    # Generated documentation
    if [[ -d "$PROJECT_ROOT/dist" ]]; then
        cp -r "$PROJECT_ROOT/dist" "$reports_backup/"
    fi
    
    log "Reports backup completed"
}

# Backup database files
backup_databases() {
    local backup_path="$1"
    
    log "Backing up database files..."
    
    local db_backup="$backup_path/databases"
    mkdir -p "$db_backup"
    
    # SQLite databases
    find "$PROJECT_ROOT" -name "*.db" -o -name "*.sqlite" -o -name "*.sqlite3" | while read -r db_file; do
        if [[ -f "$db_file" ]]; then
            cp "$db_file" "$db_backup/"
        fi
    done
    
    # Celery beat schedule
    if [[ -f "$PROJECT_ROOT/celerybeat-schedule.sqlite3" ]]; then
        cp "$PROJECT_ROOT/celerybeat-schedule.sqlite3" "$db_backup/"
    fi
    
    log "Database backup completed"
}

# Create backup manifest
create_backup_manifest() {
    local backup_path="$1"
    
    log "Creating backup manifest..."
    
    local manifest="$backup_path/BACKUP_MANIFEST.txt"
    
    {
        echo "Karen AI Secretary System Backup"
        echo "==============================="
        echo "Backup Date: $(date)"
        echo "Backup Type: $BACKUP_TYPE"
        echo "Backup Path: $backup_path"
        echo "Original Location: $PROJECT_ROOT"
        echo "Created By: $(whoami)"
        echo "Hostname: $(hostname)"
        echo ""
        echo "Backup Contents:"
        echo "---------------"
        
        find "$backup_path" -type f | sort | while read -r file; do
            local rel_path="${file#$backup_path/}"
            local size
            size=$(stat -c%s "$file" 2>/dev/null || echo "0")
            echo "$rel_path ($size bytes)"
        done
        
        echo ""
        echo "Backup Statistics:"
        echo "-----------------"
        echo "Total Files: $(find "$backup_path" -type f | wc -l)"
        echo "Total Size: $(du -sh "$backup_path" | cut -f1)"
        echo "Backup Completed: $(date)"
        
    } > "$manifest"
    
    log "Backup manifest created: $manifest"
}

# Compress backup (optional)
compress_backup() {
    local backup_path="$1"
    
    if command -v tar &> /dev/null; then
        log "Compressing backup..."
        
        local archive_name="${backup_path}.tar.gz"
        local backup_dir
        backup_dir=$(dirname "$backup_path")
        local backup_name
        backup_name=$(basename "$backup_path")
        
        cd "$backup_dir"
        tar -czf "$archive_name" "$backup_name"
        
        if [[ -f "$archive_name" ]]; then
            # Remove uncompressed backup
            rm -rf "$backup_path"
            log "Backup compressed to: $archive_name"
            echo "$archive_name"
        else
            error "Failed to compress backup"
            echo "$backup_path"
        fi
    else
        warning "tar not available - backup left uncompressed"
        echo "$backup_path"
    fi
}

# Clean old backups
cleanup_old_backups() {
    log "Cleaning up old backups (older than $RETENTION_DAYS days)..."
    
    find "$BACKUP_DESTINATION" -name "backup_*" -type d -mtime +$RETENTION_DAYS -exec rm -rf {} \; 2>/dev/null || true
    find "$BACKUP_DESTINATION" -name "backup_*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
    
    local remaining_backups
    remaining_backups=$(find "$BACKUP_DESTINATION" -name "backup_*" | wc -l)
    log "Cleanup completed. $remaining_backups backups remaining."
}

# Verify backup integrity
verify_backup() {
    local backup_path="$1"
    
    log "Verifying backup integrity..."
    
    local issues=0
    
    # Check critical files exist
    local critical_files=(
        "config/.env.backup"
        "source/src"
        "agent_data/autonomous_state.json"
        "BACKUP_MANIFEST.txt"
    )
    
    for file in "${critical_files[@]}"; do
        if [[ ! -e "$backup_path/$file" ]]; then
            error "Critical file missing from backup: $file"
            ((issues++))
        fi
    done
    
    # Check backup size
    local backup_size
    backup_size=$(du -sb "$backup_path" | cut -f1)
    
    if [[ $backup_size -lt 1000000 ]]; then  # Less than 1MB
        warning "Backup size seems unusually small: $(du -sh "$backup_path" | cut -f1)"
        ((issues++))
    fi
    
    if [[ $issues -eq 0 ]]; then
        log "Backup verification passed"
        return 0
    else
        error "Backup verification failed with $issues issues"
        return 1
    fi
}

# Generate backup report
generate_backup_report() {
    local backup_path="$1"
    local start_time="$2"
    local end_time="$3"
    
    local report_file="$PROJECT_ROOT/logs/backup_$(date +%Y%m%d_%H%M%S).log"
    mkdir -p "$(dirname "$report_file")"
    
    {
        echo "Karen AI Secretary - Backup Report"
        echo "=================================="
        echo "Backup Type: $BACKUP_TYPE"
        echo "Start Time: $start_time"
        echo "End Time: $end_time"
        echo "Duration: $((end_time - start_time)) seconds"
        echo "Backup Location: $backup_path"
        echo ""
        echo "Backup Contents:"
        find "$backup_path" -type d | sort
        echo ""
        echo "File Count by Category:"
        echo "- Config files: $(find "$backup_path/config" -type f 2>/dev/null | wc -l)"
        echo "- Source files: $(find "$backup_path/source" -type f 2>/dev/null | wc -l)"
        echo "- Agent data: $(find "$backup_path/agent_data" -type f 2>/dev/null | wc -l)"
        echo "- Log files: $(find "$backup_path/logs" -type f 2>/dev/null | wc -l)"
        echo "- Reports: $(find "$backup_path/reports" -type f 2>/dev/null | wc -l)"
        echo "- Databases: $(find "$backup_path/databases" -type f 2>/dev/null | wc -l)"
        echo ""
        echo "Total Size: $(du -sh "$backup_path" | cut -f1)"
        
    } > "$report_file"
    
    log "Backup report saved: $report_file"
}

# Main backup function
main() {
    local start_time
    start_time=$(date +%s)
    
    log "🗄️  Starting Karen AI Secretary System Backup"
    log "Backup Type: $BACKUP_TYPE"
    log "Destination: $BACKUP_DESTINATION"
    
    # Create backup directory
    local backup_path
    backup_path=$(create_backup_directory)
    
    # Perform backup operations
    backup_config "$backup_path"
    backup_source "$backup_path"
    backup_agent_data "$backup_path"
    backup_logs "$backup_path"
    backup_reports "$backup_path"
    backup_databases "$backup_path"
    
    # Create manifest
    create_backup_manifest "$backup_path"
    
    # Verify backup
    if verify_backup "$backup_path"; then
        log "✅ Backup verification successful"
    else
        error "❌ Backup verification failed"
        exit 1
    fi
    
    # Compress backup
    local final_backup_path
    final_backup_path=$(compress_backup "$backup_path")
    
    # Clean old backups
    cleanup_old_backups
    
    local end_time
    end_time=$(date +%s)
    
    # Generate report
    generate_backup_report "$final_backup_path" "$start_time" "$end_time"
    
    log "✅ Backup completed successfully!"
    log "📁 Backup location: $final_backup_path"
    log "⏱️  Duration: $((end_time - start_time)) seconds"
    log "💾 Size: $(du -sh "$final_backup_path" | cut -f1)"
}

main
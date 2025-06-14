#!/bin/bash

# Karen AI Environment Setup Script
# Configures memory allocation and environment variables for optimal performance

echo "🚀 Setting up Karen AI environment with optimized memory allocation..."

# Memory Configuration for Node.js processes
echo "📊 Configuring Node.js memory allocation (4GB)..."
export NODE_OPTIONS="--max-old-space-size=4096"

# Memory Configuration for Java-based tools (if using any)
echo "☕ Configuring Java memory allocation (4GB heap, 2GB initial)..."
export JAVA_OPTS="-Xmx4g -Xms2g"

# Python memory optimizations for NLP processing
echo "🐍 Configuring Python memory optimizations..."
export PYTHONHASHSEED=0  # Consistent hash seeds for reproducibility
export PYTHONUNBUFFERED=1  # Unbuffered output for better logging

# NLP-specific environment variables
echo "🧠 Configuring NLP engine settings..."
export NLP_CONFIDENCE_THRESHOLD=0.6
export NLP_BATCH_SIZE=10
export NLP_MAX_CONTEXT_MESSAGES=5

# Celery optimizations for background task processing
echo "🔄 Configuring Celery worker optimizations..."
export CELERY_WORKER_POOL=solo  # Use solo pool for better compatibility
export CELERY_WORKER_CONCURRENCY=2  # Limit concurrent tasks
export CELERY_TASK_SOFT_TIME_LIMIT=300  # 5 minute soft limit
export CELERY_TASK_TIME_LIMIT=600  # 10 minute hard limit

# Redis optimizations
echo "📊 Configuring Redis optimizations..."
export REDIS_MAXMEMORY=1gb
export REDIS_MAXMEMORY_POLICY=allkeys-lru

# SMS/Communication optimizations
echo "📱 Configuring SMS processing optimizations..."
export SMS_BATCH_PROCESSING=true
export SMS_RESPONSE_TIMEOUT=30
export SMS_RETRY_ATTEMPTS=3

# Logging configuration
echo "📝 Configuring logging levels..."
export LOG_LEVEL=INFO
export LOG_FORMAT=structured
export LOG_MAX_FILES=10
export LOG_MAX_SIZE=100MB

# Performance monitoring
echo "📈 Enabling performance monitoring..."
export ENABLE_PERFORMANCE_MONITORING=true
export METRICS_COLLECTION_INTERVAL=60

# Load existing .env file if it exists
if [ -f .env ]; then
    echo "📋 Loading existing .env configuration..."
    set -a  # Automatically export all variables
    source .env
    set +a
else
    echo "⚠️  No .env file found. Please ensure environment variables are configured."
fi

# Validate critical environment variables
echo "✅ Validating critical environment variables..."

validate_var() {
    if [ -z "${!1}" ]; then
        echo "❌ Missing required environment variable: $1"
        return 1
    else
        echo "✅ $1 is configured"
        return 0
    fi
}

# Critical variables for NLP integration
validate_var "GEMINI_API_KEY"
validate_var "TWILIO_ACCOUNT_SID"
validate_var "TWILIO_AUTH_TOKEN"
validate_var "CELERY_BROKER_URL"

# Optional but recommended
if [ -z "$TWILIO_PHONE_NUMBER" ]; then
    echo "⚠️  TWILIO_PHONE_NUMBER not set - SMS integration may not work"
fi

# Memory and performance checks
echo "🔍 Checking system resources..."

# Check available memory
AVAILABLE_MEMORY=$(free -g | awk 'NR==2{printf "%.0f", $7}')
if [ "$AVAILABLE_MEMORY" -lt 6 ]; then
    echo "⚠️  Warning: Available memory is ${AVAILABLE_MEMORY}GB. Consider reducing NODE_OPTIONS to --max-old-space-size=2048"
fi

# Check if Redis is running
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo "✅ Redis is running and accessible"
    else
        echo "❌ Redis is not running. Start it with: docker-compose up -d redis"
    fi
else
    echo "⚠️  Redis CLI not found. Install redis-tools or use Docker"
fi

# Create startup script for services
echo "📝 Creating optimized startup script..."
cat > start_karen_optimized.sh << 'EOF'
#!/bin/bash

# Karen AI Optimized Startup Script
echo "🚀 Starting Karen AI with optimized settings..."

# Load environment
source setup_environment.sh

# Start Redis if not running
if ! redis-cli ping &> /dev/null; then
    echo "🔧 Starting Redis..."
    docker-compose up -d redis
    sleep 5
fi

# Start Celery Beat (scheduler) with optimizations
echo "⏰ Starting Celery Beat scheduler..."
.venv/bin/python -m celery -A src.celery_app:celery_app beat \
    -l INFO \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler \
    --pidfile=celerybeat.pid \
    --detach

# Start Celery Worker with optimizations
echo "👷 Starting Celery Worker..."
.venv/bin/python -m celery -A src.celery_app:celery_app worker \
    -l INFO \
    --pool=solo \
    --concurrency=2 \
    --pidfile=celery_worker.pid \
    --detach

# Start FastAPI server (optional)
if [ "$START_API_SERVER" = "true" ]; then
    echo "🌐 Starting FastAPI server..."
    python -m src.main &
fi

# Start Frontend (if needed)
if [ "$START_FRONTEND" = "true" ]; then
    echo "🎨 Starting frontend server..."
    npm start &
fi

echo "✅ Karen AI started successfully!"
echo "📊 Monitor logs with:"
echo "  tail -f celery_worker_logs.txt"
echo "  tail -f celery_beat_logs.txt"

EOF

chmod +x start_karen_optimized.sh

# Create monitoring script
echo "📊 Creating monitoring script..."
cat > monitor_karen.sh << 'EOF'
#!/bin/bash

# Karen AI Monitoring Script
echo "📊 Karen AI System Monitor"
echo "=========================="

# Check memory usage
echo "Memory Usage:"
free -h

echo -e "\nNode.js Processes:"
ps aux | grep node | grep -v grep

echo -e "\nPython Processes:"
ps aux | grep python | grep -v grep

echo -e "\nCelery Status:"
if [ -f celery_worker.pid ]; then
    echo "✅ Celery Worker running (PID: $(cat celery_worker.pid))"
else
    echo "❌ Celery Worker not running"
fi

if [ -f celerybeat.pid ]; then
    echo "✅ Celery Beat running (PID: $(cat celerybeat.pid))"
else
    echo "❌ Celery Beat not running"
fi

echo -e "\nRedis Status:"
redis-cli ping

echo -e "\nRecent Log Entries:"
echo "Celery Worker (last 5 lines):"
tail -5 celery_worker_logs.txt 2>/dev/null || echo "No worker logs found"

echo -e "\nCelery Beat (last 5 lines):"
tail -5 celery_beat_logs.txt 2>/dev/null || echo "No beat logs found"

EOF

chmod +x monitor_karen.sh

# Create cleanup script
echo "🧹 Creating cleanup script..."
cat > cleanup_karen.sh << 'EOF'
#!/bin/bash

# Karen AI Cleanup Script
echo "🧹 Cleaning up Karen AI processes..."

# Stop Celery processes
if [ -f celery_worker.pid ]; then
    echo "🛑 Stopping Celery Worker..."
    kill $(cat celery_worker.pid) 2>/dev/null
    rm -f celery_worker.pid
fi

if [ -f celerybeat.pid ]; then
    echo "🛑 Stopping Celery Beat..."
    kill $(cat celerybeat.pid) 2>/dev/null
    rm -f celerybeat.pid
fi

# Kill any remaining processes
pkill -f "celery.*worker"
pkill -f "celery.*beat"
pkill -f "python.*src.main"

# Clean up log files (optional)
if [ "$1" = "--clean-logs" ]; then
    echo "🗑️  Cleaning log files..."
    rm -f *.log *.txt celerybeat-schedule.sqlite3
fi

echo "✅ Cleanup complete!"
EOF

chmod +x cleanup_karen.sh

# Final configuration summary
echo ""
echo "🎉 Environment setup complete!"
echo "================================"
echo ""
echo "Memory Configuration:"
echo "  • Node.js heap: 4GB (NODE_OPTIONS=$NODE_OPTIONS)"
echo "  • Java heap: 4GB max, 2GB initial (JAVA_OPTS=$JAVA_OPTS)"
echo "  • Python optimizations enabled"
echo ""
echo "Scripts Created:"
echo "  • start_karen_optimized.sh - Start all services with optimizations"
echo "  • monitor_karen.sh - Monitor system status and performance"
echo "  • cleanup_karen.sh - Clean shutdown and cleanup"
echo ""
echo "Next Steps:"
echo "1. Run: ./start_karen_optimized.sh"
echo "2. Monitor: ./monitor_karen.sh"
echo "3. Test NLP: python3 test_nlp_integration.py"
echo "4. Test SMS: python3 test_sms_nlp_integration.py"
echo ""
echo "💡 Pro Tips:"
echo "  • Monitor memory usage with: watch -n 5 free -h"
echo "  • Check logs in real-time: tail -f celery_worker_logs.txt"
echo "  • Use cleanup_karen.sh --clean-logs to reset everything"
echo ""

# Make this script executable
chmod +x setup_environment.sh

echo "✅ Setup script is now executable. Run it with: ./setup_environment.sh"
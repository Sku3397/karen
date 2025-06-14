# Karen AI Assistant - Production Deployment Guide

This comprehensive guide covers deploying the Karen AI Secretary Assistant to production environments, including containerized deployments, cloud platforms, and traditional VPS setups.

## Table of Contents
- [Architecture Overview](#architecture-overview)
- [Deployment Options](#deployment-options)
- [Docker Deployment](#docker-deployment)
- [Cloud Platform Deployment](#cloud-platform-deployment)
- [Traditional VPS Deployment](#traditional-vps-deployment)
- [Security Configuration](#security-configuration)
- [Monitoring and Logging](#monitoring-and-logging)
- [Backup and Recovery](#backup-and-recovery)
- [Troubleshooting](#troubleshooting)

## Architecture Overview

### Core Components

**Multi-Agent System:**
- **Orchestrator Agent:** Coordinates between different agents
- **Communication Agent:** Handles email/SMS/voice processing
- **Task Manager Agent:** Manages tasks and completion tracking
- **Scheduler Agent:** Handles appointment scheduling
- **Knowledge Base Agent:** Information retrieval and storage
- **Billing Agent:** Invoice and payment processing

**Infrastructure Components:**
1. **FastAPI Application:** REST API and web interface
2. **Celery Workers:** Background task processing
3. **Celery Beat Scheduler:** Periodic task scheduling
4. **Redis:** Message broker and caching
5. **Multi-Agent Communication System:** Agent coordination
6. **Frontend React Application:** User interface

### System Requirements
- **CPU:** Minimum 2 cores, Recommended 4+ cores
- **Memory:** Minimum 4GB RAM, Recommended 8GB+ RAM
- **Storage:** Minimum 20GB, Recommended 50GB+ SSD
- **Network:** Stable internet connection with low latency

## Deployment Options

### 1. Docker Deployment (Recommended)
**Best for:** Development, staging, and production environments
- Complete containerization with Docker Compose
- Easy scaling and management
- Consistent environments across development and production
- Built-in service discovery and networking

### 2. Cloud Platform Deployment
**Best for:** High-availability production deployments

#### Google Cloud Platform (GCP)
- **Cloud Run:** Serverless containers with auto-scaling
- **Google Kubernetes Engine (GKE):** Full Kubernetes orchestration
- **Compute Engine:** Virtual machines with custom configurations
- **Cloud Memorystore:** Managed Redis service
- **Cloud SQL:** Managed database services

#### Amazon Web Services (AWS)
- **ECS/Fargate:** Container orchestration
- **EKS:** Managed Kubernetes service
- **EC2:** Virtual machines
- **ElastiCache:** Managed Redis service
- **RDS:** Managed database services

#### Microsoft Azure
- **Container Instances:** Serverless containers
- **AKS:** Managed Kubernetes service
- **Virtual Machines:** Custom VM configurations
- **Azure Cache for Redis:** Managed Redis service

### 3. Traditional VPS Deployment
**Best for:** Small to medium deployments with cost constraints
- Full control over the environment
- Manual setup of Python, Redis, process managers
- Lower operational costs
- Requires more system administration knowledge

## Docker Deployment

### Prerequisites
- Docker Engine 20.10+
- Docker Compose 2.0+
- Minimum 4GB RAM available to Docker

### Quick Start with Docker Compose

1. **Clone and Setup**
```bash
git clone <repository-url>
cd karen
cp .env.example .env.production
# Edit .env.production with your production values
```

2. **Deploy the Stack**
```bash
# Production deployment
docker-compose -f docker-compose.prod.yml up -d

# Development deployment
docker-compose up -d
```

3. **Verify Deployment**
```bash
# Check all services are running
docker-compose ps

# Check logs
docker-compose logs -f

# Access application
curl http://localhost:8080/health
```

### Docker Compose Architecture

The Docker deployment includes:
- **karen-api:** FastAPI application server
- **karen-worker:** Celery worker processes
- **karen-beat:** Celery beat scheduler
- **karen-frontend:** React frontend application
- **redis:** Message broker and cache
- **nginx:** Reverse proxy and load balancer

### Scaling Services

```bash
# Scale Celery workers
docker-compose up -d --scale karen-worker=3

# Scale API servers
docker-compose up -d --scale karen-api=2
```

## Cloud Platform Deployment

### Google Cloud Platform (GCP)

#### Cloud Run Deployment

1. **Build and Push Container**
```bash
# Configure gcloud
gcloud auth configure-docker

# Build and tag image
docker build -t gcr.io/PROJECT_ID/karen-api:latest .
docker push gcr.io/PROJECT_ID/karen-api:latest
```

2. **Deploy to Cloud Run**
```bash
# Deploy API service
gcloud run deploy karen-api \
  --image gcr.io/PROJECT_ID/karen-api:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10

# Deploy worker service
gcloud run deploy karen-worker \
  --image gcr.io/PROJECT_ID/karen-worker:latest \
  --platform managed \
  --region us-central1 \
  --no-allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 5
```

3. **Setup Cloud Memorystore (Redis)**
```bash
gcloud redis instances create karen-redis \
  --size=1 \
  --region=us-central1 \
  --redis-version=redis_6_x
```

#### Google Kubernetes Engine (GKE)

1. **Create GKE Cluster**
```bash
gcloud container clusters create karen-cluster \
  --num-nodes=3 \
  --machine-type=e2-standard-2 \
  --zone=us-central1-a \
  --enable-autoscaling \
  --min-nodes=1 \
  --max-nodes=10
```

2. **Deploy with Helm**
```bash
# Install Helm chart
helm install karen ./helm/karen \
  --namespace karen \
  --create-namespace \
  --values values.prod.yaml
```

### Amazon Web Services (AWS)

#### ECS Fargate Deployment

1. **Create Task Definitions**
```bash
# Register API task definition
aws ecs register-task-definition \
  --cli-input-json file://ecs-task-def-api.json

# Register worker task definition
aws ecs register-task-definition \
  --cli-input-json file://ecs-task-def-worker.json
```

2. **Create ECS Services**
```bash
# Create API service
aws ecs create-service \
  --cluster karen-cluster \
  --service-name karen-api \
  --task-definition karen-api:1 \
  --desired-count 2 \
  --launch-type FARGATE

# Create worker service
aws ecs create-service \
  --cluster karen-cluster \
  --service-name karen-worker \
  --task-definition karen-worker:1 \
  --desired-count 3 \
  --launch-type FARGATE
```

## Traditional VPS Deployment

### System Setup

1. **Install System Dependencies**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3.9 python3.9-venv python3.9-dev \
  redis-server nginx supervisor git curl

# CentOS/RHEL
sudo yum update
sudo yum install -y python39 python39-devel redis nginx supervisor git curl
```

2. **Create Application User**
```bash
sudo useradd -r -s /bin/false karen
sudo mkdir -p /opt/karen
sudo chown karen:karen /opt/karen
```

3. **Deploy Application Code**
```bash
sudo -u karen git clone <repository-url> /opt/karen
cd /opt/karen
sudo -u karen python3.9 -m venv .venv
sudo -u karen .venv/bin/pip install -r src/requirements.txt
```

### Process Management with Systemd

1. **Create Service Files**

```ini
# /etc/systemd/system/karen-api.service
[Unit]
Description=Karen AI API Server
After=network.target redis.service

[Service]
Type=exec
User=karen
Group=karen
WorkingDirectory=/opt/karen
Environment=PATH=/opt/karen/.venv/bin
ExecStart=/opt/karen/.venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.main:app -b 127.0.0.1:8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/karen-worker.service
[Unit]
Description=Karen AI Celery Worker
After=network.target redis.service

[Service]
Type=exec
User=karen
Group=karen
WorkingDirectory=/opt/karen
Environment=PATH=/opt/karen/.venv/bin
ExecStart=/opt/karen/.venv/bin/celery -A src.celery_app:celery_app worker -l INFO --pool=solo
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/karen-beat.service
[Unit]
Description=Karen AI Celery Beat Scheduler
After=network.target redis.service

[Service]
Type=exec
User=karen
Group=karen
WorkingDirectory=/opt/karen
Environment=PATH=/opt/karen/.venv/bin
ExecStart=/opt/karen/.venv/bin/celery -A src.celery_app:celery_app beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

2. **Enable and Start Services**
```bash
sudo systemctl daemon-reload
sudo systemctl enable karen-api karen-worker karen-beat
sudo systemctl start karen-api karen-worker karen-beat
```

### Nginx Configuration

```nginx
# /etc/nginx/sites-available/karen
server {
    listen 80;
    server_name your-domain.com;

    # API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Frontend static files
    location / {
        root /opt/karen/dist;
        try_files $uri $uri/ /index.html;
    }
}
```

## Security Configuration

### Environment Variables

**Required Environment Variables:**
```bash
# Core Application
SECRET_KEY=your-secret-key-here
DEBUG=false
ENVIRONMENT=production

# Database
DATABASE_URL=postgresql://user:password@localhost/karen
REDIS_URL=redis://localhost:6379/0

# Email Configuration
SECRETARY_EMAIL_ADDRESS=karen@yourdomain.com
MONITORED_EMAIL_ACCOUNT=support@yourdomain.com
ADMIN_EMAIL_ADDRESS=admin@yourdomain.com

# API Keys
GEMINI_API_KEY=your-gemini-api-key
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
SENDGRID_API_KEY=your-sendgrid-key
STRIPE_SECRET_KEY=your-stripe-key

# Google Cloud
GOOGLE_PROJECT_ID=your-gcp-project
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Security
JWT_SECRET_KEY=your-jwt-secret
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com
CORS_ALLOWED_ORIGINS=https://yourdomain.com
```

### OAuth Token Management

1. **Generate OAuth Tokens**
```bash
# On a machine with browser access
python setup_karen_oauth.py
python setup_monitor_oauth.py
python setup_calendar_oauth.py
```

2. **Secure Token Storage**
```bash
# Set strict permissions
chmod 600 gmail_token_*.json credentials.json
chown karen:karen gmail_token_*.json credentials.json

# Or use cloud secret management
gcloud secrets create gmail-token-karen --data-file=gmail_token_karen.json
gcloud secrets create gmail-token-monitor --data-file=gmail_token_monitor.json
```

### SSL/TLS Configuration

```bash
# Install Certbot for Let's Encrypt
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Firewall Configuration

```bash
# UFW (Ubuntu Firewall)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable

# iptables (Alternative)
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -A INPUT -j DROP
```

## Monitoring and Logging

### Health Checks

```python
# Built-in health check endpoint
GET /health
{
  "status": "healthy",
  "services": {
    "redis": "connected",
    "database": "connected",
    "celery": "running"
  },
  "uptime": "2d 4h 30m",
  "version": "1.0.0"
}
```

### Log Management

1. **Centralized Logging Configuration**
```python
# src/logging_config.py
import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'json': {
            'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
        }
    },
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/karen/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'detailed'
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'detailed'
        }
    },
    'loggers': {
        'karen': {
            'level': 'INFO',
            'handlers': ['file', 'console'],
            'propagate': False
        }
    },
    'root': {
        'level': 'WARNING',
        'handlers': ['file']
    }
}
```

2. **Log Rotation Setup**
```bash
# /etc/logrotate.d/karen
/var/log/karen/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 karen karen
    postrotate
        systemctl reload karen-api
    endscript
}
```

### Monitoring Setup

1. **Prometheus Configuration**
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'karen-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    
  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:9121']
```

2. **Grafana Dashboard**
- Import pre-built Karen AI dashboard
- Monitor API response times, error rates
- Track Celery task queue length and processing time
- Monitor system resources (CPU, Memory, Disk)

### Alerting Rules

```yaml
# alerts.yml
groups:
  - name: karen_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: High error rate detected
          
      - alert: CeleryQueueBacklog
        expr: celery_queue_length > 100
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: Celery queue backlog detected
```

## Backup and Recovery

### Database Backup

```bash
#!/bin/bash
# backup_database.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups/karen"
mkdir -p $BACKUP_DIR

# PostgreSQL backup
pg_dump karen_production > $BACKUP_DIR/karen_db_$DATE.sql
gzip $BACKUP_DIR/karen_db_$DATE.sql

# Upload to cloud storage
gsutil cp $BACKUP_DIR/karen_db_$DATE.sql.gz gs://your-backup-bucket/

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
```

### Application State Backup

```bash
#!/bin/bash
# backup_application.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups/karen"

# Backup OAuth tokens
tar -czf $BACKUP_DIR/oauth_tokens_$DATE.tar.gz \
  /opt/karen/gmail_token_*.json \
  /opt/karen/credentials.json \
  /opt/karen/.env.production

# Backup agent communication data
tar -czf $BACKUP_DIR/agent_data_$DATE.tar.gz \
  /opt/karen/autonomous-agents/communication/
```

### Disaster Recovery Plan

1. **Recovery Time Objective (RTO):** 4 hours
2. **Recovery Point Objective (RPO):** 1 hour

**Recovery Steps:**
1. Provision new infrastructure
2. Restore latest database backup
3. Deploy application code
4. Restore OAuth tokens and secrets
5. Restart all services
6. Verify functionality

## Troubleshooting

### Common Issues

#### Celery Worker Not Processing Tasks
```bash
# Check worker status
celery -A src.celery_app:celery_app status

# Check Redis connection
redis-cli ping

# Restart worker
sudo systemctl restart karen-worker
```

#### OAuth Token Expired
```bash
# Re-generate tokens
python setup_karen_oauth.py
python setup_monitor_oauth.py

# Restart services
sudo systemctl restart karen-api karen-worker
```

#### High Memory Usage
```bash
# Check memory usage by service
sudo systemctl status karen-worker
ps aux | grep celery

# Restart services to clear memory
sudo systemctl restart karen-worker karen-beat
```

#### Email Processing Failures
```bash
# Check email client logs
tail -f /var/log/karen/email_agent.log

# Verify Gmail API quotas
# Check Google Cloud Console for quota usage

# Test email connectivity
python -c "from src.email_client import EmailClient; client = EmailClient(); print(client.test_connection())"
```

### Performance Optimization

1. **Redis Optimization**
```redis
# redis.conf optimizations
maxmemory 1gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

2. **Celery Optimization**
```python
# celery_config.py
task_acks_late = True
worker_prefetch_multiplier = 1
task_reject_on_worker_lost = True
task_routes = {
    'src.celery_app.high_priority_task': {'queue': 'high_priority'},
    'src.celery_app.low_priority_task': {'queue': 'low_priority'},
}
```

3. **Database Optimization**
```sql
-- PostgreSQL optimizations
CREATE INDEX CONCURRENTLY idx_emails_created_at ON emails(created_at);
CREATE INDEX CONCURRENTLY idx_tasks_status ON tasks(status);
VACUUM ANALYZE;
```

### Emergency Procedures

#### Service Outage Response
1. Check service status: `sudo systemctl status karen-*`
2. Review recent logs: `tail -f /var/log/karen/app.log`
3. Check resource usage: `htop`, `df -h`
4. Restart affected services: `sudo systemctl restart karen-api`
5. Notify stakeholders if extended downtime expected

#### Data Corruption Recovery
1. Stop all services immediately
2. Assess extent of corruption
3. Restore from latest known good backup
4. Replay transaction logs if available
5. Verify data integrity before resuming operations

This comprehensive deployment guide provides the foundation for successfully deploying Karen AI Assistant in production environments. Adapt the specific configurations based on your infrastructure requirements and organizational policies. 
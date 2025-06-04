"""
Karen AI Assistant - Production Monitoring System

This module provides comprehensive monitoring capabilities for the Karen AI system,
including health checks, metrics collection, performance monitoring, and alerting.
"""

import asyncio
import logging
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import json
import os
import redis
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
import celery
from celery import Celery

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class HealthStatus:
    """Health status for a service component"""
    name: str
    status: str  # healthy, degraded, unhealthy
    last_check: datetime
    details: Optional[Dict[str, Any]] = None
    response_time: Optional[float] = None

@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_bytes_sent: int
    network_bytes_recv: int

@dataclass
class ServiceMetrics:
    """Service-specific metrics"""
    service_name: str
    timestamp: datetime
    request_count: int
    error_count: int
    avg_response_time: float
    active_connections: int
    queue_length: Optional[int] = None

class HealthChecker:
    """Centralized health checking for all services"""
    
    def __init__(self):
        self.redis_client = None
        self.celery_app = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize service clients for health checking"""
        try:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(redis_url)
        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")
        
        try:
            self.celery_app = Celery('karen')
            self.celery_app.config_from_object('src.config')
        except Exception as e:
            logger.error(f"Failed to initialize Celery client: {e}")
    
    async def check_redis(self) -> HealthStatus:
        """Check Redis health"""
        start_time = time.time()
        try:
            if not self.redis_client:
                return HealthStatus(
                    name="redis",
                    status="unhealthy",
                    last_check=datetime.utcnow(),
                    details={"error": "Redis client not initialized"}
                )
            
            # Ping Redis
            result = self.redis_client.ping()
            response_time = time.time() - start_time
            
            # Get Redis info
            info = self.redis_client.info()
            memory_usage = info.get('used_memory', 0)
            connected_clients = info.get('connected_clients', 0)
            
            status = "healthy" if result else "unhealthy"
            
            return HealthStatus(
                name="redis",
                status=status,
                last_check=datetime.utcnow(),
                response_time=response_time,
                details={
                    "memory_usage_bytes": memory_usage,
                    "connected_clients": connected_clients,
                    "ping_result": result
                }
            )
        except Exception as e:
            return HealthStatus(
                name="redis",
                status="unhealthy",
                last_check=datetime.utcnow(),
                response_time=time.time() - start_time,
                details={"error": str(e)}
            )
    
    async def check_celery(self) -> HealthStatus:
        """Check Celery health"""
        start_time = time.time()
        try:
            if not self.celery_app:
                return HealthStatus(
                    name="celery",
                    status="unhealthy",
                    last_check=datetime.utcnow(),
                    details={"error": "Celery app not initialized"}
                )
            
            # Check active workers
            inspect = self.celery_app.control.inspect()
            active_workers = inspect.active()
            stats = inspect.stats()
            
            response_time = time.time() - start_time
            
            worker_count = len(active_workers) if active_workers else 0
            status = "healthy" if worker_count > 0 else "degraded"
            
            # Get queue information
            queue_info = {}
            if self.redis_client:
                try:
                    # Check default queue length
                    queue_length = self.redis_client.llen('celery')
                    queue_info['default_queue_length'] = queue_length
                except Exception:
                    pass
            
            return HealthStatus(
                name="celery",
                status=status,
                last_check=datetime.utcnow(),
                response_time=response_time,
                details={
                    "active_workers": worker_count,
                    "worker_stats": stats,
                    **queue_info
                }
            )
        except Exception as e:
            return HealthStatus(
                name="celery",
                status="unhealthy",
                last_check=datetime.utcnow(),
                response_time=time.time() - start_time,
                details={"error": str(e)}
            )
    
    async def check_filesystem(self) -> HealthStatus:
        """Check filesystem health"""
        start_time = time.time()
        try:
            # Check disk usage
            disk_usage = psutil.disk_usage('/')
            disk_percent = (disk_usage.used / disk_usage.total) * 100
            
            # Check if log directory is writable
            log_dir = "/app/logs"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            
            test_file = os.path.join(log_dir, f"health_check_{int(time.time())}")
            try:
                with open(test_file, 'w') as f:
                    f.write("health check")
                os.remove(test_file)
                writable = True
            except Exception:
                writable = False
            
            response_time = time.time() - start_time
            status = "healthy" if disk_percent < 90 and writable else "degraded"
            
            return HealthStatus(
                name="filesystem",
                status=status,
                last_check=datetime.utcnow(),
                response_time=response_time,
                details={
                    "disk_usage_percent": disk_percent,
                    "disk_free_gb": disk_usage.free / (1024**3),
                    "log_directory_writable": writable
                }
            )
        except Exception as e:
            return HealthStatus(
                name="filesystem",
                status="unhealthy",
                last_check=datetime.utcnow(),
                response_time=time.time() - start_time,
                details={"error": str(e)}
            )
    
    async def check_email_client(self) -> HealthStatus:
        """Check email client health"""
        start_time = time.time()
        try:
            # Import and check email client
            from src.email_client import EmailClient
            
            email_client = EmailClient()
            # Perform a basic connection test (not sending actual email)
            connection_status = email_client.test_connection()
            
            response_time = time.time() - start_time
            status = "healthy" if connection_status else "unhealthy"
            
            return HealthStatus(
                name="email_client",
                status=status,
                last_check=datetime.utcnow(),
                response_time=response_time,
                details={"connection_test": connection_status}
            )
        except Exception as e:
            return HealthStatus(
                name="email_client",
                status="unhealthy",
                last_check=datetime.utcnow(),
                response_time=time.time() - start_time,
                details={"error": str(e)}
            )

class MetricsCollector:
    """Collects and stores system and application metrics"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.system_metrics_history = deque(maxlen=max_history)
        self.service_metrics_history = defaultdict(lambda: deque(maxlen=max_history))
        self.request_counter = defaultdict(int)
        self.error_counter = defaultdict(int)
        self.response_times = defaultdict(list)
        
    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        network = psutil.net_io_counters()
        
        metrics = SystemMetrics(
            timestamp=datetime.utcnow(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_percent=(disk.used / disk.total) * 100,
            network_bytes_sent=network.bytes_sent,
            network_bytes_recv=network.bytes_recv
        )
        
        self.system_metrics_history.append(metrics)
        return metrics
    
    def record_request(self, service: str, response_time: float, is_error: bool = False):
        """Record a service request for metrics"""
        self.request_counter[service] += 1
        if is_error:
            self.error_counter[service] += 1
        
        self.response_times[service].append(response_time)
        # Keep only last 100 response times per service
        if len(self.response_times[service]) > 100:
            self.response_times[service] = self.response_times[service][-100:]
    
    def get_service_metrics(self, service: str) -> ServiceMetrics:
        """Get current metrics for a service"""
        request_count = self.request_counter[service]
        error_count = self.error_counter[service]
        
        response_times = self.response_times[service]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Get queue length for Celery services
        queue_length = None
        if service == "celery":
            try:
                redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
                redis_client = redis.from_url(redis_url)
                queue_length = redis_client.llen('celery')
            except Exception:
                pass
        
        metrics = ServiceMetrics(
            service_name=service,
            timestamp=datetime.utcnow(),
            request_count=request_count,
            error_count=error_count,
            avg_response_time=avg_response_time,
            active_connections=0,  # To be implemented based on service type
            queue_length=queue_length
        )
        
        self.service_metrics_history[service].append(metrics)
        return metrics
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of all collected metrics"""
        # Latest system metrics
        latest_system = self.system_metrics_history[-1] if self.system_metrics_history else None
        
        # Service metrics summary
        service_summaries = {}
        for service in self.request_counter.keys():
            service_summaries[service] = asdict(self.get_service_metrics(service))
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system_metrics": asdict(latest_system) if latest_system else None,
            "service_metrics": service_summaries,
            "metrics_history_count": len(self.system_metrics_history)
        }

class AlertManager:
    """Manages alerts and notifications"""
    
    def __init__(self):
        self.alert_thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_percent": 90.0,
            "error_rate": 5.0,  # percentage
            "response_time": 5.0,  # seconds
            "queue_length": 100
        }
        self.active_alerts = {}
        self.alert_history = deque(maxlen=100)
    
    def check_alerts(self, system_metrics: SystemMetrics, service_metrics: Dict[str, ServiceMetrics]):
        """Check if any metrics exceed thresholds and trigger alerts"""
        current_time = datetime.utcnow()
        
        # Check system alerts
        if system_metrics.cpu_percent > self.alert_thresholds["cpu_percent"]:
            self._trigger_alert("high_cpu", f"CPU usage {system_metrics.cpu_percent:.1f}% exceeds threshold")
        
        if system_metrics.memory_percent > self.alert_thresholds["memory_percent"]:
            self._trigger_alert("high_memory", f"Memory usage {system_metrics.memory_percent:.1f}% exceeds threshold")
        
        if system_metrics.disk_percent > self.alert_thresholds["disk_percent"]:
            self._trigger_alert("high_disk", f"Disk usage {system_metrics.disk_percent:.1f}% exceeds threshold")
        
        # Check service alerts
        for service_name, metrics in service_metrics.items():
            # Error rate check
            if metrics.request_count > 0:
                error_rate = (metrics.error_count / metrics.request_count) * 100
                if error_rate > self.alert_thresholds["error_rate"]:
                    self._trigger_alert(f"{service_name}_high_error_rate", 
                                      f"Service {service_name} error rate {error_rate:.1f}% exceeds threshold")
            
            # Response time check
            if metrics.avg_response_time > self.alert_thresholds["response_time"]:
                self._trigger_alert(f"{service_name}_slow_response", 
                                  f"Service {service_name} avg response time {metrics.avg_response_time:.2f}s exceeds threshold")
            
            # Queue length check (for Celery)
            if metrics.queue_length and metrics.queue_length > self.alert_thresholds["queue_length"]:
                self._trigger_alert(f"{service_name}_queue_backlog", 
                                  f"Service {service_name} queue length {metrics.queue_length} exceeds threshold")
    
    def _trigger_alert(self, alert_id: str, message: str):
        """Trigger an alert"""
        if alert_id not in self.active_alerts:
            alert = {
                "id": alert_id,
                "message": message,
                "timestamp": datetime.utcnow(),
                "status": "active"
            }
            
            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert.copy())
            
            logger.warning(f"ALERT: {message}")
            
            # Here you could integrate with external alerting systems
            # such as PagerDuty, Slack, email, etc.
            self._send_alert_notification(alert)
    
    def _send_alert_notification(self, alert: Dict[str, Any]):
        """Send alert notification to external systems"""
        # Placeholder for external alert integration
        # You can implement Slack, email, or webhook notifications here
        pass
    
    def resolve_alert(self, alert_id: str):
        """Resolve an active alert"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id]["status"] = "resolved"
            self.active_alerts[alert_id]["resolved_at"] = datetime.utcnow()
            del self.active_alerts[alert_id]
            logger.info(f"Alert resolved: {alert_id}")
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts"""
        return list(self.active_alerts.values())

# Global instances
health_checker = HealthChecker()
metrics_collector = MetricsCollector()
alert_manager = AlertManager()

# FastAPI router for monitoring endpoints
router = APIRouter(prefix="/monitoring", tags=["monitoring"])

@router.get("/health")
async def get_health_status():
    """Get comprehensive health status of all services"""
    health_checks = await asyncio.gather(
        health_checker.check_redis(),
        health_checker.check_celery(),
        health_checker.check_filesystem(),
        health_checker.check_email_client(),
        return_exceptions=True
    )
    
    # Convert health checks to dict format
    health_status = {}
    overall_status = "healthy"
    
    for check in health_checks:
        if isinstance(check, HealthStatus):
            health_status[check.name] = asdict(check)
            if check.status == "unhealthy":
                overall_status = "unhealthy"
            elif check.status == "degraded" and overall_status == "healthy":
                overall_status = "degraded"
        else:
            # Handle exceptions
            service_name = "unknown"
            health_status[service_name] = {
                "name": service_name,
                "status": "unhealthy",
                "last_check": datetime.utcnow().isoformat(),
                "details": {"error": str(check)}
            }
            overall_status = "unhealthy"
    
    # Add system info
    uptime_seconds = time.time() - psutil.boot_time()
    uptime_str = str(timedelta(seconds=int(uptime_seconds)))
    
    response = {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": uptime_str,
        "version": "1.0.0",
        "services": health_status
    }
    
    status_code = 200 if overall_status in ["healthy", "degraded"] else 503
    return JSONResponse(content=response, status_code=status_code)

@router.get("/metrics")
async def get_metrics():
    """Get current system and service metrics"""
    # Collect current system metrics
    system_metrics = metrics_collector.collect_system_metrics()
    
    # Get service metrics for known services
    service_metrics = {}
    for service in ["api", "celery", "email"]:
        service_metrics[service] = metrics_collector.get_service_metrics(service)
    
    # Check for alerts
    alert_manager.check_alerts(system_metrics, service_metrics)
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "system_metrics": asdict(system_metrics),
        "service_metrics": {k: asdict(v) for k, v in service_metrics.items()},
        "active_alerts": alert_manager.get_active_alerts()
    }

@router.get("/metrics/summary")
async def get_metrics_summary():
    """Get a summary of all collected metrics"""
    return metrics_collector.get_metrics_summary()

@router.get("/alerts")
async def get_alerts():
    """Get active alerts"""
    return {
        "active_alerts": alert_manager.get_active_alerts(),
        "alert_history": list(alert_manager.alert_history)[-10:]  # Last 10 alerts
    }

@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """Resolve an active alert"""
    alert_manager.resolve_alert(alert_id)
    return {"message": f"Alert {alert_id} resolved"}

@router.get("/status")
async def get_simple_status():
    """Simple health check endpoint for load balancers"""
    try:
        # Quick Redis check
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        redis_client = redis.from_url(redis_url)
        redis_client.ping()
        
        return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")

# Utility functions for integration with other parts of the application
def record_api_request(endpoint: str, response_time: float, status_code: int):
    """Record an API request for monitoring"""
    is_error = status_code >= 400
    metrics_collector.record_request("api", response_time, is_error)

def record_celery_task(task_name: str, execution_time: float, success: bool):
    """Record a Celery task execution for monitoring"""
    metrics_collector.record_request("celery", execution_time, not success)

def record_email_operation(operation: str, response_time: float, success: bool):
    """Record an email operation for monitoring"""
    metrics_collector.record_request("email", response_time, not success)

# Background task to collect metrics periodically
async def periodic_metrics_collection():
    """Background task to collect metrics every minute"""
    while True:
        try:
            metrics_collector.collect_system_metrics()
            await asyncio.sleep(60)  # Collect metrics every minute
        except Exception as e:
            logger.error(f"Error in periodic metrics collection: {e}")
            await asyncio.sleep(60)

# Initialize monitoring on startup
def initialize_monitoring():
    """Initialize monitoring system"""
    logger.info("Initializing Karen AI monitoring system...")
    
    # Start background metrics collection
    asyncio.create_task(periodic_metrics_collection())
    
    logger.info("Monitoring system initialized successfully")

if __name__ == "__main__":
    # For testing the monitoring system
    asyncio.run(periodic_metrics_collection())
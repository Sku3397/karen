"""
Karen AI Performance Dashboard - Real-time Agent Performance Monitoring

Implements:
1. Real-time agent performance metrics
2. Task completion statistics  
3. System health indicators
4. NLP accuracy tracking
5. Export data to JSON/CSV for analysis

This dashboard provides comprehensive monitoring for the Karen AI autonomous agent ecosystem,
tracking performance across all agents and system components.
"""

import os
import json
import csv
import asyncio
import logging
import redis
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from pathlib import Path
import threading
import time
from contextlib import asynccontextmanager

# Import existing monitoring components
from ..monitoring import metrics_collector, health_checker, alert_manager
from ..config import get_config

logger = logging.getLogger(__name__)

@dataclass
class AgentPerformanceMetrics:
    """Performance metrics for individual agents"""
    agent_name: str
    timestamp: datetime
    tasks_completed: int
    tasks_failed: int
    average_task_duration: float
    memory_usage_mb: float
    cpu_usage_percent: float
    success_rate: float
    last_activity: datetime
    status: str  # active, idle, error, offline
    queue_length: int
    response_time_ms: float

@dataclass
class TaskCompletionStats:
    """Task completion statistics"""
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    pending_tasks: int
    completion_rate: float
    average_completion_time: float
    task_types: Dict[str, int]
    hourly_completion_trend: List[Dict[str, Any]]

@dataclass
class NLPAccuracyMetrics:
    """NLP accuracy tracking metrics"""
    intent_classification_accuracy: float
    entity_extraction_accuracy: float
    response_relevance_score: float
    customer_satisfaction_score: float
    total_nlp_requests: int
    successful_responses: int
    failed_responses: int
    average_confidence_score: float
    language_distribution: Dict[str, int]

@dataclass
class SystemHealthIndicators:
    """System-wide health indicators"""
    overall_health_score: float
    redis_status: str
    celery_status: str
    database_status: str
    memory_system_status: str
    agent_communication_status: str
    api_response_time: float
    error_rate: float
    uptime_percentage: float

class AgentPerformanceTracker:
    """Tracks performance metrics for individual agents"""
    
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.agent_metrics = defaultdict(lambda: deque(maxlen=1000))
        self.task_durations = defaultdict(list)
        self.agent_statuses = {}
        
    def record_agent_task(self, agent_name: str, task_name: str, 
                         duration: float, success: bool, metadata: Dict[str, Any] = None):
        """Record a completed agent task"""
        timestamp = datetime.utcnow()
        
        # Store task duration
        self.task_durations[agent_name].append(duration)
        if len(self.task_durations[agent_name]) > 100:
            self.task_durations[agent_name] = self.task_durations[agent_name][-100:]
        
        # Update agent metrics
        try:
            # Get current agent stats from Redis
            agent_key = f"agent_stats:{agent_name}"
            current_stats = self.redis_client.hgetall(agent_key)
            
            completed = int(current_stats.get(b'completed', 0)) + (1 if success else 0)
            failed = int(current_stats.get(b'failed', 0)) + (0 if success else 1)
            total = completed + failed
            
            # Update Redis with new stats
            self.redis_client.hset(agent_key, mapping={
                'completed': completed,
                'failed': failed,
                'last_task': task_name,
                'last_activity': timestamp.isoformat(),
                'avg_duration': sum(self.task_durations[agent_name]) / len(self.task_durations[agent_name])
            })
            
            # Calculate success rate
            success_rate = (completed / total * 100) if total > 0 else 0
            
            # Get system metrics for this agent (if available)
            memory_usage = 0
            cpu_usage = 0
            try:
                # This would need to be implemented based on how agents are deployed
                memory_usage = psutil.virtual_memory().percent
                cpu_usage = psutil.cpu_percent()
            except Exception:
                pass
            
            # Create metrics object
            metrics = AgentPerformanceMetrics(
                agent_name=agent_name,
                timestamp=timestamp,
                tasks_completed=completed,
                tasks_failed=failed,
                average_task_duration=sum(self.task_durations[agent_name]) / len(self.task_durations[agent_name]) if self.task_durations[agent_name] else 0,
                memory_usage_mb=memory_usage,
                cpu_usage_percent=cpu_usage,
                success_rate=success_rate,
                last_activity=timestamp,
                status="active",
                queue_length=self._get_agent_queue_length(agent_name),
                response_time_ms=duration * 1000
            )
            
            self.agent_metrics[agent_name].append(metrics)
            
        except Exception as e:
            logger.error(f"Error recording agent task for {agent_name}: {e}")
    
    def _get_agent_queue_length(self, agent_name: str) -> int:
        """Get current queue length for an agent"""
        try:
            queue_key = f"agent_queue:{agent_name}"
            return self.redis_client.llen(queue_key)
        except Exception:
            return 0
    
    def get_agent_performance(self, agent_name: str) -> Optional[AgentPerformanceMetrics]:
        """Get latest performance metrics for an agent"""
        if agent_name in self.agent_metrics and self.agent_metrics[agent_name]:
            return self.agent_metrics[agent_name][-1]
        return None
    
    def get_all_agent_performance(self) -> Dict[str, AgentPerformanceMetrics]:
        """Get latest performance metrics for all agents"""
        result = {}
        for agent_name in self.agent_metrics:
            metrics = self.get_agent_performance(agent_name)
            if metrics:
                result[agent_name] = metrics
        return result

class TaskStatisticsCollector:
    """Collects and analyzes task completion statistics"""
    
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.task_history = deque(maxlen=10000)
        
    def record_task_completion(self, task_type: str, agent_name: str, 
                             completion_time: float, success: bool):
        """Record a completed task"""
        task_record = {
            'task_type': task_type,
            'agent_name': agent_name,
            'completion_time': completion_time,
            'success': success,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.task_history.append(task_record)
        
        # Store in Redis for persistence
        try:
            task_key = f"task_stats:{datetime.utcnow().strftime('%Y%m%d')}"
            self.redis_client.lpush(task_key, json.dumps(task_record))
            self.redis_client.expire(task_key, 86400 * 30)  # Keep for 30 days
        except Exception as e:
            logger.error(f"Error storing task completion: {e}")
    
    def get_task_statistics(self, hours: int = 24) -> TaskCompletionStats:
        """Get task completion statistics for the specified time period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Filter recent tasks
        recent_tasks = [
            task for task in self.task_history
            if datetime.fromisoformat(task['timestamp']) > cutoff_time
        ]
        
        total_tasks = len(recent_tasks)
        completed_tasks = sum(1 for task in recent_tasks if task['success'])
        failed_tasks = total_tasks - completed_tasks
        pending_tasks = self._get_pending_tasks_count()
        
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Calculate average completion time
        completion_times = [task['completion_time'] for task in recent_tasks if task['success']]
        avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0
        
        # Count task types
        task_types = defaultdict(int)
        for task in recent_tasks:
            task_types[task['task_type']] += 1
        
        # Generate hourly trend
        hourly_trend = self._generate_hourly_trend(recent_tasks, hours)
        
        return TaskCompletionStats(
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            pending_tasks=pending_tasks,
            completion_rate=completion_rate,
            average_completion_time=avg_completion_time,
            task_types=dict(task_types),
            hourly_completion_trend=hourly_trend
        )
    
    def _get_pending_tasks_count(self) -> int:
        """Get count of pending tasks across all agents"""
        try:
            # Check autonomous_state.json for pending tasks
            state_file = Path("/mnt/c/Users/Man/ultra/projects/karen/autonomous_state.json")
            if state_file.exists():
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    return sum(state.get('tasks_in_queues', {}).values())
        except Exception:
            pass
        return 0
    
    def _generate_hourly_trend(self, tasks: List[Dict], hours: int) -> List[Dict[str, Any]]:
        """Generate hourly completion trend"""
        hourly_counts = defaultdict(lambda: {'completed': 0, 'failed': 0})
        
        for task in tasks:
            hour = datetime.fromisoformat(task['timestamp']).replace(minute=0, second=0, microsecond=0)
            hour_key = hour.isoformat()
            
            if task['success']:
                hourly_counts[hour_key]['completed'] += 1
            else:
                hourly_counts[hour_key]['failed'] += 1
        
        # Convert to list and sort by time
        trend = []
        for hour_key, counts in hourly_counts.items():
            trend.append({
                'hour': hour_key,
                'completed': counts['completed'],
                'failed': counts['failed'],
                'total': counts['completed'] + counts['failed']
            })
        
        return sorted(trend, key=lambda x: x['hour'])

class NLPAccuracyTracker:
    """Tracks NLP accuracy and performance metrics"""
    
    def __init__(self):
        self.nlp_metrics = deque(maxlen=1000)
        self.confidence_scores = deque(maxlen=1000)
        self.language_stats = defaultdict(int)
        
    def record_nlp_request(self, intent_accuracy: float, entity_accuracy: float,
                          response_relevance: float, confidence_score: float,
                          language: str = "en", success: bool = True):
        """Record an NLP processing request"""
        timestamp = datetime.utcnow()
        
        nlp_record = {
            'timestamp': timestamp,
            'intent_accuracy': intent_accuracy,
            'entity_accuracy': entity_accuracy,
            'response_relevance': response_relevance,
            'confidence_score': confidence_score,
            'language': language,
            'success': success
        }
        
        self.nlp_metrics.append(nlp_record)
        self.confidence_scores.append(confidence_score)
        self.language_stats[language] += 1
    
    def get_nlp_accuracy_metrics(self) -> NLPAccuracyMetrics:
        """Get current NLP accuracy metrics"""
        if not self.nlp_metrics:
            return NLPAccuracyMetrics(
                intent_classification_accuracy=0.0,
                entity_extraction_accuracy=0.0,
                response_relevance_score=0.0,
                customer_satisfaction_score=0.0,
                total_nlp_requests=0,
                successful_responses=0,
                failed_responses=0,
                average_confidence_score=0.0,
                language_distribution={}
            )
        
        recent_metrics = list(self.nlp_metrics)
        successful_metrics = [m for m in recent_metrics if m['success']]
        
        # Calculate averages
        intent_avg = sum(m['intent_accuracy'] for m in successful_metrics) / len(successful_metrics) if successful_metrics else 0
        entity_avg = sum(m['entity_accuracy'] for m in successful_metrics) / len(successful_metrics) if successful_metrics else 0
        relevance_avg = sum(m['response_relevance'] for m in successful_metrics) / len(successful_metrics) if successful_metrics else 0
        confidence_avg = sum(self.confidence_scores) / len(self.confidence_scores) if self.confidence_scores else 0
        
        # Customer satisfaction approximation based on response relevance and confidence
        satisfaction_score = (relevance_avg * 0.7 + confidence_avg * 0.3) * 100
        
        return NLPAccuracyMetrics(
            intent_classification_accuracy=intent_avg * 100,
            entity_extraction_accuracy=entity_avg * 100,
            response_relevance_score=relevance_avg * 100,
            customer_satisfaction_score=satisfaction_score,
            total_nlp_requests=len(recent_metrics),
            successful_responses=len(successful_metrics),
            failed_responses=len(recent_metrics) - len(successful_metrics),
            average_confidence_score=confidence_avg * 100,
            language_distribution=dict(self.language_stats)
        )

class SystemHealthMonitor:
    """Monitors overall system health indicators"""
    
    def __init__(self, redis_client):
        self.redis_client = redis_client
        self.health_history = deque(maxlen=100)
        
    async def get_system_health(self) -> SystemHealthIndicators:
        """Get comprehensive system health indicators"""
        start_time = time.time()
        
        # Get health statuses from existing monitoring
        redis_health = await health_checker.check_redis()
        celery_health = await health_checker.check_celery()
        filesystem_health = await health_checker.check_filesystem()
        email_health = await health_checker.check_email_client()
        
        # Check memory system status
        memory_status = await self._check_memory_system()
        
        # Check agent communication status
        agent_comm_status = await self._check_agent_communication()
        
        # Calculate overall health score
        health_scores = {
            'redis': 1.0 if redis_health.status == 'healthy' else 0.5 if redis_health.status == 'degraded' else 0.0,
            'celery': 1.0 if celery_health.status == 'healthy' else 0.5 if celery_health.status == 'degraded' else 0.0,
            'filesystem': 1.0 if filesystem_health.status == 'healthy' else 0.5 if filesystem_health.status == 'degraded' else 0.0,
            'email': 1.0 if email_health.status == 'healthy' else 0.5 if email_health.status == 'degraded' else 0.0,
            'memory': 1.0 if memory_status == 'healthy' else 0.5 if memory_status == 'degraded' else 0.0,
            'agents': 1.0 if agent_comm_status == 'healthy' else 0.5 if agent_comm_status == 'degraded' else 0.0
        }
        
        overall_health_score = (sum(health_scores.values()) / len(health_scores)) * 100
        
        # Calculate uptime percentage
        uptime_percentage = await self._calculate_uptime()
        
        # Get error rate from metrics
        error_rate = await self._calculate_error_rate()
        
        api_response_time = time.time() - start_time
        
        health_indicators = SystemHealthIndicators(
            overall_health_score=overall_health_score,
            redis_status=redis_health.status,
            celery_status=celery_health.status,
            database_status=filesystem_health.status,  # Using filesystem as proxy for database
            memory_system_status=memory_status,
            agent_communication_status=agent_comm_status,
            api_response_time=api_response_time * 1000,  # Convert to ms
            error_rate=error_rate,
            uptime_percentage=uptime_percentage
        )
        
        self.health_history.append(health_indicators)
        return health_indicators
    
    async def _check_memory_system(self) -> str:
        """Check intelligent memory system status"""
        try:
            # Check if memory system is accessible
            memory_file = Path("/mnt/c/Users/Man/ultra/projects/karen/src/intelligent_memory_system.py")
            if memory_file.exists():
                return "healthy"
            else:
                return "degraded"
        except Exception:
            return "unhealthy"
    
    async def _check_agent_communication(self) -> str:
        """Check agent communication system status"""
        try:
            # Check if agent communication directories exist and are accessible
            comm_dir = Path("/mnt/c/Users/Man/ultra/projects/karen/autonomous-agents/communication")
            if comm_dir.exists() and (comm_dir / "inbox").exists():
                # Check if Redis is working for agent communication
                try:
                    self.redis_client.ping()
                    return "healthy"
                except Exception:
                    return "degraded"  # File-based communication still works
            else:
                return "unhealthy"
        except Exception:
            return "unhealthy"
    
    async def _calculate_uptime(self) -> float:
        """Calculate system uptime percentage"""
        try:
            # Get system uptime
            uptime_seconds = time.time() - psutil.boot_time()
            uptime_hours = uptime_seconds / 3600
            
            # For now, assume high uptime - in production, this would track actual downtime
            return min(99.9, (uptime_hours / (uptime_hours + 0.1)) * 100)
        except Exception:
            return 95.0  # Default fallback
    
    async def _calculate_error_rate(self) -> float:
        """Calculate current error rate"""
        try:
            # Get error metrics from metrics collector
            summary = metrics_collector.get_metrics_summary()
            service_metrics = summary.get('service_metrics', {})
            
            total_requests = 0
            total_errors = 0
            
            for service_name, metrics in service_metrics.items():
                total_requests += metrics.get('request_count', 0)
                total_errors += metrics.get('error_count', 0)
            
            if total_requests > 0:
                return (total_errors / total_requests) * 100
            else:
                return 0.0
        except Exception:
            return 0.0

class DataExporter:
    """Exports performance data to JSON/CSV formats"""
    
    def __init__(self, output_dir: str = "performance_exports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def export_agent_performance(self, agent_metrics: Dict[str, AgentPerformanceMetrics], 
                                format: str = "json") -> str:
        """Export agent performance data"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        if format.lower() == "json":
            filename = f"agent_performance_{timestamp}.json"
            filepath = self.output_dir / filename
            
            # Convert to serializable format
            export_data = {}
            for agent_name, metrics in agent_metrics.items():
                export_data[agent_name] = asdict(metrics)
                # Convert datetime to string
                export_data[agent_name]['timestamp'] = export_data[agent_name]['timestamp'].isoformat()
                export_data[agent_name]['last_activity'] = export_data[agent_name]['last_activity'].isoformat()
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
                
        elif format.lower() == "csv":
            filename = f"agent_performance_{timestamp}.csv"
            filepath = self.output_dir / filename
            
            with open(filepath, 'w', newline='') as f:
                if agent_metrics:
                    # Get field names from first metrics object
                    first_metrics = next(iter(agent_metrics.values()))
                    fieldnames = list(asdict(first_metrics).keys())
                    
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for agent_name, metrics in agent_metrics.items():
                        row = asdict(metrics)
                        row['timestamp'] = row['timestamp'].isoformat()
                        row['last_activity'] = row['last_activity'].isoformat()
                        writer.writerow(row)
        
        return str(filepath)
    
    def export_task_statistics(self, task_stats: TaskCompletionStats, format: str = "json") -> str:
        """Export task completion statistics"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        if format.lower() == "json":
            filename = f"task_statistics_{timestamp}.json"
            filepath = self.output_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(asdict(task_stats), f, indent=2)
                
        elif format.lower() == "csv":
            filename = f"task_statistics_{timestamp}.csv"
            filepath = self.output_dir / filename
            
            # Export task types as CSV
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Metric', 'Value'])
                
                stats_dict = asdict(task_stats)
                for key, value in stats_dict.items():
                    if key != 'task_types' and key != 'hourly_completion_trend':
                        writer.writerow([key, value])
                
                # Write task types
                writer.writerow(['', ''])  # Empty row
                writer.writerow(['Task Type', 'Count'])
                for task_type, count in task_stats.task_types.items():
                    writer.writerow([task_type, count])
        
        return str(filepath)
    
    def export_system_health(self, health_indicators: SystemHealthIndicators, format: str = "json") -> str:
        """Export system health data"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        if format.lower() == "json":
            filename = f"system_health_{timestamp}.json"
            filepath = self.output_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(asdict(health_indicators), f, indent=2)
                
        elif format.lower() == "csv":
            filename = f"system_health_{timestamp}.csv"
            filepath = self.output_dir / filename
            
            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Metric', 'Value'])
                
                health_dict = asdict(health_indicators)
                for key, value in health_dict.items():
                    writer.writerow([key, value])
        
        return str(filepath)

class PerformanceDashboard:
    """Main performance dashboard coordinator"""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.redis_client = None
        self._initialize_redis()
        
        # Initialize components
        self.agent_tracker = AgentPerformanceTracker(self.redis_client)
        self.task_collector = TaskStatisticsCollector(self.redis_client)
        self.nlp_tracker = NLPAccuracyTracker()
        self.health_monitor = SystemHealthMonitor(self.redis_client)
        self.data_exporter = DataExporter()
        
        # Background monitoring
        self._monitoring_active = False
        self._monitoring_task = None
        
        logger.info("Performance Dashboard initialized successfully")
    
    def _initialize_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            self.redis_client.ping()
            logger.info("Connected to Redis for performance monitoring")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    async def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get comprehensive real-time performance metrics"""
        try:
            # Gather all metrics
            agent_performance = self.agent_tracker.get_all_agent_performance()
            task_statistics = self.task_collector.get_task_statistics()
            nlp_metrics = self.nlp_tracker.get_nlp_accuracy_metrics()
            system_health = await self.health_monitor.get_system_health()
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "agent_performance": {name: asdict(metrics) for name, metrics in agent_performance.items()},
                "task_statistics": asdict(task_statistics),
                "nlp_metrics": asdict(nlp_metrics),
                "system_health": asdict(system_health),
                "summary": {
                    "total_agents": len(agent_performance),
                    "active_agents": len([m for m in agent_performance.values() if m.status == "active"]),
                    "overall_success_rate": sum(m.success_rate for m in agent_performance.values()) / len(agent_performance) if agent_performance else 0,
                    "system_health_score": system_health.overall_health_score
                }
            }
        except Exception as e:
            logger.error(f"Error getting real-time metrics: {e}")
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}
    
    def record_agent_activity(self, agent_name: str, task_name: str, 
                            duration: float, success: bool, metadata: Dict[str, Any] = None):
        """Record agent activity for performance tracking"""
        self.agent_tracker.record_agent_task(agent_name, task_name, duration, success, metadata)
        self.task_collector.record_task_completion(task_name, agent_name, duration, success)
    
    def record_nlp_activity(self, intent_accuracy: float = 1.0, entity_accuracy: float = 1.0,
                           response_relevance: float = 1.0, confidence_score: float = 1.0,
                           language: str = "en", success: bool = True):
        """Record NLP processing activity"""
        self.nlp_tracker.record_nlp_request(
            intent_accuracy, entity_accuracy, response_relevance, 
            confidence_score, language, success
        )
    
    async def export_performance_data(self, format: str = "json") -> Dict[str, str]:
        """Export all performance data to files"""
        try:
            agent_performance = self.agent_tracker.get_all_agent_performance()
            task_statistics = self.task_collector.get_task_statistics()
            system_health = await self.health_monitor.get_system_health()
            
            exported_files = {}
            
            if agent_performance:
                agent_file = self.data_exporter.export_agent_performance(agent_performance, format)
                exported_files["agent_performance"] = agent_file
            
            task_file = self.data_exporter.export_task_statistics(task_statistics, format)
            exported_files["task_statistics"] = task_file
            
            health_file = self.data_exporter.export_system_health(system_health, format)
            exported_files["system_health"] = health_file
            
            logger.info(f"Exported performance data to {len(exported_files)} files")
            return exported_files
            
        except Exception as e:
            logger.error(f"Error exporting performance data: {e}")
            return {"error": str(e)}
    
    async def start_monitoring(self, interval_seconds: int = 60):
        """Start background performance monitoring"""
        if self._monitoring_active:
            logger.warning("Performance monitoring already active")
            return
        
        self._monitoring_active = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop(interval_seconds))
        logger.info(f"Started performance monitoring with {interval_seconds}s interval")
    
    async def stop_monitoring(self):
        """Stop background performance monitoring"""
        if self._monitoring_task:
            self._monitoring_active = False
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            logger.info("Stopped performance monitoring")
    
    async def _monitoring_loop(self, interval_seconds: int):
        """Background monitoring loop"""
        while self._monitoring_active:
            try:
                # Collect metrics
                await self.get_real_time_metrics()
                
                # Export data periodically (every 10 minutes)
                if int(time.time()) % 600 == 0:
                    await self.export_performance_data()
                
                await asyncio.sleep(interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(interval_seconds)

# Global dashboard instance
_dashboard_instance = None

def get_performance_dashboard(redis_url: str = None) -> PerformanceDashboard:
    """Get or create global performance dashboard instance"""
    global _dashboard_instance
    
    if _dashboard_instance is None:
        _dashboard_instance = PerformanceDashboard(redis_url)
    
    return _dashboard_instance

# Convenience functions for easy integration
def record_agent_task(agent_name: str, task_name: str, duration: float, success: bool, metadata: Dict[str, Any] = None):
    """Record an agent task completion"""
    dashboard = get_performance_dashboard()
    dashboard.record_agent_activity(agent_name, task_name, duration, success, metadata)

def record_nlp_request(intent_accuracy: float = 1.0, entity_accuracy: float = 1.0,
                      response_relevance: float = 1.0, confidence_score: float = 1.0,
                      language: str = "en", success: bool = True):
    """Record an NLP processing request"""
    dashboard = get_performance_dashboard()
    dashboard.record_nlp_activity(intent_accuracy, entity_accuracy, response_relevance, 
                                 confidence_score, language, success)

async def get_dashboard_metrics() -> Dict[str, Any]:
    """Get current dashboard metrics"""
    dashboard = get_performance_dashboard()
    return await dashboard.get_real_time_metrics()

async def export_dashboard_data(format: str = "json") -> Dict[str, str]:
    """Export dashboard data to files"""
    dashboard = get_performance_dashboard()
    return await dashboard.export_performance_data(format)

if __name__ == "__main__":
    # Demo/test the performance dashboard
    async def demo():
        dashboard = get_performance_dashboard()
        
        # Simulate some agent activity
        dashboard.record_agent_activity("sms_engineer", "send_sms", 1.5, True)
        dashboard.record_agent_activity("memory_engineer", "store_memory", 0.8, True)
        dashboard.record_agent_activity("orchestrator", "coordinate_task", 2.1, False)
        
        # Simulate NLP activity
        dashboard.record_nlp_activity(0.95, 0.88, 0.92, 0.90, "en", True)
        
        # Get metrics
        metrics = await dashboard.get_real_time_metrics()
        print("Performance Metrics:")
        print(json.dumps(metrics, indent=2, default=str))
        
        # Export data
        files = await dashboard.export_performance_data("json")
        print(f"\nExported files: {files}")
    
    asyncio.run(demo())
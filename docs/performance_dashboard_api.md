# Performance Dashboard API Documentation

## Overview

The Karen AI Performance Dashboard provides comprehensive monitoring and analytics for the autonomous agent ecosystem. This API documentation covers all endpoints, data models, and integration patterns for real-time performance monitoring.

## Base URL

```
http://localhost:8000/monitoring/dashboard
```

## Authentication

All dashboard endpoints inherit authentication from the main Karen AI system. Ensure you have proper API keys or JWT tokens configured.

## Core Data Models

### AgentPerformanceMetrics

```json
{
  "agent_name": "string",
  "timestamp": "2025-06-04T12:00:00Z",
  "tasks_completed": 150,
  "tasks_failed": 5,
  "average_task_duration": 2.5,
  "memory_usage_mb": 128.5,
  "cpu_usage_percent": 15.2,
  "success_rate": 96.8,
  "last_activity": "2025-06-04T12:00:00Z",
  "status": "active",
  "queue_length": 3,
  "response_time_ms": 1250.0
}
```

### TaskCompletionStats

```json
{
  "total_tasks": 1000,
  "completed_tasks": 950,
  "failed_tasks": 50,
  "pending_tasks": 25,
  "completion_rate": 95.0,
  "average_completion_time": 2.8,
  "task_types": {
    "email_processing": 400,
    "sms_handling": 300,
    "calendar_scheduling": 200,
    "memory_operations": 100
  },
  "hourly_completion_trend": [
    {
      "hour": "2025-06-04T10:00:00Z",
      "completed": 45,
      "failed": 2,
      "total": 47
    }
  ]
}
```

### NLPAccuracyMetrics

```json
{
  "intent_classification_accuracy": 94.5,
  "entity_extraction_accuracy": 89.2,
  "response_relevance_score": 91.8,
  "customer_satisfaction_score": 88.6,
  "total_nlp_requests": 500,
  "successful_responses": 485,
  "failed_responses": 15,
  "average_confidence_score": 87.3,
  "language_distribution": {
    "en": 450,
    "es": 30,
    "fr": 20
  }
}
```

### SystemHealthIndicators

```json
{
  "overall_health_score": 92.5,
  "redis_status": "healthy",
  "celery_status": "healthy",
  "database_status": "healthy",
  "memory_system_status": "healthy",
  "agent_communication_status": "healthy",
  "api_response_time": 245.0,
  "error_rate": 1.2,
  "uptime_percentage": 99.8
}
```

## API Endpoints

### GET /metrics/realtime

Get comprehensive real-time performance metrics for all system components.

**Response:**
```json
{
  "timestamp": "2025-06-04T12:00:00Z",
  "agent_performance": {
    "orchestrator": { /* AgentPerformanceMetrics */ },
    "sms_engineer": { /* AgentPerformanceMetrics */ },
    "memory_engineer": { /* AgentPerformanceMetrics */ }
  },
  "task_statistics": { /* TaskCompletionStats */ },
  "nlp_metrics": { /* NLPAccuracyMetrics */ },
  "system_health": { /* SystemHealthIndicators */ },
  "summary": {
    "total_agents": 5,
    "active_agents": 5,
    "overall_success_rate": 94.2,
    "system_health_score": 92.5
  }
}
```

**Status Codes:**
- `200` - Success
- `500` - Internal server error

### GET /metrics/agent/{agent_name}

Get performance metrics for a specific agent.

**Parameters:**
- `agent_name` (path): Name of the agent (orchestrator, sms_engineer, memory_engineer, etc.)

**Response:**
```json
{
  "agent_name": "sms_engineer",
  "timestamp": "2025-06-04T12:00:00Z",
  "tasks_completed": 75,
  "tasks_failed": 2,
  "average_task_duration": 1.8,
  "memory_usage_mb": 64.2,
  "cpu_usage_percent": 8.5,
  "success_rate": 97.4,
  "last_activity": "2025-06-04T12:00:00Z",
  "status": "active",
  "queue_length": 1,
  "response_time_ms": 850.0
}
```

**Status Codes:**
- `200` - Success
- `404` - Agent not found
- `500` - Internal server error

### GET /metrics/tasks

Get task completion statistics with optional time filtering.

**Query Parameters:**
- `hours` (optional): Number of hours to look back (default: 24)
- `task_type` (optional): Filter by specific task type

**Response:**
```json
{
  "total_tasks": 500,
  "completed_tasks": 475,
  "failed_tasks": 25,
  "pending_tasks": 12,
  "completion_rate": 95.0,
  "average_completion_time": 2.2,
  "task_types": {
    "email_processing": 200,
    "sms_handling": 150,
    "calendar_scheduling": 100,
    "memory_operations": 50
  },
  "hourly_completion_trend": [
    {
      "hour": "2025-06-04T10:00:00Z",
      "completed": 22,
      "failed": 1,
      "total": 23
    }
  ]
}
```

### GET /metrics/nlp

Get NLP accuracy and performance metrics.

**Response:**
```json
{
  "intent_classification_accuracy": 94.5,
  "entity_extraction_accuracy": 89.2,
  "response_relevance_score": 91.8,
  "customer_satisfaction_score": 88.6,
  "total_nlp_requests": 250,
  "successful_responses": 242,
  "failed_responses": 8,
  "average_confidence_score": 87.3,
  "language_distribution": {
    "en": 225,
    "es": 15,
    "fr": 10
  }
}
```

### GET /health/system

Get comprehensive system health indicators.

**Response:**
```json
{
  "overall_health_score": 92.5,
  "redis_status": "healthy",
  "celery_status": "healthy",
  "database_status": "healthy",
  "memory_system_status": "healthy",
  "agent_communication_status": "healthy",
  "api_response_time": 245.0,
  "error_rate": 1.2,
  "uptime_percentage": 99.8
}
```

### POST /metrics/record/agent

Record agent task completion for performance tracking.

**Request Body:**
```json
{
  "agent_name": "sms_engineer",
  "task_name": "send_sms_notification",
  "duration": 1.5,
  "success": true,
  "metadata": {
    "message_length": 160,
    "recipient_count": 1
  }
}
```

**Response:**
```json
{
  "status": "recorded",
  "timestamp": "2025-06-04T12:00:00Z"
}
```

### POST /metrics/record/nlp

Record NLP processing activity for accuracy tracking.

**Request Body:**
```json
{
  "intent_accuracy": 0.95,
  "entity_accuracy": 0.88,
  "response_relevance": 0.92,
  "confidence_score": 0.90,
  "language": "en",
  "success": true
}
```

**Response:**
```json
{
  "status": "recorded",
  "timestamp": "2025-06-04T12:00:00Z"
}
```

### POST /export

Export performance data to JSON or CSV format.

**Request Body:**
```json
{
  "format": "json",
  "data_types": ["agent_performance", "task_statistics", "system_health"],
  "time_range": {
    "start": "2025-06-04T00:00:00Z",
    "end": "2025-06-04T23:59:59Z"
  }
}
```

**Response:**
```json
{
  "exported_files": {
    "agent_performance": "/exports/agent_performance_20250604_120000.json",
    "task_statistics": "/exports/task_statistics_20250604_120000.json",
    "system_health": "/exports/system_health_20250604_120000.json"
  },
  "export_timestamp": "2025-06-04T12:00:00Z"
}
```

### WebSocket Endpoints

#### ws://localhost:8000/monitoring/dashboard/realtime

Real-time streaming of performance metrics.

**Message Format:**
```json
{
  "type": "metrics_update",
  "timestamp": "2025-06-04T12:00:00Z",
  "data": {
    "agent_performance": { /* Latest metrics */ },
    "system_health": { /* Latest health status */ }
  }
}
```

**Subscription Message:**
```json
{
  "action": "subscribe",
  "metrics": ["agent_performance", "system_health", "task_statistics"]
}
```

## Error Handling

All API endpoints follow consistent error response format:

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Agent name is required",
    "details": {
      "field": "agent_name",
      "constraint": "not_empty"
    }
  },
  "timestamp": "2025-06-04T12:00:00Z"
}
```

### Common Error Codes

- `INVALID_REQUEST` - Invalid request parameters
- `AGENT_NOT_FOUND` - Specified agent doesn't exist
- `DATA_EXPORT_FAILED` - Failed to export data
- `REDIS_CONNECTION_ERROR` - Redis connectivity issues
- `INTERNAL_ERROR` - Unexpected server error

## Rate Limiting

- Real-time metrics: 60 requests per minute
- Export operations: 10 requests per minute
- Recording endpoints: 1000 requests per minute

## Integration Examples

### Python Client

```python
import asyncio
import aiohttp
from src.monitoring.performance_dashboard import get_performance_dashboard

# Using the dashboard directly
dashboard = get_performance_dashboard()
metrics = await dashboard.get_real_time_metrics()

# Using HTTP API
async with aiohttp.ClientSession() as session:
    async with session.get('http://localhost:8000/monitoring/dashboard/metrics/realtime') as resp:
        data = await resp.json()
        print(f"System health: {data['system_health']['overall_health_score']}")
```

### JavaScript Client

```javascript
// Fetch real-time metrics
const response = await fetch('/monitoring/dashboard/metrics/realtime');
const metrics = await response.json();

// WebSocket for real-time updates
const ws = new WebSocket('ws://localhost:8000/monitoring/dashboard/realtime');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    updateDashboard(data);
};

// Subscribe to specific metrics
ws.send(JSON.stringify({
    action: 'subscribe',
    metrics: ['agent_performance', 'system_health']
}));
```

### cURL Examples

```bash
# Get real-time metrics
curl -X GET "http://localhost:8000/monitoring/dashboard/metrics/realtime" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Record agent task
curl -X POST "http://localhost:8000/monitoring/dashboard/metrics/record/agent" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "sms_engineer",
    "task_name": "send_sms",
    "duration": 1.2,
    "success": true
  }'

# Export data
curl -X POST "http://localhost:8000/monitoring/dashboard/export" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "json",
    "data_types": ["agent_performance"]
  }'
```

## Performance Considerations

- **Caching**: Real-time metrics are cached for 30 seconds
- **Data Retention**: Raw metrics kept for 7 days, aggregated data for 90 days
- **Batch Processing**: Use batch recording for high-volume metrics
- **WebSocket Limits**: Max 100 concurrent WebSocket connections

## Security

- All endpoints require authentication via JWT tokens
- Rate limiting prevents abuse
- Data export requires elevated permissions
- WebSocket connections are authenticated and monitored

## Monitoring the Monitor

The performance dashboard itself is monitored:

- Dashboard response times tracked
- Redis connection health monitored
- Export operation success rates logged
- WebSocket connection stability tracked
#!/usr/bin/env python3
"""
Analytics for voice calls - track performance and quality
Comprehensive call metrics for 757 Handy voice system optimization

Author: Phone Engineer Agent
"""

import os
import json
import logging
import redis
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import statistics

logger = logging.getLogger(__name__)

@dataclass
class CallMetrics:
    """Comprehensive call metrics data structure"""
    call_sid: str
    caller_id: str
    timestamp: datetime
    duration: int  # seconds
    call_type: str  # inbound, outbound, emergency
    resolution_status: str  # resolved, transferred, voicemail, abandoned
    wait_time: int  # seconds in queue
    menu_selections: List[str]  # IVR path taken
    transfers: int  # number of transfers
    voicemail_left: bool
    transcription_accuracy: float  # 0-1 score
    customer_satisfaction: Optional[int] = None  # 1-5 if surveyed
    emergency_level: int = 1  # 1-5 urgency
    first_call_resolution: bool = False
    call_back_required: bool = False
    technician_assigned: Optional[str] = None
    service_type: Optional[str] = None  # appointment, quote, emergency, etc.
    
class VoiceCallAnalytics:
    """
    Comprehensive voice call analytics system
    
    Features:
    - Real-time call metrics tracking
    - Performance analytics and reporting
    - Customer journey mapping
    - Quality assurance scoring
    - Business intelligence dashboards
    - Predictive analytics for staffing
    """
    
    def __init__(self):
        # Initialize Redis for real-time metrics
        try:
            self.redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=int(os.getenv('REDIS_DB', 1)),  # Use different DB for analytics
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("Redis analytics connection established")
        except Exception as e:
            logger.warning(f"Redis connection failed, using memory storage: {e}")
            self.redis_client = None
        
        # In-memory fallback
        self.calls_db = []
        self.daily_metrics = defaultdict(list)
        self.customer_journey_map = defaultdict(list)
        
        # Analytics configuration
        self.metrics_retention_days = 90
        self.real_time_window_minutes = 15
        
        # Business hours for analysis
        self.business_hours = {
            'monday': (8, 18),
            'tuesday': (8, 18),
            'wednesday': (8, 18),
            'thursday': (8, 18),
            'friday': (8, 18),
            'saturday': (9, 16),
            'sunday': None  # Closed
        }
        
        logger.info("VoiceCallAnalytics initialized with comprehensive tracking")
    
    def log_call(self, call_data: Dict) -> str:
        """Log call with all relevant metrics and enrich with analytics"""
        try:
            # Enrich call data with analytics
            enriched_data = self._enrich_call_data(call_data)
            
            # Create CallMetrics object
            call_metrics = CallMetrics(**enriched_data)
            
            # Store in Redis for real-time access
            if self.redis_client:
                call_key = f"call:{call_metrics.call_sid}"
                metrics_dict = asdict(call_metrics)
                
                # Convert datetime to ISO string for Redis
                metrics_dict['timestamp'] = call_metrics.timestamp.isoformat()
                
                self.redis_client.hset(call_key, mapping=metrics_dict)
                self.redis_client.expire(call_key, self.metrics_retention_days * 86400)
                
                # Add to time-series data
                self._update_time_series_metrics(call_metrics)
            
            # Fallback to memory storage
            self.calls_db.append(call_metrics)
            
            # Update customer journey
            self._update_customer_journey(call_metrics)
            
            # Trigger real-time alerts if needed
            self._check_real_time_alerts(call_metrics)
            
            logger.info(f"Call logged: {call_metrics.call_sid} - {call_metrics.resolution_status}")
            return call_metrics.call_sid
            
        except Exception as e:
            logger.error(f"Failed to log call: {e}")
            return None
    
    def _enrich_call_data(self, call_data: Dict) -> Dict:
        """Enrich call data with calculated metrics"""
        enriched = call_data.copy()
        
        # Set timestamp if not provided
        if 'timestamp' not in enriched:
            enriched['timestamp'] = datetime.now()
        
        # Calculate wait time
        enriched['wait_time'] = self._calculate_wait_time(call_data)
        
        # Determine resolution status
        enriched['resolution_status'] = self._determine_resolution(call_data)
        
        # Assess emergency level
        enriched['emergency_level'] = self._assess_emergency_level(call_data)
        
        # Calculate first call resolution
        enriched['first_call_resolution'] = self._is_first_call_resolution(call_data)
        
        # Estimate transcription accuracy
        enriched['transcription_accuracy'] = self._estimate_transcription_accuracy(call_data)
        
        # Set default values for optional fields
        defaults = {
            'menu_selections': [],
            'transfers': 0,
            'voicemail_left': False,
            'call_back_required': False,
            'service_type': 'general'
        }
        
        for key, default_value in defaults.items():
            if key not in enriched:
                enriched[key] = default_value
        
        return enriched
    
    def _calculate_wait_time(self, call_data: Dict) -> int:
        """Calculate customer wait time in queue"""
        # Check if call went to queue
        if 'queue_enter_time' in call_data and 'queue_exit_time' in call_data:
            enter_time = datetime.fromisoformat(call_data['queue_enter_time'])
            exit_time = datetime.fromisoformat(call_data['queue_exit_time'])
            return int((exit_time - enter_time).total_seconds())
        
        # Estimate based on menu navigation time
        if 'menu_selections' in call_data and call_data['menu_selections']:
            return len(call_data['menu_selections']) * 10  # 10 seconds per menu
        
        return 0
    
    def _determine_resolution(self, call_data: Dict) -> str:
        """Determine call resolution status"""
        if call_data.get('transferred_to_human'):
            return 'transferred'
        elif call_data.get('voicemail_left'):
            return 'voicemail'
        elif call_data.get('appointment_scheduled'):
            return 'resolved'
        elif call_data.get('quote_requested'):
            return 'resolved'
        elif call_data.get('call_duration', 0) < 30:
            return 'abandoned'
        else:
            return 'completed'
    
    def _assess_emergency_level(self, call_data: Dict) -> int:
        """Assess emergency level from call data"""
        emergency_keywords = [
            'emergency', 'urgent', 'flood', 'leak', 'broken pipe',
            'no heat', 'no hot water', 'electrical problem', 'smoke'
        ]
        
        transcription = call_data.get('transcription', '').lower()
        
        for keyword in emergency_keywords:
            if keyword in transcription:
                if keyword in ['emergency', 'flood', 'smoke']:
                    return 5  # Critical
                elif keyword in ['urgent', 'no heat', 'electrical problem']:
                    return 4  # High
                else:
                    return 3  # Medium
        
        # Check for after-hours calls (likely more urgent)
        call_time = call_data.get('timestamp', datetime.now())
        if not self._is_business_hours(call_time):
            return 2  # Elevated
        
        return 1  # Routine
    
    def _is_first_call_resolution(self, call_data: Dict) -> bool:
        """Determine if call was resolved on first contact"""
        return (
            call_data.get('appointment_scheduled', False) or
            call_data.get('quote_provided', False) or
            (call_data.get('transfers', 0) == 0 and 
             call_data.get('resolution_status') == 'resolved')
        )
    
    def _estimate_transcription_accuracy(self, call_data: Dict) -> float:
        """Estimate transcription accuracy based on confidence scores"""
        if 'transcription_confidence' in call_data:
            return call_data['transcription_confidence']
        
        # Estimate based on call quality indicators
        transcription = call_data.get('transcription', '')
        if not transcription:
            return 0.0
        
        # Simple heuristics for accuracy estimation
        accuracy = 0.8  # Base accuracy
        
        # Adjust based on transcription characteristics
        if len(transcription) < 10:
            accuracy -= 0.2  # Very short transcriptions often incomplete
        
        if '...' in transcription or '[unclear]' in transcription:
            accuracy -= 0.3  # Contains unclear segments
        
        return max(0.0, min(1.0, accuracy))
    
    def _is_business_hours(self, timestamp: datetime) -> bool:
        """Check if timestamp falls within business hours"""
        day_name = timestamp.strftime('%A').lower()
        hours = self.business_hours.get(day_name)
        
        if hours is None:
            return False
        
        current_hour = timestamp.hour
        return hours[0] <= current_hour < hours[1]
    
    def _update_time_series_metrics(self, call_metrics: CallMetrics):
        """Update time-series metrics in Redis"""
        if not self.redis_client:
            return
        
        try:
            # Use minute-level granularity for real-time metrics
            minute_key = call_metrics.timestamp.strftime('%Y-%m-%d %H:%M')
            hour_key = call_metrics.timestamp.strftime('%Y-%m-%d %H')
            day_key = call_metrics.timestamp.strftime('%Y-%m-%d')
            
            # Increment call counters
            self.redis_client.hincrby(f"metrics:minute:{minute_key}", 'total_calls', 1)
            self.redis_client.hincrby(f"metrics:hour:{hour_key}", 'total_calls', 1)
            self.redis_client.hincrby(f"metrics:day:{day_key}", 'total_calls', 1)
            
            # Track resolution types
            self.redis_client.hincrby(f"metrics:day:{day_key}", 
                                    f"resolution_{call_metrics.resolution_status}", 1)
            
            # Track emergency calls
            if call_metrics.emergency_level >= 4:
                self.redis_client.hincrby(f"metrics:day:{day_key}", 'emergency_calls', 1)
            
            # Set expiration for time-series data
            for key in [f"metrics:minute:{minute_key}", f"metrics:hour:{hour_key}", f"metrics:day:{day_key}"]:
                self.redis_client.expire(key, self.metrics_retention_days * 86400)
                
        except Exception as e:
            logger.error(f"Failed to update time-series metrics: {e}")
    
    def _update_customer_journey(self, call_metrics: CallMetrics):
        """Track customer journey across multiple calls"""
        try:
            customer_key = f"customer:{call_metrics.caller_id}"
            journey_data = {
                'call_sid': call_metrics.call_sid,
                'timestamp': call_metrics.timestamp.isoformat(),
                'service_type': call_metrics.service_type,
                'resolution_status': call_metrics.resolution_status,
                'first_call_resolution': call_metrics.first_call_resolution
            }
            
            if self.redis_client:
                # Add to customer journey list
                self.redis_client.lpush(customer_key, json.dumps(journey_data))
                self.redis_client.ltrim(customer_key, 0, 49)  # Keep last 50 interactions
                self.redis_client.expire(customer_key, 365 * 86400)  # 1 year retention
            else:
                # Fallback to memory
                self.customer_journey_map[call_metrics.caller_id].append(journey_data)
                
        except Exception as e:
            logger.error(f"Failed to update customer journey: {e}")
    
    def _check_real_time_alerts(self, call_metrics: CallMetrics):
        """Check for conditions that require real-time alerts"""
        try:
            # High emergency level
            if call_metrics.emergency_level >= 4:
                self._trigger_alert('emergency_call', {
                    'call_sid': call_metrics.call_sid,
                    'caller_id': call_metrics.caller_id,
                    'emergency_level': call_metrics.emergency_level
                })
            
            # Long wait time
            if call_metrics.wait_time > 300:  # 5 minutes
                self._trigger_alert('long_wait_time', {
                    'call_sid': call_metrics.call_sid,
                    'wait_time': call_metrics.wait_time
                })
            
            # Multiple transfers
            if call_metrics.transfers > 2:
                self._trigger_alert('multiple_transfers', {
                    'call_sid': call_metrics.call_sid,
                    'transfers': call_metrics.transfers
                })
                
        except Exception as e:
            logger.error(f"Failed to check real-time alerts: {e}")
    
    def _trigger_alert(self, alert_type: str, alert_data: Dict):
        """Trigger real-time alert for immediate attention"""
        try:
            alert = {
                'type': alert_type,
                'timestamp': datetime.now().isoformat(),
                'data': alert_data,
                'severity': self._get_alert_severity(alert_type)
            }
            
            if self.redis_client:
                # Publish alert to subscribers
                self.redis_client.publish('voice_alerts', json.dumps(alert))
                
                # Store alert for review
                alert_key = f"alert:{alert_type}:{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                self.redis_client.hset(alert_key, mapping=alert)
                self.redis_client.expire(alert_key, 86400)  # 24 hour retention
            
            logger.warning(f"Alert triggered: {alert_type} - {alert_data}")
            
        except Exception as e:
            logger.error(f"Failed to trigger alert: {e}")
    
    def _get_alert_severity(self, alert_type: str) -> str:
        """Get severity level for alert type"""
        severity_map = {
            'emergency_call': 'critical',
            'long_wait_time': 'high',
            'multiple_transfers': 'medium',
            'system_error': 'high',
            'quality_issue': 'medium'
        }
        return severity_map.get(alert_type, 'low')
    
    def generate_call_metrics(self, time_range: str = '24h') -> Dict[str, Any]:
        """Generate comprehensive call metrics for specified time range"""
        try:
            # Calculate time range
            end_time = datetime.now()
            if time_range == '1h':
                start_time = end_time - timedelta(hours=1)
            elif time_range == '24h':
                start_time = end_time - timedelta(hours=24)
            elif time_range == '7d':
                start_time = end_time - timedelta(days=7)
            elif time_range == '30d':
                start_time = end_time - timedelta(days=30)
            else:
                start_time = end_time - timedelta(hours=24)  # Default to 24h
            
            # Get calls from time range
            calls = self._get_calls_in_range(start_time, end_time)
            
            if not calls:
                return {'error': 'No calls found in specified time range'}
            
            # Calculate metrics
            metrics = {
                'time_range': time_range,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'total_calls': len(calls),
                'call_volume_trend': self._calculate_volume_trend(calls),
                'performance_metrics': self._calculate_performance_metrics(calls),
                'quality_metrics': self._calculate_quality_metrics(calls),
                'customer_experience': self._calculate_customer_experience(calls),
                'operational_efficiency': self._calculate_operational_efficiency(calls),
                'peak_patterns': self._analyze_peak_patterns(calls),
                'common_issues': self._analyze_common_issues(calls),
                'recommendations': self._generate_recommendations(calls)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to generate call metrics: {e}")
            return {'error': str(e)}
    
    def _get_calls_in_range(self, start_time: datetime, end_time: datetime) -> List[CallMetrics]:
        """Get calls within specified time range"""
        if self.redis_client:
            # TODO: Implement Redis time-range query
            # For now, scan all calls and filter
            calls = []
            for key in self.redis_client.scan_iter(match="call:*"):
                call_data = self.redis_client.hgetall(key)
                call_time = datetime.fromisoformat(call_data['timestamp'])
                if start_time <= call_time <= end_time:
                    calls.append(CallMetrics(**call_data))
            return calls
        else:
            # Filter memory storage
            return [call for call in self.calls_db 
                   if start_time <= call.timestamp <= end_time]
    
    def _calculate_volume_trend(self, calls: List[CallMetrics]) -> Dict:
        """Calculate call volume trends"""
        hourly_counts = defaultdict(int)
        
        for call in calls:
            hour = call.timestamp.hour
            hourly_counts[hour] += 1
        
        return {
            'hourly_distribution': dict(hourly_counts),
            'peak_hour': max(hourly_counts.items(), key=lambda x: x[1])[0] if hourly_counts else None,
            'average_per_hour': len(calls) / max(1, len(hourly_counts))
        }
    
    def _calculate_performance_metrics(self, calls: List[CallMetrics]) -> Dict:
        """Calculate performance-related metrics"""
        durations = [call.duration for call in calls if call.duration > 0]
        wait_times = [call.wait_time for call in calls if call.wait_time > 0]
        
        return {
            'avg_call_duration': statistics.mean(durations) if durations else 0,
            'median_call_duration': statistics.median(durations) if durations else 0,
            'avg_wait_time': statistics.mean(wait_times) if wait_times else 0,
            'max_wait_time': max(wait_times) if wait_times else 0,
            'calls_over_5min': len([d for d in durations if d > 300]),
            'abandoned_calls': len([c for c in calls if c.resolution_status == 'abandoned'])
        }
    
    def _calculate_quality_metrics(self, calls: List[CallMetrics]) -> Dict:
        """Calculate quality-related metrics"""
        fcr_count = len([c for c in calls if c.first_call_resolution])
        transferred_count = len([c for c in calls if c.transfers > 0])
        
        return {
            'first_call_resolution_rate': fcr_count / len(calls) if calls else 0,
            'transfer_rate': transferred_count / len(calls) if calls else 0,
            'avg_transfers_per_call': statistics.mean([c.transfers for c in calls]) if calls else 0,
            'avg_transcription_accuracy': statistics.mean([c.transcription_accuracy for c in calls]) if calls else 0,
            'voicemail_rate': len([c for c in calls if c.voicemail_left]) / len(calls) if calls else 0
        }
    
    def _calculate_customer_experience(self, calls: List[CallMetrics]) -> Dict:
        """Calculate customer experience metrics"""
        satisfaction_scores = [c.customer_satisfaction for c in calls if c.customer_satisfaction]
        
        return {
            'avg_satisfaction_score': statistics.mean(satisfaction_scores) if satisfaction_scores else None,
            'callback_rate': len([c for c in calls if c.call_back_required]) / len(calls) if calls else 0,
            'emergency_response_time': self._calculate_emergency_response_time(calls),
            'resolution_distribution': self._get_resolution_distribution(calls)
        }
    
    def _calculate_operational_efficiency(self, calls: List[CallMetrics]) -> Dict:
        """Calculate operational efficiency metrics"""
        return {
            'calls_per_technician': self._calculate_calls_per_technician(calls),
            'service_type_distribution': self._get_service_type_distribution(calls),
            'peak_load_handling': self._analyze_peak_load_handling(calls),
            'cost_per_call': self._estimate_cost_per_call(calls)
        }
    
    def _analyze_peak_patterns(self, calls: List[CallMetrics]) -> Dict:
        """Analyze peak call patterns"""
        # Group by day of week and hour
        patterns = defaultdict(lambda: defaultdict(int))
        
        for call in calls:
            day_of_week = call.timestamp.strftime('%A')
            hour = call.timestamp.hour
            patterns[day_of_week][hour] += 1
        
        return {
            'daily_patterns': dict(patterns),
            'busiest_day': self._find_busiest_day(patterns),
            'busiest_hour': self._find_busiest_hour(patterns)
        }
    
    def _analyze_common_issues(self, calls: List[CallMetrics]) -> Dict:
        """Analyze common customer issues"""
        service_types = Counter([call.service_type for call in calls])
        emergency_types = Counter([call.emergency_level for call in calls])
        
        return {
            'top_service_requests': dict(service_types.most_common(5)),
            'emergency_level_distribution': dict(emergency_types),
            'frequent_callers': self._identify_frequent_callers(calls)
        }
    
    def _generate_recommendations(self, calls: List[CallMetrics]) -> List[str]:
        """Generate actionable recommendations based on metrics"""
        recommendations = []
        
        # Analyze wait times
        avg_wait = statistics.mean([c.wait_time for c in calls if c.wait_time > 0])
        if avg_wait > 120:  # 2 minutes
            recommendations.append(f"Consider adding staff during peak hours - average wait time is {avg_wait:.0f} seconds")
        
        # Analyze transfer rates
        transfer_rate = len([c for c in calls if c.transfers > 0]) / len(calls)
        if transfer_rate > 0.3:  # 30%
            recommendations.append(f"High transfer rate ({transfer_rate:.1%}) - consider additional IVR training")
        
        # Analyze FCR
        fcr_rate = len([c for c in calls if c.first_call_resolution]) / len(calls)
        if fcr_rate < 0.7:  # 70%
            recommendations.append(f"Low first-call resolution ({fcr_rate:.1%}) - review knowledge base and training")
        
        # Analyze abandoned calls
        abandoned_rate = len([c for c in calls if c.resolution_status == 'abandoned']) / len(calls)
        if abandoned_rate > 0.1:  # 10%
            recommendations.append(f"High abandonment rate ({abandoned_rate:.1%}) - reduce wait times")
        
        if not recommendations:
            recommendations.append("Call center performance is within acceptable parameters")
        
        return recommendations
    
    def get_real_time_dashboard(self) -> Dict[str, Any]:
        """Get real-time dashboard metrics"""
        try:
            now = datetime.now()
            last_hour = now - timedelta(hours=1)
            last_15min = now - timedelta(minutes=15)
            
            recent_calls = self._get_calls_in_range(last_hour, now)
            
            return {
                'current_time': now.isoformat(),
                'calls_last_hour': len(recent_calls),
                'calls_last_15min': len(self._get_calls_in_range(last_15min, now)),
                'active_emergencies': len([c for c in recent_calls if c.emergency_level >= 4]),
                'current_avg_wait': self._get_current_average_wait(),
                'system_health': self._assess_system_health(recent_calls),
                'trending_issues': self._get_trending_issues(recent_calls),
                'staff_utilization': self._get_staff_utilization()
            }
            
        except Exception as e:
            logger.error(f"Failed to get real-time dashboard: {e}")
            return {'error': str(e)}
    
    def get_customer_history(self, caller_id: str) -> Dict[str, Any]:
        """Get complete customer interaction history"""
        try:
            if self.redis_client:
                customer_key = f"customer:{caller_id}"
                journey_data = self.redis_client.lrange(customer_key, 0, -1)
                history = [json.loads(data) for data in journey_data]
            else:
                history = self.customer_journey_map.get(caller_id, [])
            
            # Calculate customer metrics
            total_calls = len(history)
            resolved_calls = len([h for h in history if h['first_call_resolution']])
            
            return {
                'caller_id': caller_id,
                'total_calls': total_calls,
                'first_call': min([h['timestamp'] for h in history]) if history else None,
                'last_call': max([h['timestamp'] for h in history]) if history else None,
                'resolution_rate': resolved_calls / total_calls if total_calls else 0,
                'preferred_services': self._get_preferred_services(history),
                'call_history': history[-10:]  # Last 10 calls
            }
            
        except Exception as e:
            logger.error(f"Failed to get customer history: {e}")
            return {'error': str(e)}
    
    # Helper methods for complex calculations
    def _calculate_emergency_response_time(self, calls: List[CallMetrics]) -> float:
        """Calculate average response time for emergency calls"""
        emergency_calls = [c for c in calls if c.emergency_level >= 4]
        if not emergency_calls:
            return 0.0
        return statistics.mean([c.wait_time for c in emergency_calls])
    
    def _get_resolution_distribution(self, calls: List[CallMetrics]) -> Dict[str, int]:
        """Get distribution of resolution types"""
        return dict(Counter([c.resolution_status for c in calls]))
    
    def _calculate_calls_per_technician(self, calls: List[CallMetrics]) -> Dict[str, int]:
        """Calculate calls handled per technician"""
        return dict(Counter([c.technician_assigned for c in calls if c.technician_assigned]))
    
    def _get_service_type_distribution(self, calls: List[CallMetrics]) -> Dict[str, int]:
        """Get distribution of service types"""
        return dict(Counter([c.service_type for c in calls]))
    
    def _analyze_peak_load_handling(self, calls: List[CallMetrics]) -> Dict:
        """Analyze how well peak loads are handled"""
        # Find peak hour
        hourly_counts = defaultdict(int)
        for call in calls:
            hourly_counts[call.timestamp.hour] += 1
        
        if not hourly_counts:
            return {'peak_hour': None, 'peak_performance': None}
        
        peak_hour = max(hourly_counts.items(), key=lambda x: x[1])[0]
        peak_calls = [c for c in calls if c.timestamp.hour == peak_hour]
        
        return {
            'peak_hour': peak_hour,
            'peak_call_count': len(peak_calls),
            'peak_avg_wait': statistics.mean([c.wait_time for c in peak_calls]),
            'peak_abandonment_rate': len([c for c in peak_calls if c.resolution_status == 'abandoned']) / len(peak_calls)
        }
    
    def _estimate_cost_per_call(self, calls: List[CallMetrics]) -> float:
        """Estimate cost per call based on duration and resources"""
        if not calls:
            return 0.0
        
        # Simple cost model: $0.50 per minute + $2.00 base cost
        total_cost = 0.0
        for call in calls:
            base_cost = 2.00
            duration_cost = (call.duration / 60) * 0.50
            total_cost += base_cost + duration_cost
        
        return total_cost / len(calls)
    
    def _find_busiest_day(self, patterns: Dict) -> str:
        """Find the busiest day of the week"""
        day_totals = {day: sum(hours.values()) for day, hours in patterns.items()}
        return max(day_totals.items(), key=lambda x: x[1])[0] if day_totals else None
    
    def _find_busiest_hour(self, patterns: Dict) -> int:
        """Find the busiest hour across all days"""
        hour_totals = defaultdict(int)
        for day_data in patterns.values():
            for hour, count in day_data.items():
                hour_totals[hour] += count
        return max(hour_totals.items(), key=lambda x: x[1])[0] if hour_totals else None
    
    def _identify_frequent_callers(self, calls: List[CallMetrics]) -> List[Dict]:
        """Identify customers who call frequently"""
        caller_counts = Counter([c.caller_id for c in calls])
        frequent = []
        
        for caller_id, count in caller_counts.most_common(10):
            if count >= 3:  # 3+ calls in time period
                frequent.append({
                    'caller_id': caller_id,
                    'call_count': count,
                    'avg_duration': statistics.mean([c.duration for c in calls if c.caller_id == caller_id])
                })
        
        return frequent
    
    def _get_current_average_wait(self) -> float:
        """Get current average wait time"""
        if not self.redis_client:
            return 0.0
        
        # Get active calls in queue
        active_calls = self.redis_client.smembers('active_calls')
        if not active_calls:
            return 0.0
        
        wait_times = []
        for call_sid in active_calls:
            call_data = self.redis_client.hgetall(f"call:{call_sid}")
            if 'queue_enter_time' in call_data:
                enter_time = datetime.fromisoformat(call_data['queue_enter_time'])
                wait_time = (datetime.now() - enter_time).total_seconds()
                wait_times.append(wait_time)
        
        return statistics.mean(wait_times) if wait_times else 0.0
    
    def _assess_system_health(self, recent_calls: List[CallMetrics]) -> str:
        """Assess overall system health"""
        if not recent_calls:
            return 'unknown'
        
        # Calculate health indicators
        avg_wait = statistics.mean([c.wait_time for c in recent_calls])
        abandonment_rate = len([c for c in recent_calls if c.resolution_status == 'abandoned']) / len(recent_calls)
        emergency_count = len([c for c in recent_calls if c.emergency_level >= 4])
        
        # Determine health status
        if avg_wait > 300 or abandonment_rate > 0.2 or emergency_count > 5:
            return 'critical'
        elif avg_wait > 120 or abandonment_rate > 0.1 or emergency_count > 2:
            return 'warning'
        else:
            return 'healthy'
    
    def _get_trending_issues(self, recent_calls: List[CallMetrics]) -> List[str]:
        """Identify trending issues"""
        issues = []
        
        # Check for increasing emergency calls
        emergency_count = len([c for c in recent_calls if c.emergency_level >= 4])
        if emergency_count > 3:
            issues.append(f"High emergency call volume: {emergency_count} in last hour")
        
        # Check for high transfer rates
        transfer_rate = len([c for c in recent_calls if c.transfers > 0]) / len(recent_calls)
        if transfer_rate > 0.4:
            issues.append(f"High transfer rate: {transfer_rate:.1%}")
        
        return issues
    
    def _get_staff_utilization(self) -> Dict:
        """Get current staff utilization metrics"""
        # This would integrate with staffing system
        # For now, return placeholder data
        return {
            'available_agents': 5,
            'busy_agents': 3,
            'utilization_rate': 0.6,
            'queue_depth': 2
        }
    
    def _get_preferred_services(self, history: List[Dict]) -> List[str]:
        """Get customer's preferred service types"""
        service_counts = Counter([h.get('service_type', 'general') for h in history])
        return [service for service, count in service_counts.most_common(3)]

if __name__ == "__main__":
    # Test the analytics system
    analytics = VoiceCallAnalytics()
    
    # Sample call data
    test_call = {
        'call_sid': 'test_123',
        'caller_id': '+15551234567',
        'duration': 180,
        'call_type': 'inbound',
        'appointment_scheduled': True,
        'transcription': 'I need someone to fix my leaky faucet',
        'transfers': 0,
        'voicemail_left': False
    }
    
    # Log the test call
    analytics.log_call(test_call)
    
    # Generate metrics
    metrics = analytics.generate_call_metrics('24h')
    print(json.dumps(metrics, indent=2, default=str))
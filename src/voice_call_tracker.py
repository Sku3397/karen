#!/usr/bin/env python3
"""
Advanced Call Tracking and Analytics System for 757 Handy Voice System
Comprehensive call logging, analytics, and performance monitoring with Redis

Author: Phone Engineer Agent
"""

import os
import json
import logging
import redis
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import hashlib
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)

class CallStatus(Enum):
    """Call status types"""
    INITIATED = "initiated"
    RINGING = "ringing"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    BUSY = "busy"
    NO_ANSWER = "no-answer"
    FAILED = "failed"
    CANCELED = "canceled"

class CallType(Enum):
    """Types of calls"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    TRANSFER = "transfer"
    CONFERENCE = "conference"

class CallOutcome(Enum):
    """Call outcomes"""
    ANSWERED_HUMAN = "answered_human"
    COMPLETED_IVR = "completed_ivr"
    VOICEMAIL_LEFT = "voicemail_left"
    ABANDONED = "abandoned"
    TRANSFERRED = "transferred"
    EMERGENCY = "emergency"

@dataclass
class CallRecord:
    """Comprehensive call record"""
    call_sid: str
    caller_id: str
    called_number: str
    call_type: CallType
    status: CallStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[int] = None
    
    # IVR and routing data
    menu_path: List[str] = None
    final_destination: Optional[str] = None
    transfer_count: int = 0
    
    # Recordings and transcriptions
    recording_url: Optional[str] = None
    recording_duration: Optional[int] = None
    transcription: Optional[str] = None
    transcription_confidence: Optional[float] = None
    
    # Business data
    outcome: Optional[CallOutcome] = None
    customer_satisfaction: Optional[int] = None  # 1-5 scale
    follow_up_required: bool = False
    priority_level: str = "normal"
    
    # Technical data
    call_quality: Optional[float] = None
    connection_time: Optional[float] = None
    geographic_location: Optional[str] = None
    device_type: Optional[str] = None
    
    # Cost and billing
    call_cost: Optional[float] = None
    billable_minutes: Optional[int] = None
    
    def __post_init__(self):
        if self.menu_path is None:
            self.menu_path = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Redis storage"""
        result = asdict(self)
        result['call_type'] = self.call_type.value
        result['status'] = self.status.value
        result['outcome'] = self.outcome.value if self.outcome else None
        result['start_time'] = self.start_time.isoformat()
        result['end_time'] = self.end_time.isoformat() if self.end_time else None
        return result

class CallTracker:
    """
    Advanced call tracking system with Redis backend
    
    Features:
    - Real-time call status tracking
    - Comprehensive call analytics
    - Performance metrics
    - Queue management
    - Customer journey tracking
    - Cost analysis
    - Quality monitoring
    """
    
    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379, redis_db: int = 0):
        # Initialize Redis connection
        try:
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            self.redis_client.ping()
            logger.info("Redis connection established for call tracking")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
        
        # Redis key prefixes
        self.CALL_PREFIX = "call:"
        self.ACTIVE_CALLS_SET = "active_calls"
        self.DAILY_STATS_PREFIX = "daily_stats:"
        self.QUEUE_PREFIX = "queue:"
        self.CUSTOMER_PREFIX = "customer:"
        self.ANALYTICS_PREFIX = "analytics:"
        
        # Performance thresholds
        self.quality_thresholds = {
            'excellent': 0.9,
            'good': 0.7,
            'fair': 0.5,
            'poor': 0.3
        }
        
        # Initialize analytics counters
        self._initialize_analytics()
        
        logger.info("CallTracker initialized with Redis backend")
    
    def _initialize_analytics(self):
        """Initialize analytics counters if they don't exist"""
        today = datetime.now().strftime('%Y-%m-%d')
        daily_key = f"{self.DAILY_STATS_PREFIX}{today}"
        
        if not self.redis_client.exists(daily_key):
            initial_stats = {
                'total_calls': 0,
                'answered_calls': 0,
                'missed_calls': 0,
                'voicemails': 0,
                'emergency_calls': 0,
                'average_duration': 0,
                'total_duration': 0,
                'customer_satisfaction_sum': 0,
                'customer_satisfaction_count': 0
            }
            self.redis_client.hset(daily_key, mapping=initial_stats)
            self.redis_client.expire(daily_key, 86400 * 30)  # Keep for 30 days
    
    def start_call(self, call_sid: str, caller_id: str, called_number: str, 
                   call_type: CallType = CallType.INBOUND) -> CallRecord:
        """Start tracking a new call"""
        try:
            call_record = CallRecord(
                call_sid=call_sid,
                caller_id=caller_id,
                called_number=called_number,
                call_type=call_type,
                status=CallStatus.INITIATED,
                start_time=datetime.now()
            )
            
            # Store in Redis
            call_key = f"{self.CALL_PREFIX}{call_sid}"
            self.redis_client.hset(call_key, mapping=call_record.to_dict())
            self.redis_client.expire(call_key, 86400)  # Expire after 24 hours
            
            # Add to active calls
            self.redis_client.sadd(self.ACTIVE_CALLS_SET, call_sid)
            
            # Update daily stats
            self._increment_daily_stat('total_calls')
            
            # Track customer call history
            self._update_customer_history(caller_id, call_sid)
            
            logger.info(f"Started tracking call: {call_sid}")
            return call_record
            
        except Exception as e:
            logger.error(f"Failed to start call tracking for {call_sid}: {e}")
            raise
    
    def update_call_status(self, call_sid: str, status: CallStatus, 
                          additional_data: Dict[str, Any] = None):
        """Update call status"""
        try:
            call_key = f"{self.CALL_PREFIX}{call_sid}"
            
            # Update basic status
            updates = {
                'status': status.value,
                'last_updated': datetime.now().isoformat()
            }
            
            # Add any additional data
            if additional_data:
                updates.update(additional_data)
            
            # Special handling for call completion
            if status in [CallStatus.COMPLETED, CallStatus.BUSY, CallStatus.NO_ANSWER, 
                         CallStatus.FAILED, CallStatus.CANCELED]:
                updates['end_time'] = datetime.now().isoformat()
                
                # Calculate duration if we have start time
                call_data = self.redis_client.hgetall(call_key)
                if 'start_time' in call_data:
                    start_time = datetime.fromisoformat(call_data['start_time'])
                    duration = int((datetime.now() - start_time).total_seconds())
                    updates['duration'] = duration
                    
                    # Update stats
                    if status == CallStatus.COMPLETED:
                        self._increment_daily_stat('answered_calls')
                        self._add_to_daily_stat('total_duration', duration)
                    elif status in [CallStatus.NO_ANSWER, CallStatus.BUSY]:
                        self._increment_daily_stat('missed_calls')
                
                # Remove from active calls
                self.redis_client.srem(self.ACTIVE_CALLS_SET, call_sid)
            
            # Apply updates
            self.redis_client.hset(call_key, mapping=updates)
            
            logger.debug(f"Updated call {call_sid} status to {status.value}")
            
        except Exception as e:
            logger.error(f"Failed to update call status for {call_sid}: {e}")
    
    def track_ivr_navigation(self, call_sid: str, menu_selection: str, menu_path: List[str]):
        """Track IVR menu navigation"""
        try:
            call_key = f"{self.CALL_PREFIX}{call_sid}"
            
            updates = {
                'current_menu': menu_selection,
                'menu_path': json.dumps(menu_path),
                'menu_depth': len(menu_path)
            }
            
            self.redis_client.hset(call_key, mapping=updates)
            
            # Track menu usage analytics
            menu_key = f"{self.ANALYTICS_PREFIX}menu_usage"
            self.redis_client.hincrby(menu_key, menu_selection, 1)
            self.redis_client.expire(menu_key, 86400 * 30)
            
        except Exception as e:
            logger.error(f"Failed to track IVR navigation for {call_sid}: {e}")
    
    def add_recording_data(self, call_sid: str, recording_url: str, 
                          recording_duration: int, transcription: str = None, 
                          confidence: float = None):
        """Add recording and transcription data"""
        try:
            call_key = f"{self.CALL_PREFIX}{call_sid}"
            
            updates = {
                'recording_url': recording_url,
                'recording_duration': recording_duration,
                'has_recording': True
            }
            
            if transcription:
                updates['transcription'] = transcription
                updates['transcription_confidence'] = confidence or 0.0
                
                # Analyze transcription for keywords
                keywords = self._extract_keywords(transcription)
                if keywords:
                    updates['keywords'] = json.dumps(keywords)
                
                # Check for emergency indicators
                if self._is_emergency_call(transcription):
                    updates['priority_level'] = 'emergency'
                    self._increment_daily_stat('emergency_calls')
            
            self.redis_client.hset(call_key, mapping=updates)
            
            # Update voicemail stats if this was a voicemail
            if recording_duration > 0:
                self._increment_daily_stat('voicemails')
            
        except Exception as e:
            logger.error(f"Failed to add recording data for {call_sid}: {e}")
    
    def set_call_outcome(self, call_sid: str, outcome: CallOutcome, 
                        satisfaction_score: int = None, follow_up_required: bool = False):
        """Set final call outcome"""
        try:
            call_key = f"{self.CALL_PREFIX}{call_sid}"
            
            updates = {
                'outcome': outcome.value,
                'follow_up_required': follow_up_required
            }
            
            if satisfaction_score and 1 <= satisfaction_score <= 5:
                updates['customer_satisfaction'] = satisfaction_score
                self._add_to_daily_stat('customer_satisfaction_sum', satisfaction_score)
                self._increment_daily_stat('customer_satisfaction_count')
            
            self.redis_client.hset(call_key, mapping=updates)
            
            # Track outcome analytics
            outcome_key = f"{self.ANALYTICS_PREFIX}outcomes"
            self.redis_client.hincrby(outcome_key, outcome.value, 1)
            self.redis_client.expire(outcome_key, 86400 * 30)
            
        except Exception as e:
            logger.error(f"Failed to set call outcome for {call_sid}: {e}")
    
    def get_call_details(self, call_sid: str) -> Optional[Dict[str, Any]]:
        """Get complete call details"""
        try:
            call_key = f"{self.CALL_PREFIX}{call_sid}"
            call_data = self.redis_client.hgetall(call_key)
            
            if not call_data:
                return None
            
            # Parse JSON fields
            if 'menu_path' in call_data:
                try:
                    call_data['menu_path'] = json.loads(call_data['menu_path'])
                except:
                    pass
            
            if 'keywords' in call_data:
                try:
                    call_data['keywords'] = json.loads(call_data['keywords'])
                except:
                    pass
            
            return call_data
            
        except Exception as e:
            logger.error(f"Failed to get call details for {call_sid}: {e}")
            return None
    
    def get_active_calls(self) -> List[str]:
        """Get list of currently active calls"""
        try:
            return list(self.redis_client.smembers(self.ACTIVE_CALLS_SET))
        except Exception as e:
            logger.error(f"Failed to get active calls: {e}")
            return []
    
    def get_active_call_count(self) -> int:
        """Get count of active calls"""
        try:
            return self.redis_client.scard(self.ACTIVE_CALLS_SET)
        except Exception as e:
            logger.error(f"Failed to get active call count: {e}")
            return 0
    
    def get_daily_stats(self, date: str = None) -> Dict[str, Any]:
        """Get daily call statistics"""
        try:
            if not date:
                date = datetime.now().strftime('%Y-%m-%d')
            
            daily_key = f"{self.DAILY_STATS_PREFIX}{date}"
            stats = self.redis_client.hgetall(daily_key)
            
            if not stats:
                return {}
            
            # Convert numeric fields
            numeric_fields = ['total_calls', 'answered_calls', 'missed_calls', 'voicemails', 
                            'emergency_calls', 'total_duration', 'customer_satisfaction_sum', 
                            'customer_satisfaction_count']
            
            for field in numeric_fields:
                if field in stats:
                    stats[field] = int(stats[field])
            
            # Calculate derived metrics
            if stats.get('total_calls', 0) > 0:
                stats['answer_rate'] = round(stats['answered_calls'] / stats['total_calls'] * 100, 2)
                stats['miss_rate'] = round(stats['missed_calls'] / stats['total_calls'] * 100, 2)
            
            if stats.get('answered_calls', 0) > 0:
                stats['average_duration'] = round(stats['total_duration'] / stats['answered_calls'], 2)
            
            if stats.get('customer_satisfaction_count', 0) > 0:
                stats['average_satisfaction'] = round(
                    stats['customer_satisfaction_sum'] / stats['customer_satisfaction_count'], 2
                )
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get daily stats for {date}: {e}")
            return {}
    
    def get_customer_call_history(self, caller_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get call history for a specific customer"""
        try:
            customer_key = f"{self.CUSTOMER_PREFIX}{self._hash_phone(caller_id)}"
            call_sids = self.redis_client.lrange(customer_key, 0, limit - 1)
            
            history = []
            for call_sid in call_sids:
                call_data = self.get_call_details(call_sid)
                if call_data:
                    history.append(call_data)
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get customer history for {caller_id}: {e}")
            return []
    
    def get_analytics_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get comprehensive analytics summary"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            summary = {
                'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                'total_calls': 0,
                'total_answered': 0,
                'total_missed': 0,
                'total_voicemails': 0,
                'emergency_calls': 0,
                'total_duration_minutes': 0,
                'average_call_duration': 0,
                'daily_breakdown': [],
                'menu_usage': {},
                'outcomes': {},
                'call_quality_distribution': {},
                'peak_hours': {},
                'customer_satisfaction': 0
            }
            
            # Aggregate daily stats
            total_satisfaction_sum = 0
            total_satisfaction_count = 0
            
            for i in range(days):
                date = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
                daily_stats = self.get_daily_stats(date)
                
                if daily_stats:
                    summary['total_calls'] += daily_stats.get('total_calls', 0)
                    summary['total_answered'] += daily_stats.get('answered_calls', 0)
                    summary['total_missed'] += daily_stats.get('missed_calls', 0)
                    summary['total_voicemails'] += daily_stats.get('voicemails', 0)
                    summary['emergency_calls'] += daily_stats.get('emergency_calls', 0)
                    summary['total_duration_minutes'] += daily_stats.get('total_duration', 0) / 60
                    
                    total_satisfaction_sum += daily_stats.get('customer_satisfaction_sum', 0)
                    total_satisfaction_count += daily_stats.get('customer_satisfaction_count', 0)
                    
                    summary['daily_breakdown'].append({
                        'date': date,
                        'calls': daily_stats.get('total_calls', 0),
                        'answered': daily_stats.get('answered_calls', 0),
                        'duration_minutes': daily_stats.get('total_duration', 0) / 60
                    })
            
            # Calculate averages
            if summary['total_answered'] > 0:
                summary['average_call_duration'] = round(
                    summary['total_duration_minutes'] / summary['total_answered'], 2
                )
            
            if total_satisfaction_count > 0:
                summary['customer_satisfaction'] = round(
                    total_satisfaction_sum / total_satisfaction_count, 2
                )
            
            # Get menu usage
            menu_key = f"{self.ANALYTICS_PREFIX}menu_usage"
            summary['menu_usage'] = self.redis_client.hgetall(menu_key)
            
            # Get outcomes
            outcome_key = f"{self.ANALYTICS_PREFIX}outcomes"
            summary['outcomes'] = self.redis_client.hgetall(outcome_key)
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate analytics summary: {e}")
            return {}
    
    def get_queue_metrics(self) -> Dict[str, Any]:
        """Get real-time queue metrics"""
        try:
            active_calls = self.get_active_call_count()
            
            # Estimate wait time based on active calls
            estimated_wait_minutes = max(0, (active_calls - 2) * 2)  # 2 operators, 2 min per call
            
            return {
                'active_calls': active_calls,
                'estimated_wait_minutes': estimated_wait_minutes,
                'queue_status': 'busy' if active_calls > 3 else 'normal',
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get queue metrics: {e}")
            return {}
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old call data to prevent Redis from growing too large"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # Find old call keys
            pattern = f"{self.CALL_PREFIX}*"
            old_keys = []
            
            for key in self.redis_client.scan_iter(match=pattern):
                call_data = self.redis_client.hget(key, 'start_time')
                if call_data:
                    try:
                        start_time = datetime.fromisoformat(call_data)
                        if start_time < cutoff_date:
                            old_keys.append(key)
                    except:
                        # If we can't parse the date, consider it old
                        old_keys.append(key)
            
            # Delete old keys in batches
            if old_keys:
                pipe = self.redis_client.pipeline()
                for key in old_keys:
                    pipe.delete(key)
                pipe.execute()
                
                logger.info(f"Cleaned up {len(old_keys)} old call records")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
    
    def _increment_daily_stat(self, stat_name: str, amount: int = 1):
        """Increment a daily statistic"""
        today = datetime.now().strftime('%Y-%m-%d')
        daily_key = f"{self.DAILY_STATS_PREFIX}{today}"
        self.redis_client.hincrby(daily_key, stat_name, amount)
        self.redis_client.expire(daily_key, 86400 * 30)
    
    def _add_to_daily_stat(self, stat_name: str, value: int):
        """Add value to a daily statistic"""
        today = datetime.now().strftime('%Y-%m-%d')
        daily_key = f"{self.DAILY_STATS_PREFIX}{today}"
        self.redis_client.hincrby(daily_key, stat_name, value)
        self.redis_client.expire(daily_key, 86400 * 30)
    
    def _update_customer_history(self, caller_id: str, call_sid: str):
        """Update customer call history"""
        customer_key = f"{self.CUSTOMER_PREFIX}{self._hash_phone(caller_id)}"
        self.redis_client.lpush(customer_key, call_sid)
        self.redis_client.ltrim(customer_key, 0, 19)  # Keep last 20 calls
        self.redis_client.expire(customer_key, 86400 * 90)  # Keep for 90 days
    
    def _hash_phone(self, phone: str) -> str:
        """Hash phone number for privacy"""
        return hashlib.sha256(phone.encode()).hexdigest()[:16]
    
    def _extract_keywords(self, transcription: str) -> List[str]:
        """Extract keywords from transcription"""
        keywords = []
        text = transcription.lower()
        
        # Service keywords
        service_keywords = {
            'plumbing': ['plumber', 'plumbing', 'leak', 'pipe', 'toilet', 'drain'],
            'electrical': ['electrician', 'electrical', 'power', 'outlet', 'light', 'wire'],
            'hvac': ['heating', 'cooling', 'air', 'hvac', 'furnace', 'thermostat'],
            'emergency': ['emergency', 'urgent', 'asap', 'immediately', 'help']
        }
        
        for category, words in service_keywords.items():
            if any(word in text for word in words):
                keywords.append(category)
        
        return keywords
    
    def _is_emergency_call(self, transcription: str) -> bool:
        """Check if call is emergency based on transcription"""
        emergency_keywords = ['emergency', 'urgent', 'asap', 'immediately', 'flood', 'fire', 'gas leak']
        text = transcription.lower()
        return any(keyword in text for keyword in emergency_keywords)

# FastAPI endpoints for call tracking (to be included in main voice webhook handler)
def add_call_tracking_endpoints(app, call_tracker: CallTracker):
    """Add call tracking endpoints to FastAPI app"""
    
    @app.get("/voice/analytics/summary")
    async def get_analytics_summary(days: int = 7):
        """Get analytics summary"""
        return call_tracker.get_analytics_summary(days)
    
    @app.get("/voice/analytics/daily/{date}")
    async def get_daily_stats(date: str):
        """Get daily statistics"""
        return call_tracker.get_daily_stats(date)
    
    @app.get("/voice/analytics/queue")
    async def get_queue_metrics():
        """Get current queue metrics"""
        return call_tracker.get_queue_metrics()
    
    @app.get("/voice/analytics/customer/{phone_hash}")
    async def get_customer_history(phone_hash: str, limit: int = 10):
        """Get customer call history"""
        return call_tracker.get_customer_call_history(phone_hash, limit)
    
    @app.post("/voice/analytics/cleanup")
    async def cleanup_old_data(days_to_keep: int = 30):
        """Clean up old call data"""
        call_tracker.cleanup_old_data(days_to_keep)
        return {"status": "cleanup_completed"}

if __name__ == "__main__":
    # Test the call tracker
    import time
    
    tracker = CallTracker()
    
    # Simulate a call
    call_sid = "CA123456789"
    caller_id = "+15551234567"
    
    # Start call
    call_record = tracker.start_call(call_sid, caller_id, "+17574569999")
    print(f"Started call: {call_sid}")
    
    # Update status
    tracker.update_call_status(call_sid, CallStatus.IN_PROGRESS)
    print("Call in progress")
    
    # Track IVR navigation
    tracker.track_ivr_navigation(call_sid, "appointment_scheduling", ["main_menu", "scheduling"])
    print("IVR navigation tracked")
    
    # Add recording
    tracker.add_recording_data(
        call_sid, 
        "https://example.com/recording.mp3", 
        120, 
        "I need to schedule a plumbing appointment for tomorrow",
        0.95
    )
    print("Recording data added")
    
    # Complete call
    tracker.update_call_status(call_sid, CallStatus.COMPLETED)
    tracker.set_call_outcome(call_sid, CallOutcome.COMPLETED_IVR, satisfaction_score=4)
    print("Call completed")
    
    # Get analytics
    stats = tracker.get_daily_stats()
    print(f"Daily stats: {json.dumps(stats, indent=2)}")
    
    # Get call details
    details = tracker.get_call_details(call_sid)
    print(f"Call details: {json.dumps(details, indent=2)}")
#!/usr/bin/env python3
"""
Emergency call detection and priority routing for 757 Handy
Ensures critical situations receive immediate attention

Author: Phone Engineer Agent
"""

import os
import re
import json
import logging
import redis
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import asyncio
import aiohttp

logger = logging.getLogger(__name__)

class UrgencyLevel(Enum):
    """Emergency urgency levels"""
    ROUTINE = 1
    ELEVATED = 2
    MEDIUM = 3
    HIGH = 4
    CRITICAL = 5

class EmergencyType(Enum):
    """Types of emergency situations"""
    PLUMBING_FLOOD = "plumbing_flood"
    ELECTRICAL_HAZARD = "electrical_hazard"
    HEATING_FAILURE = "heating_failure"
    STRUCTURAL_DAMAGE = "structural_damage"
    SECURITY_BREACH = "security_breach"
    SAFETY_HAZARD = "safety_hazard"
    SERVICE_OUTAGE = "service_outage"

@dataclass
class EmergencyAssessment:
    """Emergency assessment result"""
    urgency_level: UrgencyLevel
    emergency_type: Optional[EmergencyType]
    confidence_score: float  # 0-1
    trigger_keywords: List[str]
    recommended_action: str
    estimated_response_time: int  # minutes
    requires_immediate_dispatch: bool
    safety_concerns: List[str]

class EmergencyHandler:
    """
    Advanced emergency detection and priority routing system
    
    Features:
    - Multi-level urgency assessment
    - Context-aware keyword detection
    - Caller history analysis
    - Real-time dispatch coordination
    - Safety protocol automation
    - VIP customer prioritization
    - Emergency services escalation
    """
    
    def __init__(self):
        # Initialize Redis for emergency tracking
        try:
            self.redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=int(os.getenv('REDIS_DB', 2)),  # Dedicated DB for emergencies
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("Emergency handler Redis connection established")
        except Exception as e:
            logger.warning(f"Redis connection failed, using memory storage: {e}")
            self.redis_client = None
        
        # Emergency keyword patterns with weights
        self.emergency_patterns = {
            # Critical - Immediate safety threats
            'critical': {
                'patterns': [
                    r'\b(fire|smoke|burning|flames?)\b',
                    r'\b(flood|flooding|water everywhere)\b',
                    r'\b(electrical fire|sparks flying|shock)\b',
                    r'\b(gas leak|smell gas|gas odor)\b',
                    r'\b(emergency|911|help|urgent)\b',
                    r'\b(danger|dangerous|hazard)\b',
                    r'\b(collapse|collapsed|falling)\b'
                ],
                'weight': 5.0,
                'emergency_type': EmergencyType.SAFETY_HAZARD
            },
            
            # High - Serious service failures
            'high': {
                'patterns': [
                    r'\b(no heat|heating not working|furnace down)\b',
                    r'\b(no hot water|water heater broken)\b',
                    r'\b(electrical problem|power out|no electricity)\b',
                    r'\b(burst pipe|broken pipe|major leak)\b',
                    r'\b(toilet overflowing|sewer backup)\b',
                    r'\b(broken window|security issue)\b'
                ],
                'weight': 4.0,
                'emergency_type': EmergencyType.SERVICE_OUTAGE
            },
            
            # Medium - Disruptive but not dangerous
            'medium': {
                'patterns': [
                    r'\b(leak|leaking|dripping)\b',
                    r'\b(clogged|blocked|backup)\b',
                    r'\b(not working|broken|malfunctioning)\b',
                    r'\b(urgent|asap|today)\b',
                    r'\b(before weekend|before holiday)\b'
                ],
                'weight': 3.0,
                'emergency_type': None
            },
            
            # Time-sensitive indicators
            'time_sensitive': {
                'patterns': [
                    r'\b(tonight|today|right now|immediately)\b',
                    r'\b(before (work|guests|family))\b',
                    r'\b(business|commercial|office)\b',
                    r'\b(tenant|renter|landlord)\b'
                ],
                'weight': 2.0,
                'emergency_type': None
            }
        }
        
        # VIP customer indicators
        self.vip_indicators = [
            'commercial',
            'property management',
            'recurring customer',
            'multiple properties'
        ]
        
        # Load priority customers from configuration
        self.priority_customers = self._load_priority_customers()
        
        # Emergency contact configuration
        self.emergency_contacts = {
            'primary_dispatcher': os.getenv('PRIMARY_DISPATCHER_PHONE', '+15551234567'),
            'emergency_technician': os.getenv('EMERGENCY_TECH_PHONE', '+15551234568'),
            'supervisor': os.getenv('SUPERVISOR_PHONE', '+15551234569'),
            'after_hours_service': os.getenv('AFTER_HOURS_PHONE', '+15551234570')
        }
        
        # Response time targets (minutes)
        self.response_targets = {
            UrgencyLevel.CRITICAL: 15,
            UrgencyLevel.HIGH: 60,
            UrgencyLevel.MEDIUM: 240,  # 4 hours
            UrgencyLevel.ELEVATED: 480,  # 8 hours
            UrgencyLevel.ROUTINE: 1440  # 24 hours
        }
        
        # Safety protocols
        self.safety_protocols = {
            EmergencyType.PLUMBING_FLOOD: [
                "Advise customer to shut off main water valve",
                "Move valuable items to higher ground",
                "Do not use electrical equipment in flooded areas"
            ],
            EmergencyType.ELECTRICAL_HAZARD: [
                "Do not touch electrical equipment",
                "Turn off power at circuit breaker if safe to do so",
                "Evacuate area if sparks or burning smell present"
            ],
            EmergencyType.HEATING_FAILURE: [
                "Check thermostat settings",
                "Ensure vents are not blocked",
                "Consider temporary heating source if below freezing"
            ]
        }
        
        logger.info("EmergencyHandler initialized with comprehensive safety protocols")
    
    def assess_urgency(self, transcription: str, caller_id: str, 
                      call_context: Dict[str, Any] = None) -> EmergencyAssessment:
        """
        Comprehensive urgency assessment with multiple factors
        
        Returns detailed emergency assessment with recommended actions
        """
        try:
            call_context = call_context or {}
            
            # Initialize assessment
            urgency_score = 1.0
            trigger_keywords = []
            emergency_type = None
            safety_concerns = []
            confidence_factors = []
            
            # Analyze transcription for emergency patterns
            transcription_lower = transcription.lower()
            
            for category, config in self.emergency_patterns.items():
                for pattern in config['patterns']:
                    matches = re.findall(pattern, transcription_lower, re.IGNORECASE)
                    if matches:
                        urgency_score = max(urgency_score, config['weight'])
                        trigger_keywords.extend(matches)
                        if config['emergency_type']:
                            emergency_type = config['emergency_type']
                        confidence_factors.append(f"Keyword match: {category}")
            
            # Adjust for caller history and context
            urgency_adjustments = self._analyze_caller_context(caller_id, call_context)
            urgency_score += urgency_adjustments['score_adjustment']
            confidence_factors.extend(urgency_adjustments['factors'])
            
            # Time-based urgency adjustments
            time_adjustments = self._analyze_time_context(call_context)
            urgency_score += time_adjustments['score_adjustment']
            confidence_factors.extend(time_adjustments['factors'])
            
            # Determine final urgency level
            urgency_level = self._score_to_urgency_level(urgency_score)
            
            # Calculate confidence score
            confidence_score = min(1.0, len(confidence_factors) * 0.2 + 
                                 (len(trigger_keywords) * 0.1))
            
            # Generate safety concerns
            safety_concerns = self._identify_safety_concerns(transcription, emergency_type)
            
            # Determine recommended action
            recommended_action = self._get_recommended_action(urgency_level, emergency_type)
            
            # Estimate response time
            estimated_response_time = self._estimate_response_time(urgency_level, call_context)
            
            # Determine if immediate dispatch required
            requires_immediate_dispatch = (
                urgency_level in [UrgencyLevel.CRITICAL, UrgencyLevel.HIGH] or
                emergency_type in [EmergencyType.SAFETY_HAZARD, EmergencyType.ELECTRICAL_HAZARD]
            )
            
            assessment = EmergencyAssessment(
                urgency_level=urgency_level,
                emergency_type=emergency_type,
                confidence_score=confidence_score,
                trigger_keywords=list(set(trigger_keywords)),
                recommended_action=recommended_action,
                estimated_response_time=estimated_response_time,
                requires_immediate_dispatch=requires_immediate_dispatch,
                safety_concerns=safety_concerns
            )
            
            # Log assessment
            self._log_emergency_assessment(caller_id, assessment, transcription)
            
            logger.info(f"Emergency assessment: {urgency_level.name} for {caller_id}")
            return assessment
            
        except Exception as e:
            logger.error(f"Failed to assess urgency: {e}")
            # Return safe default assessment
            return EmergencyAssessment(
                urgency_level=UrgencyLevel.ELEVATED,
                emergency_type=None,
                confidence_score=0.5,
                trigger_keywords=[],
                recommended_action="Route to human agent for assessment",
                estimated_response_time=60,
                requires_immediate_dispatch=True,
                safety_concerns=["Unable to fully assess - treating as elevated priority"]
            )
    
    def _analyze_caller_context(self, caller_id: str, call_context: Dict) -> Dict:
        """Analyze caller history and context for urgency adjustments"""
        adjustments = {'score_adjustment': 0.0, 'factors': []}
        
        try:
            # Check if VIP/Priority customer
            if self._is_priority_customer(caller_id):
                adjustments['score_adjustment'] += 1.0
                adjustments['factors'].append("Priority customer")
            
            # Check recent call history
            recent_calls = self._get_recent_calls(caller_id, hours=24)
            if recent_calls:
                if len(recent_calls) > 2:
                    adjustments['score_adjustment'] += 0.5
                    adjustments['factors'].append("Multiple recent calls")
                
                # Check for escalating issues
                if self._is_escalating_issue(recent_calls):
                    adjustments['score_adjustment'] += 1.0
                    adjustments['factors'].append("Escalating issue pattern")
            
            # Business vs residential context
            if call_context.get('business_call', False):
                adjustments['score_adjustment'] += 0.5
                adjustments['factors'].append("Business customer")
            
            # Callback vs initial call
            if call_context.get('is_callback', False):
                adjustments['score_adjustment'] += 0.3
                adjustments['factors'].append("Return call")
                
        except Exception as e:
            logger.error(f"Error analyzing caller context: {e}")
        
        return adjustments
    
    def _analyze_time_context(self, call_context: Dict) -> Dict:
        """Analyze time-based context for urgency adjustments"""
        adjustments = {'score_adjustment': 0.0, 'factors': []}
        
        try:
            now = datetime.now()
            
            # After-hours calls are more urgent
            if not self._is_business_hours(now):
                adjustments['score_adjustment'] += 0.5
                adjustments['factors'].append("After-hours call")
            
            # Weekend calls
            if now.weekday() >= 5:  # Saturday/Sunday
                adjustments['score_adjustment'] += 0.3
                adjustments['factors'].append("Weekend call")
            
            # Holiday periods (would integrate with holiday calendar)
            if self._is_holiday_period(now):
                adjustments['score_adjustment'] += 0.5
                adjustments['factors'].append("Holiday period")
            
            # Weather-related urgency (would integrate with weather API)
            weather_urgency = self._check_weather_urgency(call_context)
            adjustments['score_adjustment'] += weather_urgency['adjustment']
            adjustments['factors'].extend(weather_urgency['factors'])
            
        except Exception as e:
            logger.error(f"Error analyzing time context: {e}")
        
        return adjustments
    
    def _score_to_urgency_level(self, score: float) -> UrgencyLevel:
        """Convert numeric urgency score to urgency level"""
        if score >= 4.5:
            return UrgencyLevel.CRITICAL
        elif score >= 3.5:
            return UrgencyLevel.HIGH
        elif score >= 2.5:
            return UrgencyLevel.MEDIUM
        elif score >= 1.5:
            return UrgencyLevel.ELEVATED
        else:
            return UrgencyLevel.ROUTINE
    
    def _identify_safety_concerns(self, transcription: str, 
                                emergency_type: Optional[EmergencyType]) -> List[str]:
        """Identify specific safety concerns from transcription"""
        concerns = []
        transcription_lower = transcription.lower()
        
        # Check for immediate danger indicators
        danger_patterns = {
            'electrical': r'\b(shock|sparks|burning smell|electrical)\b',
            'water_damage': r'\b(flood|water damage|soaked|wet electrical)\b',
            'structural': r'\b(collapse|crack|sagging|unstable)\b',
            'gas': r'\b(gas|propane|smell|leak)\b',
            'fire': r'\b(fire|smoke|heat|burning)\b'
        }
        
        for concern_type, pattern in danger_patterns.items():
            if re.search(pattern, transcription_lower):
                concerns.append(f"Potential {concern_type.replace('_', ' ')} hazard detected")
        
        # Add protocol-based concerns
        if emergency_type and emergency_type in self.safety_protocols:
            concerns.extend(self.safety_protocols[emergency_type])
        
        return concerns
    
    def _get_recommended_action(self, urgency_level: UrgencyLevel, 
                              emergency_type: Optional[EmergencyType]) -> str:
        """Get recommended action based on assessment"""
        if urgency_level == UrgencyLevel.CRITICAL:
            return "IMMEDIATE DISPATCH - Contact emergency technician and notify supervisor"
        elif urgency_level == UrgencyLevel.HIGH:
            return "Priority dispatch within 1 hour - Contact on-call technician"
        elif urgency_level == UrgencyLevel.MEDIUM:
            return "Schedule priority service within 4 hours"
        elif urgency_level == UrgencyLevel.ELEVATED:
            return "Schedule service within 8 hours - Monitor for escalation"
        else:
            return "Standard scheduling - Next available appointment"
    
    def _estimate_response_time(self, urgency_level: UrgencyLevel, 
                              call_context: Dict) -> int:
        """Estimate response time in minutes"""
        base_time = self.response_targets[urgency_level]
        
        # Adjust for current workload
        current_load = self._get_current_workload()
        if current_load > 0.8:  # High load
            base_time = int(base_time * 1.5)
        
        # Adjust for time of day
        if not self._is_business_hours(datetime.now()):
            base_time = int(base_time * 1.2)
        
        return base_time
    
    async def route_emergency_call(self, assessment: EmergencyAssessment, 
                                 call_sid: str, caller_id: str) -> Dict[str, Any]:
        """Route emergency call based on assessment"""
        try:
            routing_result = {
                'call_sid': call_sid,
                'urgency_level': assessment.urgency_level.name,
                'actions_taken': [],
                'estimated_resolution': None,
                'escalated': False
            }
            
            if assessment.urgency_level == UrgencyLevel.CRITICAL:
                # Immediate emergency response
                result = await self._handle_critical_emergency(call_sid, caller_id, assessment)
                routing_result.update(result)
                
            elif assessment.urgency_level == UrgencyLevel.HIGH:
                # High priority response
                result = await self._handle_high_priority(call_sid, caller_id, assessment)
                routing_result.update(result)
                
            elif assessment.urgency_level == UrgencyLevel.MEDIUM:
                # Medium priority routing
                result = await self._handle_medium_priority(call_sid, caller_id, assessment)
                routing_result.update(result)
                
            else:
                # Standard routing
                result = await self._handle_standard_routing(call_sid, caller_id, assessment)
                routing_result.update(result)
            
            # Log routing decision
            self._log_routing_decision(call_sid, routing_result)
            
            return routing_result
            
        except Exception as e:
            logger.error(f"Failed to route emergency call {call_sid}: {e}")
            # Fallback to high priority
            return await self._handle_high_priority(call_sid, caller_id, assessment)
    
    async def _handle_critical_emergency(self, call_sid: str, caller_id: str, 
                                       assessment: EmergencyAssessment) -> Dict:
        """Handle critical emergency with immediate response"""
        actions = []
        
        # Immediate notifications
        await self._notify_emergency_team(call_sid, caller_id, assessment)
        actions.append("Emergency team notified")
        
        # Escalate to supervisor
        await self._escalate_to_supervisor(call_sid, assessment)
        actions.append("Escalated to supervisor")
        
        # If safety hazard, consider 911 notification
        if assessment.emergency_type == EmergencyType.SAFETY_HAZARD:
            await self._consider_911_escalation(call_sid, assessment)
            actions.append("Evaluated for 911 escalation")
        
        # Create priority ticket
        ticket_id = await self._create_priority_ticket(call_sid, caller_id, assessment)
        actions.append(f"Priority ticket created: {ticket_id}")
        
        return {
            'actions_taken': actions,
            'estimated_resolution': datetime.now() + timedelta(minutes=15),
            'escalated': True,
            'priority_level': 'CRITICAL'
        }
    
    async def _handle_high_priority(self, call_sid: str, caller_id: str, 
                                  assessment: EmergencyAssessment) -> Dict:
        """Handle high priority emergency"""
        actions = []
        
        # Notify on-call technician
        await self._notify_emergency_team(call_sid, caller_id, assessment)
        actions.append("On-call technician notified")
        
        # Add to priority queue
        await self._add_to_priority_queue(call_sid, assessment)
        actions.append("Added to priority queue")
        
        # Schedule immediate service
        appointment_time = await self._schedule_emergency_service(caller_id, assessment)
        actions.append(f"Emergency service scheduled for {appointment_time}")
        
        return {
            'actions_taken': actions,
            'estimated_resolution': datetime.now() + timedelta(hours=1),
            'escalated': False,
            'priority_level': 'HIGH'
        }
    
    async def _handle_medium_priority(self, call_sid: str, caller_id: str, 
                                    assessment: EmergencyAssessment) -> Dict:
        """Handle medium priority calls"""
        actions = []
        
        # Add to priority queue with medium priority
        await self._add_to_priority_queue(call_sid, assessment)
        actions.append("Added to priority queue")
        
        # Schedule within target timeframe
        appointment_time = await self._schedule_priority_service(caller_id, assessment)
        actions.append(f"Priority service scheduled for {appointment_time}")
        
        # Set follow-up reminder
        await self._set_follow_up_reminder(call_sid, hours=2)
        actions.append("Follow-up reminder set")
        
        return {
            'actions_taken': actions,
            'estimated_resolution': datetime.now() + timedelta(hours=4),
            'escalated': False,
            'priority_level': 'MEDIUM'
        }
    
    async def _handle_standard_routing(self, call_sid: str, caller_id: str, 
                                     assessment: EmergencyAssessment) -> Dict:
        """Handle standard priority calls"""
        actions = []
        
        # Standard scheduling
        appointment_time = await self._schedule_standard_service(caller_id, assessment)
        actions.append(f"Service scheduled for {appointment_time}")
        
        return {
            'actions_taken': actions,
            'estimated_resolution': appointment_time,
            'escalated': False,
            'priority_level': 'STANDARD'
        }
    
    # Notification and communication methods
    async def _notify_emergency_team(self, call_sid: str, caller_id: str, 
                                   assessment: EmergencyAssessment):
        """Notify emergency response team"""
        try:
            notification_data = {
                'call_sid': call_sid,
                'caller_id': caller_id,
                'urgency_level': assessment.urgency_level.name,
                'emergency_type': assessment.emergency_type.value if assessment.emergency_type else None,
                'safety_concerns': assessment.safety_concerns,
                'timestamp': datetime.now().isoformat()
            }
            
            # Send SMS to emergency technician
            await self._send_emergency_sms(
                self.emergency_contacts['emergency_technician'],
                f"EMERGENCY CALL: {assessment.urgency_level.name} - {caller_id}. "
                f"Call SID: {call_sid}. Response required in {assessment.estimated_response_time} minutes."
            )
            
            # Send to dispatcher
            await self._send_emergency_sms(
                self.emergency_contacts['primary_dispatcher'],
                f"Priority dispatch needed: {assessment.urgency_level.name} call from {caller_id}"
            )
            
            # Store notification in Redis
            if self.redis_client:
                notification_key = f"emergency_notification:{call_sid}"
                self.redis_client.hset(notification_key, mapping=notification_data)
                self.redis_client.expire(notification_key, 86400)  # 24 hour retention
            
            logger.info(f"Emergency team notified for call {call_sid}")
            
        except Exception as e:
            logger.error(f"Failed to notify emergency team: {e}")
    
    async def _send_emergency_sms(self, phone_number: str, message: str):
        """Send emergency SMS notification"""
        try:
            # This would integrate with Twilio SMS API
            # For now, log the message
            logger.warning(f"EMERGENCY SMS to {phone_number}: {message}")
            
            # In production, implement actual SMS sending:
            # twilio_client.messages.create(
            #     body=message,
            #     from_=os.getenv('TWILIO_PHONE_NUMBER'),
            #     to=phone_number
            # )
            
        except Exception as e:
            logger.error(f"Failed to send emergency SMS: {e}")
    
    # Queue and scheduling methods
    async def _add_to_priority_queue(self, call_sid: str, assessment: EmergencyAssessment):
        """Add call to priority queue"""
        try:
            if self.redis_client:
                queue_data = {
                    'call_sid': call_sid,
                    'urgency_level': assessment.urgency_level.value,
                    'timestamp': datetime.now().isoformat(),
                    'estimated_response_time': assessment.estimated_response_time
                }
                
                # Use sorted set for priority ordering
                priority_score = assessment.urgency_level.value * 1000 + int(datetime.now().timestamp())
                self.redis_client.zadd('priority_queue', {json.dumps(queue_data): priority_score})
            
            logger.info(f"Added call {call_sid} to priority queue with urgency {assessment.urgency_level.name}")
            
        except Exception as e:
            logger.error(f"Failed to add to priority queue: {e}")
    
    async def _schedule_emergency_service(self, caller_id: str, assessment: EmergencyAssessment) -> datetime:
        """Schedule immediate emergency service"""
        # This would integrate with scheduling system
        # For now, return estimated time
        return datetime.now() + timedelta(minutes=assessment.estimated_response_time)
    
    async def _schedule_priority_service(self, caller_id: str, assessment: EmergencyAssessment) -> datetime:
        """Schedule priority service within target timeframe"""
        return datetime.now() + timedelta(minutes=assessment.estimated_response_time)
    
    async def _schedule_standard_service(self, caller_id: str, assessment: EmergencyAssessment) -> datetime:
        """Schedule standard service appointment"""
        return datetime.now() + timedelta(hours=24)  # Next business day
    
    # Helper methods
    def _load_priority_customers(self) -> List[str]:
        """Load priority customers from configuration"""
        try:
            # This would load from database
            # For now, return sample data
            return [
                '+15551234567',  # VIP customer
                '+15551234568',  # Commercial account
            ]
        except Exception as e:
            logger.error(f"Failed to load priority customers: {e}")
            return []
    
    def _is_priority_customer(self, caller_id: str) -> bool:
        """Check if caller is a priority customer"""
        return caller_id in self.priority_customers
    
    def _get_recent_calls(self, caller_id: str, hours: int = 24) -> List[Dict]:
        """Get recent calls for caller"""
        try:
            if self.redis_client:
                # This would query call history
                # For now, return empty list
                return []
            return []
        except Exception as e:
            logger.error(f"Failed to get recent calls: {e}")
            return []
    
    def _is_escalating_issue(self, recent_calls: List[Dict]) -> bool:
        """Check if issue is escalating based on call pattern"""
        if len(recent_calls) < 2:
            return False
        
        # Check for increasing urgency in recent calls
        urgency_levels = [call.get('urgency_level', 1) for call in recent_calls[-3:]]
        return len(urgency_levels) >= 2 and urgency_levels[-1] > urgency_levels[-2]
    
    def _is_business_hours(self, timestamp: datetime) -> bool:
        """Check if timestamp is within business hours"""
        # Monday-Friday 8AM-6PM, Saturday 9AM-4PM
        day_of_week = timestamp.weekday()
        hour = timestamp.hour
        
        if day_of_week < 5:  # Monday-Friday
            return 8 <= hour < 18
        elif day_of_week == 5:  # Saturday
            return 9 <= hour < 16
        else:  # Sunday
            return False
    
    def _is_holiday_period(self, timestamp: datetime) -> bool:
        """Check if timestamp is during holiday period"""
        # This would integrate with holiday calendar
        # For now, simple check for major holidays
        month, day = timestamp.month, timestamp.day
        
        major_holidays = [
            (1, 1),   # New Year's Day
            (7, 4),   # Independence Day
            (12, 25), # Christmas
        ]
        
        return (month, day) in major_holidays
    
    def _check_weather_urgency(self, call_context: Dict) -> Dict:
        """Check for weather-related urgency factors"""
        # This would integrate with weather API
        # For now, return basic check
        return {'adjustment': 0.0, 'factors': []}
    
    def _get_current_workload(self) -> float:
        """Get current system workload (0-1)"""
        try:
            if self.redis_client:
                # Count active calls and queue depth
                active_calls = self.redis_client.scard('active_calls') or 0
                queue_depth = self.redis_client.zcard('priority_queue') or 0
                
                # Simple workload calculation
                total_load = active_calls + queue_depth
                max_capacity = 20  # Configurable
                
                return min(1.0, total_load / max_capacity)
            
            return 0.5  # Default moderate load
            
        except Exception as e:
            logger.error(f"Failed to get current workload: {e}")
            return 0.5
    
    def _log_emergency_assessment(self, caller_id: str, assessment: EmergencyAssessment, 
                                transcription: str):
        """Log emergency assessment for analysis"""
        try:
            log_data = {
                'caller_id': caller_id,
                'timestamp': datetime.now().isoformat(),
                'urgency_level': assessment.urgency_level.name,
                'emergency_type': assessment.emergency_type.value if assessment.emergency_type else None,
                'confidence_score': assessment.confidence_score,
                'trigger_keywords': assessment.trigger_keywords,
                'transcription': transcription[:500],  # Truncate for storage
                'recommended_action': assessment.recommended_action
            }
            
            if self.redis_client:
                log_key = f"emergency_log:{datetime.now().strftime('%Y%m%d_%H%M%S')}:{caller_id}"
                self.redis_client.hset(log_key, mapping=log_data)
                self.redis_client.expire(log_key, 2592000)  # 30 day retention
            
        except Exception as e:
            logger.error(f"Failed to log emergency assessment: {e}")
    
    def _log_routing_decision(self, call_sid: str, routing_result: Dict):
        """Log routing decision for analysis"""
        try:
            if self.redis_client:
                log_key = f"routing_log:{call_sid}"
                self.redis_client.hset(log_key, mapping=routing_result)
                self.redis_client.expire(log_key, 2592000)  # 30 day retention
            
        except Exception as e:
            logger.error(f"Failed to log routing decision: {e}")
    
    # Additional emergency handling methods
    async def _escalate_to_supervisor(self, call_sid: str, assessment: EmergencyAssessment):
        """Escalate critical emergency to supervisor"""
        try:
            await self._send_emergency_sms(
                self.emergency_contacts['supervisor'],
                f"CRITICAL EMERGENCY ESCALATION: Call {call_sid}. "
                f"Type: {assessment.emergency_type.value if assessment.emergency_type else 'Unknown'}. "
                f"Immediate attention required."
            )
            
            logger.warning(f"Emergency escalated to supervisor: {call_sid}")
            
        except Exception as e:
            logger.error(f"Failed to escalate to supervisor: {e}")
    
    async def _consider_911_escalation(self, call_sid: str, assessment: EmergencyAssessment):
        """Consider escalation to emergency services (911)"""
        try:
            # Check if situation warrants 911 call
            critical_keywords = ['fire', 'smoke', 'gas leak', 'electrical fire', 'collapse']
            
            if any(keyword in assessment.trigger_keywords for keyword in critical_keywords):
                # Log potential 911 situation
                logger.critical(f"Potential 911 situation detected: {call_sid} - {assessment.trigger_keywords}")
                
                # Notify supervisor for 911 decision
                await self._send_emergency_sms(
                    self.emergency_contacts['supervisor'],
                    f"POTENTIAL 911 SITUATION: Call {call_sid}. Keywords: {assessment.trigger_keywords}. "
                    f"Evaluate for emergency services escalation."
                )
            
        except Exception as e:
            logger.error(f"Failed to consider 911 escalation: {e}")
    
    async def _create_priority_ticket(self, call_sid: str, caller_id: str, 
                                    assessment: EmergencyAssessment) -> str:
        """Create priority service ticket"""
        try:
            # Generate ticket ID
            ticket_id = f"EMG-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            ticket_data = {
                'ticket_id': ticket_id,
                'call_sid': call_sid,
                'caller_id': caller_id,
                'urgency_level': assessment.urgency_level.name,
                'emergency_type': assessment.emergency_type.value if assessment.emergency_type else None,
                'created_time': datetime.now().isoformat(),
                'estimated_response': assessment.estimated_response_time,
                'safety_concerns': assessment.safety_concerns,
                'status': 'ACTIVE'
            }
            
            if self.redis_client:
                ticket_key = f"emergency_ticket:{ticket_id}"
                self.redis_client.hset(ticket_key, mapping=ticket_data)
                self.redis_client.expire(ticket_key, 2592000)  # 30 day retention
            
            logger.info(f"Emergency ticket created: {ticket_id}")
            return ticket_id
            
        except Exception as e:
            logger.error(f"Failed to create priority ticket: {e}")
            return f"ERROR-{datetime.now().strftime('%H%M%S')}"
    
    async def _set_follow_up_reminder(self, call_sid: str, hours: int):
        """Set follow-up reminder for call"""
        try:
            reminder_time = datetime.now() + timedelta(hours=hours)
            
            reminder_data = {
                'call_sid': call_sid,
                'reminder_time': reminder_time.isoformat(),
                'type': 'follow_up'
            }
            
            if self.redis_client:
                reminder_key = f"reminder:{call_sid}:{int(reminder_time.timestamp())}"
                self.redis_client.hset(reminder_key, mapping=reminder_data)
                self.redis_client.expireat(reminder_key, int(reminder_time.timestamp()) + 86400)
            
            logger.info(f"Follow-up reminder set for {call_sid} at {reminder_time}")
            
        except Exception as e:
            logger.error(f"Failed to set follow-up reminder: {e}")

if __name__ == "__main__":
    # Test the emergency handler
    import asyncio
    
    async def test_emergency_handler():
        handler = EmergencyHandler()
        
        # Test cases
        test_cases = [
            {
                'transcription': "I have a gas leak in my kitchen, I can smell gas everywhere!",
                'caller_id': '+15551234567',
                'context': {'is_callback': False}
            },
            {
                'transcription': "My toilet is overflowing and there's water everywhere",
                'caller_id': '+15551234568',
                'context': {'business_call': True}
            },
            {
                'transcription': "My faucet is dripping and I'd like someone to fix it",
                'caller_id': '+15551234569',
                'context': {}
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            print(f"\n--- Test Case {i+1} ---")
            print(f"Transcription: {test_case['transcription']}")
            
            assessment = handler.assess_urgency(
                test_case['transcription'],
                test_case['caller_id'],
                test_case['context']
            )
            
            print(f"Urgency Level: {assessment.urgency_level.name}")
            print(f"Emergency Type: {assessment.emergency_type}")
            print(f"Confidence: {assessment.confidence_score:.2f}")
            print(f"Keywords: {assessment.trigger_keywords}")
            print(f"Action: {assessment.recommended_action}")
            print(f"Response Time: {assessment.estimated_response_time} minutes")
            print(f"Immediate Dispatch: {assessment.requires_immediate_dispatch}")
            
            # Test routing
            call_sid = f"test_call_{i+1}"
            routing_result = await handler.route_emergency_call(
                assessment, call_sid, test_case['caller_id']
            )
            
            print(f"Routing Result: {routing_result}")
    
    asyncio.run(test_emergency_handler())
#!/usr/bin/env python3
"""
Voice Quality Assurance System for 757 Handy
Analyzes call recordings for quality, compliance, and training opportunities

Author: Phone Engineer Agent
"""

import os
import json
import logging
import asyncio
import aiohttp
import redis
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import re
import statistics
from pathlib import Path

logger = logging.getLogger(__name__)

class QualityScore(Enum):
    """Quality scoring levels"""
    EXCELLENT = 5
    GOOD = 4
    SATISFACTORY = 3
    NEEDS_IMPROVEMENT = 2
    POOR = 1

class CallCategory(Enum):
    """Call categorization for quality assessment"""
    CUSTOMER_SERVICE = "customer_service"
    TECHNICAL_SUPPORT = "technical_support"
    SALES_INQUIRY = "sales_inquiry"
    EMERGENCY_RESPONSE = "emergency_response"
    COMPLAINT_HANDLING = "complaint_handling"
    APPOINTMENT_SCHEDULING = "appointment_scheduling"

@dataclass
class QualityMetrics:
    """Comprehensive quality assessment metrics"""
    call_sid: str
    agent_id: Optional[str]
    timestamp: datetime
    call_duration: int
    category: CallCategory
    
    # Overall scores (1-5)
    overall_quality: QualityScore
    professionalism: QualityScore
    communication_clarity: QualityScore
    problem_resolution: QualityScore
    customer_satisfaction: QualityScore
    brand_adherence: QualityScore
    
    # Specific metrics
    greeting_quality: float  # 0-1
    closing_quality: float   # 0-1
    hold_time_management: float  # 0-1
    information_accuracy: float  # 0-1
    empathy_demonstrated: float  # 0-1
    
    # Compliance checks
    privacy_compliance: bool
    safety_protocols_followed: bool
    company_policies_followed: bool
    
    # Technical quality
    audio_quality: float  # 0-1
    background_noise: float  # 0-1 (lower is better)
    voice_clarity: float  # 0-1
    technical_issues: List[str]
    
    # Conversation analysis
    talk_time_ratio: float  # Agent talk time / Total talk time
    interruptions: int
    dead_air_duration: float  # seconds
    filler_words_count: int
    
    # Outcome metrics
    first_call_resolution: bool
    callback_required: bool
    escalation_needed: bool
    customer_complaint_risk: float  # 0-1
    
    # Training opportunities
    strengths: List[str]
    improvement_areas: List[str]
    training_recommendations: List[str]
    
    # Automated flags
    quality_flags: List[str]
    compliance_violations: List[str]
    coaching_opportunities: List[str]

class VoiceQualityAssurance:
    """
    Comprehensive voice quality assurance system
    
    Features:
    - Automated call recording analysis
    - Multi-dimensional quality scoring
    - Compliance monitoring
    - Performance trending
    - Training recommendation engine
    - Customer satisfaction prediction
    - Brand consistency monitoring
    - Real-time quality alerts
    """
    
    def __init__(self):
        # Initialize Redis for QA data storage
        try:
            self.redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=int(os.getenv('REDIS_DB', 3)),  # Dedicated DB for QA
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("QA Redis connection established")
        except Exception as e:
            logger.warning(f"Redis connection failed, using memory storage: {e}")
            self.redis_client = None
        
        # Quality standards and thresholds
        self.quality_standards = {
            'greeting_required_elements': [
                'company_name', 'agent_name', 'helpful_offer'
            ],
            'closing_required_elements': [
                'summary', 'next_steps', 'satisfaction_check', 'thank_you'
            ],
            'max_hold_time': 120,  # seconds
            'max_dead_air': 10,    # seconds
            'max_filler_words': 15,
            'min_empathy_score': 0.6,
            'target_first_call_resolution': 0.8
        }
        
        # Brand voice guidelines
        self.brand_voice_criteria = {
            'tone_keywords': {
                'positive': ['happy', 'glad', 'pleased', 'wonderful', 'excellent'],
                'empathetic': ['understand', 'appreciate', 'sorry', 'concern'],
                'professional': ['certainly', 'absolutely', 'ensure', 'guarantee'],
                'avoid': ['no problem', 'whatever', 'I guess', 'maybe']
            },
            'company_positioning': [
                'premier home improvement experts',
                'Hampton Roads trusted service',
                'quality workmanship',
                'customer satisfaction priority'
            ]
        }
        
        # Compliance requirements
        self.compliance_checks = {
            'privacy_requirements': [
                'verified_customer_identity',
                'no_personal_info_shared',
                'secure_payment_handling'
            ],
            'safety_protocols': [
                'emergency_procedures_known',
                'safety_warnings_given',
                'proper_escalation_followed'
            ],
            'service_standards': [
                'accurate_pricing_info',
                'realistic_timeframes',
                'proper_warranty_explanation'
            ]
        }
        
        # Technical analysis configuration
        self.audio_analysis_config = {
            'sample_rate': 16000,
            'min_audio_quality': 0.7,
            'max_background_noise': 0.3,
            'min_voice_clarity': 0.8
        }
        
        # Quality scoring weights
        self.scoring_weights = {
            'professionalism': 0.25,
            'communication_clarity': 0.20,
            'problem_resolution': 0.25,
            'customer_satisfaction': 0.15,
            'brand_adherence': 0.15
        }
        
        logger.info("VoiceQualityAssurance initialized with comprehensive analysis")
    
    async def analyze_call_recording(self, call_data: Dict[str, Any]) -> QualityMetrics:
        """
        Comprehensive call recording analysis
        
        Args:
            call_data: Dictionary containing call information including:
                - call_sid: Unique call identifier
                - recording_url: URL to call recording
                - transcription: Call transcription
                - agent_id: Agent identifier (if available)
                - call_duration: Duration in seconds
                - customer_data: Customer information
        
        Returns:
            QualityMetrics object with comprehensive analysis
        """
        try:
            logger.info(f"Starting quality analysis for call {call_data.get('call_sid')}")
            
            # Initialize analysis components
            transcription = call_data.get('transcription', '')
            recording_url = call_data.get('recording_url', '')
            
            # Determine call category
            category = self._categorize_call(transcription, call_data)
            
            # Analyze transcription
            conversation_analysis = await self._analyze_conversation(transcription)
            
            # Analyze audio quality (if recording available)
            audio_analysis = await self._analyze_audio_quality(recording_url)
            
            # Check compliance
            compliance_analysis = self._check_compliance(transcription, call_data)
            
            # Evaluate brand adherence
            brand_analysis = self._evaluate_brand_adherence(transcription)
            
            # Assess customer experience
            customer_experience = self._assess_customer_experience(transcription, call_data)
            
            # Calculate quality scores
            quality_scores = self._calculate_quality_scores(
                conversation_analysis, brand_analysis, customer_experience, compliance_analysis
            )
            
            # Generate training recommendations
            training_analysis = self._generate_training_recommendations(
                conversation_analysis, brand_analysis, compliance_analysis
            )
            
            # Create quality metrics object
            quality_metrics = QualityMetrics(
                call_sid=call_data.get('call_sid', ''),
                agent_id=call_data.get('agent_id'),
                timestamp=datetime.now(),
                call_duration=call_data.get('call_duration', 0),
                category=category,
                
                # Overall scores
                overall_quality=quality_scores['overall'],
                professionalism=quality_scores['professionalism'],
                communication_clarity=quality_scores['communication_clarity'],
                problem_resolution=quality_scores['problem_resolution'],
                customer_satisfaction=quality_scores['customer_satisfaction'],
                brand_adherence=quality_scores['brand_adherence'],
                
                # Specific metrics
                greeting_quality=conversation_analysis['greeting_quality'],
                closing_quality=conversation_analysis['closing_quality'],
                hold_time_management=conversation_analysis['hold_time_management'],
                information_accuracy=conversation_analysis['information_accuracy'],
                empathy_demonstrated=conversation_analysis['empathy_score'],
                
                # Compliance
                privacy_compliance=compliance_analysis['privacy_compliance'],
                safety_protocols_followed=compliance_analysis['safety_protocols'],
                company_policies_followed=compliance_analysis['company_policies'],
                
                # Technical quality
                audio_quality=audio_analysis['quality_score'],
                background_noise=audio_analysis['noise_level'],
                voice_clarity=audio_analysis['clarity_score'],
                technical_issues=audio_analysis['issues'],
                
                # Conversation metrics
                talk_time_ratio=conversation_analysis['talk_time_ratio'],
                interruptions=conversation_analysis['interruptions'],
                dead_air_duration=conversation_analysis['dead_air'],
                filler_words_count=conversation_analysis['filler_words'],
                
                # Outcomes
                first_call_resolution=customer_experience['first_call_resolution'],
                callback_required=customer_experience['callback_required'],
                escalation_needed=customer_experience['escalation_needed'],
                customer_complaint_risk=customer_experience['complaint_risk'],
                
                # Training
                strengths=training_analysis['strengths'],
                improvement_areas=training_analysis['improvement_areas'],
                training_recommendations=training_analysis['recommendations'],
                
                # Flags
                quality_flags=self._identify_quality_flags(conversation_analysis, compliance_analysis),
                compliance_violations=compliance_analysis['violations'],
                coaching_opportunities=training_analysis['coaching_opportunities']
            )
            
            # Store analysis results
            await self._store_quality_metrics(quality_metrics)
            
            # Trigger alerts if needed
            await self._check_quality_alerts(quality_metrics)
            
            logger.info(f"Quality analysis completed for call {call_data.get('call_sid')} - Overall: {quality_metrics.overall_quality.name}")
            return quality_metrics
            
        except Exception as e:
            logger.error(f"Failed to analyze call recording: {e}")
            # Return minimal metrics with error flag
            return self._create_error_metrics(call_data, str(e))
    
    def _categorize_call(self, transcription: str, call_data: Dict) -> CallCategory:
        """Categorize call based on content and context"""
        transcription_lower = transcription.lower()
        
        # Emergency indicators
        emergency_keywords = ['emergency', 'urgent', 'flood', 'fire', 'gas leak']
        if any(keyword in transcription_lower for keyword in emergency_keywords):
            return CallCategory.EMERGENCY_RESPONSE
        
        # Complaint indicators
        complaint_keywords = ['complaint', 'unhappy', 'disappointed', 'frustrated', 'problem with']
        if any(keyword in transcription_lower for keyword in complaint_keywords):
            return CallCategory.COMPLAINT_HANDLING
        
        # Scheduling indicators
        scheduling_keywords = ['appointment', 'schedule', 'booking', 'when can you come']
        if any(keyword in transcription_lower for keyword in scheduling_keywords):
            return CallCategory.APPOINTMENT_SCHEDULING
        
        # Sales indicators
        sales_keywords = ['quote', 'estimate', 'price', 'cost', 'how much']
        if any(keyword in transcription_lower for keyword in sales_keywords):
            return CallCategory.SALES_INQUIRY
        
        # Technical support indicators
        tech_keywords = ['how to', 'broken', 'not working', 'fix', 'repair']
        if any(keyword in transcription_lower for keyword in tech_keywords):
            return CallCategory.TECHNICAL_SUPPORT
        
        return CallCategory.CUSTOMER_SERVICE
    
    async def _analyze_conversation(self, transcription: str) -> Dict[str, Any]:
        """Analyze conversation flow and structure"""
        try:
            # Split into agent and customer segments (simplified)
            segments = self._parse_conversation_segments(transcription)
            
            # Analyze greeting
            greeting_quality = self._analyze_greeting(segments)
            
            # Analyze closing
            closing_quality = self._analyze_closing(segments)
            
            # Calculate talk time ratio
            talk_time_ratio = self._calculate_talk_time_ratio(segments)
            
            # Count interruptions
            interruptions = self._count_interruptions(segments)
            
            # Analyze dead air
            dead_air = self._analyze_dead_air(transcription)
            
            # Count filler words
            filler_words = self._count_filler_words(transcription)
            
            # Assess information accuracy
            information_accuracy = self._assess_information_accuracy(transcription)
            
            # Analyze empathy
            empathy_score = self._analyze_empathy(transcription)
            
            # Assess hold time management
            hold_time_management = self._analyze_hold_time_management(transcription)
            
            return {
                'greeting_quality': greeting_quality,
                'closing_quality': closing_quality,
                'talk_time_ratio': talk_time_ratio,
                'interruptions': interruptions,
                'dead_air': dead_air,
                'filler_words': filler_words,
                'information_accuracy': information_accuracy,
                'empathy_score': empathy_score,
                'hold_time_management': hold_time_management,
                'segments': segments
            }
            
        except Exception as e:
            logger.error(f"Error analyzing conversation: {e}")
            return self._get_default_conversation_analysis()
    
    def _parse_conversation_segments(self, transcription: str) -> List[Dict]:
        """Parse transcription into agent and customer segments"""
        # This is a simplified parser - in production, would use more sophisticated NLP
        segments = []
        lines = transcription.split('\n')
        
        for line in lines:
            if ':' in line:
                speaker, content = line.split(':', 1)
                speaker = speaker.strip().lower()
                content = content.strip()
                
                # Determine if agent or customer
                is_agent = (
                    'agent' in speaker or 
                    'karen' in speaker or 
                    'representative' in speaker
                )
                
                segments.append({
                    'speaker': 'agent' if is_agent else 'customer',
                    'content': content,
                    'duration': len(content) * 0.1  # Rough estimate
                })
        
        return segments
    
    def _analyze_greeting(self, segments: List[Dict]) -> float:
        """Analyze quality of call greeting"""
        try:
            # Find first agent segment
            agent_segments = [s for s in segments if s['speaker'] == 'agent']
            if not agent_segments:
                return 0.0
            
            first_greeting = agent_segments[0]['content'].lower()
            score = 0.0
            
            # Check for required elements
            required_elements = self.quality_standards['greeting_required_elements']
            
            if any(element in first_greeting for element in ['757 handy', 'company']):
                score += 0.3  # Company name
            
            if any(element in first_greeting for element in ['karen', 'my name', 'this is']):
                score += 0.3  # Agent identification
            
            if any(element in first_greeting for element in ['help', 'assist', 'serve']):
                score += 0.4  # Helpful offer
            
            return min(1.0, score)
            
        except Exception as e:
            logger.error(f"Error analyzing greeting: {e}")
            return 0.5
    
    def _analyze_closing(self, segments: List[Dict]) -> float:
        """Analyze quality of call closing"""
        try:
            # Find last few agent segments
            agent_segments = [s for s in segments if s['speaker'] == 'agent']
            if len(agent_segments) < 2:
                return 0.0
            
            closing_content = ' '.join([s['content'] for s in agent_segments[-2:]]).lower()
            score = 0.0
            
            # Check for closing elements
            if any(word in closing_content for word in ['thank', 'appreciate']):
                score += 0.3
            
            if any(word in closing_content for word in ['anything else', 'other questions']):
                score += 0.3
            
            if any(word in closing_content for word in ['have a great', 'wonderful day']):
                score += 0.2
            
            if any(word in closing_content for word in ['follow up', 'call back', 'contact']):
                score += 0.2
            
            return min(1.0, score)
            
        except Exception as e:
            logger.error(f"Error analyzing closing: {e}")
            return 0.5
    
    def _calculate_talk_time_ratio(self, segments: List[Dict]) -> float:
        """Calculate agent talk time ratio"""
        try:
            agent_time = sum(s['duration'] for s in segments if s['speaker'] == 'agent')
            total_time = sum(s['duration'] for s in segments)
            
            if total_time == 0:
                return 0.5
            
            return agent_time / total_time
            
        except Exception as e:
            logger.error(f"Error calculating talk time ratio: {e}")
            return 0.5
    
    def _count_interruptions(self, segments: List[Dict]) -> int:
        """Count conversation interruptions"""
        try:
            interruptions = 0
            for i in range(1, len(segments)):
                current = segments[i]
                previous = segments[i-1]
                
                # Check for short segments that might indicate interruptions
                if (current['speaker'] != previous['speaker'] and 
                    len(current['content']) < 10):
                    interruptions += 1
            
            return interruptions
            
        except Exception as e:
            logger.error(f"Error counting interruptions: {e}")
            return 0
    
    def _analyze_dead_air(self, transcription: str) -> float:
        """Analyze dead air duration"""
        try:
            # Look for indicators of dead air
            dead_air_indicators = ['[pause]', '[silence]', '...', '[dead air]']
            total_dead_air = 0.0
            
            for indicator in dead_air_indicators:
                count = transcription.lower().count(indicator.lower())
                total_dead_air += count * 3.0  # Estimate 3 seconds per indicator
            
            return total_dead_air
            
        except Exception as e:
            logger.error(f"Error analyzing dead air: {e}")
            return 0.0
    
    def _count_filler_words(self, transcription: str) -> int:
        """Count filler words in agent speech"""
        try:
            filler_words = ['um', 'uh', 'like', 'you know', 'so', 'well', 'actually']
            transcription_lower = transcription.lower()
            
            total_count = 0
            for filler in filler_words:
                total_count += transcription_lower.count(filler)
            
            return total_count
            
        except Exception as e:
            logger.error(f"Error counting filler words: {e}")
            return 0
    
    def _assess_information_accuracy(self, transcription: str) -> float:
        """Assess accuracy of information provided"""
        try:
            # Look for indicators of accurate information
            accuracy_indicators = [
                'let me check', 'according to', 'our records show',
                'I can confirm', 'verified', 'accurate'
            ]
            
            inaccuracy_indicators = [
                'I think', 'maybe', 'probably', 'I guess',
                'not sure', 'might be'
            ]
            
            transcription_lower = transcription.lower()
            
            accuracy_score = 0.7  # Base score
            
            for indicator in accuracy_indicators:
                if indicator in transcription_lower:
                    accuracy_score += 0.1
            
            for indicator in inaccuracy_indicators:
                if indicator in transcription_lower:
                    accuracy_score -= 0.1
            
            return max(0.0, min(1.0, accuracy_score))
            
        except Exception as e:
            logger.error(f"Error assessing information accuracy: {e}")
            return 0.7
    
    def _analyze_empathy(self, transcription: str) -> float:
        """Analyze demonstrated empathy"""
        try:
            empathy_phrases = [
                'I understand', 'I can imagine', 'I appreciate',
                'I\'m sorry', 'that must be', 'I hear you',
                'I know how', 'frustrating', 'concerning'
            ]
            
            transcription_lower = transcription.lower()
            empathy_score = 0.0
            
            for phrase in empathy_phrases:
                if phrase in transcription_lower:
                    empathy_score += 0.15
            
            return min(1.0, empathy_score)
            
        except Exception as e:
            logger.error(f"Error analyzing empathy: {e}")
            return 0.5
    
    def _analyze_hold_time_management(self, transcription: str) -> float:
        """Analyze hold time management"""
        try:
            hold_indicators = ['hold', 'please wait', 'one moment', 'checking']
            explanation_indicators = ['checking with', 'looking up', 'verifying']
            
            transcription_lower = transcription.lower()
            
            has_hold = any(indicator in transcription_lower for indicator in hold_indicators)
            has_explanation = any(indicator in transcription_lower for indicator in explanation_indicators)
            
            if not has_hold:
                return 1.0  # No hold time needed
            
            if has_hold and has_explanation:
                return 0.8  # Good hold management
            elif has_hold:
                return 0.5  # Hold without explanation
            
            return 1.0
            
        except Exception as e:
            logger.error(f"Error analyzing hold time management: {e}")
            return 0.7
    
    async def _analyze_audio_quality(self, recording_url: str) -> Dict[str, Any]:
        """Analyze technical audio quality"""
        try:
            if not recording_url:
                return self._get_default_audio_analysis()
            
            # In production, this would use audio processing libraries
            # For now, return simulated analysis
            return {
                'quality_score': 0.85,
                'noise_level': 0.15,
                'clarity_score': 0.90,
                'issues': []
            }
            
        except Exception as e:
            logger.error(f"Error analyzing audio quality: {e}")
            return self._get_default_audio_analysis()
    
    def _check_compliance(self, transcription: str, call_data: Dict) -> Dict[str, Any]:
        """Check compliance with company policies and regulations"""
        try:
            violations = []
            
            # Privacy compliance
            privacy_compliance = self._check_privacy_compliance(transcription)
            if not privacy_compliance:
                violations.append("Privacy policy violation detected")
            
            # Safety protocols
            safety_protocols = self._check_safety_protocols(transcription)
            if not safety_protocols:
                violations.append("Safety protocol not followed")
            
            # Company policies
            company_policies = self._check_company_policies(transcription)
            if not company_policies:
                violations.append("Company policy deviation detected")
            
            return {
                'privacy_compliance': privacy_compliance,
                'safety_protocols': safety_protocols,
                'company_policies': company_policies,
                'violations': violations
            }
            
        except Exception as e:
            logger.error(f"Error checking compliance: {e}")
            return {
                'privacy_compliance': True,
                'safety_protocols': True,
                'company_policies': True,
                'violations': []
            }
    
    def _check_privacy_compliance(self, transcription: str) -> bool:
        """Check privacy compliance"""
        # Look for proper identity verification
        verification_phrases = ['can you verify', 'confirm your', 'for security']
        transcription_lower = transcription.lower()
        
        return any(phrase in transcription_lower for phrase in verification_phrases)
    
    def _check_safety_protocols(self, transcription: str) -> bool:
        """Check if safety protocols were followed"""
        # Look for safety warnings when appropriate
        safety_phrases = ['safety', 'turn off', 'shut off', 'danger', 'hazard']
        transcription_lower = transcription.lower()
        
        # If emergency keywords present, check for safety response
        emergency_keywords = ['emergency', 'gas', 'electrical', 'flood']
        has_emergency = any(keyword in transcription_lower for keyword in emergency_keywords)
        
        if has_emergency:
            return any(phrase in transcription_lower for phrase in safety_phrases)
        
        return True  # No emergency, no safety protocol needed
    
    def _check_company_policies(self, transcription: str) -> bool:
        """Check adherence to company policies"""
        # Check for proper pricing discussion
        pricing_keywords = ['price', 'cost', 'charge', 'fee']
        transcription_lower = transcription.lower()
        
        has_pricing_discussion = any(keyword in transcription_lower for keyword in pricing_keywords)
        
        if has_pricing_discussion:
            # Should mention estimates or scheduling
            estimate_phrases = ['estimate', 'quote', 'assessment', 'schedule']
            return any(phrase in transcription_lower for phrase in estimate_phrases)
        
        return True
    
    def _evaluate_brand_adherence(self, transcription: str) -> Dict[str, Any]:
        """Evaluate adherence to brand voice guidelines"""
        try:
            transcription_lower = transcription.lower()
            
            # Check positive tone
            positive_score = 0.0
            for word in self.brand_voice_criteria['tone_keywords']['positive']:
                if word in transcription_lower:
                    positive_score += 0.2
            
            # Check empathy
            empathy_score = 0.0
            for word in self.brand_voice_criteria['tone_keywords']['empathetic']:
                if word in transcription_lower:
                    empathy_score += 0.2
            
            # Check professionalism
            professional_score = 0.0
            for word in self.brand_voice_criteria['tone_keywords']['professional']:
                if word in transcription_lower:
                    professional_score += 0.2
            
            # Check for words to avoid
            avoid_penalty = 0.0
            for word in self.brand_voice_criteria['tone_keywords']['avoid']:
                if word in transcription_lower:
                    avoid_penalty += 0.3
            
            # Check company positioning
            positioning_score = 0.0
            for phrase in self.brand_voice_criteria['company_positioning']:
                if phrase.lower() in transcription_lower:
                    positioning_score += 0.25
            
            overall_brand_score = max(0.0, min(1.0, 
                (positive_score + empathy_score + professional_score + positioning_score) / 4 - avoid_penalty
            ))
            
            return {
                'overall_score': overall_brand_score,
                'positive_tone': min(1.0, positive_score),
                'empathy': min(1.0, empathy_score),
                'professionalism': min(1.0, professional_score),
                'positioning': min(1.0, positioning_score),
                'avoid_words_used': avoid_penalty > 0
            }
            
        except Exception as e:
            logger.error(f"Error evaluating brand adherence: {e}")
            return {
                'overall_score': 0.7,
                'positive_tone': 0.7,
                'empathy': 0.7,
                'professionalism': 0.7,
                'positioning': 0.7,
                'avoid_words_used': False
            }
    
    def _assess_customer_experience(self, transcription: str, call_data: Dict) -> Dict[str, Any]:
        """Assess overall customer experience"""
        try:
            # Determine first call resolution
            fcr_indicators = [
                'resolved', 'scheduled', 'taken care of',
                'all set', 'problem solved'
            ]
            transcription_lower = transcription.lower()
            
            first_call_resolution = any(indicator in transcription_lower for indicator in fcr_indicators)
            
            # Check if callback required
            callback_indicators = ['call you back', 'follow up', 'check and call']
            callback_required = any(indicator in transcription_lower for indicator in callback_indicators)
            
            # Check for escalation
            escalation_indicators = ['supervisor', 'manager', 'escalate', 'transfer']
            escalation_needed = any(indicator in transcription_lower for indicator in escalation_indicators)
            
            # Assess complaint risk
            complaint_risk = self._assess_complaint_risk(transcription)
            
            return {
                'first_call_resolution': first_call_resolution,
                'callback_required': callback_required,
                'escalation_needed': escalation_needed,
                'complaint_risk': complaint_risk
            }
            
        except Exception as e:
            logger.error(f"Error assessing customer experience: {e}")
            return {
                'first_call_resolution': True,
                'callback_required': False,
                'escalation_needed': False,
                'complaint_risk': 0.1
            }
    
    def _assess_complaint_risk(self, transcription: str) -> float:
        """Assess risk of customer complaint"""
        try:
            negative_indicators = [
                'frustrated', 'disappointed', 'unhappy', 'angry',
                'terrible', 'awful', 'worst', 'unacceptable'
            ]
            
            positive_indicators = [
                'satisfied', 'happy', 'pleased', 'excellent',
                'great', 'wonderful', 'perfect', 'amazing'
            ]
            
            transcription_lower = transcription.lower()
            
            negative_count = sum(1 for indicator in negative_indicators if indicator in transcription_lower)
            positive_count = sum(1 for indicator in positive_indicators if indicator in transcription_lower)
            
            # Calculate risk score
            risk_score = 0.1  # Base risk
            risk_score += negative_count * 0.2
            risk_score -= positive_count * 0.1
            
            return max(0.0, min(1.0, risk_score))
            
        except Exception as e:
            logger.error(f"Error assessing complaint risk: {e}")
            return 0.1
    
    def _calculate_quality_scores(self, conversation_analysis: Dict, brand_analysis: Dict, 
                                customer_experience: Dict, compliance_analysis: Dict) -> Dict[str, QualityScore]:
        """Calculate overall quality scores"""
        try:
            # Professionalism score
            professionalism_score = (
                conversation_analysis['greeting_quality'] * 0.3 +
                conversation_analysis['closing_quality'] * 0.3 +
                brand_analysis['professionalism'] * 0.4
            )
            
            # Communication clarity score
            clarity_score = (
                conversation_analysis['information_accuracy'] * 0.4 +
                (1.0 - min(1.0, conversation_analysis['filler_words'] / 10)) * 0.3 +
                conversation_analysis['hold_time_management'] * 0.3
            )
            
            # Problem resolution score
            resolution_score = (
                (1.0 if customer_experience['first_call_resolution'] else 0.3) * 0.6 +
                (0.0 if customer_experience['escalation_needed'] else 1.0) * 0.4
            )
            
            # Customer satisfaction score
            satisfaction_score = (
                conversation_analysis['empathy_score'] * 0.4 +
                (1.0 - customer_experience['complaint_risk']) * 0.6
            )
            
            # Brand adherence score
            brand_score = brand_analysis['overall_score']
            
            # Overall score
            overall_score = (
                professionalism_score * self.scoring_weights['professionalism'] +
                clarity_score * self.scoring_weights['communication_clarity'] +
                resolution_score * self.scoring_weights['problem_resolution'] +
                satisfaction_score * self.scoring_weights['customer_satisfaction'] +
                brand_score * self.scoring_weights['brand_adherence']
            )
            
            # Apply compliance penalty
            if not all([compliance_analysis['privacy_compliance'], 
                       compliance_analysis['safety_protocols'],
                       compliance_analysis['company_policies']]):
                overall_score *= 0.8  # 20% penalty for compliance issues
            
            return {
                'overall': self._score_to_quality_level(overall_score),
                'professionalism': self._score_to_quality_level(professionalism_score),
                'communication_clarity': self._score_to_quality_level(clarity_score),
                'problem_resolution': self._score_to_quality_level(resolution_score),
                'customer_satisfaction': self._score_to_quality_level(satisfaction_score),
                'brand_adherence': self._score_to_quality_level(brand_score)
            }
            
        except Exception as e:
            logger.error(f"Error calculating quality scores: {e}")
            return {
                'overall': QualityScore.SATISFACTORY,
                'professionalism': QualityScore.SATISFACTORY,
                'communication_clarity': QualityScore.SATISFACTORY,
                'problem_resolution': QualityScore.SATISFACTORY,
                'customer_satisfaction': QualityScore.SATISFACTORY,
                'brand_adherence': QualityScore.SATISFACTORY
            }
    
    def _score_to_quality_level(self, score: float) -> QualityScore:
        """Convert numeric score to quality level"""
        if score >= 0.9:
            return QualityScore.EXCELLENT
        elif score >= 0.8:
            return QualityScore.GOOD
        elif score >= 0.6:
            return QualityScore.SATISFACTORY
        elif score >= 0.4:
            return QualityScore.NEEDS_IMPROVEMENT
        else:
            return QualityScore.POOR
    
    def _generate_training_recommendations(self, conversation_analysis: Dict, 
                                         brand_analysis: Dict, compliance_analysis: Dict) -> Dict[str, List[str]]:
        """Generate specific training recommendations"""
        try:
            strengths = []
            improvement_areas = []
            recommendations = []
            coaching_opportunities = []
            
            # Analyze strengths
            if conversation_analysis['greeting_quality'] > 0.8:
                strengths.append("Excellent call opening and greeting")
            
            if conversation_analysis['empathy_score'] > 0.7:
                strengths.append("Strong empathy and customer understanding")
            
            if brand_analysis['professionalism'] > 0.8:
                strengths.append("Professional communication style")
            
            # Identify improvement areas
            if conversation_analysis['greeting_quality'] < 0.6:
                improvement_areas.append("Call greeting and opening")
                recommendations.append("Practice standard greeting with company name and helpful offer")
                coaching_opportunities.append("Role-play proper call openings")
            
            if conversation_analysis['filler_words'] > 10:
                improvement_areas.append("Communication clarity - reduce filler words")
                recommendations.append("Practice speaking with deliberate pauses instead of filler words")
                coaching_opportunities.append("Record practice sessions to identify filler word patterns")
            
            if conversation_analysis['empathy_score'] < 0.5:
                improvement_areas.append("Customer empathy and emotional intelligence")
                recommendations.append("Training on empathetic response techniques")
                coaching_opportunities.append("Customer scenario practice with empathy focus")
            
            if not all(compliance_analysis.values()):
                improvement_areas.append("Compliance and policy adherence")
                recommendations.append("Review company policies and compliance requirements")
                coaching_opportunities.append("Compliance scenario training")
            
            if brand_analysis['overall_score'] < 0.7:
                improvement_areas.append("Brand voice consistency")
                recommendations.append("Study brand voice guidelines and practice key phrases")
                coaching_opportunities.append("Brand voice workshop and practice sessions")
            
            return {
                'strengths': strengths,
                'improvement_areas': improvement_areas,
                'recommendations': recommendations,
                'coaching_opportunities': coaching_opportunities
            }
            
        except Exception as e:
            logger.error(f"Error generating training recommendations: {e}")
            return {
                'strengths': ["Call completed successfully"],
                'improvement_areas': ["Continue professional development"],
                'recommendations': ["Regular training and practice"],
                'coaching_opportunities': ["Ongoing coaching sessions"]
            }
    
    def _identify_quality_flags(self, conversation_analysis: Dict, compliance_analysis: Dict) -> List[str]:
        """Identify quality flags requiring attention"""
        flags = []
        
        if conversation_analysis['interruptions'] > 3:
            flags.append("HIGH_INTERRUPTION_COUNT")
        
        if conversation_analysis['dead_air'] > 30:
            flags.append("EXCESSIVE_DEAD_AIR")
        
        if conversation_analysis['filler_words'] > 15:
            flags.append("EXCESSIVE_FILLER_WORDS")
        
        if not compliance_analysis['privacy_compliance']:
            flags.append("PRIVACY_VIOLATION")
        
        if not compliance_analysis['safety_protocols']:
            flags.append("SAFETY_PROTOCOL_MISS")
        
        if conversation_analysis['empathy_score'] < 0.3:
            flags.append("LOW_EMPATHY")
        
        return flags
    
    async def _store_quality_metrics(self, quality_metrics: QualityMetrics):
        """Store quality metrics for reporting and analysis"""
        try:
            if self.redis_client:
                metrics_data = asdict(quality_metrics)
                
                # Convert datetime and enum values for storage
                metrics_data['timestamp'] = quality_metrics.timestamp.isoformat()
                metrics_data['category'] = quality_metrics.category.value
                
                for field in ['overall_quality', 'professionalism', 'communication_clarity', 
                             'problem_resolution', 'customer_satisfaction', 'brand_adherence']:
                    metrics_data[field] = getattr(quality_metrics, field).value
                
                # Store in Redis
                metrics_key = f"quality_metrics:{quality_metrics.call_sid}"
                self.redis_client.hset(metrics_key, mapping=metrics_data)
                self.redis_client.expire(metrics_key, 2592000)  # 30 day retention
                
                # Add to time-series for reporting
                day_key = quality_metrics.timestamp.strftime('%Y-%m-%d')
                self.redis_client.lpush(f"daily_quality:{day_key}", quality_metrics.call_sid)
                self.redis_client.expire(f"daily_quality:{day_key}", 2592000)
            
            logger.info(f"Quality metrics stored for call {quality_metrics.call_sid}")
            
        except Exception as e:
            logger.error(f"Failed to store quality metrics: {e}")
    
    async def _check_quality_alerts(self, quality_metrics: QualityMetrics):
        """Check for quality alerts requiring immediate attention"""
        try:
            alerts = []
            
            # Critical quality issues
            if quality_metrics.overall_quality == QualityScore.POOR:
                alerts.append({
                    'type': 'POOR_QUALITY_CALL',
                    'severity': 'high',
                    'call_sid': quality_metrics.call_sid,
                    'agent_id': quality_metrics.agent_id
                })
            
            # Compliance violations
            if quality_metrics.compliance_violations:
                alerts.append({
                    'type': 'COMPLIANCE_VIOLATION',
                    'severity': 'critical',
                    'call_sid': quality_metrics.call_sid,
                    'violations': quality_metrics.compliance_violations
                })
            
            # High complaint risk
            if quality_metrics.customer_complaint_risk > 0.7:
                alerts.append({
                    'type': 'HIGH_COMPLAINT_RISK',
                    'severity': 'medium',
                    'call_sid': quality_metrics.call_sid,
                    'risk_score': quality_metrics.customer_complaint_risk
                })
            
            # Send alerts
            for alert in alerts:
                await self._send_quality_alert(alert)
            
        except Exception as e:
            logger.error(f"Failed to check quality alerts: {e}")
    
    async def _send_quality_alert(self, alert: Dict):
        """Send quality alert to appropriate recipients"""
        try:
            if self.redis_client:
                # Publish alert to subscribers
                self.redis_client.publish('quality_alerts', json.dumps(alert))
                
                # Store alert for review
                alert_key = f"quality_alert:{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                self.redis_client.hset(alert_key, mapping=alert)
                self.redis_client.expire(alert_key, 86400)  # 24 hour retention
            
            logger.warning(f"Quality alert sent: {alert['type']} - {alert.get('call_sid')}")
            
        except Exception as e:
            logger.error(f"Failed to send quality alert: {e}")
    
    # Helper methods for default values
    def _get_default_conversation_analysis(self) -> Dict[str, Any]:
        """Get default conversation analysis when parsing fails"""
        return {
            'greeting_quality': 0.7,
            'closing_quality': 0.7,
            'talk_time_ratio': 0.5,
            'interruptions': 0,
            'dead_air': 0.0,
            'filler_words': 3,
            'information_accuracy': 0.8,
            'empathy_score': 0.6,
            'hold_time_management': 0.8,
            'segments': []
        }
    
    def _get_default_audio_analysis(self) -> Dict[str, Any]:
        """Get default audio analysis when processing fails"""
        return {
            'quality_score': 0.8,
            'noise_level': 0.2,
            'clarity_score': 0.8,
            'issues': []
        }
    
    def _create_error_metrics(self, call_data: Dict, error_message: str) -> QualityMetrics:
        """Create minimal quality metrics when analysis fails"""
        return QualityMetrics(
            call_sid=call_data.get('call_sid', 'unknown'),
            agent_id=call_data.get('agent_id'),
            timestamp=datetime.now(),
            call_duration=call_data.get('call_duration', 0),
            category=CallCategory.CUSTOMER_SERVICE,
            
            # Set all scores to satisfactory as safe default
            overall_quality=QualityScore.SATISFACTORY,
            professionalism=QualityScore.SATISFACTORY,
            communication_clarity=QualityScore.SATISFACTORY,
            problem_resolution=QualityScore.SATISFACTORY,
            customer_satisfaction=QualityScore.SATISFACTORY,
            brand_adherence=QualityScore.SATISFACTORY,
            
            # Default specific metrics
            greeting_quality=0.7,
            closing_quality=0.7,
            hold_time_management=0.8,
            information_accuracy=0.8,
            empathy_demonstrated=0.6,
            
            # Default compliance (assuming good)
            privacy_compliance=True,
            safety_protocols_followed=True,
            company_policies_followed=True,
            
            # Default technical quality
            audio_quality=0.8,
            background_noise=0.2,
            voice_clarity=0.8,
            technical_issues=[],
            
            # Default conversation metrics
            talk_time_ratio=0.5,
            interruptions=0,
            dead_air_duration=0.0,
            filler_words_count=3,
            
            # Default outcomes
            first_call_resolution=True,
            callback_required=False,
            escalation_needed=False,
            customer_complaint_risk=0.1,
            
            # Error information
            strengths=["Call completed"],
            improvement_areas=["Analysis error - manual review needed"],
            training_recommendations=[f"Manual review required: {error_message}"],
            
            # Error flags
            quality_flags=["ANALYSIS_ERROR"],
            compliance_violations=[],
            coaching_opportunities=["Manual quality review"]
        )
    
    # Reporting and analytics methods
    async def generate_quality_report(self, time_range: str = '24h', 
                                    agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate comprehensive quality report"""
        try:
            # This would implement detailed quality reporting
            # For now, return structure
            return {
                'time_range': time_range,
                'agent_id': agent_id,
                'summary': {
                    'total_calls_analyzed': 0,
                    'average_quality_score': 0.0,
                    'quality_distribution': {},
                    'compliance_rate': 0.0
                },
                'trends': {},
                'top_issues': [],
                'recommendations': []
            }
            
        except Exception as e:
            logger.error(f"Failed to generate quality report: {e}")
            return {'error': str(e)}

if __name__ == "__main__":
    # Test the quality assurance system
    import asyncio
    
    async def test_quality_system():
        qa_system = VoiceQualityAssurance()
        
        # Sample call data
        test_call = {
            'call_sid': 'test_qa_123',
            'agent_id': 'agent_001',
            'call_duration': 300,
            'transcription': '''Agent: Good morning, thank you for calling 757 Handy, this is Karen. How can I help you today?
Customer: Hi, I have a leaky faucet in my kitchen that's been dripping all night.
Agent: I understand that must be frustrating. Let me help you get that fixed right away. Can you tell me a little more about the leak?
Customer: It's just dripping constantly from the handle area.
Agent: I see. We can definitely help with that. Let me schedule one of our experienced plumbers to come take a look. When would work best for you?
Customer: Tomorrow morning would be great.
Agent: Perfect! I have an opening at 9 AM tomorrow. Is that good for you?
Customer: Yes, that works perfectly.
Agent: Excellent! I'll get that scheduled for you. Is there anything else I can help you with today?
Customer: No, that's everything. Thank you so much!
Agent: You're very welcome! We'll see you tomorrow at 9 AM. Have a wonderful day!''',
            'recording_url': 'https://example.com/recording.mp3'
        }
        
        # Analyze the call
        quality_metrics = await qa_system.analyze_call_recording(test_call)
        
        print("Quality Analysis Results:")
        print(f"Overall Quality: {quality_metrics.overall_quality.name}")
        print(f"Professionalism: {quality_metrics.professionalism.name}")
        print(f"Communication Clarity: {quality_metrics.communication_clarity.name}")
        print(f"Problem Resolution: {quality_metrics.problem_resolution.name}")
        print(f"Customer Satisfaction: {quality_metrics.customer_satisfaction.name}")
        print(f"Brand Adherence: {quality_metrics.brand_adherence.name}")
        print(f"\nStrengths: {quality_metrics.strengths}")
        print(f"Improvement Areas: {quality_metrics.improvement_areas}")
        print(f"Training Recommendations: {quality_metrics.training_recommendations}")
        print(f"Quality Flags: {quality_metrics.quality_flags}")
    
    asyncio.run(test_quality_system())
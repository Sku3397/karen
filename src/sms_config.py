"""
SMS Configuration Management
Centralized configuration for SMS service types, response times, template selection, and priorities.
"""

import os
import logging
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

class ServiceType(Enum):
    """Service types for SMS handling"""
    PLUMBING = "plumbing"
    ELECTRICAL = "electrical"
    HVAC = "hvac"
    CARPENTRY = "carpentry"
    PAINTING = "painting"
    FLOORING = "flooring"
    ROOFING = "roofing"
    GENERAL_HANDYMAN = "general_handyman"
    APPLIANCE_REPAIR = "appliance_repair"
    TILE_WORK = "tile_work"
    DRYWALL = "drywall"
    EMERGENCY = "emergency"
    CONSULTATION = "consultation"
    QUOTE_REQUEST = "quote_request"
    SCHEDULING = "scheduling"

class MessagePriority(Enum):
    """Message priority levels"""
    EMERGENCY = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4

class ResponseTimeType(Enum):
    """Response time categories"""
    IMMEDIATE = "immediate"  # <1 minute
    URGENT = "urgent"        # <15 minutes
    STANDARD = "standard"    # <2 hours
    BUSINESS_HOURS = "business_hours"  # Next business day

@dataclass
class ServiceConfig:
    """Configuration for a specific service type"""
    service_type: ServiceType
    display_name: str
    keywords: List[str]
    default_priority: MessagePriority
    response_time: ResponseTimeType
    template_categories: List[str]
    emergency_keywords: List[str] = field(default_factory=list)
    requires_immediate_response: bool = False
    business_hours_only: bool = False
    
class SMSConfig:
    """Central SMS configuration management"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._load_configuration()
    
    def _load_configuration(self):
        """Load SMS configuration from environment and defaults"""
        
        # Response time settings (in minutes)
        self.response_times = {
            ResponseTimeType.IMMEDIATE: {
                'target_minutes': 1,
                'max_minutes': 5,
                'retry_interval': 30,  # seconds
                'escalation_after': 3   # attempts
            },
            ResponseTimeType.URGENT: {
                'target_minutes': 15,
                'max_minutes': 30,
                'retry_interval': 300,  # 5 minutes
                'escalation_after': 2
            },
            ResponseTimeType.STANDARD: {
                'target_minutes': 120,  # 2 hours
                'max_minutes': 480,     # 8 hours
                'retry_interval': 1800, # 30 minutes
                'escalation_after': 1
            },
            ResponseTimeType.BUSINESS_HOURS: {
                'target_minutes': 480,  # 8 hours
                'max_minutes': 1440,    # 24 hours
                'retry_interval': 3600, # 1 hour
                'escalation_after': 1
            }
        }
        
        # Service type mappings
        self.service_configs = {
            ServiceType.EMERGENCY: ServiceConfig(
                service_type=ServiceType.EMERGENCY,
                display_name="Emergency Service",
                keywords=["emergency", "urgent", "leak", "flood", "electrical fire", "gas leak", "no heat", "no power"],
                emergency_keywords=["emergency", "urgent", "fire", "flood", "leak", "gas", "electrical", "danger"],
                default_priority=MessagePriority.EMERGENCY,
                response_time=ResponseTimeType.IMMEDIATE,
                template_categories=["emergency"],
                requires_immediate_response=True
            ),
            
            ServiceType.PLUMBING: ServiceConfig(
                service_type=ServiceType.PLUMBING,
                display_name="Plumbing",
                keywords=["plumbing", "plumber", "leak", "pipe", "drain", "toilet", "faucet", "water", "sink", "bathroom"],
                emergency_keywords=["burst pipe", "major leak", "flooding", "no water"],
                default_priority=MessagePriority.HIGH,
                response_time=ResponseTimeType.URGENT,
                template_categories=["scheduling", "quote", "emergency"]
            ),
            
            ServiceType.ELECTRICAL: ServiceConfig(
                service_type=ServiceType.ELECTRICAL,
                display_name="Electrical",
                keywords=["electrical", "electrician", "wiring", "outlet", "switch", "breaker", "power", "lights"],
                emergency_keywords=["no power", "electrical fire", "sparking", "shock"],
                default_priority=MessagePriority.HIGH,
                response_time=ResponseTimeType.URGENT,
                template_categories=["scheduling", "quote", "emergency"]
            ),
            
            ServiceType.HVAC: ServiceConfig(
                service_type=ServiceType.HVAC,
                display_name="HVAC",
                keywords=["hvac", "heating", "cooling", "ac", "air conditioning", "furnace", "heat pump", "thermostat"],
                emergency_keywords=["no heat", "no cooling", "hvac emergency"],
                default_priority=MessagePriority.HIGH,
                response_time=ResponseTimeType.URGENT,
                template_categories=["scheduling", "quote", "emergency"]
            ),
            
            ServiceType.GENERAL_HANDYMAN: ServiceConfig(
                service_type=ServiceType.GENERAL_HANDYMAN,
                display_name="General Handyman",
                keywords=["handyman", "repair", "fix", "install", "maintenance", "general"],
                default_priority=MessagePriority.NORMAL,
                response_time=ResponseTimeType.STANDARD,
                template_categories=["scheduling", "quote", "greeting"],
                business_hours_only=True
            ),
            
            ServiceType.QUOTE_REQUEST: ServiceConfig(
                service_type=ServiceType.QUOTE_REQUEST,
                display_name="Quote Request",
                keywords=["quote", "estimate", "price", "cost", "how much", "pricing", "charge", "what.*cost", "how much.*charge"],
                default_priority=MessagePriority.NORMAL,
                response_time=ResponseTimeType.STANDARD,
                template_categories=["sales", "quote"],
                business_hours_only=True
            ),
            
            ServiceType.SCHEDULING: ServiceConfig(
                service_type=ServiceType.SCHEDULING,
                display_name="Scheduling",
                keywords=["schedule", "appointment", "book", "available", "when", "time", "appt", "confirm", "reschedule", "change.*time"],
                default_priority=MessagePriority.NORMAL,
                response_time=ResponseTimeType.STANDARD,
                template_categories=["scheduling", "automation"]
            )
        }
        
        # Template selection rules
        self.template_selection_rules = {
            'emergency': {
                'primary_template': 'emergency_response',
                'fallback_template': 'business_hours_response',
                'required_variables': ['customer_name', 'issue_type', 'eta'],
                'auto_escalate': True
            },
            'scheduling': {
                'primary_template': 'appointment_confirmation',
                'fallback_template': 'business_hours_response',
                'required_variables': ['customer_name', 'service_type', 'date', 'time'],
                'business_hours_only': False
            },
            'sales': {
                'primary_template': 'quote_response',
                'fallback_template': 'quote_delivery',
                'required_variables': ['customer_name', 'service_description'],
                'business_hours_only': True
            },
            'greeting': {
                'primary_template': 'initial_greeting',
                'fallback_template': 'test_greeting',
                'required_variables': ['customer_name'],
                'business_hours_only': False
            },
            'automation': {
                'primary_template': 'business_hours_response',
                'fallback_template': 'initial_greeting',
                'required_variables': [],
                'business_hours_only': False
            }
        }
        
        # Priority configurations
        self.priority_configs = {
            MessagePriority.EMERGENCY: {
                'escalation_chain': ['manager', 'owner', 'on_call_tech'],
                'notification_methods': ['sms', 'phone_call', 'email'],
                'max_response_time': 5,  # minutes
                'retry_count': 3,
                'auto_dispatch': True
            },
            MessagePriority.HIGH: {
                'escalation_chain': ['manager', 'supervisor'],
                'notification_methods': ['sms', 'email'],
                'max_response_time': 30,  # minutes
                'retry_count': 2,
                'auto_dispatch': False
            },
            MessagePriority.NORMAL: {
                'escalation_chain': ['customer_service'],
                'notification_methods': ['sms'],
                'max_response_time': 120,  # minutes
                'retry_count': 1,
                'auto_dispatch': False
            },
            MessagePriority.LOW: {
                'escalation_chain': ['customer_service'],
                'notification_methods': ['email'],
                'max_response_time': 1440,  # 24 hours
                'retry_count': 0,
                'auto_dispatch': False
            }
        }
        
        # Business hours configuration
        self.business_hours = {
            'monday': {'start': '08:00', 'end': '18:00'},
            'tuesday': {'start': '08:00', 'end': '18:00'},
            'wednesday': {'start': '08:00', 'end': '18:00'},
            'thursday': {'start': '08:00', 'end': '18:00'},
            'friday': {'start': '08:00', 'end': '18:00'},
            'saturday': {'start': '08:00', 'end': '16:00'},
            'sunday': {'closed': True}
        }
        
        # Twilio configuration
        self.twilio_config = {
            'phone_number': os.getenv('TWILIO_PHONE_NUMBER', '+17575551234'),
            'account_sid': os.getenv('TWILIO_ACCOUNT_SID'),
            'auth_token': os.getenv('TWILIO_AUTH_TOKEN'),
            'webhook_url': os.getenv('SMS_WEBHOOK_URL'),
            'status_callback_url': os.getenv('SMS_STATUS_CALLBACK_URL'),
            'max_message_length': 1600,
            'rate_limit_per_hour': 100,
            'rate_limit_per_day': 1000
        }
        
        self.logger.info("SMS configuration loaded successfully")
    
    def classify_service_type(self, message_content: str) -> ServiceType:
        """
        Classify the service type based on message content
        
        Args:
            message_content: The SMS message content
            
        Returns:
            ServiceType enum value
        """
        message_lower = message_content.lower()
        
        # Check for explicit emergency indicators first
        explicit_emergency_indicators = ["emergency", "urgent", "asap", "help", "911", "fire", "flooding", "danger", "crisis", "burst pipe", "major leak", "no power", "no heat"]
        has_explicit_emergency = any(indicator in message_lower for indicator in explicit_emergency_indicators)
        
        # Check for specific service type keywords (excluding emergency for now)
        keyword_scores = {}
        for service_type, config in self.service_configs.items():
            if service_type == ServiceType.EMERGENCY:
                continue  # Handle emergency separately
                
            score = 0
            for keyword in config.keywords:
                if keyword.lower() in message_lower:
                    score += 1
            
            # Add points for emergency keywords if there's explicit emergency context
            if has_explicit_emergency and config.emergency_keywords:
                for emergency_keyword in config.emergency_keywords:
                    if emergency_keyword.lower() in message_lower:
                        score += 2  # Higher weight for emergency context
            
            if score > 0:
                keyword_scores[service_type] = score
        
        # If explicit emergency indicators AND service-specific emergency keywords, classify as emergency
        if has_explicit_emergency and keyword_scores:
            # Check if any service has emergency keywords that match
            for service_type, config in self.service_configs.items():
                if service_type in keyword_scores and config.emergency_keywords:
                    for emergency_keyword in config.emergency_keywords:
                        if emergency_keyword.lower() in message_lower:
                            return ServiceType.EMERGENCY
        
        # Otherwise, return highest scoring service type
        if keyword_scores:
            return max(keyword_scores.items(), key=lambda x: x[1])[0]
        
        # If only explicit emergency words without service context
        if has_explicit_emergency:
            return ServiceType.EMERGENCY
        
        # Default to general handyman if no specific keywords found
        return ServiceType.GENERAL_HANDYMAN
    
    def get_priority_for_service(self, service_type: ServiceType, 
                                message_content: str = "") -> MessagePriority:
        """
        Determine message priority based on service type and content
        
        Args:
            service_type: The classified service type
            message_content: Optional message content for emergency detection
            
        Returns:
            MessagePriority enum value
        """
        # Check for emergency keywords in any message
        if message_content:
            message_lower = message_content.lower()
            emergency_indicators = ["emergency", "urgent", "asap", "help", "911", "fire", "flood", "danger"]
            if any(indicator in message_lower for indicator in emergency_indicators):
                return MessagePriority.EMERGENCY
        
        # Return default priority for service type
        config = self.service_configs.get(service_type)
        return config.default_priority if config else MessagePriority.NORMAL
    
    def get_response_time_config(self, service_type: ServiceType) -> Dict[str, Any]:
        """
        Get response time configuration for a service type
        
        Args:
            service_type: The service type
            
        Returns:
            Response time configuration dictionary
        """
        config = self.service_configs.get(service_type)
        if not config:
            return self.response_times[ResponseTimeType.STANDARD]
        
        return self.response_times[config.response_time]
    
    def get_template_for_service(self, service_type: ServiceType, 
                                intent: str = "general") -> Dict[str, Any]:
        """
        Get appropriate template configuration for service type and intent
        
        Args:
            service_type: The service type
            intent: The message intent (emergency, scheduling, sales, etc.)
            
        Returns:
            Template configuration dictionary
        """
        config = self.service_configs.get(service_type)
        if not config:
            return self.template_selection_rules.get('automation', {})
        
        # Find matching template category
        for category in config.template_categories:
            if category == intent or (intent == "general" and category in ["greeting", "automation"]):
                return self.template_selection_rules.get(category, {})
        
        # Fallback to first available category
        if config.template_categories:
            return self.template_selection_rules.get(config.template_categories[0], {})
        
        return self.template_selection_rules.get('automation', {})
    
    def get_escalation_config(self, priority: MessagePriority) -> Dict[str, Any]:
        """
        Get escalation configuration for a message priority
        
        Args:
            priority: The message priority
            
        Returns:
            Escalation configuration dictionary
        """
        return self.priority_configs.get(priority, self.priority_configs[MessagePriority.NORMAL])
    
    def is_business_hours(self, day_of_week: str, current_time: str) -> bool:
        """
        Check if current time is within business hours
        
        Args:
            day_of_week: Day name (e.g., 'monday', 'tuesday')
            current_time: Time in HH:MM format
            
        Returns:
            True if within business hours, False otherwise
        """
        day_config = self.business_hours.get(day_of_week.lower())
        if not day_config or day_config.get('closed'):
            return False
        
        start_time = day_config.get('start', '08:00')
        end_time = day_config.get('end', '18:00')
        
        return start_time <= current_time <= end_time
    
    def should_auto_respond(self, service_type: ServiceType, priority: MessagePriority) -> bool:
        """
        Determine if message should trigger automatic response
        
        Args:
            service_type: The service type
            priority: The message priority
            
        Returns:
            True if auto-response should be sent
        """
        # Always auto-respond to emergencies
        if priority == MessagePriority.EMERGENCY:
            return True
        
        # Check service configuration
        config = self.service_configs.get(service_type)
        if config and config.requires_immediate_response:
            return True
        
        # Auto-respond during business hours for high priority
        if priority == MessagePriority.HIGH:
            return True
        
        return False
    
    def get_rate_limit_config(self) -> Dict[str, int]:
        """Get SMS rate limiting configuration"""
        return {
            'max_per_hour': self.twilio_config.get('rate_limit_per_hour', 100),
            'max_per_day': self.twilio_config.get('rate_limit_per_day', 1000),
            'max_message_length': self.twilio_config.get('max_message_length', 1600)
        }
    
    def get_twilio_config(self) -> Dict[str, str]:
        """Get Twilio configuration"""
        return {
            'phone_number': self.twilio_config.get('phone_number'),
            'account_sid': self.twilio_config.get('account_sid'),
            'auth_token': self.twilio_config.get('auth_token'),
            'webhook_url': self.twilio_config.get('webhook_url'),
            'status_callback_url': self.twilio_config.get('status_callback_url')
        }
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate SMS configuration completeness
        
        Returns:
            Validation results dictionary
        """
        results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check required Twilio configuration
        required_twilio = ['phone_number', 'account_sid', 'auth_token']
        for key in required_twilio:
            if not self.twilio_config.get(key):
                results['errors'].append(f"Missing required Twilio configuration: {key}")
                results['valid'] = False
        
        # Check service configurations
        if not self.service_configs:
            results['errors'].append("No service configurations defined")
            results['valid'] = False
        
        # Check template selection rules
        if not self.template_selection_rules:
            results['warnings'].append("No template selection rules defined")
        
        # Check business hours
        if not self.business_hours:
            results['warnings'].append("No business hours configured")
        
        return results

# Global SMS configuration instance
sms_config = SMSConfig()

# Convenience functions for common operations
def classify_sms_service(message: str) -> ServiceType:
    """Classify service type from SMS content"""
    return sms_config.classify_service_type(message)

def get_sms_priority(service_type: ServiceType, message: str = "") -> MessagePriority:
    """Get priority for SMS based on service and content"""
    return sms_config.get_priority_for_service(service_type, message)

def get_sms_response_time(service_type: ServiceType) -> Dict[str, Any]:
    """Get response time config for service type"""
    return sms_config.get_response_time_config(service_type)

def should_auto_respond_sms(service_type: ServiceType, priority: MessagePriority) -> bool:
    """Check if SMS should trigger auto-response"""
    return sms_config.should_auto_respond(service_type, priority)
# Define Pydantic models for Firestore collections
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum

# Enums for constrained values
class CustomerType(str, Enum):
    INDIVIDUAL = "individual"
    BUSINESS = "business"
    PROPERTY_MANAGER = "property_manager"

class CustomerStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PROSPECT = "prospect"

class CustomerTier(str, Enum):
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"
    VIP = "vip"

class ContactMethod(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PHONE = "phone"
    VOICE = "voice"

class MessageDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"

class ConversationMedium(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    VOICE = "voice"
    CHAT = "chat"

class ServiceType(str, Enum):
    REPAIR = "repair"
    INSTALLATION = "installation"
    MAINTENANCE = "maintenance"
    INSPECTION = "inspection"
    CONSULTATION = "consultation"

class ComplexityLevel(str, Enum):
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class PricingType(str, Enum):
    FIXED = "fixed"
    HOURLY = "hourly"
    FIXED_BASE_PLUS_MATERIALS = "fixed_base_plus_materials"
    HOURLY_PLUS_MATERIALS = "hourly_plus_materials"
    CUSTOM_QUOTE = "custom_quote"

# Address Model
class Address(BaseModel):
    street: str
    city: str
    state: str
    zip_code: str
    country: str = "USA"
    apartment: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

# Customer Models
class Customer(BaseModel):
    id: str
    external_id: Optional[str] = None
    first_name: str
    last_name: str
    company_name: Optional[str] = None
    customer_type: CustomerType
    
    # Contact Information
    primary_email: str
    primary_phone: str
    secondary_email: Optional[str] = None
    secondary_phone: Optional[str] = None
    
    # Addresses
    billing_address: Address
    service_address: Address
    
    # Status and Preferences
    status: CustomerStatus
    customer_tier: CustomerTier
    preferred_contact_method: ContactMethod
    preferred_contact_time: str
    communication_style: str
    
    # Business Data
    referral_source: Optional[str] = None
    customer_since: str
    lifetime_value: float = 0.0
    total_jobs: int = 0
    
    # Metadata
    notes: Optional[str] = None
    tags: List[str] = []
    metadata: Dict[str, Any] = {}
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    last_contact_at: Optional[datetime] = None

class CustomerPreference(BaseModel):
    id: str
    customer_id: str
    preference_type: str  # communication_method, scheduling, service, communication_style
    preference_key: str
    preference_value: Dict[str, Any]
    confidence_score: float = Field(ge=0.0, le=1.0)
    source: str  # learned, explicit, inferred
    medium: str  # email, sms, voice, general
    context: Dict[str, Any] = {}
    learned_from_interaction_id: Optional[str] = None
    learned_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool = True
    priority: int = 1
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str

# Conversation Models
class ConversationMessage(BaseModel):
    id: str
    customer_id: str
    conversation_thread_id: str
    external_id: Optional[str] = None
    
    # Message Content
    medium: ConversationMedium
    direction: MessageDirection
    subject: Optional[str] = None
    content: str
    content_type: str = "text/plain"
    raw_content: Dict[str, Any] = {}
    
    # Contact Information
    from_address: str
    to_address: str
    cc_addresses: List[str] = []
    phone_number: Optional[str] = None
    
    # Processing Status
    status: str  # received, processing, processed, sent, failed
    processing_stage: str
    
    # NLP Analysis
    nlp_analysis: Dict[str, Any] = {}
    
    # Response Information
    response_id: Optional[str] = None
    response_to_id: Optional[str] = None
    response_template_used: Optional[str] = None
    response_generated_at: Optional[datetime] = None
    response_method: Optional[str] = None
    
    # Timing
    message_timestamp: datetime
    received_at: datetime
    processed_at: Optional[datetime] = None
    
    # Metadata
    metadata: Dict[str, Any] = {}
    agent_id: Optional[str] = None
    session_id: Optional[str] = None
    
    created_at: datetime
    updated_at: datetime

class ConversationAttachment(BaseModel):
    id: str
    conversation_id: str
    file_name: str
    file_type: str
    file_size: int
    storage_path: str
    content_id: Optional[str] = None
    is_inline: bool = False
    checksum: Optional[str] = None
    virus_scan_status: str = "pending"
    virus_scan_result: Dict[str, Any] = {}
    created_at: datetime

class ConversationThread(BaseModel):
    thread_id: str
    customer_id: str
    primary_medium: ConversationMedium
    conversation_ids: List[str]
    status: str  # active, closed, archived
    last_message_at: datetime
    total_messages: int
    awaiting_response: bool
    escalated_to_sms: Optional[bool] = None
    escalation_thread_id: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime

class CrossMediumLink(BaseModel):
    customer_id: str
    linked_conversations: List[Dict[str, Any]]
    link_type: str  # escalation, follow_up, continuation
    link_reason: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    detected_by: str  # nlp_analysis, manual, rule_based
    context: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime

# Service Catalog Models
class ServiceCategory(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    color: str
    display_order: int
    is_active: bool = True
    requires_license: bool = False
    emergency_available: bool = False
    typical_duration_range: Dict[str, int]  # min, max in minutes
    created_at: datetime
    updated_at: datetime

class PricingTier(BaseModel):
    name: str
    price: float
    includes: List[str]
    excludes: List[str] = []

class ServiceAvailability(BaseModel):
    standard_hours: Dict[str, Optional[Dict[str, str]]]  # day -> {start, end} or None
    emergency_available: bool = False
    emergency_hours: Optional[str] = None
    emergency_surcharge: float = 0.0
    same_day_available: bool = False
    same_day_surcharge: float = 0.0
    booking_lead_time_hours: int = 2

class ServiceRequirements(BaseModel):
    tools_required: List[str]
    materials_commonly_needed: List[str]
    skill_level_required: ComplexityLevel
    license_required: bool = False
    insurance_coverage: str
    safety_equipment: List[str] = []

class ServiceFeatures(BaseModel):
    warranty_period_days: int = 30
    parts_warranty_days: int = 90
    follow_up_included: bool = True
    photo_documentation: bool = False
    before_after_photos: bool = False
    customer_approval_required: bool = False
    estimate_required_above: Optional[float] = None
    permit_required: bool = False

class Service(BaseModel):
    id: str
    category_id: str
    name: str
    short_description: str
    detailed_description: str
    service_type: ServiceType
    complexity_level: ComplexityLevel
    
    # Duration
    estimated_duration_minutes: int
    duration_range: Dict[str, int]  # min, max
    
    # Pricing
    base_price: float
    hourly_rate: Optional[float] = None
    materials_markup: float = 0.0
    pricing_type: PricingType
    pricing_tiers: Dict[str, PricingTier] = {}
    
    # Availability
    availability: ServiceAvailability
    
    # Requirements
    requirements: ServiceRequirements
    
    # Features
    features: ServiceFeatures
    
    # SEO and Marketing
    seo_keywords: List[str] = []
    popular_keywords: List[str] = []
    seasonal_demand: Dict[str, str] = {}  # season -> demand_level
    
    # Status
    status: str = "active"
    is_featured: bool = False
    display_order: int = 999
    last_price_update: datetime
    
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str

class SeasonalPricing(BaseModel):
    id: str
    name: str
    service_category_ids: List[str]
    season: str
    months: List[int]
    price_multiplier: float
    is_active: bool = True
    start_date: str
    end_date: str
    description: str
    created_at: datetime

class ServicePackage(BaseModel):
    id: str
    name: str
    description: str
    service_ids: List[str]
    package_price: float
    individual_price_total: float
    savings_amount: float
    savings_percentage: float
    estimated_duration_minutes: int
    is_active: bool = True
    package_type: str  # maintenance, installation, repair_bundle
    features: Dict[str, Any] = {}
    created_at: datetime

# Analytics Models
class CustomerAnalytics(BaseModel):
    customer_id: str
    type: str
    period: str
    data: Dict[str, Any]
    calculated_at: datetime
    metadata: Dict[str, Any] = {}

class ConversationAnalytics(BaseModel):
    customer_id: str
    type: str
    period: str
    data: Dict[str, Any]
    calculated_at: datetime
    metadata: Dict[str, Any] = {}

class ServiceAnalytics(BaseModel):
    type: str
    data: Dict[str, Any]
    calculated_at: datetime
    metadata: Dict[str, Any] = {}

# Legacy Models (maintained for compatibility)
class User(BaseModel):
    id: str
    name: str
    email: str

class Procedure(BaseModel):
    id: str
    name: str
    description: str
    estimated_time_minutes: int
    required_tools: List[str]
    price: float

class FAQ(BaseModel):
    id: str
    question: str
    answer: str
    category: str = "general"

class ClientHistory(BaseModel):
    client_id: str
    interactions: List[Dict[str, Any]]

class Pricing(BaseModel):
    service_id: str
    base_price: float
    hourly_rate: float

# Define other models following the same structure for tasks, appointments, etc.
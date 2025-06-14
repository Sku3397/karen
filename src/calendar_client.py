# src/calendar_client.py - Enhanced calendar client with intelligent scheduling
import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
import re
import requests
from dataclasses import dataclass, field
from enum import Enum

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleAuthRequest
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import google.auth.exceptions

# Import enhanced OAuth token manager
from .token_manager import get_credentials_with_auto_refresh

# Google Calendar API scopes
CALENDAR_SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events'
]

logger = logging.getLogger(__name__)

@dataclass
class TimeSlot:
    """Represents a time slot with start and end times"""
    start: datetime
    end: datetime
    
    def overlaps_with(self, other: 'TimeSlot') -> bool:
        """Check if this time slot overlaps with another"""
        return self.start < other.end and self.end > other.start
    
    def duration_minutes(self) -> int:
        """Get duration in minutes"""
        return int((self.end - self.start).total_seconds() / 60)

class AppointmentPriority(Enum):
    """Priority levels for appointments"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    EMERGENCY = 5

class AppointmentUrgency(Enum):
    """Urgency levels for scheduling"""
    FLEXIBLE = "flexible"  # Can be scheduled weeks out
    PREFERRED = "preferred"  # Should be within preferred timeframe
    URGENT = "urgent"  # Needs to be within 2-3 days
    EMERGENCY = "emergency"  # Same day if possible

@dataclass
class ServiceType:
    """Represents a service type with duration and buffer requirements"""
    name: str
    duration_minutes: int
    buffer_before_minutes: int = 15
    buffer_after_minutes: int = 15
    travel_time_minutes: int = 0
    priority: AppointmentPriority = AppointmentPriority.NORMAL
    urgency: AppointmentUrgency = AppointmentUrgency.PREFERRED
    keywords: List[str] = field(default_factory=list)

# Enhanced service types for handyman services with priority and keywords
DEFAULT_SERVICE_TYPES = {
    'consultation': ServiceType(
        'Consultation', 30, 10, 10,
        priority=AppointmentPriority.NORMAL,
        urgency=AppointmentUrgency.FLEXIBLE,
        keywords=['consult', 'discuss', 'plan', 'advice', 'meeting', 'talk']
    ),
    'repair': ServiceType(
        'Repair', 120, 15, 15,
        priority=AppointmentPriority.HIGH,
        urgency=AppointmentUrgency.URGENT,
        keywords=['repair', 'fix', 'broken', 'replace', 'restore', 'mend']
    ),
    'installation': ServiceType(
        'Installation', 180, 30, 15,
        priority=AppointmentPriority.NORMAL,
        urgency=AppointmentUrgency.PREFERRED,
        keywords=['install', 'installation', 'mount', 'setup', 'assemble', 'put in']
    ),
    'maintenance': ServiceType(
        'Maintenance', 90, 15, 15,
        priority=AppointmentPriority.NORMAL,
        urgency=AppointmentUrgency.FLEXIBLE,
        keywords=['maintenance', 'service', 'clean', 'tune', 'upkeep', 'check up']
    ),
    'inspection': ServiceType(
        'Inspection', 60, 10, 10,
        priority=AppointmentPriority.LOW,
        urgency=AppointmentUrgency.FLEXIBLE,
        keywords=['inspect', 'check', 'look', 'assess', 'examine', 'evaluate']
    ),
    'estimate': ServiceType(
        'Estimate', 45, 15, 10,
        priority=AppointmentPriority.LOW,
        urgency=AppointmentUrgency.FLEXIBLE,
        keywords=['estimate', 'quote', 'pricing', 'cost', 'bid', 'proposal']
    ),
    'emergency': ServiceType(
        'Emergency', 60, 5, 5,
        priority=AppointmentPriority.EMERGENCY,
        urgency=AppointmentUrgency.EMERGENCY,
        keywords=['emergency', 'urgent', 'leak', 'broken', 'flooding', 'no heat', 'no power']
    ),
    'plumbing': ServiceType(
        'Plumbing', 90, 15, 15,
        priority=AppointmentPriority.HIGH,
        urgency=AppointmentUrgency.URGENT,
        keywords=['plumbing', 'pipe', 'faucet', 'toilet', 'drain', 'water', 'sink']
    ),
    'electrical': ServiceType(
        'Electrical', 120, 20, 15,
        priority=AppointmentPriority.HIGH,
        urgency=AppointmentUrgency.URGENT,
        keywords=['electrical', 'electric', 'outlet', 'switch', 'wiring', 'breaker', 'power']
    ),
    'hvac': ServiceType(
        'HVAC', 150, 20, 15,
        priority=AppointmentPriority.HIGH,
        urgency=AppointmentUrgency.URGENT,
        keywords=['hvac', 'heating', 'cooling', 'air conditioning', 'furnace', 'ac', 'heat pump']
    ),
    'default': ServiceType(
        'General Service', 60, 15, 15,
        priority=AppointmentPriority.NORMAL,
        urgency=AppointmentUrgency.PREFERRED,
        keywords=[]
    )
}

class CalendarClient:
    def __init__(self, email_address: str, token_path: str = None, credentials_path: str = None):
        """
        Initialize CalendarClient with secure OAuth token management
        
        Args:
            email_address: Email address for calendar access
            token_path: Legacy parameter, ignored (for backward compatibility)
            credentials_path: Legacy parameter, ignored (for backward compatibility)
        """
        self.email_address = email_address
        
        # Legacy compatibility warnings
        if token_path:
            logger.warning(f"token_path parameter is deprecated. Using secure token manager instead.")
        if credentials_path:
            logger.warning(f"credentials_path parameter is deprecated. Using secure token manager instead.")
        
        logger.info(f"Initializing secure CalendarClient for {email_address}")
        
        # Use secure token manager for credentials
        self.creds = self._get_secure_credentials()
        
        if not self.creds:
            msg = f"Failed to obtain secure OAuth credentials for calendar access: {email_address}"
            logger.error(msg)
            raise ValueError(msg)
        
        try:
            self.service = build('calendar', 'v3', credentials=self.creds)
            logger.info(f"Secure Google Calendar service built successfully for {email_address}")
        except Exception as e:
            logger.error(f"Failed to build Google Calendar service for {email_address}: {e}", exc_info=True)
            raise

    def _get_secure_credentials(self) -> Optional[Credentials]:
        """Get secure OAuth credentials using the enhanced token manager"""
        try:
            logger.debug(f"Requesting secure calendar credentials for {self.email_address}")
            
            # Use the enhanced token manager with automatic refresh
            creds = get_credentials_with_auto_refresh('calendar', self.email_address)
            
            if creds and creds.valid:
                logger.info(f"Secure calendar credentials obtained for {self.email_address}")
                return creds
            else:
                logger.error(f"Failed to obtain valid secure calendar credentials for {self.email_address}")
                return None
                
        except Exception as e:
            logger.error(f"Error obtaining secure calendar credentials for {self.email_address}: {e}", exc_info=True)
            return None
    
    def refresh_credentials(self) -> bool:
        """Refresh credentials using the enhanced token manager"""
        try:
            logger.info(f"Refreshing calendar credentials for {self.email_address}")
            
            # Get fresh credentials from enhanced token manager
            new_creds = get_credentials_with_auto_refresh('calendar', self.email_address)
            
            if new_creds and new_creds.valid:
                self.creds = new_creds
                # Rebuild service with new credentials
                self.service = build('calendar', 'v3', credentials=self.creds)
                logger.info(f"Calendar credentials refreshed successfully for {self.email_address}")
                return True
            else:
                logger.error(f"Failed to refresh calendar credentials for {self.email_address}")
                return False
                
        except Exception as e:
            logger.error(f"Error refreshing calendar credentials for {self.email_address}: {e}", exc_info=True)
            return False
    
    def _ensure_valid_credentials(self) -> bool:
        """Ensure credentials are valid, refresh if necessary"""
        if not self.creds or not self.creds.valid:
            logger.warning(f"Invalid calendar credentials detected for {self.email_address}, attempting refresh")
            return self.refresh_credentials()
        return True
    
    def estimate_service_duration(self, service_description: str) -> ServiceType:
        """Enhanced service duration estimation based on description with priority scoring"""
        description_lower = service_description.lower()
        
        # Score each service type based on keyword matches
        service_scores = {}
        for service_key, service_type in DEFAULT_SERVICE_TYPES.items():
            if service_key == 'default':
                continue
            
            score = 0
            for keyword in service_type.keywords:
                if keyword in description_lower:
                    # Give higher scores for exact matches and emergency terms
                    if service_type.priority == AppointmentPriority.EMERGENCY:
                        score += 10
                    elif service_type.priority == AppointmentPriority.HIGH:
                        score += 5
                    else:
                        score += 2
            
            if score > 0:
                service_scores[service_key] = score
        
        # Return the service type with the highest score
        if service_scores:
            best_service = max(service_scores.items(), key=lambda x: x[1])
            logger.info(f"Service classification: '{description_lower}' -> {best_service[0]} (score: {best_service[1]})")
            return DEFAULT_SERVICE_TYPES[best_service[0]]
        
        # Fallback to original logic for backward compatibility
        emergency_keywords = ['emergency', 'urgent', 'leak', 'broken', 'flooding', 'no heat', 'no power']
        if any(word in description_lower for word in emergency_keywords):
            return DEFAULT_SERVICE_TYPES['emergency']
        
        return DEFAULT_SERVICE_TYPES['default']
    
    def calculate_travel_time(self, from_address: Optional[str], to_address: Optional[str]) -> int:
        """Calculate travel time between addresses in minutes with enhanced logic"""
        if not from_address or not to_address:
            return 0
        
        try:
            # Check for Google Maps API key for accurate travel times
            google_maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
            if google_maps_api_key:
                return self._calculate_travel_time_google_maps(from_address, to_address, google_maps_api_key)
            
            # Fallback to heuristic-based calculation
            return self._calculate_travel_time_heuristic(from_address, to_address)
                
        except Exception as e:
            logger.warning(f"Error calculating travel time: {e}")
            return 20  # Default travel time
    
    def _calculate_travel_time_google_maps(self, from_address: str, to_address: str, api_key: str) -> int:
        """Calculate travel time using Google Maps Distance Matrix API"""
        try:
            base_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
            params = {
                'origins': from_address,
                'destinations': to_address,
                'mode': 'driving',
                'units': 'imperial',
                'departure_time': 'now',
                'traffic_model': 'best_guess',
                'key': api_key
            }
            
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK' and data['rows']:
                element = data['rows'][0]['elements'][0]
                if element['status'] == 'OK':
                    # Get duration in traffic if available, otherwise regular duration
                    duration_key = 'duration_in_traffic' if 'duration_in_traffic' in element else 'duration'
                    travel_seconds = element[duration_key]['value']
                    travel_minutes = max(5, int(travel_seconds / 60))  # Minimum 5 minutes
                    
                    logger.info(f"Google Maps travel time: {from_address} -> {to_address}: {travel_minutes} minutes")
                    return travel_minutes
            
            logger.warning(f"Google Maps API returned no results for {from_address} -> {to_address}")
            return self._calculate_travel_time_heuristic(from_address, to_address)
            
        except requests.RequestException as e:
            logger.warning(f"Google Maps API request failed: {e}")
            return self._calculate_travel_time_heuristic(from_address, to_address)
        except Exception as e:
            logger.warning(f"Error with Google Maps travel time calculation: {e}")
            return self._calculate_travel_time_heuristic(from_address, to_address)
    
    def _calculate_travel_time_heuristic(self, from_address: str, to_address: str) -> int:
        """Calculate travel time using heuristic-based approach"""
        # Extract zip codes or city names for rough distance estimation
        from_zip = self._extract_zip_code(from_address)
        to_zip = self._extract_zip_code(to_address)
        
        # Extract city/state for additional context
        from_city = self._extract_city_state(from_address)
        to_city = self._extract_city_state(to_address)
        
        if from_zip and to_zip:
            if from_zip == to_zip:
                # Same zip code - local travel
                return 15
            else:
                # Different zip codes - calculate based on zip code distance
                zip_distance = self._estimate_zip_distance(from_zip, to_zip)
                if zip_distance <= 5:
                    return 20  # Nearby zip codes
                elif zip_distance <= 15:
                    return 35  # Moderate distance
                else:
                    return 50  # Longer distance
        
        elif from_city and to_city:
            if from_city == to_city:
                # Same city - moderate travel time
                return 25
            else:
                # Different cities - longer travel time
                return 45
        
        else:
            # Default travel time when we can't parse addresses
            return 20
    
    def _extract_zip_code(self, address: str) -> Optional[str]:
        """Extract zip code from address string"""
        zip_pattern = r'\b\d{5}(?:-\d{4})?\b'
        match = re.search(zip_pattern, address)
        return match.group() if match else None
    
    def _extract_city_state(self, address: str) -> Optional[str]:
        """Extract city and state from address string"""
        # Common patterns for city, state
        patterns = [
            r'([A-Za-z\s]+),\s*([A-Z]{2})\s*\d{5}',  # City, ST 12345
            r'([A-Za-z\s]+),\s*([A-Za-z\s]+)\s*\d{5}',  # City, State 12345
        ]
        
        for pattern in patterns:
            match = re.search(pattern, address)
            if match:
                city = match.group(1).strip()
                state = match.group(2).strip()
                return f"{city}, {state}"
        
        return None
    
    def _estimate_zip_distance(self, zip1: str, zip2: str) -> int:
        """Estimate distance between zip codes (rough approximation)"""
        try:
            # Simple heuristic: assume each zip code digit difference represents ~5 miles
            zip1_num = int(zip1[:5])
            zip2_num = int(zip2[:5])
            
            # Calculate rough distance based on zip code numerical difference
            zip_diff = abs(zip1_num - zip2_num)
            
            if zip_diff < 10:
                return 5  # Very close
            elif zip_diff < 100:
                return 10  # Nearby
            elif zip_diff < 1000:
                return 25  # Moderate distance
            else:
                return 50  # Far apart
        
        except (ValueError, TypeError):
            return 20  # Default distance if parsing fails
    
    def detect_conflicts(self, proposed_start: datetime, proposed_end: datetime, 
                        calendar_id: str = 'primary', buffer_minutes: int = 15) -> List[Dict[str, Any]]:
        """Detect scheduling conflicts for a proposed appointment"""
        if not self._ensure_valid_credentials():
            logger.error("Failed to ensure valid credentials for conflict detection.")
            return []
        
        # Expand search window to include buffer time
        search_start = proposed_start - timedelta(minutes=buffer_minutes)
        search_end = proposed_end + timedelta(minutes=buffer_minutes)
        
        start_iso = search_start.isoformat() + 'Z'
        end_iso = search_end.isoformat() + 'Z'
        
        busy_slots = self.get_availability(start_iso, end_iso, calendar_id)
        if busy_slots is None:
            logger.error("Failed to get availability for conflict detection")
            return []
        
        proposed_slot = TimeSlot(proposed_start, proposed_end)
        conflicts = []
        
        for busy_slot in busy_slots:
            try:
                busy_start = datetime.fromisoformat(busy_slot['start'].replace('Z', '+00:00'))
                busy_end = datetime.fromisoformat(busy_slot['end'].replace('Z', '+00:00'))
                busy_time_slot = TimeSlot(busy_start, busy_end)
                
                if proposed_slot.overlaps_with(busy_time_slot):
                    conflicts.append({
                        'start': busy_slot['start'],
                        'end': busy_slot['end'],
                        'duration_minutes': busy_time_slot.duration_minutes(),
                        'overlap_type': self._determine_overlap_type(proposed_slot, busy_time_slot)
                    })
                    
            except Exception as e:
                logger.warning(f"Error processing busy slot for conflict detection: {e}")
                continue
        
        logger.info(f"Found {len(conflicts)} conflicts for proposed time {proposed_start} - {proposed_end}")
        return conflicts
    
    def _determine_overlap_type(self, proposed: TimeSlot, existing: TimeSlot) -> str:
        """Determine the type of overlap between two time slots"""
        if proposed.start >= existing.start and proposed.end <= existing.end:
            return 'complete_overlap'  # Proposed is completely within existing
        elif existing.start >= proposed.start and existing.end <= proposed.end:
            return 'contains_existing'  # Proposed contains the existing event
        elif proposed.start < existing.start < proposed.end:
            return 'partial_end_overlap'  # Proposed overlaps the start of existing
        elif proposed.start < existing.end < proposed.end:
            return 'partial_start_overlap'  # Proposed overlaps the end of existing
        else:
            return 'adjacent'  # Events are adjacent (within buffer time)
    
    def suggest_alternative_slots(self, preferred_start: datetime, duration_minutes: int,
                                 search_days: int = 7, calendar_id: str = 'primary',
                                 business_hours_start: int = 8, business_hours_end: int = 17,
                                 buffer_minutes: int = 15, urgency: AppointmentUrgency = AppointmentUrgency.PREFERRED,
                                 priority: AppointmentPriority = AppointmentPriority.NORMAL) -> List[Dict[str, Any]]:
        """Suggest alternative time slots when the preferred time has conflicts
        
        Args:
            preferred_start: Preferred appointment start time
            duration_minutes: Duration of appointment in minutes
            search_days: Number of days to search for alternatives
            calendar_id: Calendar to check for conflicts
            business_hours_start: Start of business hours (24-hour format)
            business_hours_end: End of business hours (24-hour format)
            buffer_minutes: Buffer time around appointments
            urgency: Urgency level affecting search parameters
            priority: Priority level affecting slot selection
        """
        suggestions = []
        
        # Adjust search parameters based on urgency
        if urgency == AppointmentUrgency.EMERGENCY:
            search_days = min(1, search_days)  # Same day only
            business_hours_start = 7  # Extended hours for emergency
            business_hours_end = 19
        elif urgency == AppointmentUrgency.URGENT:
            search_days = min(3, search_days)  # Within 3 days
            business_hours_start = 7  # Slightly extended hours
            business_hours_end = 18
        elif urgency == AppointmentUrgency.FLEXIBLE:
            search_days = max(14, search_days)  # Extended search for flexible appointments
        
        # Get busy periods for the search window
        search_start = preferred_start.replace(hour=0, minute=0, second=0, microsecond=0)
        search_end = search_start + timedelta(days=search_days)
        
        start_iso = search_start.isoformat() + 'Z'
        end_iso = search_end.isoformat() + 'Z'
        
        busy_slots = self.get_availability(start_iso, end_iso, calendar_id)
        if busy_slots is None:
            logger.error("Failed to get availability for alternative slot suggestions")
            return []
        
        # Convert busy slots to TimeSlot objects
        busy_periods = []
        for slot in busy_slots:
            try:
                start_dt = datetime.fromisoformat(slot['start'].replace('Z', '+00:00')).replace(tzinfo=None)
                end_dt = datetime.fromisoformat(slot['end'].replace('Z', '+00:00')).replace(tzinfo=None)
                busy_periods.append(TimeSlot(start_dt, end_dt))
            except Exception as e:
                logger.warning(f"Error parsing busy slot: {e}")
                continue
        
        # Sort busy periods by start time
        busy_periods.sort(key=lambda x: x.start)
        
        # Find free slots
        current_day = preferred_start.date()
        for day_offset in range(search_days):
            check_date = current_day + timedelta(days=day_offset)
            
            # Skip weekends for business appointments unless emergency/urgent
            if check_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                if urgency not in [AppointmentUrgency.EMERGENCY, AppointmentUrgency.URGENT]:
                    continue
                # For emergency/urgent, allow limited weekend hours
                if check_date.weekday() == 5:  # Saturday
                    business_hours_start = 9
                    business_hours_end = 15
                else:  # Sunday
                    business_hours_start = 10
                    business_hours_end = 14
            
            # Check time slots throughout the business day
            day_start = datetime.combine(check_date, datetime.min.time().replace(hour=business_hours_start))
            day_end = datetime.combine(check_date, datetime.min.time().replace(hour=business_hours_end))
            
            # Generate 30-minute intervals throughout the day
            current_time = day_start
            while current_time + timedelta(minutes=duration_minutes + buffer_minutes) <= day_end:
                proposed_end = current_time + timedelta(minutes=duration_minutes)
                proposed_slot = TimeSlot(current_time, proposed_end)
                
                # Check if this slot conflicts with any busy period
                has_conflict = False
                for busy_period in busy_periods:
                    # Add buffer time to busy periods
                    buffered_busy = TimeSlot(
                        busy_period.start - timedelta(minutes=buffer_minutes),
                        busy_period.end + timedelta(minutes=buffer_minutes)
                    )
                    if proposed_slot.overlaps_with(buffered_busy):
                        has_conflict = True
                        break
                
                if not has_conflict:
                    # Calculate priority score (closer to preferred time = higher score)
                    time_diff = abs((current_time - preferred_start).total_seconds())
                    base_score = max(0, 100 - (time_diff / 3600))  # Decrease by 1 point per hour
                    
                    # Adjust score based on urgency and priority
                    urgency_multiplier = {
                        AppointmentUrgency.EMERGENCY: 2.0,
                        AppointmentUrgency.URGENT: 1.5,
                        AppointmentUrgency.PREFERRED: 1.0,
                        AppointmentUrgency.FLEXIBLE: 0.8
                    }.get(urgency, 1.0)
                    
                    priority_bonus = {
                        AppointmentPriority.EMERGENCY: 50,
                        AppointmentPriority.HIGH: 20,
                        AppointmentPriority.NORMAL: 0,
                        AppointmentPriority.LOW: -10
                    }.get(priority, 0)
                    
                    final_score = (base_score * urgency_multiplier) + priority_bonus
                    
                    # Bonus for same day (emergency/urgent preference)
                    if current_time.date() == preferred_start.date() and urgency in [AppointmentUrgency.EMERGENCY, AppointmentUrgency.URGENT]:
                        final_score += 30
                    
                    suggestions.append({
                        'start': current_time.isoformat() + 'Z',
                        'end': proposed_end.isoformat() + 'Z',
                        'duration_minutes': duration_minutes,
                        'priority_score': final_score,
                        'day_of_week': check_date.strftime('%A'),
                        'time_difference_hours': round(time_diff / 3600, 1),
                        'urgency_level': urgency.value,
                        'priority_level': priority.name
                    })
                    
                    # Stop after finding enough suggestions (more for emergency/urgent)
                    max_suggestions = {
                        AppointmentUrgency.EMERGENCY: 15,
                        AppointmentUrgency.URGENT: 12,
                        AppointmentUrgency.PREFERRED: 10,
                        AppointmentUrgency.FLEXIBLE: 8
                    }.get(urgency, 10)
                    
                    if len(suggestions) >= max_suggestions:
                        break
                
                # Move to next 30-minute slot
                current_time += timedelta(minutes=30)
            
            max_suggestions = {
                AppointmentUrgency.EMERGENCY: 15,
                AppointmentUrgency.URGENT: 12,
                AppointmentUrgency.PREFERRED: 10,
                AppointmentUrgency.FLEXIBLE: 8
            }.get(urgency, 10)
            
            if len(suggestions) >= max_suggestions:
                break
        
        # Sort suggestions by priority score (highest first)
        suggestions.sort(key=lambda x: x['priority_score'], reverse=True)
        
        # Return different numbers of suggestions based on urgency
        return_count = {
            AppointmentUrgency.EMERGENCY: 8,
            AppointmentUrgency.URGENT: 6,
            AppointmentUrgency.PREFERRED: 5,
            AppointmentUrgency.FLEXIBLE: 4
        }.get(urgency, 5)
        
        logger.info(f"Generated {len(suggestions)} alternative time slot suggestions for {urgency.value} urgency")
        return suggestions[:return_count]
    
    def find_optimal_slot(self, service_description: str, preferred_start: datetime,
                         from_address: Optional[str] = None, to_address: Optional[str] = None,
                         calendar_id: str = 'primary', customer_priority: Optional[str] = None) -> Dict[str, Any]:
        """Find the optimal appointment slot considering all factors including priority and urgency
        
        Args:
            service_description: Description of the service needed
            preferred_start: Customer's preferred start time
            from_address: Previous appointment location (for travel time)
            to_address: Customer's address
            calendar_id: Calendar to check for conflicts
            customer_priority: Optional customer priority level ('emergency', 'high', 'normal', 'low')
        """
        # Estimate service requirements
        service_type = self.estimate_service_duration(service_description)
        travel_time = self.calculate_travel_time(from_address, to_address)
        
        # Override priority if specified by customer
        if customer_priority:
            priority_map = {
                'emergency': AppointmentPriority.EMERGENCY,
                'high': AppointmentPriority.HIGH,
                'normal': AppointmentPriority.NORMAL,
                'low': AppointmentPriority.LOW
            }
            if customer_priority.lower() in priority_map:
                service_type.priority = priority_map[customer_priority.lower()]
                # Adjust urgency based on priority override
                if service_type.priority == AppointmentPriority.EMERGENCY:
                    service_type.urgency = AppointmentUrgency.EMERGENCY
                elif service_type.priority == AppointmentPriority.HIGH:
                    service_type.urgency = AppointmentUrgency.URGENT
        
        # Add travel time to service type
        service_type.travel_time_minutes = travel_time
        total_duration = service_type.duration_minutes + travel_time
        
        proposed_end = preferred_start + timedelta(minutes=total_duration)
        
        logger.info(f"Analyzing optimal slot for '{service_description}': "
                   f"Duration: {service_type.duration_minutes}min, Travel: {travel_time}min, "
                   f"Buffer: {service_type.buffer_before_minutes}/{service_type.buffer_after_minutes}min")
        
        # Check for conflicts
        conflicts = self.detect_conflicts(
            preferred_start, 
            proposed_end, 
            calendar_id, 
            max(service_type.buffer_before_minutes, service_type.buffer_after_minutes)
        )
        
        result = {
            'requested_start': preferred_start.isoformat() + 'Z',
            'requested_end': proposed_end.isoformat() + 'Z',
            'service_type': service_type.name,
            'duration_minutes': service_type.duration_minutes,
            'travel_time_minutes': travel_time,
            'total_duration_minutes': total_duration,
            'buffer_before_minutes': service_type.buffer_before_minutes,
            'buffer_after_minutes': service_type.buffer_after_minutes,
            'priority_level': service_type.priority.name,
            'urgency_level': service_type.urgency.value,
            'has_conflicts': len(conflicts) > 0,
            'conflicts': conflicts
        }
        
        if conflicts:
            # Determine search window based on urgency
            search_days = {
                AppointmentUrgency.EMERGENCY: 1,
                AppointmentUrgency.URGENT: 3,
                AppointmentUrgency.PREFERRED: 14,
                AppointmentUrgency.FLEXIBLE: 30
            }.get(service_type.urgency, 14)
            
            # Generate alternative suggestions with priority and urgency consideration
            alternatives = self.suggest_alternative_slots(
                preferred_start,
                total_duration,
                search_days=search_days,
                calendar_id=calendar_id,
                buffer_minutes=max(service_type.buffer_before_minutes, service_type.buffer_after_minutes),
                urgency=service_type.urgency,
                priority=service_type.priority
            )
            result['alternative_slots'] = alternatives
            result['recommendation'] = 'conflict_found'
            
            # Add urgency-specific messaging
            if service_type.urgency == AppointmentUrgency.EMERGENCY:
                result['urgency_message'] = 'Emergency service - seeking same-day alternatives'
            elif service_type.urgency == AppointmentUrgency.URGENT:
                result['urgency_message'] = 'Urgent service - prioritizing earliest available slots'
            
        else:
            result['alternative_slots'] = []
            result['recommendation'] = 'slot_available'
        
        return result


    # --- Calendar specific methods will go here ---
    def get_availability(self, start_time_iso: str, end_time_iso: str, calendar_id: str = 'primary') -> Optional[List[Dict[str, str]]]:
        """Gets free/busy information for a calendar."""
        if not self._ensure_valid_credentials():
            logger.error("Failed to ensure valid credentials for calendar operation.")
            return None
        
        if not self.service:
            logger.error("Calendar service not available.")
            return None
        
        body = {
            "timeMin": start_time_iso,
            "timeMax": end_time_iso,
            "items": [{"id": calendar_id}]
        }
        try:
            logger.debug(f"Fetching freeBusy for {calendar_id} from {start_time_iso} to {end_time_iso}")
            events_result = self.service.freebusy().query(body=body).execute()
            calendar_busy_info = events_result.get('calendars', {}).get(calendar_id, {})
            busy_slots = calendar_busy_info.get('busy', []) # List of {'start': ..., 'end': ...}
            logger.info(f"Found {len(busy_slots)} busy slots for {calendar_id}.")
            return busy_slots
        except HttpError as e:
            logger.error(f"HttpError fetching free/busy for {calendar_id}: {e.resp.status} - {e._get_reason()}", exc_info=True)
            if e.resp.status == 404:
                 logger.error(f"Calendar with ID '{calendar_id}' not found.")
            return None
        except Exception as e:
            logger.error(f"Error fetching free/busy for {calendar_id}: {e}", exc_info=True)
            return None

    def create_event(self, summary: str, start_datetime_iso: str, end_datetime_iso: str, 
                     attendees: Optional[List[str]] = None, description: Optional[str] = None, 
                     calendar_id: str = 'primary') -> Optional[Dict[str, Any]]:
        """Creates an event on the calendar."""
        if not self._ensure_valid_credentials():
            logger.error("Failed to ensure valid credentials for event creation.")
            return None
            
        if not self.service:
            logger.error("Calendar service not available.")
            return None

        event = {
            'summary': summary,
            'description': description or '',
            'start': {
                'dateTime': start_datetime_iso,
                # 'timeZone': 'America/New_York', # Consider making timezone configurable or getting from system/user
            },
            'end': {
                'dateTime': end_datetime_iso,
                # 'timeZone': 'America/New_York',
            },
        }
        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]

        try:
            logger.info(f"Creating event '{summary}' from {start_datetime_iso} to {end_datetime_iso} on calendar {calendar_id}")
            created_event = self.service.events().insert(calendarId=calendar_id, body=event).execute()
            logger.info(f"Event created successfully: ID: {created_event.get('id')}, Link: {created_event.get('htmlLink')}")
            return created_event
        except HttpError as e:
            logger.error(f"HttpError creating event '{summary}': {e.resp.status} - {e._get_reason()}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Error creating event '{summary}': {e}", exc_info=True)
            return None
    
    def create_optimized_appointment(self, summary: str, service_description: str, 
                                   preferred_start: datetime, customer_email: str,
                                   customer_address: Optional[str] = None,
                                   customer_priority: Optional[str] = None,
                                   calendar_id: str = 'primary') -> Dict[str, Any]:
        """Create an appointment with optimal scheduling using enhanced logic
        
        Args:
            summary: Appointment title/summary
            service_description: Description of the service needed
            preferred_start: Customer's preferred start time
            customer_email: Customer's email address
            customer_address: Customer's address for travel time calculation
            customer_priority: Optional priority override ('emergency', 'high', 'normal', 'low')
            calendar_id: Calendar to create the appointment on
        """
        
        # Find the optimal slot with priority consideration
        optimal_slot = self.find_optimal_slot(
            service_description=service_description,
            preferred_start=preferred_start,
            to_address=customer_address,
            calendar_id=calendar_id,
            customer_priority=customer_priority
        )
        
        result = {
            'optimization_analysis': optimal_slot,
            'appointment_created': False,
            'appointment_details': None,
            'message': ''
        }
        
        if optimal_slot['recommendation'] == 'slot_available':
            # No conflicts, create the appointment
            event_description = f"{service_description}\\n\\nService Details:\\n"
            event_description += f"- Service Type: {optimal_slot['service_type']}\\n"
            event_description += f"- Priority: {optimal_slot['priority_level']}\\n"
            event_description += f"- Urgency: {optimal_slot['urgency_level']}\\n"
            event_description += f"- Estimated Duration: {optimal_slot['duration_minutes']} minutes\\n"
            if optimal_slot['travel_time_minutes'] > 0:
                event_description += f"- Travel Time: {optimal_slot['travel_time_minutes']} minutes\\n"
            event_description += f"- Total Duration: {optimal_slot['total_duration_minutes']} minutes\\n"
            if customer_address:
                event_description += f"- Location: {customer_address}\\n"
            event_description += f"- Buffer Before: {optimal_slot['buffer_before_minutes']} minutes\\n"
            event_description += f"- Buffer After: {optimal_slot['buffer_after_minutes']} minutes\\n"
            
            created_event = self.create_event(
                summary=summary,
                start_datetime_iso=optimal_slot['requested_start'],
                end_datetime_iso=optimal_slot['requested_end'],
                attendees=[customer_email] if customer_email else None,
                description=event_description,
                calendar_id=calendar_id
            )
            
            if created_event:
                result['appointment_created'] = True
                result['appointment_details'] = created_event
                urgency = optimal_slot.get('urgency_level', 'preferred')
                priority = optimal_slot.get('priority_level', 'NORMAL')
                
                success_message = f"Appointment scheduled successfully for {preferred_start.strftime('%B %d, %Y at %I:%M %p')}"
                if urgency == 'emergency':
                    success_message += " - EMERGENCY SERVICE SCHEDULED"
                elif urgency == 'urgent':
                    success_message += " - URGENT SERVICE SCHEDULED"
                elif priority == 'HIGH':
                    success_message += " - HIGH PRIORITY SERVICE"
                
                result['message'] = success_message
            else:
                result['message'] = "Failed to create appointment due to calendar service error"
        
        else:
            # Conflicts found, provide alternatives
            alternatives = optimal_slot.get('alternative_slots', [])
            urgency_message = optimal_slot.get('urgency_message', '')
            
            if alternatives:
                message = f"Your requested time has conflicts. "
                if urgency_message:
                    message += f"{urgency_message}. "
                message += f"Here are {len(alternatives)} alternative options available:"
                result['message'] = message
            else:
                urgency = optimal_slot.get('urgency_level', 'preferred')
                if urgency == 'emergency':
                    result['message'] = "URGENT: Your emergency request has conflicts and no same-day alternatives found. Please call for immediate assistance."
                elif urgency == 'urgent':
                    result['message'] = "Your urgent request has conflicts and no alternatives found within 3 days. Expanding search or please call for priority scheduling."
                else:
                    search_period = "2 weeks" if urgency == 'preferred' else "1 month"
                    result['message'] = f"Your requested time has conflicts and no suitable alternatives were found in the next {search_period}."
        
        return result

# Example usage (for testing this client directly)
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logger.info("Running CalendarClient direct test...")

    # Adjust path for direct execution to find src.config
    import sys
    if 'src' not in sys.path and 'src' not in os.getcwd(): # Be careful with cwd if script is in src
        # Assuming script is in src, parent is project root
        project_root_for_test = os.path.dirname(os.path.abspath(__file__))
        if os.path.basename(project_root_for_test) == 'src': # if script is in /src
            project_root_for_test = os.path.dirname(project_root_for_test)
        sys.path.insert(0, project_root_for_test) 
        logger.debug(f"Adjusted sys.path for direct execution: added {project_root_for_test}")

    from dotenv import load_dotenv
    # Load .env from project root, assuming this script is in /src
    # Determine project root based on this script's location if it's in /src
    current_script_path = os.path.abspath(__file__)
    project_dir = os.path.dirname(current_script_path) # This will be /src
    if os.path.basename(project_dir) == 'src':
        project_dir = os.path.dirname(project_dir) # This is project root
    
    dotenv_path = os.path.join(project_dir, '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path=dotenv_path)
        logger.debug(f"Loaded .env from {dotenv_path} for direct test.")
    else:
        logger.warning(f".env file not found at {dotenv_path} for direct test.")

    try:
        from src.config import GOOGLE_CALENDAR_TOKEN_PATH as CFG_TOKEN_PATH, \
                               GOOGLE_APP_CREDENTIALS_PATH as CFG_CREDS_PATH, \
                               MONITORED_EMAIL_ACCOUNT as CFG_MONITORED_ACCOUNT
        logger.debug("Successfully imported config variables for direct test.")
    except ImportError as e:
        logger.error(f"Could not import from src.config for direct test: {e}. Ensure PYTHONPATH or script location is correct.")
        sys.exit(1)

    monitored_account = CFG_MONITORED_ACCOUNT
    token_p = CFG_TOKEN_PATH # Uses the value from config, which reads from .env
    creds_p = CFG_CREDS_PATH # Uses the value from config

    if not monitored_account or not token_p or not creds_p:
        logger.error("MONITORED_EMAIL_ACCOUNT, GOOGLE_CALENDAR_TOKEN_PATH, or GOOGLE_APP_CREDENTIALS_PATH not in .env. Skipping test.")
    else:
        logger.info(f"Testing with account: {monitored_account}, token path: {token_p}")
        try:
            calendar_client = CalendarClient(email_address=monitored_account, token_path=token_p, credentials_path=creds_p)
            
            # Test get_availability
            now = datetime.utcnow()
            start_iso = now.isoformat() + 'Z'  # 'Z' indicates UTC
            end_iso = (now + timedelta(days=7)).isoformat() + 'Z'
            logger.info(f"\nTesting get_availability for next 7 days ({start_iso} to {end_iso})...")
            busy_slots = calendar_client.get_availability(start_iso, end_iso)
            if busy_slots is not None:
                logger.info(f"Busy slots: {json.dumps(busy_slots, indent=2)}")
            else:
                logger.error("Failed to get availability.")

            # Test create_event
            logger.info("\nTesting create_event...")
            event_start = (now + timedelta(days=1, hours=2)).replace(minute=0, second=0, microsecond=0)
            event_end = (event_start + timedelta(hours=1))
            event_summary = "Test Appointment via CalendarClient"
            created = calendar_client.create_event(
                summary=event_summary,
                start_datetime_iso=event_start.isoformat() + 'Z',
                end_datetime_iso=event_end.isoformat() + 'Z',
                attendees=[monitored_account] # Self-invite
            )
            if created:
                logger.info(f"Event '{event_summary}' created successfully. ID: {created.get('id')}")
            else:
                logger.error(f"Failed to create event '{event_summary}'.")

        except ValueError as ve:
            logger.error(f"Setup error for CalendarClient test: {ve}")
        except Exception as e:
            logger.error(f"Error during CalendarClient direct test: {e}", exc_info=True) 
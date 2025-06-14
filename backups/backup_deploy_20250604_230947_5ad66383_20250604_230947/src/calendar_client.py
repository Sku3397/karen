# src/calendar_client.py - Secure calendar client with OAuth token management
import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
import re
import requests
from dataclasses import dataclass

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleAuthRequest
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import google.auth.exceptions

# Import enhanced OAuth token manager
from .token_manager import get_credentials_with_auto_refresh

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

@dataclass
class ServiceType:
    """Represents a service type with duration and buffer requirements"""
    name: str
    duration_minutes: int
    buffer_before_minutes: int = 15
    buffer_after_minutes: int = 15
    travel_time_minutes: int = 0

# Default service types for handyman services
DEFAULT_SERVICE_TYPES = {
    'consultation': ServiceType('Consultation', 30, 10, 10),
    'repair': ServiceType('Repair', 120, 15, 15),
    'installation': ServiceType('Installation', 180, 30, 15),
    'maintenance': ServiceType('Maintenance', 90, 15, 15),
    'inspection': ServiceType('Inspection', 60, 10, 10),
    'estimate': ServiceType('Estimate', 45, 15, 10),
    'emergency': ServiceType('Emergency', 60, 5, 5),
    'default': ServiceType('General Service', 60, 15, 15)
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
        """Estimate service duration based on description"""
        description_lower = service_description.lower()
        
        # Emergency keywords
        if any(word in description_lower for word in ['emergency', 'urgent', 'leak', 'broken']):
            return DEFAULT_SERVICE_TYPES['emergency']
        
        # Installation keywords
        if any(word in description_lower for word in ['install', 'installation', 'mount', 'setup']):
            return DEFAULT_SERVICE_TYPES['installation']
        
        # Repair keywords
        if any(word in description_lower for word in ['repair', 'fix', 'broken', 'replace']):
            return DEFAULT_SERVICE_TYPES['repair']
        
        # Maintenance keywords
        if any(word in description_lower for word in ['maintenance', 'service', 'clean', 'tune']):
            return DEFAULT_SERVICE_TYPES['maintenance']
        
        # Inspection keywords
        if any(word in description_lower for word in ['inspect', 'check', 'look', 'assess']):
            return DEFAULT_SERVICE_TYPES['inspection']
        
        # Estimate keywords
        if any(word in description_lower for word in ['estimate', 'quote', 'pricing', 'cost']):
            return DEFAULT_SERVICE_TYPES['estimate']
        
        # Consultation keywords
        if any(word in description_lower for word in ['consult', 'discuss', 'plan', 'advice']):
            return DEFAULT_SERVICE_TYPES['consultation']
        
        return DEFAULT_SERVICE_TYPES['default']
    
    def calculate_travel_time(self, from_address: Optional[str], to_address: Optional[str]) -> int:
        """Calculate travel time between addresses in minutes"""
        if not from_address or not to_address:
            return 0
        
        try:
            # For production, you'd use Google Maps API or similar
            # For now, use a simple heuristic based on distance
            
            # Extract zip codes or city names for rough distance estimation
            from_zip = self._extract_zip_code(from_address)
            to_zip = self._extract_zip_code(to_address)
            
            if from_zip and to_zip and from_zip == to_zip:
                # Same zip code - local travel
                return 15
            elif from_zip and to_zip:
                # Different zip codes - assume longer travel
                return 30
            else:
                # Default travel time
                return 20
                
        except Exception as e:
            logger.warning(f"Error calculating travel time: {e}")
            return 20  # Default travel time
    
    def _extract_zip_code(self, address: str) -> Optional[str]:
        """Extract zip code from address string"""
        zip_pattern = r'\b\d{5}(?:-\d{4})?\b'
        match = re.search(zip_pattern, address)
        return match.group() if match else None
    
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
                                 buffer_minutes: int = 15) -> List[Dict[str, Any]]:
        """Suggest alternative time slots when the preferred time has conflicts"""
        suggestions = []
        
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
            
            # Skip weekends for business appointments
            if check_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                continue
            
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
                    priority_score = max(0, 100 - (time_diff / 3600))  # Decrease by 1 point per hour
                    
                    suggestions.append({
                        'start': current_time.isoformat() + 'Z',
                        'end': proposed_end.isoformat() + 'Z',
                        'duration_minutes': duration_minutes,
                        'priority_score': priority_score,
                        'day_of_week': check_date.strftime('%A'),
                        'time_difference_hours': round(time_diff / 3600, 1)
                    })
                    
                    # Stop after finding enough suggestions
                    if len(suggestions) >= 10:
                        break
                
                # Move to next 30-minute slot
                current_time += timedelta(minutes=30)
            
            if len(suggestions) >= 10:
                break
        
        # Sort suggestions by priority score (highest first)
        suggestions.sort(key=lambda x: x['priority_score'], reverse=True)
        
        logger.info(f"Generated {len(suggestions)} alternative time slot suggestions")
        return suggestions[:5]  # Return top 5 suggestions
    
    def find_optimal_slot(self, service_description: str, preferred_start: datetime,
                         from_address: Optional[str] = None, to_address: Optional[str] = None,
                         calendar_id: str = 'primary') -> Dict[str, Any]:
        """Find the optimal appointment slot considering all factors"""
        # Estimate service requirements
        service_type = self.estimate_service_duration(service_description)
        travel_time = self.calculate_travel_time(from_address, to_address)
        
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
            'has_conflicts': len(conflicts) > 0,
            'conflicts': conflicts
        }
        
        if conflicts:
            # Generate alternative suggestions
            alternatives = self.suggest_alternative_slots(
                preferred_start,
                total_duration,
                search_days=14,  # Search up to 2 weeks
                calendar_id=calendar_id,
                buffer_minutes=max(service_type.buffer_before_minutes, service_type.buffer_after_minutes)
            )
            result['alternative_slots'] = alternatives
            result['recommendation'] = 'conflict_found'
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
                                   calendar_id: str = 'primary') -> Dict[str, Any]:
        """Create an appointment with optimal scheduling using enhanced logic"""
        
        # Find the optimal slot
        optimal_slot = self.find_optimal_slot(
            service_description=service_description,
            preferred_start=preferred_start,
            to_address=customer_address,
            calendar_id=calendar_id
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
            event_description += f"- Estimated Duration: {optimal_slot['duration_minutes']} minutes\\n"
            if optimal_slot['travel_time_minutes'] > 0:
                event_description += f"- Travel Time: {optimal_slot['travel_time_minutes']} minutes\\n"
            if customer_address:
                event_description += f"- Location: {customer_address}\\n"
            
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
                result['message'] = f"Appointment scheduled successfully for {preferred_start.strftime('%B %d, %Y at %I:%M %p')}"
            else:
                result['message'] = "Failed to create appointment due to calendar service error"
        
        else:
            # Conflicts found, provide alternatives
            alternatives = optimal_slot.get('alternative_slots', [])
            if alternatives:
                result['message'] = f"Your requested time has conflicts. Here are {len(alternatives)} alternative options available:"
            else:
                result['message'] = "Your requested time has conflicts and no suitable alternatives were found in the next 2 weeks."
        
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
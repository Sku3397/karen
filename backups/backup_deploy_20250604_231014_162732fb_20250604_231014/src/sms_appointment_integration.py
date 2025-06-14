"""
SMS-Calendar Integration for appointment booking via text
Seamlessly connects SMS conversations with calendar system
"""
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta, time
import re
import logging
from dataclasses import dataclass
from enum import Enum

from src.calendar_client import CalendarClient
from src.sms_conversation_manager import ConversationManager
from src.datetime_utils import parse_natural_datetime

logger = logging.getLogger(__name__)

class AppointmentStatus(Enum):
    REQUESTED = "requested"
    CONFIRMED = "confirmed"
    RESCHEDULED = "rescheduled"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

@dataclass
class AppointmentSlot:
    """Represents an available appointment slot"""
    datetime: datetime
    duration_minutes: int
    available: bool
    display_text: str
    slot_id: str

@dataclass
class AppointmentRequest:
    """Represents a customer's appointment request"""
    customer_phone: str
    requested_datetime: Optional[datetime]
    service_type: str
    urgency: str
    notes: str
    preferred_times: List[str]
    status: AppointmentStatus

class SMSAppointmentBooking:
    """Handles appointment booking through SMS with calendar integration"""
    
    def __init__(self, calendar_client: CalendarClient = None):
        """Initialize with calendar and conversation managers"""
        self.calendar = calendar_client or CalendarClient()
        self.conversation_manager = ConversationManager()
        
        # Service duration estimates (in minutes)
        self.service_durations = {
            'plumbing': 120,
            'electrical': 90,
            'hvac': 180,
            'general_repair': 60,
            'maintenance': 45,
            'emergency': 180,
            'consultation': 30,
            'installation': 240,
            'default': 90
        }
        
        # Common time phrases and their interpretations
        self.time_patterns = {
            r'morning': {'start_hour': 8, 'end_hour': 12},
            r'afternoon': {'start_hour': 12, 'end_hour': 17},
            r'evening': {'start_hour': 17, 'end_hour': 20},
            r'early morning': {'start_hour': 8, 'end_hour': 10},
            r'late morning': {'start_hour': 10, 'end_hour': 12},
            r'early afternoon': {'start_hour': 12, 'end_hour': 15},
            r'late afternoon': {'start_hour': 15, 'end_hour': 17},
            r'before noon': {'start_hour': 8, 'end_hour': 12},
            r'after lunch': {'start_hour': 13, 'end_hour': 17},
            r'weekday': {'weekdays_only': True},
            r'weekend': {'weekends_only': True}
        }
    
    def parse_appointment_request(self, message: str, customer_phone: str) -> AppointmentRequest:
        """
        Extract appointment details from natural language SMS
        
        Args:
            message: Customer's SMS message
            customer_phone: Customer's phone number
            
        Returns:
            AppointmentRequest object with parsed details
        """
        message_lower = message.lower()
        
        # Extract service type
        service_type = self._detect_service_type(message_lower)
        
        # Extract urgency
        urgency = self._detect_urgency(message_lower)
        
        # Extract datetime preferences
        requested_datetime = self._extract_datetime(message)
        preferred_times = self._extract_time_preferences(message_lower)
        
        # Extract additional notes
        notes = self._extract_notes(message, service_type)
        
        return AppointmentRequest(
            customer_phone=customer_phone,
            requested_datetime=requested_datetime,
            service_type=service_type,
            urgency=urgency,
            notes=notes,
            preferred_times=preferred_times,
            status=AppointmentStatus.REQUESTED
        )
    
    def _detect_service_type(self, message: str) -> str:
        """Detect the type of service requested"""
        service_keywords = {
            'plumbing': ['plumb', 'leak', 'pipe', 'faucet', 'toilet', 'drain', 'water', 'sink'],
            'electrical': ['electric', 'outlet', 'wire', 'light', 'power', 'breaker', 'switch'],
            'hvac': ['heat', 'air', 'hvac', 'furnace', 'ac', 'temperature', 'thermostat'],
            'general_repair': ['fix', 'repair', 'broken', 'replace', 'install'],
            'maintenance': ['maintain', 'check', 'service', 'tune up', 'inspection'],
            'emergency': ['emergency', 'urgent', 'asap', 'immediate'],
            'consultation': ['consult', 'estimate', 'quote', 'look at', 'assess']
        }
        
        for service, keywords in service_keywords.items():
            if any(keyword in message for keyword in keywords):
                return service
        
        return 'general_repair'  # Default
    
    def _detect_urgency(self, message: str) -> str:
        """Detect urgency level from message"""
        high_urgency = ['emergency', 'urgent', 'asap', 'immediate', 'now', 'today']
        medium_urgency = ['soon', 'this week', 'quick', 'fast']
        
        if any(word in message for word in high_urgency):
            return 'high'
        elif any(word in message for word in medium_urgency):
            return 'medium'
        else:
            return 'normal'
    
    def _extract_datetime(self, message: str) -> Optional[datetime]:
        """Extract specific datetime from message using natural language parsing"""
        try:
            # Use the datetime_utils parser for natural language
            return parse_natural_datetime(message)
        except Exception as e:
            logger.debug(f"Could not parse datetime from '{message}': {e}")
            return None
    
    def _extract_time_preferences(self, message: str) -> List[str]:
        """Extract general time preferences from message"""
        preferences = []
        
        for pattern, info in self.time_patterns.items():
            if re.search(pattern, message):
                preferences.append(pattern)
        
        return preferences
    
    def _extract_notes(self, message: str, service_type: str) -> str:
        """Extract relevant notes/details from the message"""
        # Remove common appointment keywords to get the actual details
        clean_message = message
        removal_words = ['schedule', 'appointment', 'book', 'need', 'want', 'can you']
        
        for word in removal_words:
            clean_message = re.sub(rf'\b{word}\b', '', clean_message, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        clean_message = ' '.join(clean_message.split())
        
        return clean_message.strip()
    
    def find_available_slots(self, appointment_request: AppointmentRequest, 
                           days_ahead: int = 14) -> List[AppointmentSlot]:
        """
        Find available appointment slots based on request preferences
        
        Args:
            appointment_request: The appointment request details
            days_ahead: How many days to look ahead for availability
            
        Returns:
            List of available AppointmentSlot objects
        """
        service_duration = self.service_durations.get(
            appointment_request.service_type, 
            self.service_durations['default']
        )
        
        # Get busy times from calendar
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=days_ahead)
        
        try:
            busy_times = self.calendar.get_busy_times(start_date, end_date)
        except Exception as e:
            logger.error(f"Failed to get busy times from calendar: {e}")
            busy_times = []
        
        # Generate potential slots
        slots = []
        current_date = start_date
        
        while current_date <= end_date:
            # Skip past dates
            if current_date.date() < datetime.now().date():
                current_date += timedelta(days=1)
                continue
                
            # Generate slots for this day
            day_slots = self._generate_day_slots(
                current_date, 
                service_duration, 
                busy_times,
                appointment_request
            )
            slots.extend(day_slots)
            current_date += timedelta(days=1)
        
        # Sort by date and return top matches
        slots.sort(key=lambda x: x.datetime)
        return slots[:10]  # Return top 10 options
    
    def _generate_day_slots(self, date: datetime, duration_minutes: int, 
                           busy_times: List[Dict], request: AppointmentRequest) -> List[AppointmentSlot]:
        """Generate available slots for a specific day"""
        slots = []
        
        # Business hours (8 AM to 6 PM by default)
        start_hour = 8
        end_hour = 18
        
        # Adjust based on preferences
        if 'morning' in request.preferred_times:
            end_hour = min(end_hour, 12)
        elif 'afternoon' in request.preferred_times:
            start_hour = max(start_hour, 12)
        elif 'evening' in request.preferred_times:
            start_hour = max(start_hour, 17)
            end_hour = 20  # Extend for evening
        
        # Skip weekends unless specifically requested
        if date.weekday() >= 5:  # Saturday or Sunday
            if 'weekend' not in request.preferred_times:
                return slots
        
        # Generate hourly slots
        current_time = date.replace(hour=start_hour, minute=0)
        end_time = date.replace(hour=end_hour, minute=0)
        
        while current_time < end_time:
            # Check if slot conflicts with busy times
            slot_end = current_time + timedelta(minutes=duration_minutes)
            
            if not self._conflicts_with_busy_times(current_time, slot_end, busy_times):
                # Check if it's a reasonable time (not too early if same day)
                if self._is_reasonable_time(current_time, request.urgency):
                    slot = AppointmentSlot(
                        datetime=current_time,
                        duration_minutes=duration_minutes,
                        available=True,
                        display_text=self._format_slot_display(current_time, duration_minutes),
                        slot_id=f"{current_time.strftime('%Y%m%d_%H%M')}"
                    )
                    slots.append(slot)
            
            # Move to next hour
            current_time += timedelta(hours=1)
        
        return slots
    
    def _conflicts_with_busy_times(self, start_time: datetime, end_time: datetime, 
                                 busy_times: List[Dict]) -> bool:
        """Check if proposed slot conflicts with existing appointments"""
        for busy_period in busy_times:
            busy_start = busy_period.get('start')
            busy_end = busy_period.get('end')
            
            if isinstance(busy_start, str):
                busy_start = datetime.fromisoformat(busy_start.replace('Z', '+00:00'))
            if isinstance(busy_end, str):
                busy_end = datetime.fromisoformat(busy_end.replace('Z', '+00:00'))
            
            # Check for overlap
            if start_time < busy_end and end_time > busy_start:
                return True
        
        return False
    
    def _is_reasonable_time(self, slot_time: datetime, urgency: str) -> bool:
        """Check if the slot time is reasonable given current time and urgency"""
        now = datetime.now()
        
        # For same-day appointments
        if slot_time.date() == now.date():
            # Need at least 2 hours notice for normal appointments
            min_notice_hours = 2 if urgency == 'normal' else 1
            if slot_time <= now + timedelta(hours=min_notice_hours):
                return False
        
        return True
    
    def _format_slot_display(self, slot_time: datetime, duration_minutes: int) -> str:
        """Format slot for human-readable display"""
        day_name = slot_time.strftime('%A')
        date_str = slot_time.strftime('%B %d')
        time_str = slot_time.strftime('%I:%M %p').lower().replace('0', '')
        duration_str = f"{duration_minutes // 60}h" if duration_minutes >= 60 else f"{duration_minutes}min"
        
        # Make it conversational
        if slot_time.date() == datetime.now().date():
            return f"Today at {time_str} ({duration_str})"
        elif slot_time.date() == (datetime.now() + timedelta(days=1)).date():
            return f"Tomorrow at {time_str} ({duration_str})"
        else:
            return f"{day_name}, {date_str} at {time_str} ({duration_str})"
    
    def create_sms_appointment_options(self, slots: List[AppointmentSlot]) -> str:
        """
        Create SMS-friendly appointment options message
        
        Args:
            slots: List of available appointment slots
            
        Returns:
            Formatted SMS message with numbered options
        """
        if not slots:
            return ("I don't see any available slots that match your preferences right now. "
                   "Let me check with the team and get back to you with some options!")
        
        message = "Here are some available times:\n\n"
        
        for i, slot in enumerate(slots[:5], 1):  # Show max 5 options
            message += f"{i}. {slot.display_text}\n"
        
        message += f"\nJust reply with the number that works best (like '2') or let me know if you need different times! 📅"
        
        return message
    
    def confirm_appointment(self, slot: AppointmentSlot, customer_phone: str, 
                          service_details: Dict) -> Dict[str, Any]:
        """
        Confirm appointment by creating calendar event
        
        Args:
            slot: Selected appointment slot
            customer_phone: Customer's phone number
            service_details: Details about the service
            
        Returns:
            Confirmation details including event ID
        """
        try:
            # Create calendar event
            event_details = {
                'summary': f"{service_details.get('service_type', 'Service')} - {customer_phone}",
                'description': (
                    f"Customer: {customer_phone}\n"
                    f"Service: {service_details.get('service_type', 'General')}\n"
                    f"Notes: {service_details.get('notes', 'None')}\n"
                    f"Urgency: {service_details.get('urgency', 'Normal')}\n"
                    f"Booked via SMS"
                ),
                'start_time': slot.datetime,
                'end_time': slot.datetime + timedelta(minutes=slot.duration_minutes),
                'attendees': [service_details.get('customer_email')] if service_details.get('customer_email') else []
            }
            
            event_id = self.calendar.create_event(event_details)
            
            # Update conversation state
            conversation_context = {
                'state': 'appointment_confirmed',
                'appointment_datetime': slot.datetime,
                'event_id': event_id,
                'service_type': service_details.get('service_type'),
                'confirmation_time': datetime.now()
            }
            
            self.conversation_manager.update_conversation_state(
                customer_phone, 
                conversation_context
            )
            
            return {
                'success': True,
                'event_id': event_id,
                'appointment_datetime': slot.datetime,
                'confirmation_message': self._generate_confirmation_message(slot, service_details)
            }
            
        except Exception as e:
            logger.error(f"Failed to confirm appointment: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback_message': ("I'm having trouble accessing the calendar right now. "
                                   "Let me have someone call you to confirm this appointment!")
            }
    
    def _generate_confirmation_message(self, slot: AppointmentSlot, service_details: Dict) -> str:
        """Generate confirmation message for SMS"""
        return (
            f"Perfect! ✅ Your appointment is confirmed:\n\n"
            f"📅 {slot.display_text}\n"
            f"🔧 {service_details.get('service_type', 'Service').title()}\n"
            f"📱 We'll send a reminder the day before\n\n"
            f"Need to change anything? Just text me!"
        )
    
    def reschedule_appointment(self, customer_phone: str, current_event_id: str, 
                             new_slot: AppointmentSlot) -> Dict[str, Any]:
        """
        Reschedule an existing appointment
        
        Args:
            customer_phone: Customer's phone number  
            current_event_id: ID of current calendar event
            new_slot: New appointment slot
            
        Returns:
            Reschedule confirmation details
        """
        try:
            # Update calendar event
            updated_event = self.calendar.update_event(
                current_event_id,
                {
                    'start_time': new_slot.datetime,
                    'end_time': new_slot.datetime + timedelta(minutes=new_slot.duration_minutes)
                }
            )
            
            # Update conversation state
            conversation_context = {
                'state': 'appointment_rescheduled',
                'appointment_datetime': new_slot.datetime,
                'event_id': current_event_id,
                'reschedule_time': datetime.now()
            }
            
            self.conversation_manager.update_conversation_state(
                customer_phone,
                conversation_context
            )
            
            return {
                'success': True,
                'new_datetime': new_slot.datetime,
                'message': (
                    f"Done! ✅ Your appointment has been moved to:\n\n"
                    f"📅 {new_slot.display_text}\n\n"
                    f"We'll send an updated reminder. Thanks for letting me know!"
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to reschedule appointment: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': ("I'm having trouble updating the calendar. "
                          "Let me have someone call you to reschedule!")
            }
    
    def cancel_appointment(self, customer_phone: str, event_id: str) -> Dict[str, Any]:
        """
        Cancel an appointment
        
        Args:
            customer_phone: Customer's phone number
            event_id: Calendar event ID to cancel
            
        Returns:
            Cancellation confirmation
        """
        try:
            # Cancel calendar event
            self.calendar.delete_event(event_id)
            
            # Update conversation state
            conversation_context = {
                'state': 'appointment_cancelled',
                'cancellation_time': datetime.now()
            }
            
            self.conversation_manager.update_conversation_state(
                customer_phone,
                conversation_context
            )
            
            return {
                'success': True,
                'message': (
                    "Your appointment has been cancelled. ❌\n\n"
                    "No problem at all! If you need anything in the future, "
                    "just send me a text. Have a great day! 😊"
                )
            }
            
        except Exception as e:
            logger.error(f"Failed to cancel appointment: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': ("I'm having trouble canceling in the system. "
                          "Let me have someone call you to confirm the cancellation.")
            }
    
    def get_appointment_status(self, customer_phone: str) -> Dict[str, Any]:
        """
        Get current appointment status for customer
        
        Args:
            customer_phone: Customer's phone number
            
        Returns:
            Current appointment information
        """
        try:
            conversation_state = self.conversation_manager.get_conversation_state(customer_phone)
            
            if not conversation_state:
                return {'has_appointment': False}
            
            appointment_datetime = conversation_state.get('appointment_datetime')
            event_id = conversation_state.get('event_id')
            state = conversation_state.get('state', '')
            
            if appointment_datetime and 'appointment' in state:
                # Check if appointment is still valid in calendar
                try:
                    event = self.calendar.get_event(event_id) if event_id else None
                    is_valid = event is not None
                except:
                    is_valid = False
                
                return {
                    'has_appointment': True,
                    'datetime': appointment_datetime,
                    'event_id': event_id,
                    'status': state,
                    'is_valid': is_valid,
                    'display_text': self._format_slot_display(
                        appointment_datetime, 
                        self.service_durations['default']
                    )
                }
            
            return {'has_appointment': False}
            
        except Exception as e:
            logger.error(f"Failed to get appointment status: {e}")
            return {'has_appointment': False, 'error': str(e)}

# Global instance
_sms_appointment_booking = None

def get_sms_appointment_booking() -> SMSAppointmentBooking:
    """Get singleton SMS appointment booking instance"""
    global _sms_appointment_booking
    if _sms_appointment_booking is None:
        _sms_appointment_booking = SMSAppointmentBooking()
    return _sms_appointment_booking
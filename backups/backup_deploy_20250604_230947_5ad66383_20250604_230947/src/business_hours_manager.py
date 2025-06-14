#!/usr/bin/env python3
"""
Advanced Business Hours Management System for 757 Handy
Handles complex scheduling including holidays, special hours, and seasonal adjustments

Author: Phone Engineer Agent
"""

import os
import json
import logging
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import pytz
from calendar import monthrange
import holidays

logger = logging.getLogger(__name__)

class DayType(Enum):
    """Types of business days"""
    NORMAL = "normal"
    HOLIDAY = "holiday"
    EMERGENCY_ONLY = "emergency_only"
    EXTENDED = "extended"
    REDUCED = "reduced"
    CLOSED = "closed"

class ServiceLevel(Enum):
    """Service levels available"""
    FULL_SERVICE = "full_service"
    EMERGENCY_ONLY = "emergency_only"
    APPOINTMENT_ONLY = "appointment_only"
    CLOSED = "closed"

@dataclass
class BusinessHours:
    """Business hours for a specific day"""
    open_time: Optional[time] = None
    close_time: Optional[time] = None
    service_level: ServiceLevel = ServiceLevel.FULL_SERVICE
    special_message: Optional[str] = None
    emergency_available: bool = True
    
    def is_open_at(self, check_time: time) -> bool:
        """Check if business is open at specific time"""
        if not self.open_time or not self.close_time:
            return False
        
        if self.open_time <= self.close_time:
            # Normal day (e.g., 9 AM to 5 PM)
            return self.open_time <= check_time <= self.close_time
        else:
            # Overnight hours (e.g., 10 PM to 6 AM)
            return check_time >= self.open_time or check_time <= self.close_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'open_time': self.open_time.strftime('%H:%M') if self.open_time else None,
            'close_time': self.close_time.strftime('%H:%M') if self.close_time else None,
            'service_level': self.service_level.value,
            'special_message': self.special_message,
            'emergency_available': self.emergency_available
        }

@dataclass
class SpecialDay:
    """Special day configuration (holidays, etc.)"""
    date: datetime
    day_type: DayType
    hours: BusinessHours
    description: str
    recurring_annual: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'date': self.date.strftime('%Y-%m-%d'),
            'day_type': self.day_type.value,
            'hours': self.hours.to_dict(),
            'description': self.description,
            'recurring_annual': self.recurring_annual
        }

class BusinessHoursManager:
    """
    Comprehensive business hours management with:
    - Regular weekly schedule
    - Holiday handling with custom messages
    - Seasonal hour adjustments
    - Emergency service availability
    - Special events and closures
    - Time zone support
    - Dynamic messaging based on context
    """
    
    def __init__(self, timezone: str = 'America/New_York'):
        self.timezone = pytz.timezone(timezone)
        self.company_name = "757 Handy"
        
        # Standard weekly hours
        self.weekly_hours = {
            0: BusinessHours(  # Monday
                open_time=time(8, 0),
                close_time=time(18, 0),
                service_level=ServiceLevel.FULL_SERVICE
            ),
            1: BusinessHours(  # Tuesday
                open_time=time(8, 0),
                close_time=time(18, 0),
                service_level=ServiceLevel.FULL_SERVICE
            ),
            2: BusinessHours(  # Wednesday
                open_time=time(8, 0),
                close_time=time(18, 0),
                service_level=ServiceLevel.FULL_SERVICE
            ),
            3: BusinessHours(  # Thursday
                open_time=time(8, 0),
                close_time=time(18, 0),
                service_level=ServiceLevel.FULL_SERVICE
            ),
            4: BusinessHours(  # Friday
                open_time=time(8, 0),
                close_time=time(18, 0),
                service_level=ServiceLevel.FULL_SERVICE
            ),
            5: BusinessHours(  # Saturday
                open_time=time(9, 0),
                close_time=time(16, 0),
                service_level=ServiceLevel.FULL_SERVICE
            ),
            6: BusinessHours(  # Sunday
                open_time=None,
                close_time=None,
                service_level=ServiceLevel.EMERGENCY_ONLY,
                special_message="We're closed Sundays for regular service, but emergency repairs are available 24/7."
            )
        }
        
        # Initialize US holidays
        self.us_holidays = holidays.US(years=range(2024, 2030))
        
        # Special days and company holidays
        self.special_days: Dict[str, SpecialDay] = {}
        self._initialize_company_holidays()
        
        # Seasonal adjustments
        self.seasonal_adjustments = {
            'summer': {  # June 1 - August 31
                'extended_hours': True,
                'saturday_hours': BusinessHours(time(8, 0), time(17, 0), ServiceLevel.FULL_SERVICE)
            },
            'winter': {  # December 1 - February 28
                'reduced_hours': True,
                'friday_close_early': time(17, 0)
            }
        }
        
        # Emergency service configuration
        self.emergency_config = {
            'available_24_7': True,
            'response_time_hours': 2,
            'additional_fee': True,
            'services': ['plumbing emergencies', 'electrical issues', 'heating failures', 'security concerns']
        }
        
        logger.info(f"BusinessHoursManager initialized for {timezone}")
    
    def _initialize_company_holidays(self):
        """Initialize company-specific holidays and special days"""
        current_year = datetime.now().year
        
        # Company holidays (in addition to federal holidays)
        company_holidays = [
            # Christmas week closure
            SpecialDay(
                date=datetime(current_year, 12, 26),
                day_type=DayType.CLOSED,
                hours=BusinessHours(service_level=ServiceLevel.EMERGENCY_ONLY, 
                                  special_message="We're closed the week after Christmas. Emergency service available."),
                description="Christmas Week Closure",
                recurring_annual=True
            ),
            SpecialDay(
                date=datetime(current_year, 12, 27),
                day_type=DayType.CLOSED,
                hours=BusinessHours(service_level=ServiceLevel.EMERGENCY_ONLY, 
                                  special_message="We're closed the week after Christmas. Emergency service available."),
                description="Christmas Week Closure",
                recurring_annual=True
            ),
            SpecialDay(
                date=datetime(current_year, 12, 30),
                day_type=DayType.CLOSED,
                hours=BusinessHours(service_level=ServiceLevel.EMERGENCY_ONLY, 
                                  special_message="We're closed the week after Christmas. Emergency service available."),
                description="Christmas Week Closure",
                recurring_annual=True
            ),
            SpecialDay(
                date=datetime(current_year, 12, 31),
                day_type=DayType.CLOSED,
                hours=BusinessHours(service_level=ServiceLevel.EMERGENCY_ONLY, 
                                  special_message="We're closed New Year's Eve. Emergency service available."),
                description="New Year's Eve",
                recurring_annual=True
            ),
            # Day after Thanksgiving
            SpecialDay(
                date=self._get_black_friday(current_year),
                day_type=DayType.REDUCED,
                hours=BusinessHours(time(10, 0), time(15, 0), ServiceLevel.APPOINTMENT_ONLY, 
                                  "Limited hours today - appointments only."),
                description="Black Friday - Limited Hours",
                recurring_annual=True
            ),
        ]
        
        # Add to special days
        for holiday in company_holidays:
            self.special_days[holiday.date.strftime('%Y-%m-%d')] = holiday
    
    def _get_black_friday(self, year: int) -> datetime:
        """Calculate Black Friday for given year"""
        # Thanksgiving is 4th Thursday of November
        november_first = datetime(year, 11, 1)
        first_thursday = november_first + timedelta(days=(3 - november_first.weekday()) % 7)
        thanksgiving = first_thursday + timedelta(weeks=3)
        black_friday = thanksgiving + timedelta(days=1)
        return black_friday
    
    def is_open(self, check_time: Optional[datetime] = None) -> bool:
        """Check if business is currently open"""
        if check_time is None:
            check_time = datetime.now(self.timezone)
        
        # Localize if naive datetime
        if check_time.tzinfo is None:
            check_time = self.timezone.localize(check_time)
        
        # Convert to business timezone
        local_time = check_time.astimezone(self.timezone)
        
        # Check for special days first
        date_str = local_time.strftime('%Y-%m-%d')
        if date_str in self.special_days:
            special_day = self.special_days[date_str]
            return special_day.hours.is_open_at(local_time.time())
        
        # Check if it's a federal holiday
        if local_time.date() in self.us_holidays:
            return False  # Closed on federal holidays
        
        # Check regular weekly hours
        weekday = local_time.weekday()
        if weekday in self.weekly_hours:
            business_hours = self._get_adjusted_hours(local_time, weekday)
            return business_hours.is_open_at(local_time.time())
        
        return False
    
    def _get_adjusted_hours(self, check_date: datetime, weekday: int) -> BusinessHours:
        """Get business hours adjusted for seasonal changes"""
        base_hours = self.weekly_hours[weekday]
        
        # Apply seasonal adjustments
        month = check_date.month
        
        # Summer adjustments (June-August)
        if 6 <= month <= 8 and 'summer' in self.seasonal_adjustments:
            summer_config = self.seasonal_adjustments['summer']
            if weekday == 5 and 'saturday_hours' in summer_config:  # Saturday
                return summer_config['saturday_hours']
        
        # Winter adjustments (December-February)
        elif month in [12, 1, 2] and 'winter' in self.seasonal_adjustments:
            winter_config = self.seasonal_adjustments['winter']
            if weekday == 4 and 'friday_close_early' in winter_config:  # Friday
                adjusted_hours = BusinessHours(
                    open_time=base_hours.open_time,
                    close_time=winter_config['friday_close_early'],
                    service_level=base_hours.service_level,
                    special_message="We close early on winter Fridays.",
                    emergency_available=base_hours.emergency_available
                )
                return adjusted_hours
        
        return base_hours
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get comprehensive current business status"""
        now = datetime.now(self.timezone)
        is_currently_open = self.is_open(now)
        
        status = {
            'is_open': is_currently_open,
            'current_time': now.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'service_level': self._get_current_service_level(now),
            'message': self._get_current_message(now),
            'emergency_available': self._is_emergency_available(now),
            'next_opening': None,
            'next_closing': None
        }
        
        if not is_currently_open:
            status['next_opening'] = self._get_next_opening(now)
        else:
            status['next_closing'] = self._get_next_closing(now)
        
        return status
    
    def _get_current_service_level(self, check_time: datetime) -> str:
        """Get current service level"""
        date_str = check_time.strftime('%Y-%m-%d')
        
        # Check special days
        if date_str in self.special_days:
            return self.special_days[date_str].hours.service_level.value
        
        # Check if it's a federal holiday
        if check_time.date() in self.us_holidays:
            return ServiceLevel.EMERGENCY_ONLY.value
        
        # Check regular hours
        weekday = check_time.weekday()
        if weekday in self.weekly_hours:
            business_hours = self._get_adjusted_hours(check_time, weekday)
            if business_hours.is_open_at(check_time.time()):
                return business_hours.service_level.value
        
        return ServiceLevel.EMERGENCY_ONLY.value
    
    def _get_current_message(self, check_time: datetime) -> str:
        """Get appropriate message for current time"""
        date_str = check_time.strftime('%Y-%m-%d')
        
        # Check for special day messages
        if date_str in self.special_days:
            special_day = self.special_days[date_str]
            if special_day.hours.special_message:
                return special_day.hours.special_message
            return f"Today is {special_day.description}."
        
        # Check for holiday messages
        if check_time.date() in self.us_holidays:
            holiday_name = self.us_holidays.get(check_time.date())
            return f"We're closed today in observance of {holiday_name}. Emergency service is available 24/7."
        
        # Regular business messages
        if self.is_open(check_time):
            weekday = check_time.weekday()
            business_hours = self._get_adjusted_hours(check_time, weekday)
            if business_hours.special_message:
                return business_hours.special_message
            
            close_time = business_hours.close_time
            if close_time:
                return f"We're open until {close_time.strftime('%I:%M %p')} today."
            return "We're currently open and ready to help you."
        else:
            return self._get_closed_message(check_time)
    
    def _get_closed_message(self, check_time: datetime) -> str:
        """Get appropriate closed message"""
        next_opening = self._get_next_opening(check_time)
        
        if next_opening:
            if next_opening['is_today']:
                return f"We're currently closed but will reopen today at {next_opening['time']}. Emergency service is available 24/7."
            elif next_opening['is_tomorrow']:
                return f"We're closed for the day. We'll reopen tomorrow at {next_opening['time']}. Emergency service is available 24/7."
            else:
                return f"We're currently closed. We'll reopen {next_opening['day']} at {next_opening['time']}. Emergency service is available 24/7."
        
        return "We're currently closed. Please check our hours or call for emergency service."
    
    def _is_emergency_available(self, check_time: datetime) -> bool:
        """Check if emergency service is available"""
        return self.emergency_config['available_24_7']
    
    def _get_next_opening(self, from_time: datetime) -> Optional[Dict[str, Any]]:
        """Get next opening time"""
        search_date = from_time.date()
        search_time = from_time.time()
        
        # Search up to 14 days ahead
        for days_ahead in range(14):
            check_date = search_date + timedelta(days=days_ahead)
            check_datetime = datetime.combine(check_date, time.min).replace(tzinfo=self.timezone)
            weekday = check_date.weekday()
            
            # Skip if no hours defined for this weekday
            if weekday not in self.weekly_hours:
                continue
            
            # Check for special day
            date_str = check_date.strftime('%Y-%m-%d')
            if date_str in self.special_days:
                special_day = self.special_days[date_str]
                if special_day.hours.open_time:
                    open_time = special_day.hours.open_time
                    if days_ahead == 0 and open_time <= search_time:
                        continue  # Already passed today's opening
                    
                    return {
                        'time': open_time.strftime('%I:%M %p'),
                        'date': check_date.strftime('%Y-%m-%d'),
                        'day': check_date.strftime('%A'),
                        'is_today': days_ahead == 0,
                        'is_tomorrow': days_ahead == 1
                    }
                continue
            
            # Check federal holiday
            if check_date in self.us_holidays:
                continue
            
            # Check regular hours
            business_hours = self._get_adjusted_hours(check_datetime, weekday)
            if business_hours.open_time:
                if days_ahead == 0 and business_hours.open_time <= search_time:
                    continue  # Already passed today's opening
                
                return {
                    'time': business_hours.open_time.strftime('%I:%M %p'),
                    'date': check_date.strftime('%Y-%m-%d'),
                    'day': check_date.strftime('%A'),
                    'is_today': days_ahead == 0,
                    'is_tomorrow': days_ahead == 1
                }
        
        return None
    
    def _get_next_closing(self, from_time: datetime) -> Optional[Dict[str, Any]]:
        """Get next closing time"""
        check_date = from_time.date()
        weekday = check_date.weekday()
        
        # Check today first
        date_str = check_date.strftime('%Y-%m-%d')
        if date_str in self.special_days:
            special_day = self.special_days[date_str]
            if special_day.hours.close_time and special_day.hours.close_time > from_time.time():
                return {
                    'time': special_day.hours.close_time.strftime('%I:%M %p'),
                    'date': check_date.strftime('%Y-%m-%d'),
                    'day': check_date.strftime('%A'),
                    'is_today': True
                }
        elif weekday in self.weekly_hours:
            check_datetime = datetime.combine(check_date, time.min).replace(tzinfo=self.timezone)
            business_hours = self._get_adjusted_hours(check_datetime, weekday)
            if business_hours.close_time and business_hours.close_time > from_time.time():
                return {
                    'time': business_hours.close_time.strftime('%I:%M %p'),
                    'date': check_date.strftime('%Y-%m-%d'),
                    'day': check_date.strftime('%A'),
                    'is_today': True
                }
        
        return None
    
    def add_special_day(self, special_day: SpecialDay):
        """Add a special day (holiday, closure, etc.)"""
        date_str = special_day.date.strftime('%Y-%m-%d')
        self.special_days[date_str] = special_day
        logger.info(f"Added special day: {date_str} - {special_day.description}")
    
    def remove_special_day(self, date: datetime):
        """Remove a special day"""
        date_str = date.strftime('%Y-%m-%d')
        if date_str in self.special_days:
            del self.special_days[date_str]
            logger.info(f"Removed special day: {date_str}")
    
    def update_weekly_hours(self, weekday: int, hours: BusinessHours):
        """Update regular weekly hours"""
        if 0 <= weekday <= 6:
            self.weekly_hours[weekday] = hours
            logger.info(f"Updated hours for {['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][weekday]}")
    
    def get_weekly_schedule(self) -> Dict[str, Any]:
        """Get the weekly schedule"""
        schedule = {}
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for i, day_name in enumerate(days):
            if i in self.weekly_hours:
                hours = self.weekly_hours[i]
                schedule[day_name] = {
                    'open': hours.open_time.strftime('%I:%M %p') if hours.open_time else 'Closed',
                    'close': hours.close_time.strftime('%I:%M %p') if hours.close_time else 'Closed',
                    'service_level': hours.service_level.value,
                    'emergency_available': hours.emergency_available
                }
        
        return schedule
    
    def get_upcoming_special_days(self, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """Get upcoming special days and holidays"""
        today = datetime.now(self.timezone).date()
        end_date = today + timedelta(days=days_ahead)
        
        upcoming = []
        
        # Check special days
        for date_str, special_day in self.special_days.items():
            if today <= special_day.date.date() <= end_date:
                upcoming.append({
                    'date': special_day.date.strftime('%Y-%m-%d'),
                    'type': 'special',
                    'description': special_day.description,
                    'day_type': special_day.day_type.value,
                    'hours': special_day.hours.to_dict()
                })
        
        # Check federal holidays
        for date in self.us_holidays:
            if today <= date <= end_date:
                upcoming.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'type': 'holiday',
                    'description': self.us_holidays[date],
                    'day_type': 'holiday',
                    'hours': BusinessHours(service_level=ServiceLevel.EMERGENCY_ONLY).to_dict()
                })
        
        # Sort by date
        upcoming.sort(key=lambda x: x['date'])
        return upcoming
    
    def generate_hours_announcement(self) -> str:
        """Generate a professional hours announcement for voice system"""
        schedule = self.get_weekly_schedule()
        
        announcement = f"{self.company_name} is open "
        
        # Weekday hours
        weekday_hours = schedule['Monday']
        announcement += f"Monday through Friday from {weekday_hours['open']} to {weekday_hours['close']}, "
        
        # Saturday hours
        saturday_hours = schedule['Saturday']
        if saturday_hours['open'] != 'Closed':
            announcement += f"Saturday from {saturday_hours['open']} to {saturday_hours['close']}, "
        
        # Sunday
        announcement += "and closed on Sundays for regular service. "
        
        # Emergency service
        announcement += "Emergency service is available 24 hours a day, 7 days a week with an additional service fee. "
        
        # Location
        announcement += "We serve the Hampton Roads area including Norfolk, Virginia Beach, Chesapeake, Hampton, and Newport News."
        
        return announcement
    
    def save_configuration(self, file_path: str):
        """Save current configuration to JSON file"""
        config = {
            'weekly_hours': {str(k): v.to_dict() for k, v in self.weekly_hours.items()},
            'special_days': {k: v.to_dict() for k, v in self.special_days.items()},
            'seasonal_adjustments': self.seasonal_adjustments,
            'emergency_config': self.emergency_config,
            'timezone': str(self.timezone)
        }
        
        with open(file_path, 'w') as f:
            json.dump(config, f, indent=2, default=str)
        
        logger.info(f"Configuration saved to {file_path}")
    
    def load_configuration(self, file_path: str):
        """Load configuration from JSON file"""
        try:
            with open(file_path, 'r') as f:
                config = json.load(f)
            
            # Load weekly hours
            for weekday_str, hours_dict in config.get('weekly_hours', {}).items():
                weekday = int(weekday_str)
                self.weekly_hours[weekday] = BusinessHours(
                    open_time=datetime.strptime(hours_dict['open_time'], '%H:%M').time() if hours_dict['open_time'] else None,
                    close_time=datetime.strptime(hours_dict['close_time'], '%H:%M').time() if hours_dict['close_time'] else None,
                    service_level=ServiceLevel(hours_dict['service_level']),
                    special_message=hours_dict.get('special_message'),
                    emergency_available=hours_dict.get('emergency_available', True)
                )
            
            # Load special days
            for date_str, special_dict in config.get('special_days', {}).items():
                hours_dict = special_dict['hours']
                special_day = SpecialDay(
                    date=datetime.strptime(special_dict['date'], '%Y-%m-%d'),
                    day_type=DayType(special_dict['day_type']),
                    hours=BusinessHours(
                        open_time=datetime.strptime(hours_dict['open_time'], '%H:%M').time() if hours_dict['open_time'] else None,
                        close_time=datetime.strptime(hours_dict['close_time'], '%H:%M').time() if hours_dict['close_time'] else None,
                        service_level=ServiceLevel(hours_dict['service_level']),
                        special_message=hours_dict.get('special_message'),
                        emergency_available=hours_dict.get('emergency_available', True)
                    ),
                    description=special_dict['description'],
                    recurring_annual=special_dict.get('recurring_annual', False)
                )
                self.special_days[date_str] = special_day
            
            logger.info(f"Configuration loaded from {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to load configuration from {file_path}: {e}")

if __name__ == "__main__":
    # Test the business hours manager
    manager = BusinessHoursManager()
    
    # Test current status
    status = manager.get_current_status()
    print("Current Status:")
    print(json.dumps(status, indent=2, default=str))
    
    # Test hours announcement
    announcement = manager.generate_hours_announcement()
    print(f"\nHours Announcement:\n{announcement}")
    
    # Test special day
    special_day = SpecialDay(
        date=datetime(2024, 7, 4),
        day_type=DayType.HOLIDAY,
        hours=BusinessHours(service_level=ServiceLevel.EMERGENCY_ONLY, 
                          special_message="We're closed for Independence Day. Emergency service available."),
        description="Independence Day",
        recurring_annual=True
    )
    manager.add_special_day(special_day)
    
    # Test upcoming special days
    upcoming = manager.get_upcoming_special_days()
    print(f"\nUpcoming Special Days: {len(upcoming)}")
    for day in upcoming[:3]:
        print(f"  {day['date']}: {day['description']}")
    
    # Test schedule
    schedule = manager.get_weekly_schedule()
    print(f"\nWeekly Schedule:")
    for day, hours in schedule.items():
        print(f"  {day}: {hours['open']} - {hours['close']}")
#!/usr/bin/env python3
"""
Calendar Integration Testing Module for Karen AI Secretary
QA Agent Instance: QA-001

Comprehensive testing of calendar functionality including:
- Google Calendar API integration
- Appointment scheduling
- Availability checking
- Event creation and management
- Calendar conflict resolution
"""

import pytest
import os
import sys
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, MagicMock
import json

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestCalendarClientCore:
    """Core calendar client functionality tests"""
    
    @pytest.fixture
    def mock_calendar_service(self):
        """Mock Google Calendar service for testing"""
        mock_service = Mock()
        
        # Mock freebusy query response
        mock_service.freebusy().query().execute.return_value = {
            'calendars': {
                'primary': {
                    'busy': [
                        {
                            'start': '2024-01-15T10:00:00Z',
                            'end': '2024-01-15T11:00:00Z'
                        },
                        {
                            'start': '2024-01-15T14:00:00Z',
                            'end': '2024-01-15T15:30:00Z'
                        }
                    ]
                }
            }
        }
        
        # Mock event creation response
        mock_service.events().insert().execute.return_value = {
            'id': 'event123',
            'status': 'confirmed',
            'htmlLink': 'https://calendar.google.com/event?eid=event123',
            'summary': 'Test Appointment',
            'start': {'dateTime': '2024-01-15T13:00:00Z'},
            'end': {'dateTime': '2024-01-15T14:00:00Z'}
        }
        
        # Mock event list response
        mock_service.events().list().execute.return_value = {
            'items': [
                {
                    'id': 'event123',
                    'summary': 'Existing Appointment',
                    'start': {'dateTime': '2024-01-15T10:00:00Z'},
                    'end': {'dateTime': '2024-01-15T11:00:00Z'}
                }
            ]
        }
        
        return mock_service
    
    @pytest.fixture
    def calendar_client(self, mock_calendar_service):
        """Create calendar client with mocked service"""
        with patch('src.calendar_client.build') as mock_build:
            mock_build.return_value = mock_calendar_service
            from src.calendar_client import CalendarClient
            client = CalendarClient()
            return client
    
    def test_calendar_client_initialization(self):
        """Test calendar client initializes properly"""
        try:
            from src.calendar_client import CalendarClient
            # Test with mock to avoid OAuth requirements
            with patch('src.calendar_client.build'):
                client = CalendarClient()
                assert client is not None
        except ImportError as e:
            pytest.fail(f"Cannot import CalendarClient: {e}")
    
    def test_get_calendar_service(self, calendar_client):
        """Test calendar service is properly initialized"""
        assert calendar_client.service is not None
        assert hasattr(calendar_client.service, 'events')
        assert hasattr(calendar_client.service, 'freebusy')

class TestAvailabilityChecking:
    """Calendar availability checking functionality"""
    
    @pytest.fixture
    def calendar_client_with_events(self, mock_calendar_service):
        """Calendar client with mock events"""
        with patch('src.calendar_client.build') as mock_build:
            mock_build.return_value = mock_calendar_service
            from src.calendar_client import CalendarClient
            return CalendarClient()
    
    def test_check_availability_free_time(self, calendar_client_with_events):
        """Test checking availability for free time slots"""
        start_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        end_time = datetime(2024, 1, 15, 13, 0, 0, tzinfo=timezone.utc)
        
        is_available = calendar_client_with_events.is_time_available(start_time, end_time)
        assert is_available is True
    
    def test_check_availability_busy_time(self, calendar_client_with_events):
        """Test checking availability for busy time slots"""
        # This time conflicts with mock busy period (10:00-11:00)
        start_time = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        end_time = datetime(2024, 1, 15, 11, 30, 0, tzinfo=timezone.utc)
        
        is_available = calendar_client_with_events.is_time_available(start_time, end_time)
        assert is_available is False
    
    def test_get_free_busy_periods(self, calendar_client_with_events):
        """Test retrieving free/busy information"""
        start_date = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 15, 17, 0, 0, tzinfo=timezone.utc)
        
        busy_periods = calendar_client_with_events.get_busy_periods(start_date, end_date)
        
        assert isinstance(busy_periods, list)
        assert len(busy_periods) >= 0
        
        # Check format of busy periods
        if busy_periods:
            for period in busy_periods:
                assert 'start' in period
                assert 'end' in period
    
    def test_find_available_slots(self, calendar_client_with_events):
        """Test finding available time slots"""
        start_date = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 15, 17, 0, 0, tzinfo=timezone.utc)
        duration_minutes = 60
        
        available_slots = calendar_client_with_events.find_available_slots(
            start_date, end_date, duration_minutes
        )
        
        assert isinstance(available_slots, list)
        # Should find slots between busy periods
        
        if available_slots:
            for slot in available_slots:
                assert 'start' in slot
                assert 'end' in slot
                
                # Verify slot duration
                slot_start = datetime.fromisoformat(slot['start'].replace('Z', '+00:00'))
                slot_end = datetime.fromisoformat(slot['end'].replace('Z', '+00:00'))
                duration = (slot_end - slot_start).total_seconds() / 60
                assert duration >= duration_minutes

class TestEventCreation:
    """Calendar event creation and management"""
    
    @pytest.fixture
    def calendar_client_for_events(self, mock_calendar_service):
        """Calendar client configured for event operations"""
        with patch('src.calendar_client.build') as mock_build:
            mock_build.return_value = mock_calendar_service
            from src.calendar_client import CalendarClient
            return CalendarClient()
    
    def test_create_basic_event(self, calendar_client_for_events):
        """Test creating a basic calendar event"""
        event_data = {
            'summary': 'Plumbing Appointment',
            'description': 'Kitchen sink repair',
            'start_time': datetime(2024, 1, 15, 13, 0, 0, tzinfo=timezone.utc),
            'end_time': datetime(2024, 1, 15, 14, 0, 0, tzinfo=timezone.utc),
            'attendees': ['client@example.com']
        }
        
        created_event = calendar_client_for_events.create_event(event_data)
        
        assert created_event is not None
        assert 'id' in created_event
        assert created_event['status'] == 'confirmed'
        assert created_event['summary'] == 'Plumbing Appointment'
    
    def test_create_event_with_location(self, calendar_client_for_events):
        """Test creating event with location information"""
        event_data = {
            'summary': 'Home Service Call',
            'description': 'Bathroom plumbing issue',
            'start_time': datetime(2024, 1, 15, 13, 0, 0, tzinfo=timezone.utc),
            'end_time': datetime(2024, 1, 15, 14, 0, 0, tzinfo=timezone.utc),
            'location': '123 Main St, Anytown, USA',
            'attendees': ['client@example.com']
        }
        
        created_event = calendar_client_for_events.create_event(event_data)
        
        assert created_event is not None
        assert 'id' in created_event
    
    def test_create_recurring_event(self, calendar_client_for_events):
        """Test creating recurring calendar event"""
        event_data = {
            'summary': 'Weekly Maintenance Check',
            'description': 'Regular maintenance visit',
            'start_time': datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            'end_time': datetime(2024, 1, 15, 11, 0, 0, tzinfo=timezone.utc),
            'recurrence': ['RRULE:FREQ=WEEKLY;COUNT=4'],
            'attendees': ['client@example.com']
        }
        
        created_event = calendar_client_for_events.create_event(event_data)
        
        assert created_event is not None
        assert 'id' in created_event
    
    def test_event_creation_conflict_detection(self, calendar_client_for_events):
        """Test detection of calendar conflicts during event creation"""
        # Try to create event during busy time (10:00-11:00 from mock)
        conflicting_event = {
            'summary': 'Conflicting Appointment',
            'start_time': datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            'end_time': datetime(2024, 1, 15, 11, 30, 0, tzinfo=timezone.utc),
            'attendees': ['client@example.com']
        }
        
        # Should detect conflict and handle appropriately
        with pytest.raises(Exception) as exc_info:
            calendar_client_for_events.create_event_with_conflict_check(conflicting_event)
        
        assert "conflict" in str(exc_info.value).lower() or "busy" in str(exc_info.value).lower()

class TestCalendarSearch:
    """Calendar search and query functionality"""
    
    @pytest.fixture
    def calendar_with_events(self, mock_calendar_service):
        """Calendar client with sample events"""
        with patch('src.calendar_client.build') as mock_build:
            mock_build.return_value = mock_calendar_service
            from src.calendar_client import CalendarClient
            return CalendarClient()
    
    def test_search_events_by_date_range(self, calendar_with_events):
        """Test searching events within date range"""
        start_date = datetime(2024, 1, 15, 0, 0, 0, tzinfo=timezone.utc)
        end_date = datetime(2024, 1, 15, 23, 59, 59, tzinfo=timezone.utc)
        
        events = calendar_with_events.get_events_in_range(start_date, end_date)
        
        assert isinstance(events, list)
        if events:
            for event in events:
                assert 'id' in event
                assert 'summary' in event
    
    def test_search_events_by_keyword(self, calendar_with_events):
        """Test searching events by keyword"""
        keyword = "Appointment"
        
        events = calendar_with_events.search_events(keyword)
        
        assert isinstance(events, list)
        if events:
            for event in events:
                summary = event.get('summary', '').lower()
                description = event.get('description', '').lower()
                assert keyword.lower() in summary or keyword.lower() in description
    
    def test_get_next_available_appointment(self, calendar_with_events):
        """Test finding next available appointment slot"""
        duration_minutes = 60
        
        next_slot = calendar_with_events.get_next_available_slot(duration_minutes)
        
        assert next_slot is not None
        assert 'start' in next_slot
        assert 'end' in next_slot
        
        # Verify the slot is in the future
        slot_start = datetime.fromisoformat(next_slot['start'].replace('Z', '+00:00'))
        assert slot_start > datetime.now(timezone.utc)

class TestCalendarNotifications:
    """Calendar notification and reminder functionality"""
    
    @pytest.fixture
    def calendar_with_notifications(self, mock_calendar_service):
        """Calendar client with notification support"""
        with patch('src.calendar_client.build') as mock_build:
            mock_build.return_value = mock_calendar_service
            from src.calendar_client import CalendarClient
            return CalendarClient()
    
    def test_create_event_with_reminders(self, calendar_with_notifications):
        """Test creating event with email/popup reminders"""
        event_data = {
            'summary': 'Important Meeting',
            'start_time': datetime(2024, 1, 15, 13, 0, 0, tzinfo=timezone.utc),
            'end_time': datetime(2024, 1, 15, 14, 0, 0, tzinfo=timezone.utc),
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},  # 24 hours
                    {'method': 'popup', 'minutes': 10}  # 10 minutes
                ]
            }
        }
        
        created_event = calendar_with_notifications.create_event(event_data)
        
        assert created_event is not None
        assert 'id' in created_event
    
    def test_update_event_reminders(self, calendar_with_notifications):
        """Test updating reminders for existing event"""
        event_id = 'event123'
        new_reminders = {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 60}  # 1 hour
            ]
        }
        
        updated_event = calendar_with_notifications.update_event_reminders(
            event_id, new_reminders
        )
        
        assert updated_event is not None

class TestCalendarErrorHandling:
    """Calendar API error handling tests"""
    
    @pytest.fixture
    def failing_calendar_service(self):
        """Calendar service that simulates various failure modes"""
        mock_service = Mock()
        
        # Configure different failure scenarios
        mock_service.freebusy().query().execute.side_effect = Exception("Calendar API Error")
        mock_service.events().insert().execute.side_effect = Exception("Event Creation Failed")
        mock_service.events().list().execute.side_effect = Exception("Event List Failed")
        
        return mock_service
    
    @pytest.fixture
    def failing_calendar_client(self, failing_calendar_service):
        """Calendar client with failing service"""
        with patch('src.calendar_client.build') as mock_build:
            mock_build.return_value = failing_calendar_service
            from src.calendar_client import CalendarClient
            return CalendarClient()
    
    def test_calendar_api_error_handling(self, failing_calendar_client):
        """Test handling of Calendar API errors"""
        start_date = datetime.now(timezone.utc)
        end_date = start_date + timedelta(hours=1)
        
        with pytest.raises(Exception) as exc_info:
            failing_calendar_client.get_busy_periods(start_date, end_date)
        
        assert "Calendar API Error" in str(exc_info.value)
    
    def test_event_creation_error_handling(self, failing_calendar_client):
        """Test handling of event creation errors"""
        event_data = {
            'summary': 'Test Event',
            'start_time': datetime.now(timezone.utc),
            'end_time': datetime.now(timezone.utc) + timedelta(hours=1)
        }
        
        with pytest.raises(Exception) as exc_info:
            failing_calendar_client.create_event(event_data)
        
        assert "Event Creation Failed" in str(exc_info.value)
    
    def test_invalid_date_handling(self):
        """Test handling of invalid date formats"""
        from src.calendar_client import CalendarClient
        
        with patch('src.calendar_client.build'):
            client = CalendarClient()
            
            # Test with invalid date strings
            invalid_dates = [
                "not-a-date",
                "2024-13-40",  # Invalid month/day
                "2024-01-01T25:00:00Z"  # Invalid hour
            ]
            
            for invalid_date in invalid_dates:
                with pytest.raises((ValueError, TypeError)):
                    client._parse_datetime(invalid_date)

class TestCalendarTimeZones:
    """Calendar timezone handling tests"""
    
    @pytest.fixture
    def calendar_timezone_client(self, mock_calendar_service):
        """Calendar client for timezone testing"""
        with patch('src.calendar_client.build') as mock_build:
            mock_build.return_value = mock_calendar_service
            from src.calendar_client import CalendarClient
            return CalendarClient()
    
    def test_timezone_conversion(self, calendar_timezone_client):
        """Test timezone conversion for events"""
        # Test converting from local time to UTC
        local_time = datetime(2024, 1, 15, 13, 0, 0)  # No timezone
        utc_time = calendar_timezone_client._convert_to_utc(local_time, 'America/New_York')
        
        assert utc_time.tzinfo == timezone.utc
        # EST is UTC-5, so 1PM EST = 6PM UTC
        assert utc_time.hour == 18
    
    def test_different_timezone_events(self, calendar_timezone_client):
        """Test creating events in different timezones"""
        timezones_to_test = [
            'America/New_York',
            'Europe/London',
            'Asia/Tokyo',
            'Australia/Sydney'
        ]
        
        for tz in timezones_to_test:
            event_data = {
                'summary': f'Event in {tz}',
                'start_time': datetime(2024, 1, 15, 13, 0, 0),
                'end_time': datetime(2024, 1, 15, 14, 0, 0),
                'timezone': tz
            }
            
            created_event = calendar_timezone_client.create_event(event_data)
            assert created_event is not None

@pytest.mark.integration
class TestCalendarIntegration:
    """Integration tests for calendar functionality"""
    
    @pytest.mark.skip(reason="Requires live Google Calendar API credentials")
    def test_live_calendar_access(self):
        """Test accessing live Google Calendar"""
        from src.calendar_client import CalendarClient
        
        client = CalendarClient()
        
        # Test basic calendar access
        start_date = datetime.now(timezone.utc)
        end_date = start_date + timedelta(days=1)
        
        events = client.get_events_in_range(start_date, end_date)
        assert isinstance(events, list)
    
    @pytest.mark.skip(reason="Requires live Google Calendar API credentials")
    def test_live_event_creation(self):
        """Test creating actual calendar event"""
        from src.calendar_client import CalendarClient
        
        client = CalendarClient()
        
        event_data = {
            'summary': 'Test Event - Please Delete',
            'description': 'This is a test event created by automated tests',
            'start_time': datetime.now(timezone.utc) + timedelta(hours=1),
            'end_time': datetime.now(timezone.utc) + timedelta(hours=2)
        }
        
        created_event = client.create_event(event_data)
        assert created_event is not None
        assert 'id' in created_event
        
        # Clean up - delete the test event
        client.delete_event(created_event['id'])

@pytest.mark.performance
class TestCalendarPerformance:
    """Performance tests for calendar operations"""
    
    def test_availability_check_performance(self):
        """Test performance of availability checking"""
        import time
        
        with patch('src.calendar_client.build') as mock_build:
            mock_service = Mock()
            
            # Mock response with many busy periods
            busy_periods = []
            for i in range(100):  # 100 busy periods
                start_time = datetime(2024, 1, 15, 9, 0, 0) + timedelta(minutes=i*10)
                end_time = start_time + timedelta(minutes=30)
                busy_periods.append({
                    'start': start_time.isoformat() + 'Z',
                    'end': end_time.isoformat() + 'Z'
                })
            
            mock_service.freebusy().query().execute.return_value = {
                'calendars': {'primary': {'busy': busy_periods}}
            }
            
            mock_build.return_value = mock_service
            
            from src.calendar_client import CalendarClient
            client = CalendarClient()
            
            start_time = time.time()
            
            # Check availability for 10 different time slots
            test_date = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)
            for i in range(10):
                slot_start = test_date + timedelta(hours=i)
                slot_end = slot_start + timedelta(hours=1)
                client.is_time_available(slot_start, slot_end)
            
            processing_time = time.time() - start_time
            
            # Should process 10 availability checks in under 2 seconds
            assert processing_time < 2.0
    
    def test_event_creation_performance(self):
        """Test performance of event creation"""
        import time
        
        with patch('src.calendar_client.build') as mock_build:
            mock_service = Mock()
            mock_service.events().insert().execute.return_value = {'id': 'test123'}
            mock_build.return_value = mock_service
            
            from src.calendar_client import CalendarClient
            client = CalendarClient()
            
            start_time = time.time()
            
            # Create 10 events
            for i in range(10):
                event_data = {
                    'summary': f'Test Event {i}',
                    'start_time': datetime.now(timezone.utc) + timedelta(hours=i),
                    'end_time': datetime.now(timezone.utc) + timedelta(hours=i+1)
                }
                client.create_event(event_data)
            
            processing_time = time.time() - start_time
            
            # Should create 10 events in under 3 seconds
            assert processing_time < 3.0

if __name__ == "__main__":
    # Run calendar integration tests
    pytest.main([__file__, "-v", "--tb=short"])
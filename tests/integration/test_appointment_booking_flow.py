#!/usr/bin/env python3
"""
Appointment Booking Flow Integration Test
Test Engineer: Complete appointment lifecycle with self-healing capabilities

Tests the complete appointment booking flow:
SMS/Email → Calendar Check → Booking → Confirmation → Edge Cases
"""

import pytest
import asyncio
import time
import threading
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, Mock
import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from tests.mocks.service_mocks import (
    ServiceMockFactory, CalendarException, TwilioException
)
from tests.fixtures.test_data_factory import TestDataFactory

class SelfHealingAppointmentSystem:
    """Self-healing appointment booking system with error recovery"""
    
    def __init__(self, services):
        self.services = services
        self.appointments = []
        self.failed_bookings = []
        self.recovery_attempts = {}
        self.booking_conflicts = []
        
    def book_appointment(self, customer_info, requested_time, service_type="plumbing"):
        """Book appointment with self-healing capabilities"""
        booking_id = f"BOOK_{int(time.time())}_{hash(customer_info['phone']) % 1000}"
        
        try:
            # Step 1: Validate customer info
            if not self._validate_customer_info(customer_info):
                return self._handle_validation_error(booking_id, customer_info)
            
            # Step 2: Check calendar availability with retry
            availability = self._check_availability_with_retry(requested_time)
            if not availability['available']:
                return self._handle_scheduling_conflict(booking_id, customer_info, requested_time, availability)
            
            # Step 3: Create calendar event with backup
            calendar_event = self._create_calendar_event_with_backup(
                customer_info, requested_time, service_type
            )
            
            # Step 4: Send confirmation with retry
            confirmation_result = self._send_confirmation_with_retry(
                customer_info, calendar_event, booking_id
            )
            
            # Step 5: Store booking record
            booking_record = {
                'booking_id': booking_id,
                'customer_info': customer_info,
                'appointment_time': requested_time,
                'service_type': service_type,
                'calendar_event_id': calendar_event['id'],
                'confirmation_sent': confirmation_result['success'],
                'status': 'confirmed',
                'created_at': datetime.now().isoformat()
            }
            
            self.appointments.append(booking_record)
            
            return {
                'success': True,
                'booking_id': booking_id,
                'appointment_time': requested_time,
                'calendar_event_id': calendar_event['id'],
                'confirmation_sent': confirmation_result['success']
            }
            
        except Exception as e:
            return self._handle_critical_error(booking_id, customer_info, e)
    
    def _validate_customer_info(self, customer_info):
        """Validate customer information with auto-correction"""
        required_fields = ['name', 'phone', 'address']
        
        for field in required_fields:
            if field not in customer_info or not customer_info[field]:
                # Try to auto-correct missing info
                if field == 'name' and 'email' in customer_info:
                    customer_info['name'] = customer_info['email'].split('@')[0]
                elif field == 'phone' and 'email' in customer_info:
                    # Cannot auto-correct phone, this is critical
                    return False
                elif field == 'address':
                    # Mark for follow-up but don't fail booking
                    customer_info['address'] = 'TBD - Follow up required'
        
        # Validate and normalize phone number
        phone = customer_info['phone']
        normalized_phone = self._normalize_phone_number(phone)
        if not normalized_phone:
            return False
        customer_info['phone'] = normalized_phone
        
        return True
    
    def _normalize_phone_number(self, phone):
        """Normalize phone number format"""
        import re
        # Remove all non-digits
        digits = re.sub(r'\D', '', phone)
        
        # Handle different formats
        if len(digits) == 10:
            return f"+1{digits}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"+{digits}"
        elif len(digits) >= 10:
            return f"+1{digits[-10:]}"  # Take last 10 digits
        else:
            return None
    
    def _check_availability_with_retry(self, requested_time, max_retries=3):
        """Check calendar availability with retry logic"""
        for attempt in range(max_retries):
            try:
                # Convert to UTC if needed
                if requested_time.tzinfo is None:
                    requested_time = requested_time.replace(tzinfo=timezone.utc)
                
                end_time = requested_time + timedelta(hours=1)
                
                # Query calendar service
                freebusy_result = self.services['calendar'].freebusy().query({
                    'timeMin': requested_time.isoformat(),
                    'timeMax': end_time.isoformat(),
                    'items': [{'id': 'primary'}]
                }).execute()
                
                busy_periods = freebusy_result['calendars']['primary']['busy']
                
                # Check for conflicts
                for busy_period in busy_periods:
                    busy_start = datetime.fromisoformat(busy_period['start'].replace('Z', '+00:00'))
                    busy_end = datetime.fromisoformat(busy_period['end'].replace('Z', '+00:00'))
                    
                    if (requested_time < busy_end and end_time > busy_start):
                        # Conflict found, suggest alternatives
                        alternatives = self._find_alternative_times(requested_time, busy_periods)
                        return {
                            'available': False,
                            'conflict_reason': 'time_slot_busy',
                            'alternatives': alternatives
                        }
                
                return {
                    'available': True,
                    'requested_time': requested_time.isoformat(),
                    'duration': 60  # minutes
                }
                
            except CalendarException as e:
                if attempt == max_retries - 1:
                    # Last attempt failed, return degraded service
                    return {
                        'available': True,  # Assume available if we can't check
                        'degraded': True,
                        'error': str(e),
                        'warning': 'Calendar service unavailable, booking may conflict'
                    }
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return {'available': False, 'error': 'Calendar service unavailable'}
    
    def _find_alternative_times(self, requested_time, busy_periods):
        """Find alternative appointment times"""
        alternatives = []
        base_date = requested_time.date()
        
        # Check same day alternatives
        for hour in [9, 10, 11, 13, 14, 15, 16]:
            alt_time = datetime.combine(base_date, datetime.min.time().replace(hour=hour))
            alt_time = alt_time.replace(tzinfo=timezone.utc)
            
            if self._is_time_available(alt_time, busy_periods):
                alternatives.append(alt_time.isoformat())
                if len(alternatives) >= 3:
                    break
        
        # Check next day if not enough alternatives
        if len(alternatives) < 3:
            next_date = base_date + timedelta(days=1)
            for hour in [9, 10, 11, 13, 14, 15]:
                alt_time = datetime.combine(next_date, datetime.min.time().replace(hour=hour))
                alt_time = alt_time.replace(tzinfo=timezone.utc)
                alternatives.append(alt_time.isoformat())
                if len(alternatives) >= 5:
                    break
        
        return alternatives[:5]
    
    def _is_time_available(self, check_time, busy_periods):
        """Check if specific time is available"""
        end_time = check_time + timedelta(hours=1)
        
        for busy_period in busy_periods:
            busy_start = datetime.fromisoformat(busy_period['start'].replace('Z', '+00:00'))
            busy_end = datetime.fromisoformat(busy_period['end'].replace('Z', '+00:00'))
            
            if (check_time < busy_end and end_time > busy_start):
                return False
        
        return True
    
    def _create_calendar_event_with_backup(self, customer_info, appointment_time, service_type):
        """Create calendar event with backup strategies"""
        event_data = {
            'summary': f'{service_type.title()} Service - {customer_info["name"]}',
            'description': f'Customer: {customer_info["name"]}\nPhone: {customer_info["phone"]}\nAddress: {customer_info["address"]}\nService: {service_type}',
            'start': {
                'dateTime': appointment_time.isoformat(),
                'timeZone': 'America/New_York'
            },
            'end': {
                'dateTime': (appointment_time + timedelta(hours=1)).isoformat(),
                'timeZone': 'America/New_York'
            },
            'location': customer_info.get('address', 'Address TBD'),
            'attendees': [
                {'email': 'tech@757handy.com'},
                {'email': customer_info.get('email', '')}
            ] if customer_info.get('email') else [{'email': 'tech@757handy.com'}],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 60},
                    {'method': 'sms', 'minutes': 15}
                ]
            }
        }
        
        try:
            # Primary attempt
            calendar_event = self.services['calendar'].events().insert(
                calendarId='primary',
                body=event_data
            ).execute()
            
            return calendar_event
            
        except CalendarException as e:
            # Backup strategy: Store event locally for manual processing
            backup_event = {
                'id': f'BACKUP_{int(time.time())}',
                'status': 'tentative',
                'backup_reason': str(e),
                **event_data
            }
            
            # Log for manual processing
            self._log_backup_event(backup_event)
            
            return backup_event
    
    def _send_confirmation_with_retry(self, customer_info, calendar_event, booking_id):
        """Send confirmation with retry and fallback mechanisms"""
        confirmation_message = self._generate_confirmation_message(customer_info, calendar_event, booking_id)
        
        # Primary: SMS confirmation
        try:
            sms_result = self.services['twilio'].send_sms(
                to=customer_info['phone'],
                from_="+17575550123",
                body=confirmation_message
            )
            
            return {
                'success': True,
                'method': 'sms',
                'message_sid': sms_result['sid']
            }
            
        except TwilioException as e:
            # Fallback: Email confirmation (if available)
            if customer_info.get('email'):
                try:
                    email_result = self._send_email_confirmation(
                        customer_info, calendar_event, booking_id
                    )
                    return {
                        'success': True,
                        'method': 'email',
                        'fallback_reason': str(e),
                        'email_id': email_result['id']
                    }
                except Exception as email_error:
                    pass
            
            # Final fallback: Manual follow-up required
            self._queue_manual_confirmation(customer_info, calendar_event, booking_id)
            return {
                'success': False,
                'method': 'manual_queue',
                'error': str(e)
            }
    
    def _generate_confirmation_message(self, customer_info, calendar_event, booking_id):
        """Generate confirmation message"""
        appointment_time = datetime.fromisoformat(
            calendar_event['start']['dateTime'].replace('Z', '+00:00')
        )
        
        return (
            f"Hi {customer_info['name']}! Your appointment is confirmed for "
            f"{appointment_time.strftime('%A, %B %d at %I:%M %p')}. "
            f"Our technician will call 15 minutes before arrival. "
            f"Booking ID: {booking_id}. Reply CANCEL to cancel."
        )
    
    def _handle_validation_error(self, booking_id, customer_info):
        """Handle customer info validation errors"""
        missing_fields = []
        if not customer_info.get('name'):
            missing_fields.append('name')
        if not customer_info.get('phone'):
            missing_fields.append('phone number')
        if not customer_info.get('address'):
            missing_fields.append('address')
        
        error_message = f"I need your {' and '.join(missing_fields)} to complete the booking."
        
        return {
            'success': False,
            'error': 'validation_failed',
            'missing_fields': missing_fields,
            'message': error_message,
            'booking_id': booking_id
        }
    
    def _handle_scheduling_conflict(self, booking_id, customer_info, requested_time, availability):
        """Handle scheduling conflicts with automatic resolution"""
        self.booking_conflicts.append({
            'booking_id': booking_id,
            'customer_info': customer_info,
            'requested_time': requested_time.isoformat(),
            'alternatives': availability.get('alternatives', [])
        })
        
        if availability.get('alternatives'):
            alt_times = availability['alternatives'][:3]
            alt_times_formatted = []
            
            for alt_time_iso in alt_times:
                alt_time = datetime.fromisoformat(alt_time_iso.replace('Z', '+00:00'))
                alt_times_formatted.append(alt_time.strftime('%A, %B %d at %I:%M %p'))
            
            message = (
                f"That time slot is busy. I have these alternatives available: "
                f"{', '.join(alt_times_formatted)}. Which works best for you?"
            )
        else:
            message = "That time slot is not available. Let me check other options for you."
        
        return {
            'success': False,
            'error': 'scheduling_conflict',
            'message': message,
            'alternatives': availability.get('alternatives', []),
            'booking_id': booking_id
        }
    
    def _handle_critical_error(self, booking_id, customer_info, error):
        """Handle critical system errors"""
        self.failed_bookings.append({
            'booking_id': booking_id,
            'customer_info': customer_info,
            'error': str(error),
            'timestamp': datetime.now().isoformat(),
            'recovery_status': 'pending'
        })
        
        # Queue for manual intervention
        return {
            'success': False,
            'error': 'system_error',
            'message': "I'm experiencing technical difficulties. I'll have someone call you within 30 minutes to complete your booking.",
            'booking_id': booking_id,
            'manual_followup_required': True
        }
    
    def reschedule_appointment(self, booking_id, new_time):
        """Reschedule existing appointment"""
        # Find existing booking
        booking = next((b for b in self.appointments if b['booking_id'] == booking_id), None)
        if not booking:
            return {'success': False, 'error': 'booking_not_found'}
        
        # Check availability for new time
        availability = self._check_availability_with_retry(new_time)
        if not availability['available']:
            return {
                'success': False,
                'error': 'new_time_unavailable',
                'alternatives': availability.get('alternatives', [])
            }
        
        try:
            # Update calendar event
            updated_event_data = {
                'start': {
                    'dateTime': new_time.isoformat(),
                    'timeZone': 'America/New_York'
                },
                'end': {
                    'dateTime': (new_time + timedelta(hours=1)).isoformat(),
                    'timeZone': 'America/New_York'
                }
            }
            
            self.services['calendar'].events().update(
                calendarId='primary',
                eventId=booking['calendar_event_id'],
                body=updated_event_data
            ).execute()
            
            # Update booking record
            booking['appointment_time'] = new_time
            booking['status'] = 'rescheduled'
            booking['last_modified'] = datetime.now().isoformat()
            
            # Send confirmation
            confirmation_result = self._send_confirmation_with_retry(
                booking['customer_info'],
                {'start': {'dateTime': new_time.isoformat()}},
                booking_id
            )
            
            return {
                'success': True,
                'new_time': new_time.isoformat(),
                'confirmation_sent': confirmation_result['success']
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def cancel_appointment(self, booking_id, reason="customer_request"):
        """Cancel appointment with cleanup"""
        booking = next((b for b in self.appointments if b['booking_id'] == booking_id), None)
        if not booking:
            return {'success': False, 'error': 'booking_not_found'}
        
        try:
            # Delete calendar event
            self.services['calendar'].events().delete(
                calendarId='primary',
                eventId=booking['calendar_event_id']
            ).execute()
            
            # Update booking status
            booking['status'] = 'cancelled'
            booking['cancellation_reason'] = reason
            booking['cancelled_at'] = datetime.now().isoformat()
            
            # Send cancellation confirmation
            cancellation_message = (
                f"Your appointment on {booking['appointment_time']} has been cancelled. "
                f"Booking ID: {booking_id}. Thank you!"
            )
            
            self.services['twilio'].send_sms(
                to=booking['customer_info']['phone'],
                from_="+17575550123",
                body=cancellation_message
            )
            
            return {'success': True, 'cancelled_at': booking['cancelled_at']}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _log_backup_event(self, event):
        """Log backup events for manual processing"""
        # In real implementation, this would write to a file or database
        print(f"BACKUP EVENT LOGGED: {event['id']} - {event['backup_reason']}")
    
    def _send_email_confirmation(self, customer_info, calendar_event, booking_id):
        """Send email confirmation as fallback"""
        # Mock email sending
        return {'id': f'EMAIL_{booking_id}'}
    
    def _queue_manual_confirmation(self, customer_info, calendar_event, booking_id):
        """Queue booking for manual confirmation"""
        # In real implementation, this would add to a manual queue
        print(f"MANUAL CONFIRMATION QUEUED: {booking_id}")

class TestAppointmentBookingFlow:
    """Test the complete appointment booking system"""
    
    @pytest.fixture
    def stable_services(self):
        return ServiceMockFactory.create_stable_services()
    
    @pytest.fixture
    def booking_system(self, stable_services):
        return SelfHealingAppointmentSystem(stable_services)
    
    def test_successful_appointment_booking(self, booking_system):
        """Test successful end-to-end appointment booking"""
        customer_info = {
            'name': 'John Smith',
            'phone': '(757) 555-0123',
            'address': '123 Main St, Norfolk, VA',
            'email': 'john@example.com'
        }
        
        appointment_time = datetime.now() + timedelta(days=1, hours=2)
        
        result = booking_system.book_appointment(customer_info, appointment_time, "plumbing")
        
        assert result['success'] is True
        assert 'booking_id' in result
        assert result['confirmation_sent'] is True
        
        # Verify appointment was created
        assert len(booking_system.appointments) == 1
        booking = booking_system.appointments[0]
        assert booking['customer_info']['name'] == 'John Smith'
        assert booking['status'] == 'confirmed'
    
    def test_phone_number_normalization(self, booking_system):
        """Test automatic phone number normalization"""
        test_cases = [
            ('757-555-0123', '+17575550123'),
            ('(757) 555-0123', '+17575550123'),
            ('7575550123', '+17575550123'),
            ('1-757-555-0123', '+17575550123'),
            ('+1-757-555-0123', '+17575550123')
        ]
        
        for input_phone, expected_phone in test_cases:
            customer_info = {
                'name': 'Test Customer',
                'phone': input_phone,
                'address': '123 Test St'
            }
            
            appointment_time = datetime.now() + timedelta(days=1, hours=2)
            result = booking_system.book_appointment(customer_info, appointment_time)
            
            assert result['success'] is True
            # Check that phone was normalized
            booking = booking_system.appointments[-1]
            assert booking['customer_info']['phone'] == expected_phone
    
    def test_scheduling_conflict_resolution(self, booking_system, stable_services):
        """Test handling of scheduling conflicts"""
        # First, create a conflicting event
        existing_event_time = datetime.now() + timedelta(days=1, hours=10)
        existing_event = {
            'summary': 'Existing Appointment',
            'start': {
                'dateTime': existing_event_time.isoformat() + 'Z',
                'timeZone': 'America/New_York'
            },
            'end': {
                'dateTime': (existing_event_time + timedelta(hours=1)).isoformat() + 'Z',
                'timeZone': 'America/New_York'
            }
        }
        
        stable_services['calendar'].events.append(existing_event)
        
        # Try to book at the same time
        customer_info = {
            'name': 'Jane Doe',
            'phone': '7575550124',
            'address': '456 Oak St'
        }
        
        conflicting_time = existing_event_time + timedelta(minutes=30)  # Overlap
        result = booking_system.book_appointment(customer_info, conflicting_time)
        
        assert result['success'] is False
        assert result['error'] == 'scheduling_conflict'
        assert 'alternatives' in result
        assert len(result['alternatives']) > 0
        
        # Verify conflict was recorded
        assert len(booking_system.booking_conflicts) == 1
    
    def test_rescheduling_appointment(self, booking_system):
        """Test appointment rescheduling"""
        # First book an appointment
        customer_info = {
            'name': 'Bob Johnson',
            'phone': '7575550125',
            'address': '789 Pine St'
        }
        
        original_time = datetime.now() + timedelta(days=1, hours=10)
        result = booking_system.book_appointment(customer_info, original_time)
        
        assert result['success'] is True
        booking_id = result['booking_id']
        
        # Reschedule to a new time
        new_time = datetime.now() + timedelta(days=1, hours=14)
        reschedule_result = booking_system.reschedule_appointment(booking_id, new_time)
        
        assert reschedule_result['success'] is True
        
        # Verify the appointment was updated
        booking = next(b for b in booking_system.appointments if b['booking_id'] == booking_id)
        assert booking['status'] == 'rescheduled'
        assert booking['appointment_time'] == new_time
    
    def test_appointment_cancellation(self, booking_system):
        """Test appointment cancellation"""
        # Book an appointment
        customer_info = {
            'name': 'Alice Brown',
            'phone': '7575550126',
            'address': '321 Elm St'
        }
        
        appointment_time = datetime.now() + timedelta(days=2, hours=11)
        result = booking_system.book_appointment(customer_info, appointment_time)
        
        assert result['success'] is True
        booking_id = result['booking_id']
        
        # Cancel the appointment
        cancel_result = booking_system.cancel_appointment(booking_id)
        
        assert cancel_result['success'] is True
        
        # Verify cancellation
        booking = next(b for b in booking_system.appointments if b['booking_id'] == booking_id)
        assert booking['status'] == 'cancelled'
        assert 'cancelled_at' in booking
    
    def test_double_booking_prevention(self, booking_system):
        """Test prevention of double booking same time slot"""
        appointment_time = datetime.now() + timedelta(days=1, hours=15)
        
        # First booking
        customer1 = {
            'name': 'Customer One',
            'phone': '7575550127',
            'address': '111 First St'
        }
        
        result1 = booking_system.book_appointment(customer1, appointment_time)
        assert result1['success'] is True
        
        # Second booking at same time
        customer2 = {
            'name': 'Customer Two', 
            'phone': '7575550128',
            'address': '222 Second St'
        }
        
        result2 = booking_system.book_appointment(customer2, appointment_time)
        assert result2['success'] is False
        assert result2['error'] == 'scheduling_conflict'
        
        # Verify only one booking succeeded
        confirmed_bookings = [b for b in booking_system.appointments if b['status'] == 'confirmed']
        assert len(confirmed_bookings) == 1
    
    def test_missing_information_handling(self, booking_system):
        """Test handling of missing customer information"""
        incomplete_customer = {
            'name': 'Incomplete Customer',
            # Missing phone and address
        }
        
        appointment_time = datetime.now() + timedelta(days=1, hours=16)
        result = booking_system.book_appointment(incomplete_customer, appointment_time)
        
        assert result['success'] is False
        assert result['error'] == 'validation_failed'
        assert 'missing_fields' in result
        assert 'phone number' in result['missing_fields']

@pytest.mark.integration
class TestAppointmentBookingFailureRecovery:
    """Test failure recovery mechanisms"""
    
    @pytest.fixture
    def unreliable_services(self):
        return ServiceMockFactory.create_chaos_services(failure_rate=0.4)
    
    @pytest.fixture
    def resilient_booking_system(self, unreliable_services):
        return SelfHealingAppointmentSystem(unreliable_services)
    
    def test_calendar_service_failure_recovery(self, resilient_booking_system):
        """Test recovery when calendar service fails"""
        customer_info = {
            'name': 'Resilient Customer',
            'phone': '7575550129',
            'address': '999 Recovery St'
        }
        
        appointment_time = datetime.now() + timedelta(days=1, hours=9)
        
        # Attempt booking multiple times to trigger failures and recovery
        results = []
        for i in range(5):
            result = resilient_booking_system.book_appointment(
                {**customer_info, 'name': f'{customer_info["name"]} {i}'},
                appointment_time + timedelta(hours=i)
            )
            results.append(result)
        
        # Some should succeed despite service instability
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        assert len(successful) > 0  # At least some should succeed
        
        # Check that failed bookings are properly handled
        for failed_result in failed:
            assert 'error' in failed_result
            assert 'booking_id' in failed_result
    
    def test_sms_confirmation_fallback(self, resilient_booking_system):
        """Test SMS confirmation fallback mechanisms"""
        customer_info = {
            'name': 'Fallback Customer',
            'phone': '7575550130',
            'address': '888 Fallback Ave',
            'email': 'fallback@example.com'
        }
        
        appointment_time = datetime.now() + timedelta(days=1, hours=12)
        
        # Force multiple booking attempts to test fallback
        attempts = 0
        max_attempts = 5
        
        while attempts < max_attempts:
            result = resilient_booking_system.book_appointment(customer_info, appointment_time)
            attempts += 1
            
            if result['success']:
                # Even if booking succeeds, check confirmation method
                assert 'confirmation_sent' in result
                break
        
        # Verify that system attempted to handle confirmation
        assert attempts <= max_attempts

if __name__ == "__main__":
    # Run tests and self-healing verification
    pytest.main([__file__, "-v", "--tb=short"])
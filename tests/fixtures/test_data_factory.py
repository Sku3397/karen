#!/usr/bin/env python3
"""
Test Data Factory for Karen AI Testing
Generates realistic test data for comprehensive testing scenarios
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import faker
import json

# Initialize Faker for realistic data generation
fake = faker.Faker()

class TestDataFactory:
    """Factory for generating realistic test data"""
    
    @staticmethod
    def create_customer_email(
        intent: str = "appointment_request",
        urgency: str = "normal",
        include_phone: bool = True
    ) -> Dict[str, Any]:
        """Create realistic customer email"""
        
        intents = {
            "appointment_request": {
                "subjects": [
                    "Need plumbing service ASAP",
                    "Kitchen sink is leaking",
                    "Bathroom repair needed",
                    "Water heater not working",
                    "Emergency plumbing help",
                    "Schedule appointment for next week"
                ],
                "templates": [
                    "Hi, I need a plumber to fix my {issue}. I'm available {availability}. Please call me at {phone}.",
                    "Hello, we have a {issue} and need it fixed {urgency_text}. My number is {phone}.",
                    "My {issue} is {problem_description}. Can you come {availability}? Contact: {phone}",
                    "Emergency! {issue} - need immediate help. Call {phone} ASAP.",
                    "Looking to schedule service for {issue}. Available {availability}. Phone: {phone}"
                ]
            },
            "general_inquiry": {
                "subjects": [
                    "Service pricing question",
                    "Do you work on weekends?",
                    "What services do you offer?",
                    "Service area coverage",
                    "Business hours inquiry"
                ],
                "templates": [
                    "Hi, I'm wondering about {inquiry}. Could you provide more information?",
                    "Hello, I have a question about {inquiry}. Please let me know.",
                    "Can you tell me about {inquiry}? Thanks!",
                    "I'd like to know more about {inquiry}."
                ]
            },
            "complaint": {
                "subjects": [
                    "Unsatisfied with recent service",
                    "Problem with last repair",
                    "Need to reschedule appointment",
                    "Billing question"
                ],
                "templates": [
                    "I'm not happy with the service I received on {date}. {complaint_details}",
                    "There's an issue with {complaint_issue}. Please contact me at {phone}.",
                    "I need to discuss {complaint_issue}. My number is {phone}."
                ]
            }
        }
        
        intent_data = intents.get(intent, intents["appointment_request"])
        subject = random.choice(intent_data["subjects"])
        template = random.choice(intent_data["templates"])
        
        # Generate context data
        issues = ["kitchen sink", "bathroom faucet", "water heater", "toilet", "garbage disposal", "shower head"]
        availabilities = ["this afternoon", "tomorrow morning", "next week", "this weekend", "ASAP"]
        phone = fake.phone_number() if include_phone else "not provided"
        
        urgency_texts = {
            "low": "when convenient",
            "normal": "soon",
            "high": "as soon as possible",
            "emergency": "immediately"
        }
        
        # Format email body
        body = template.format(
            issue=random.choice(issues),
            availability=random.choice(availabilities),
            phone=phone,
            urgency_text=urgency_texts.get(urgency, "soon"),
            problem_description="not working properly",
            inquiry="your services and pricing",
            date=(datetime.now() - timedelta(days=random.randint(1, 7))).strftime("%B %d"),
            complaint_details="The issue wasn't fully resolved",
            complaint_issue="the recent repair work"
        )
        
        return {
            "id": f"EMAIL_{uuid.uuid4().hex[:8]}",
            "subject": subject,
            "from": fake.email(),
            "to": "hello@757handy.com",
            "body": body,
            "date": (datetime.now() - timedelta(minutes=random.randint(1, 60))).isoformat(),
            "labels": ["INBOX", "UNREAD"],
            "intent": intent,
            "urgency": urgency,
            "phone_extracted": phone if include_phone else None
        }
    
    @staticmethod
    def create_sms_conversation(
        conversation_type: str = "appointment_booking",
        num_messages: int = 5
    ) -> List[Dict[str, Any]]:
        """Create realistic SMS conversation"""
        
        conversations = {
            "appointment_booking": [
                ("customer", "Hi, I need a plumber for my kitchen sink. It's been leaking for 2 days."),
                ("karen", "Hi! I'm Karen, your AI assistant. I can help schedule a plumber. What's your address?"),
                ("customer", "123 Main St, Norfolk, VA"),
                ("karen", "Perfect! I have availability tomorrow at 2 PM or Thursday at 10 AM. Which works better?"),
                ("customer", "Thursday at 10 AM works great"),
                ("karen", "Excellent! I've scheduled your appointment for Thursday at 10 AM. You'll receive a confirmation shortly. Is this the best number to reach you?"),
                ("customer", "Yes, this number is fine. Thank you!")
            ],
            "emergency_request": [
                ("customer", "EMERGENCY! Water everywhere in basement!"),
                ("karen", "I understand this is urgent. I'm dispatching our emergency team now. Can you turn off the main water valve?"),
                ("customer", "I don't know where it is!"),
                ("karen", "Usually near where water enters your house. Look for a wheel or lever. Our plumber will arrive in 30 minutes. Stay on this line."),
                ("customer", "Found it! Water is off."),
                ("karen", "Great work! Technician John will arrive at 3:15 PM. His number is (757) 555-0123.")
            ],
            "pricing_inquiry": [
                ("customer", "How much do you charge for drain cleaning?"),
                ("karen", "Our drain cleaning starts at $150 for standard service. Would you like to schedule an assessment?"),
                ("customer", "What's included in that price?"),
                ("karen", "The $150 includes snake cleaning for most clogs. If we need hydro-jetting, that's an additional service. Would you like a free estimate?"),
                ("customer", "Yes, please schedule an estimate")
            ]
        }
        
        base_conversation = conversations.get(conversation_type, conversations["appointment_booking"])
        phone_number = fake.phone_number()
        karen_number = "+17575550123"
        
        messages = []
        for i, (sender, text) in enumerate(base_conversation[:num_messages]):
            message = {
                "sid": f"MM{uuid.uuid4().hex}",
                "from": phone_number if sender == "customer" else karen_number,
                "to": karen_number if sender == "customer" else phone_number,
                "body": text,
                "direction": "inbound" if sender == "customer" else "outbound",
                "status": "delivered",
                "date_created": (datetime.now() - timedelta(minutes=num_messages-i)).isoformat(),
                "conversation_id": f"CONV_{uuid.uuid4().hex[:8]}",
                "sender_type": sender
            }
            messages.append(message)
            
        return messages
    
    @staticmethod
    def create_calendar_event(
        event_type: str = "service_appointment",
        start_time: Optional[datetime] = None,
        duration_minutes: int = 60
    ) -> Dict[str, Any]:
        """Create realistic calendar event"""
        
        if start_time is None:
            start_time = datetime.now() + timedelta(days=random.randint(1, 14))
            
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        event_types = {
            "service_appointment": {
                "summaries": [
                    "Plumbing Service - Kitchen Sink Repair",
                    "Water Heater Maintenance",
                    "Bathroom Faucet Installation",
                    "Emergency Pipe Repair",
                    "Drain Cleaning Service"
                ],
                "descriptions": [
                    "Customer reported leaking kitchen sink. Bring standard tools.",
                    "Annual water heater maintenance and inspection.",
                    "Install new bathroom faucet. Customer has purchased fixture.",
                    "Emergency pipe burst repair in basement.",
                    "Routine drain cleaning for kitchen and bathroom."
                ]
            },
            "consultation": {
                "summaries": [
                    "Home Plumbing Consultation",
                    "Bathroom Renovation Planning",
                    "Water System Assessment",
                    "Estimate for Kitchen Remodel"
                ],
                "descriptions": [
                    "Initial consultation for home plumbing assessment.",
                    "Discuss bathroom renovation plumbing requirements.",
                    "Comprehensive water system evaluation.",
                    "Provide estimate for kitchen plumbing updates."
                ]
            }
        }
        
        event_data = event_types.get(event_type, event_types["service_appointment"])
        
        return {
            "id": f"EVENT_{uuid.uuid4().hex[:8]}",
            "summary": random.choice(event_data["summaries"]),
            "description": random.choice(event_data["descriptions"]),
            "start": {
                "dateTime": start_time.isoformat() + "Z",
                "timeZone": "America/New_York"
            },
            "end": {
                "dateTime": end_time.isoformat() + "Z", 
                "timeZone": "America/New_York"
            },
            "location": f"{fake.street_address()}, {fake.city()}, VA",
            "attendees": [
                {"email": "tech@757handy.com"},
                {"email": fake.email()}
            ],
            "status": "confirmed",
            "created": datetime.now().isoformat() + "Z",
            "updated": datetime.now().isoformat() + "Z",
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 60},
                    {"method": "sms", "minutes": 15}
                ]
            }
        }
    
    @staticmethod
    def create_load_test_scenario(
        num_customers: int = 100,
        time_span_minutes: int = 60
    ) -> Dict[str, List[Any]]:
        """Create load testing scenario with multiple concurrent interactions"""
        
        scenario = {
            "emails": [],
            "sms_conversations": [],
            "calendar_events": [],
            "phone_calls": []
        }
        
        # Generate customer interactions spread over time
        for i in range(num_customers):
            # Random time within the span
            interaction_time = datetime.now() + timedelta(
                minutes=random.randint(0, time_span_minutes)
            )
            
            # Random interaction type
            interaction_type = random.choice([
                "email_then_sms", "sms_only", "emergency_call", 
                "appointment_booking", "service_inquiry"
            ])
            
            if interaction_type == "email_then_sms":
                # Email followed by SMS
                email = TestDataFactory.create_customer_email(
                    intent="appointment_request",
                    urgency=random.choice(["normal", "high"])
                )
                email["date"] = interaction_time.isoformat()
                scenario["emails"].append(email)
                
                # SMS follow-up 15 minutes later
                sms_time = interaction_time + timedelta(minutes=15)
                sms_conv = TestDataFactory.create_sms_conversation(
                    "appointment_booking", num_messages=3
                )
                for msg in sms_conv:
                    msg["date_created"] = sms_time.isoformat()
                scenario["sms_conversations"].extend(sms_conv)
                
            elif interaction_type == "emergency_call":
                # Emergency SMS conversation
                emergency_conv = TestDataFactory.create_sms_conversation(
                    "emergency_request", num_messages=6
                )
                for msg in emergency_conv:
                    msg["date_created"] = interaction_time.isoformat()
                scenario["sms_conversations"].extend(emergency_conv)
                
                # Emergency calendar slot
                emergency_event = TestDataFactory.create_calendar_event(
                    "service_appointment",
                    start_time=interaction_time + timedelta(hours=1),
                    duration_minutes=120
                )
                scenario["calendar_events"].append(emergency_event)
                
            elif interaction_type == "appointment_booking":
                # Standard appointment booking flow
                booking_conv = TestDataFactory.create_sms_conversation(
                    "appointment_booking", num_messages=7
                )
                for msg in booking_conv:
                    msg["date_created"] = interaction_time.isoformat()
                scenario["sms_conversations"].extend(booking_conv)
                
                # Scheduled appointment
                appt_event = TestDataFactory.create_calendar_event(
                    "service_appointment",
                    start_time=interaction_time + timedelta(days=random.randint(1, 7))
                )
                scenario["calendar_events"].append(appt_event)
                
        return scenario
    
    @staticmethod
    def create_chaos_scenario() -> Dict[str, Any]:
        """Create chaos testing scenario with coordinated failures"""
        
        return {
            "failure_timeline": {
                0: {"service": "redis", "failure_type": "connection_lost"},
                30: {"service": "twilio", "failure_type": "rate_limit"},
                60: {"service": "gmail", "failure_type": "quota_exceeded"},
                90: {"service": "calendar", "failure_type": "service_unavailable"},
                120: {"service": "all", "failure_type": "recovery_start"},
                180: {"service": "all", "failure_type": "full_recovery"}
            },
            "test_interactions": [
                {
                    "type": "high_volume_sms",
                    "start_time": 0,
                    "num_messages": 50,
                    "expected_failures": 5
                },
                {
                    "type": "email_processing",
                    "start_time": 45,
                    "num_emails": 20,
                    "expected_failures": 8
                },
                {
                    "type": "calendar_booking",
                    "start_time": 75,
                    "num_bookings": 15,
                    "expected_failures": 12
                }
            ],
            "recovery_expectations": {
                "max_recovery_time": 300,  # seconds
                "data_loss_tolerance": 0,   # zero tolerance
                "service_availability_target": 0.99
            }
        }
    
    @staticmethod
    def create_performance_baseline() -> Dict[str, Any]:
        """Create performance baseline test data"""
        
        return {
            "metrics": {
                "email_processing_time_ms": 500,
                "sms_response_time_ms": 200,
                "calendar_booking_time_ms": 1000,
                "memory_usage_mb": 128,
                "cpu_usage_percent": 15
            },
            "load_targets": {
                "concurrent_sms_conversations": 100,
                "emails_per_minute": 50,
                "calendar_events_per_hour": 30
            },
            "sla_requirements": {
                "response_time_p95_ms": 2000,
                "availability_percent": 99.9,
                "error_rate_percent": 0.1
            }
        }

class ConversationFlowFactory:
    """Factory for creating complex conversation flows"""
    
    @staticmethod
    def create_multi_channel_conversation():
        """Create conversation that spans email, SMS, and phone"""
        
        conversation_id = f"CONV_{uuid.uuid4().hex[:8]}"
        customer_email = fake.email()
        customer_phone = fake.phone_number()
        
        timeline = []
        
        # Start with email
        initial_email = TestDataFactory.create_customer_email(
            intent="appointment_request",
            urgency="high"
        )
        initial_email["conversation_id"] = conversation_id
        timeline.append({
            "timestamp": 0,
            "channel": "email",
            "data": initial_email
        })
        
        # SMS follow-up after 30 minutes
        sms_messages = TestDataFactory.create_sms_conversation(
            "appointment_booking", num_messages=5
        )
        for i, msg in enumerate(sms_messages):
            msg["conversation_id"] = conversation_id
            timeline.append({
                "timestamp": 30 + (i * 2),  # 2 minute intervals
                "channel": "sms", 
                "data": msg
            })
            
        # Calendar booking
        calendar_event = TestDataFactory.create_calendar_event(
            "service_appointment",
            start_time=datetime.now() + timedelta(days=2)
        )
        calendar_event["conversation_id"] = conversation_id
        timeline.append({
            "timestamp": 45,
            "channel": "calendar",
            "data": calendar_event
        })
        
        return {
            "conversation_id": conversation_id,
            "customer_email": customer_email,
            "customer_phone": customer_phone,
            "timeline": timeline,
            "expected_outcome": "appointment_scheduled"
        }
    
    @staticmethod
    def create_edge_case_scenarios():
        """Create edge case testing scenarios"""
        
        return [
            {
                "name": "double_booking_attempt",
                "description": "Customer tries to book same time slot twice",
                "data": {
                    "first_booking": TestDataFactory.create_calendar_event(
                        start_time=datetime.now() + timedelta(days=1, hours=10)
                    ),
                    "second_booking": TestDataFactory.create_calendar_event(
                        start_time=datetime.now() + timedelta(days=1, hours=10, minutes=15)
                    )
                },
                "expected_result": "conflict_detected"
            },
            {
                "name": "malformed_phone_number",
                "description": "SMS with invalid phone number format",
                "data": {
                    "sms": {
                        "from": "not-a-phone-number",
                        "body": "Help! Emergency plumbing needed!"
                    }
                },
                "expected_result": "graceful_error_handling"
            },
            {
                "name": "extremely_long_message",
                "description": "SMS exceeding length limits",
                "data": {
                    "sms": {
                        "from": fake.phone_number(),
                        "body": "Emergency! " + "This is a very long message. " * 100
                    }
                },
                "expected_result": "message_truncated_or_split"
            },
            {
                "name": "unicode_and_emoji_content",
                "description": "Messages with special characters",
                "data": {
                    "sms": {
                        "from": fake.phone_number(),
                        "body": "Hëlp! 🚰💧 Wäter everywhere! Çan you come ASAP? 🆘"
                    }
                },
                "expected_result": "proper_encoding_handling"
            }
        ]
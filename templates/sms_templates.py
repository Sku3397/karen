"""
SMS Message Templates for Karen AI Secretary
Communications Agent (COMMS-001)

Pre-defined SMS templates for consistent, professional communication
"""

from datetime import datetime
from typing import Dict, Any

class SMSTemplates:
    """Collection of SMS message templates"""
    
    @staticmethod
    def emergency_response(customer_name: str = "", service_type: str = "") -> str:
        """Emergency response template"""
        return f"🚨 URGENT: {customer_name}, we received your emergency call about {service_type}. Our team is being dispatched immediately. ETA: 15-30 mins. Stay safe!"
    
    @staticmethod
    def appointment_confirmation(customer_name: str, date: str, time: str, service: str) -> str:
        """Appointment confirmation template"""
        return f"Hi {customer_name}! Your {service} appointment is confirmed for {date} at {time}. We'll send tech details 1 hour before. Questions? Reply here."
    
    @staticmethod
    def appointment_reminder(customer_name: str, time: str, tech_name: str, tech_phone: str) -> str:
        """24-hour appointment reminder"""
        return f"Reminder: {customer_name}, your service appointment is tomorrow at {time}. Tech {tech_name} will call from {tech_phone}. Be ready!"
    
    @staticmethod
    def quote_provided(customer_name: str, service: str, price_range: str) -> str:
        """Quote estimation template"""
        return f"Hi {customer_name}! For your {service}, estimated cost: {price_range}. Includes labor & materials. Book free assessment to confirm? Reply YES."
    
    @staticmethod
    def service_complete(customer_name: str, service: str, tech_name: str) -> str:
        """Service completion follow-up"""
        return f"{customer_name}, your {service} is complete! How was {tech_name}'s work? Rate 1-5 & reply. We value your feedback. Thank you!"
    
    @staticmethod
    def out_of_hours(customer_name: str = "") -> str:
        """After hours auto-response"""
        name_part = f"{customer_name}, " if customer_name else ""
        return f"Hi {name_part}Thanks for contacting us! Office hours: 8AM-6PM Mon-Fri. For emergencies, reply URGENT. Otherwise, we'll respond tomorrow!"
    
    @staticmethod
    def payment_reminder(customer_name: str, amount: str, service: str) -> str:
        """Payment reminder template"""
        return f"Hi {customer_name}! Friendly reminder: ${amount} due for {service} completed on [date]. Pay online: [link] or call us. Thanks!"
    
    @staticmethod
    def weather_delay(customer_name: str, original_time: str, new_time: str) -> str:
        """Weather-related delay notification"""
        return f"{customer_name}, weather delay! Your {original_time} appointment moved to {new_time}. Safety first. Sorry for inconvenience!"
    
    @staticmethod
    def arrival_notification(customer_name: str, tech_name: str, eta_minutes: int) -> str:
        """Technician arrival notification"""
        return f"{customer_name}, {tech_name} is {eta_minutes} minutes away! Please be available. He'll call if any issues finding you."
    
    @staticmethod
    def upsell_opportunity(customer_name: str, current_service: str, additional_service: str, discount: str = "") -> str:
        """Upsell service opportunity"""
        discount_text = f" ({discount} off today!)" if discount else ""
        return f"{customer_name}, while we're here for {current_service}, want {additional_service}?{discount_text} Let us know!"
    
    @staticmethod
    def welcome_new_customer(customer_name: str) -> str:
        """Welcome message for new customers"""
        return f"Welcome {customer_name}! Thanks for choosing us. You'll get updates via SMS. Reply STOP to opt out, HELP for assistance."
    
    @staticmethod
    def seasonal_maintenance(customer_name: str, season: str, service: str) -> str:
        """Seasonal maintenance reminder"""
        return f"Hi {customer_name}! {season} is here. Time for {service}? Book now for early bird pricing. Reply BOOK or call us!"
    
    @staticmethod
    def warranty_expiration(customer_name: str, service: str, expiry_date: str) -> str:
        """Warranty expiration notice"""
        return f"{customer_name}, your {service} warranty expires {expiry_date}. Need any adjustments? Contact us before expiry!"
    
    @staticmethod
    def referral_request(customer_name: str) -> str:
        """Referral request template"""
        return f"Hi {customer_name}! Glad you're happy with our service! Know someone who needs handyman work? Refer & both get $25 credit!"
    
    @staticmethod
    def custom_template(template_name: str, **kwargs) -> str:
        """Custom template with variable substitution"""
        templates = {
            "parts_delay": "Hi {customer_name}! Parts for your {service} are delayed. New completion date: {new_date}. Sorry for the wait!",
            "inspection_passed": "{customer_name}, great news! Your {service} passed inspection. All done! Thanks for choosing us.",
            "follow_up_needed": "Hi {customer_name}! We may need a follow-up visit for your {service}. When works best? Reply with times.",
            "price_change": "{customer_name}, material costs have changed. Your {service} quote is now {new_price}. Still interested?",
            "tech_running_late": "{customer_name}, {tech_name} is running {delay_minutes} mins late for your {time} appointment. Sorry!",
        }
        
        template = templates.get(template_name, "Template not found: {template_name}")
        try:
            return template.format(**kwargs)
        except KeyError as e:
            return f"Missing parameter for template {template_name}: {e}"

class EmailTemplates:
    """Collection of email templates for detailed communications"""
    
    @staticmethod
    def detailed_quote(customer_data: Dict[str, Any]) -> Dict[str, str]:
        """Detailed quote email template"""
        subject = f"Service Quote for {customer_data.get('service', 'Your Project')} - {customer_data.get('name', 'Valued Customer')}"
        
        body = f"""
Dear {customer_data.get('name', 'Valued Customer')},

Thank you for contacting us about your {customer_data.get('service', 'project')}. Based on your description, here's your detailed quote:

SERVICE DETAILS:
- Service Type: {customer_data.get('service', 'N/A')}
- Location: {customer_data.get('address', 'N/A')}
- Scope of Work: {customer_data.get('description', 'N/A')}

PRICING BREAKDOWN:
- Labor: ${customer_data.get('labor_cost', '0')}
- Materials: ${customer_data.get('material_cost', '0')}
- Total Estimate: ${customer_data.get('total_cost', '0')}

TIMELINE:
- Estimated Duration: {customer_data.get('duration', 'TBD')}
- Availability: {customer_data.get('availability', 'Within 1-2 weeks')}

This quote is valid for 30 days. Final pricing may vary based on on-site assessment.

To schedule your service or if you have questions, please:
- Reply to this email
- Call us at {customer_data.get('phone', '(555) 123-4567')}
- Text us for quick questions

Thank you for considering our services!

Best regards,
Karen - AI Secretary
Handyman Services Team
"""
        return {"subject": subject, "body": body}
    
    @staticmethod
    def appointment_confirmation_detailed(appointment_data: Dict[str, Any]) -> Dict[str, str]:
        """Detailed appointment confirmation email"""
        subject = f"Appointment Confirmed: {appointment_data.get('service')} on {appointment_data.get('date')}"
        
        body = f"""
Dear {appointment_data.get('customer_name')},

Your service appointment has been confirmed! Here are the details:

APPOINTMENT INFORMATION:
- Date: {appointment_data.get('date')}
- Time: {appointment_data.get('time')}
- Service: {appointment_data.get('service')}
- Address: {appointment_data.get('address')}

TECHNICIAN DETAILS:
- Name: {appointment_data.get('tech_name', 'Will be assigned')}
- Phone: {appointment_data.get('tech_phone', 'Will be provided')}
- Estimated Duration: {appointment_data.get('duration', '1-2 hours')}

PREPARATION CHECKLIST:
□ Ensure access to work area
□ Remove any valuable or fragile items
□ Ensure someone 18+ will be present
□ Have any relevant documentation ready

WHAT TO EXPECT:
1. Technician will call 30 minutes before arrival
2. Quick assessment and confirmation of work
3. Professional completion of service
4. Clean-up and final walkthrough

PAYMENT OPTIONS:
- Cash, Check, or Card accepted
- Payment due upon completion
- Estimates provided before additional work

We'll send a reminder 24 hours before your appointment.

Questions? Reply to this email or call us anytime.

Best regards,
Karen - AI Secretary
Handyman Services Team
"""
        return {"subject": subject, "body": body}

class PhoneScripts:
    """Phone call scripts and responses"""
    
    @staticmethod
    def incoming_call_greeting() -> str:
        """Standard incoming call greeting"""
        return "Hello! You've reached Karen, your AI assistant for handyman services. Please describe what you need help with after the beep, and I'll assist you."
    
    @staticmethod
    def emergency_callback_script(customer_name: str, issue: str) -> str:
        """Emergency callback script"""
        return f"Hello {customer_name}, this is Karen from the handyman service. We received your emergency call about {issue}. Our technician is on the way and should arrive within 30 minutes. Are you in a safe location?"
    
    @staticmethod
    def appointment_confirmation_call(customer_name: str, date: str, time: str) -> str:
        """Appointment confirmation call script"""
        return f"Hi {customer_name}, this is Karen calling to confirm your service appointment scheduled for {date} at {time}. Please press 1 to confirm, or 2 to reschedule."
    
    @staticmethod
    def after_hours_message() -> str:
        """After hours phone message"""
        return "Thank you for calling! Our office hours are 8 AM to 6 PM, Monday through Friday. If this is an emergency, please stay on the line and I'll connect you. Otherwise, please call back during business hours or send us a text message. Press 1 if this is an emergency, or hang up to call back later."

# Template utility functions
def get_template_by_intent(intent: str, channel: str = "sms") -> str:
    """
    Get appropriate template based on message intent and channel
    
    Args:
        intent: Message intent (emergency, appointment, quote, etc.)
        channel: Communication channel (sms, email, phone)
    
    Returns:
        Template string or template data
    """
    if channel == "sms":
        template_map = {
            "emergency": SMSTemplates.emergency_response(),
            "appointment": SMSTemplates.appointment_confirmation("", "", "", ""),
            "quote": SMSTemplates.quote_provided("", "", ""),
            "out_of_hours": SMSTemplates.out_of_hours(),
            "general": "Thank you for contacting us! We'll get back to you shortly."
        }
        return template_map.get(intent, template_map["general"])
    
    elif channel == "phone":
        script_map = {
            "incoming": PhoneScripts.incoming_call_greeting(),
            "emergency": PhoneScripts.emergency_callback_script("", ""),
            "after_hours": PhoneScripts.after_hours_message()
        }
        return script_map.get(intent, script_map["incoming"])
    
    return "Template not found for channel: " + channel

def validate_template_variables(template: str, variables: Dict[str, str]) -> bool:
    """
    Validate that all required template variables are provided
    
    Args:
        template: Template string with placeholders
        variables: Dictionary of variable values
    
    Returns:
        True if all variables are provided
    """
    try:
        template.format(**variables)
        return True
    except KeyError:
        return False
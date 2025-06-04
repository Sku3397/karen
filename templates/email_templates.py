"""
Email Templates for Karen AI Secretary
Communications Agent (COMMS-001)

Professional email templates for detailed customer communications
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any

class EmailTemplates:
    """Professional email templates for various scenarios"""
    
    @staticmethod
    def service_inquiry_response(customer_data: Dict[str, Any]) -> Dict[str, str]:
        """Response to general service inquiry"""
        subject = f"Re: Service Inquiry - {customer_data.get('service', 'General Services')}"
        
        body = f"""
Dear {customer_data.get('name', 'Valued Customer')},

Thank you for your interest in our handyman services! I'm Karen, your AI assistant, and I'm here to help coordinate your service needs.

Based on your inquiry about {customer_data.get('service', 'general services')}, I'd like to gather a few more details to provide you with the best possible service:

NEXT STEPS:
1. I'll schedule a brief consultation call at your convenience
2. Our team will provide a detailed assessment and quote
3. We'll coordinate the service at a time that works for you

ABOUT OUR SERVICES:
• Licensed and insured professionals
• Upfront pricing with no hidden fees
• Satisfaction guarantee on all work
• Same-day emergency service available
• Free estimates for projects over $200

AVAILABILITY:
Regular hours: Monday-Friday, 8 AM - 6 PM
Emergency service: Available 24/7
Response time: Within 2 hours during business hours

To move forward, please reply with:
- Preferred contact method (phone/email/text)
- Best times to reach you
- Any additional details about your project

I look forward to helping you with your {customer_data.get('service', 'project')}!

Best regards,
Karen - AI Secretary
Handyman Services Team
Phone: {customer_data.get('business_phone', '(555) 123-4567')}
Email: service@handymanteam.com
"""
        return {"subject": subject, "body": body}
    
    @staticmethod
    def detailed_estimate(estimate_data: Dict[str, Any]) -> Dict[str, str]:
        """Comprehensive project estimate"""
        subject = f"Detailed Estimate #{estimate_data.get('estimate_id', '001')} - {estimate_data.get('service')}"
        
        # Calculate totals
        labor_total = estimate_data.get('labor_hours', 0) * estimate_data.get('hourly_rate', 75)
        material_total = sum(item.get('cost', 0) for item in estimate_data.get('materials', []))
        subtotal = labor_total + material_total
        tax = subtotal * estimate_data.get('tax_rate', 0.08)
        total = subtotal + tax
        
        materials_list = ""
        for item in estimate_data.get('materials', []):
            materials_list += f"  • {item.get('description', '')}: ${item.get('cost', 0):.2f}\n"
        
        body = f"""
Dear {estimate_data.get('customer_name')},

Thank you for the opportunity to provide an estimate for your {estimate_data.get('service')} project.

PROJECT DETAILS:
Service Address: {estimate_data.get('address', '')}
Project Description: {estimate_data.get('description', '')}
Estimated Start Date: {estimate_data.get('start_date', 'TBD')}
Estimated Completion: {estimate_data.get('completion_date', 'TBD')}

DETAILED BREAKDOWN:

LABOR:
- Hours Required: {estimate_data.get('labor_hours', 0)} hours
- Rate: ${estimate_data.get('hourly_rate', 75)}/hour
- Labor Subtotal: ${labor_total:.2f}

MATERIALS & SUPPLIES:
{materials_list if materials_list else "  • Will be determined based on final specifications"}
- Materials Subtotal: ${material_total:.2f}

PRICING SUMMARY:
- Labor: ${labor_total:.2f}
- Materials: ${material_total:.2f}
- Subtotal: ${subtotal:.2f}
- Tax ({estimate_data.get('tax_rate', 0.08)*100:.1f}%): ${tax:.2f}
- TOTAL ESTIMATE: ${total:.2f}

TERMS & CONDITIONS:
• Estimate valid for 30 days from date issued
• 50% deposit required to begin work
• Final pricing may vary based on unforeseen circumstances
• All work guaranteed for 1 year
• Payment due upon completion

WHAT'S INCLUDED:
✓ All labor and standard materials listed
✓ Clean-up and disposal of debris
✓ Post-work inspection and walkthrough
✓ 1-year warranty on workmanship

NOT INCLUDED:
• Permits (if required - we can assist with applications)
• Electrical/plumbing work requiring licensed specialist
• Structural modifications beyond scope
• Premium material upgrades (available upon request)

NEXT STEPS:
To accept this estimate and schedule your project:
1. Reply to confirm acceptance
2. We'll send a service agreement for signature
3. Schedule convenient start date
4. Coordinate any material selections

Questions? I'm here to help clarify any aspect of this estimate.

Best regards,
Karen - AI Secretary
Handyman Services Team

Estimate #{estimate_data.get('estimate_id', '001')}
Valid through: {(datetime.now() + timedelta(days=30)).strftime('%B %d, %Y')}
"""
        return {"subject": subject, "body": body}
    
    @staticmethod
    def appointment_confirmation(appointment: Dict[str, Any]) -> Dict[str, str]:
        """Detailed appointment confirmation with prep instructions"""
        subject = f"Service Confirmed: {appointment.get('date')} at {appointment.get('time')} - {appointment.get('service')}"
        
        body = f"""
Dear {appointment.get('customer_name')},

Your service appointment is confirmed! Here are all the details:

APPOINTMENT SUMMARY:
📅 Date: {appointment.get('date')}
🕐 Time: {appointment.get('time')}
🔧 Service: {appointment.get('service')}
📍 Address: {appointment.get('address')}
⏱️ Duration: {appointment.get('estimated_duration', '1-3 hours')}

TECHNICIAN INFORMATION:
👨‍🔧 Name: {appointment.get('tech_name', 'Will be assigned 24 hours prior')}
📱 Phone: {appointment.get('tech_phone', 'Will be provided')}
🚛 Vehicle: Look for our branded service vehicle

PRE-APPOINTMENT CHECKLIST:
□ Clear access to work area
□ Remove fragile/valuable items from work zone
□ Ensure adequate lighting in work area
□ Locate electrical panel/water shutoffs (if applicable)
□ Arrange for adult (18+) to be present
□ Secure pets away from work area
□ Have previous work documentation ready (if follow-up)

WHAT TO EXPECT:
1. Technician will call 30-60 minutes before arrival
2. Photo ID and branded uniform for identification
3. Professional assessment and work confirmation
4. Real-time updates on progress
5. Clean workspace upon completion
6. Final walkthrough and sign-off

PAYMENT & BILLING:
💳 Methods: Cash, Check, Credit/Debit Cards
💰 When: Payment due upon satisfactory completion
📄 Invoice: Detailed receipt provided
🛡️ Warranty: All work covered under our guarantee

WEATHER POLICY:
Outdoor work may be rescheduled for safety due to severe weather.
We'll contact you by 7 AM if rescheduling is necessary.

CONTACT INFORMATION:
📧 Email: service@handymanteam.com
📱 Text: {appointment.get('business_phone', '(555) 123-4567')}
☎️ Call: {appointment.get('business_phone', '(555) 123-4567')}
⏰ Office Hours: Monday-Friday, 8 AM - 6 PM

NEED TO RESCHEDULE?
Please contact us at least 24 hours in advance to avoid any fees.

We appreciate your business and look forward to serving you!

Best regards,
Karen - AI Secretary
Handyman Services Team

Confirmation #: {appointment.get('confirmation_id', datetime.now().strftime('%Y%m%d%H%M'))}
"""
        return {"subject": subject, "body": body}
    
    @staticmethod
    def service_completion_followup(service_data: Dict[str, Any]) -> Dict[str, str]:
        """Post-service completion follow-up"""
        subject = f"Service Complete: {service_data.get('service')} - How did we do?"
        
        body = f"""
Dear {service_data.get('customer_name')},

Thank you for choosing our handyman services! Your {service_data.get('service')} project has been completed.

SERVICE SUMMARY:
Date Completed: {service_data.get('completion_date')}
Technician: {service_data.get('tech_name')}
Service Performed: {service_data.get('service')}
Total Investment: ${service_data.get('total_cost', '0')}

HOW DID WE DO?
Your feedback helps us improve! Please take a moment to rate your experience:

⭐⭐⭐⭐⭐ Overall Service Quality
⭐⭐⭐⭐⭐ Technician Professionalism  
⭐⭐⭐⭐⭐ Timeliness & Communication
⭐⭐⭐⭐⭐ Value for Money

[Reply with ratings 1-5 for each category]

REVIEW OPPORTUNITIES:
Help others find great service! Please consider leaving a review:
• Google Business Profile
• Yelp
• Facebook
• Better Business Bureau

YOUR WARRANTY:
✅ 1-year warranty on workmanship
✅ Manufacturer warranty on parts/materials
✅ Call us immediately if any issues arise
✅ No additional charge for warranty work

NEED ADDITIONAL SERVICES?
We're here for all your home maintenance needs:
🔧 Regular maintenance schedules available
🏠 Seasonal home preparation services
🛠️ Additional handyman projects
📞 Priority booking for existing customers

REFER A FRIEND:
Know someone who could use our services?
Both you and your friend receive $25 credit!
Just mention referral when they book.

MAINTENANCE REMINDERS:
We can send you helpful reminders for:
• Seasonal HVAC filter changes
• Gutter cleaning schedules  
• Smoke detector battery replacements
• Annual home maintenance tasks

Reply "REMIND" to enroll in our maintenance reminder service.

Thank you again for your business! We look forward to serving you in the future.

Best regards,
Karen - AI Secretary
Handyman Services Team

Invoice #{service_data.get('invoice_number', 'N/A')}
Service Date: {service_data.get('completion_date')}
"""
        return {"subject": subject, "body": body}
    
    @staticmethod
    def emergency_service_confirmation(emergency_data: Dict[str, Any]) -> Dict[str, str]:
        """Emergency service dispatch confirmation"""
        subject = f"🚨 EMERGENCY DISPATCH CONFIRMED - ETA {emergency_data.get('eta', '30 minutes')}"
        
        body = f"""
EMERGENCY SERVICE DISPATCH

Dear {emergency_data.get('customer_name')},

We have received and prioritized your EMERGENCY service request.

DISPATCH DETAILS:
🚨 Emergency Type: {emergency_data.get('emergency_type')}
📍 Service Address: {emergency_data.get('address')}
⏰ Dispatch Time: {emergency_data.get('dispatch_time')}
🕐 Estimated Arrival: {emergency_data.get('eta', '15-30 minutes')}

TECHNICIAN EN ROUTE:
👨‍🔧 Name: {emergency_data.get('tech_name')}
📱 Direct Phone: {emergency_data.get('tech_phone')}
🚛 Vehicle: {emergency_data.get('vehicle_description', 'Branded service truck')}

IMMEDIATE SAFETY INSTRUCTIONS:
{emergency_data.get('safety_instructions', '''
• If water leak: Turn off main water supply if possible
• If electrical: Turn off power at main breaker
• If gas leak: Evacuate immediately and call gas company
• If fire/smoke: Call 911 immediately
• Stay in a safe location until technician arrives
''')}

WHAT HAPPENS NEXT:
1. Technician will call you upon arrival
2. Emergency assessment and immediate stabilization
3. Detailed evaluation and repair plan
4. Priority completion of critical repairs

EMERGENCY CONTACT:
📱 Technician Direct: {emergency_data.get('tech_phone', 'Will call you')}
☎️ Our Emergency Line: {emergency_data.get('emergency_phone', '(555) 911-HELP')}

BILLING INFORMATION:
Emergency service calls include:
• Priority dispatch fee: $150
• After-hours rate applies if outside business hours
• All major cards and cash accepted
• Payment due upon completion

Stay safe! Help is on the way.

Emergency Response Team
Handyman Services

Dispatch #: {emergency_data.get('dispatch_id', datetime.now().strftime('%Y%m%d%H%M%S'))}
Priority Level: EMERGENCY
"""
        return {"subject": subject, "body": body}
    
    @staticmethod
    def seasonal_maintenance_offer(customer_data: Dict[str, Any]) -> Dict[str, str]:
        """Seasonal maintenance service offering"""
        season = customer_data.get('season', 'Spring')
        subject = f"{season} Home Maintenance - Special Offer for {customer_data.get('name')}"
        
        seasonal_services = {
            'Spring': [
                'HVAC system tune-up and filter replacement',
                'Gutter cleaning and inspection', 
                'Exterior power washing and surface prep',
                'Deck/patio inspection and maintenance',
                'Window and screen cleaning/repair'
            ],
            'Summer': [
                'Air conditioning optimization check',
                'Outdoor lighting installation/repair',
                'Irrigation system maintenance',
                'Fence and gate repairs',
                'Outdoor entertainment area setup'
            ],
            'Fall': [
                'Heating system inspection and tune-up',
                'Weatherproofing and caulking renewal',
                'Leaf guard installation',
                'Storm window installation',
                'Chimney and fireplace inspection'
            ],
            'Winter': [
                'Emergency heating repairs',
                'Pipe freeze prevention',
                'Snow/ice damage repairs',
                'Indoor air quality improvements',
                'Holiday lighting installation'
            ]
        }
        
        services_list = '\n'.join([f"• {service}" for service in seasonal_services.get(season, [])])
        
        body = f"""
Dear {customer_data.get('name')},

{season} is here! Time to prepare your home for the season ahead.

🏠 SEASONAL HOME MAINTENANCE SPECIAL 🏠

Our {season.lower()} maintenance package includes:
{services_list}

SPECIAL PRICING:
💰 Complete Package: ${customer_data.get('package_price', '299')} (Save $100!)
💰 Individual Services: Starting at ${customer_data.get('individual_price', '75')}
💰 Existing Customer Discount: Additional 10% off

PACKAGE BENEFITS:
✅ Comprehensive home assessment
✅ Priority scheduling
✅ Bulk service discount
✅ Detailed maintenance report
✅ Next season preparation tips
✅ 6-month warranty on all work

WHY SEASONAL MAINTENANCE MATTERS:
• Prevent costly emergency repairs
• Improve energy efficiency
• Extend equipment lifespan  
• Maintain home value
• Peace of mind year-round

BOOK BY {(datetime.now() + timedelta(days=14)).strftime('%B %d')} AND RECEIVE:
🎁 FREE basic tool kit ($25 value)
🎁 Yearly maintenance calendar
🎁 Emergency service priority status

SCHEDULING:
We're booking {season.lower()} appointments now!
Popular time slots fill quickly.

Book online: www.handymanservices.com/seasonal
Call/Text: {customer_data.get('business_phone', '(555) 123-4567')}
Email: seasonal@handymanservices.com

Ready to protect your home this {season.lower()}?

Best regards,
Karen - AI Secretary
Handyman Services Team

P.S. Ask about our Annual Maintenance Plan for year-round coverage!
"""
        return {"subject": subject, "body": body}

def create_custom_email(template_type: str, data: Dict[str, Any]) -> Dict[str, str]:
    """
    Create custom email from template type and data
    
    Args:
        template_type: Type of email template
        data: Data to populate template
        
    Returns:
        Dictionary with subject and body
    """
    templates = EmailTemplates()
    
    template_methods = {
        'service_inquiry': templates.service_inquiry_response,
        'estimate': templates.detailed_estimate,
        'appointment': templates.appointment_confirmation,
        'completion': templates.service_completion_followup,
        'emergency': templates.emergency_service_confirmation,
        'seasonal': templates.seasonal_maintenance_offer
    }
    
    method = template_methods.get(template_type)
    if method:
        return method(data)
    else:
        return {
            "subject": "Service Update",
            "body": f"Thank you for contacting us, {data.get('name', 'Valued Customer')}. We'll get back to you shortly."
        }
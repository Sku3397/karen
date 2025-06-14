"""
SMS Templates System - Manages templated responses with variable substitution
Provides consistent, professional messaging across all SMS interactions.
"""

import json
import re
import random
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime

class TemplateCategory(Enum):
    """Template categories for organization"""
    GREETING = "greeting"
    APPOINTMENT = "appointment"
    QUOTE = "quote"
    CONFIRMATION = "confirmation"
    FOLLOW_UP = "follow_up"
    EMERGENCY = "emergency"
    BUSINESS_HOURS = "business_hours"
    PAYMENT = "payment"
    GENERAL = "general"

class SMSTemplateSystem:
    """Manages SMS templates with variable substitution and intent-based selection"""
    
    def __init__(self, templates_dir: str = "src/templates"):
        """Initialize template system"""
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Load templates
        self.templates = self._load_templates()
        
        # Quick reply patterns
        self.quick_replies = self._load_quick_replies()
        
        # Intent to template mapping
        self.intent_templates = self._build_intent_mapping()
    
    def _load_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load all SMS templates"""
        default_templates = {
            # Greeting Templates
            "welcome_new_customer": {
                "category": TemplateCategory.GREETING.value,
                "template": "Hi {customer_name}! Welcome to 757 Handy. I'm Karen, your AI assistant. How can I help you today?",
                "variables": ["customer_name"],
                "fallback": "Hi! Welcome to 757 Handy. I'm Karen, your AI assistant. How can I help you today?"
            },
            "general_greeting": {
                "category": TemplateCategory.GREETING.value,
                "template": "Hello {customer_name}! Thanks for contacting 757 Handy. What can I help you with today?",
                "variables": ["customer_name"],
                "fallback": "Hello! Thanks for contacting 757 Handy. What can I help you with today?"
            },
            "returning_customer": {
                "category": TemplateCategory.GREETING.value,
                "template": "Hi {customer_name}! Great to hear from you again. How can I help you today?",
                "variables": ["customer_name"],
                "fallback": "Hi! Great to hear from you again. How can I help you today?"
            },
            
            # Appointment Templates
            "appointment_confirmation": {
                "category": TemplateCategory.APPOINTMENT.value,
                "template": "✅ Confirmed! {customer_name}, your {service_type} appointment is scheduled for {date} at {time}. Address: {address}. Reply Y to confirm or C to change.",
                "variables": ["customer_name", "service_type", "date", "time", "address"],
                "fallback": "✅ Your appointment is confirmed! We'll send details shortly."
            },
            "appointment_reminder": {
                "category": TemplateCategory.APPOINTMENT.value,
                "template": "📅 Reminder: {customer_name}, you have a {service_type} appointment tomorrow at {time}. Our tech {tech_name} will arrive then. Questions?",
                "variables": ["customer_name", "service_type", "time", "tech_name"],
                "fallback": "📅 Reminder: You have a service appointment tomorrow. Our tech will contact you."
            },
            "appointment_scheduling": {
                "category": TemplateCategory.APPOINTMENT.value,
                "template": "I'd be happy to schedule your {service_type}! I have these times available: {available_times}. Which works best for you?",
                "variables": ["service_type", "available_times"],
                "fallback": "I'd be happy to schedule your service! What times work best for you?"
            },
            "tech_arrival": {
                "category": TemplateCategory.APPOINTMENT.value,
                "template": "🚛 {tech_name} is {eta_minutes} minutes away for your {service_type} appointment! Please be available. His contact: {tech_phone}",
                "variables": ["tech_name", "eta_minutes", "service_type", "tech_phone"],
                "fallback": "🚛 Our technician is on the way! Please be available."
            },
            
            # Quote Templates
            "quote_request_response": {
                "category": TemplateCategory.QUOTE.value,
                "template": "I'd be happy to provide a quote for {service_description}! To give you an accurate estimate, I need: 1) Your address 2) Photos if possible 3) When you need it done",
                "variables": ["service_description"],
                "fallback": "I'd be happy to provide a quote! Can you describe what you need done and your address?"
            },
            "quote_provided": {
                "category": TemplateCategory.QUOTE.value,
                "template": "💰 Quote for {customer_name}: {service_description} - Estimated ${min_cost}-${max_cost}. Includes {what_included}. Valid 30 days. Book now?",
                "variables": ["customer_name", "service_description", "min_cost", "max_cost", "what_included"],
                "fallback": "💰 Here's your quote! I'll send the detailed estimate shortly."
            },
            "quote_followup": {
                "category": TemplateCategory.QUOTE.value,
                "template": "Hi {customer_name}! Following up on your {service_type} quote from {days_ago} days ago. Any questions? Ready to schedule?",
                "variables": ["customer_name", "service_type", "days_ago"],
                "fallback": "Hi! Following up on your recent quote. Any questions? Ready to schedule?"
            },
            
            # Confirmation Templates
            "yes_confirmation": {
                "category": TemplateCategory.CONFIRMATION.value,
                "template": "Perfect! {customer_name}, I've confirmed your request. {next_steps}",
                "variables": ["customer_name", "next_steps"],
                "fallback": "Perfect! I've confirmed your request. You'll hear from us shortly."
            },
            "reschedule_confirmation": {
                "category": TemplateCategory.CONFIRMATION.value,
                "template": "No problem! I'll help you reschedule your {service_type}. What dates/times work better for you?",
                "variables": ["service_type"],
                "fallback": "No problem! I'll help you reschedule. What dates/times work better for you?"
            },
            "cancellation_confirmation": {
                "category": TemplateCategory.CONFIRMATION.value,
                "template": "Understood, {customer_name}. I've cancelled your {service_type} appointment for {date}. Hope to help you in the future!",
                "variables": ["customer_name", "service_type", "date"],
                "fallback": "Understood. I've cancelled your appointment. Hope to help you in the future!"
            },
            
            # Emergency Templates
            "emergency_response": {
                "category": TemplateCategory.EMERGENCY.value,
                "template": "🚨 EMERGENCY received! {customer_name}, I'm dispatching our emergency team to {address} immediately. ETA: {eta}. Stay safe!",
                "variables": ["customer_name", "address", "eta"],
                "fallback": "🚨 EMERGENCY received! I'm dispatching our emergency team immediately. Stay safe!"
            },
            "emergency_followup": {
                "category": TemplateCategory.EMERGENCY.value,
                "template": "Emergency update: Our tech {tech_name} is en route to your {issue_type} emergency. ETA: {eta}. Direct contact: {tech_phone}",
                "variables": ["tech_name", "issue_type", "eta", "tech_phone"],
                "fallback": "Emergency update: Our technician is on the way. You'll receive contact info shortly."
            },
            
            # Business Hours Templates
            "after_hours": {
                "category": TemplateCategory.BUSINESS_HOURS.value,
                "template": "Thanks for contacting 757 Handy! Our office hours are {business_hours}. For emergencies, reply URGENT. We'll respond first thing tomorrow!",
                "variables": ["business_hours"],
                "fallback": "Thanks for contacting 757 Handy! Our office hours are 8AM-6PM Mon-Fri. For emergencies, reply URGENT."
            },
            "holiday_hours": {
                "category": TemplateCategory.BUSINESS_HOURS.value,
                "template": "Happy {holiday}! We're closed today but will respond to your message on {return_date}. For emergencies, reply URGENT.",
                "variables": ["holiday", "return_date"],
                "fallback": "We're closed for the holiday but will respond soon. For emergencies, reply URGENT."
            },
            
            # Follow-up Templates
            "service_completion": {
                "category": TemplateCategory.FOLLOW_UP.value,
                "template": "✅ Service complete! {customer_name}, your {service_type} is finished. Total: ${amount}. How was {tech_name}'s work? Rate 1-5:",
                "variables": ["customer_name", "service_type", "amount", "tech_name"],
                "fallback": "✅ Service complete! How was our work? Please rate 1-5 and share any feedback."
            },
            "feedback_request": {
                "category": TemplateCategory.FOLLOW_UP.value,
                "template": "Hi {customer_name}! How was your {service_type} experience? Your feedback helps us improve. Reply with any comments or concerns.",
                "variables": ["customer_name", "service_type"],
                "fallback": "Hi! How was your service experience? Your feedback helps us improve."
            },
            "referral_request": {
                "category": TemplateCategory.FOLLOW_UP.value,
                "template": "Glad you're happy with our service, {customer_name}! Know someone who needs {service_type} work? You both get $25 off when they mention you!",
                "variables": ["customer_name", "service_type"],
                "fallback": "Glad you're happy with our service! Refer a friend and you both get $25 off!"
            },
            
            # Payment Templates
            "payment_reminder": {
                "category": TemplateCategory.PAYMENT.value,
                "template": "Friendly reminder: {customer_name}, ${amount} is due for {service_type} completed on {service_date}. Pay online: {payment_link}",
                "variables": ["customer_name", "amount", "service_type", "service_date", "payment_link"],
                "fallback": "Friendly reminder: Payment is due for your recent service. Please contact us to complete payment."
            },
            "payment_received": {
                "category": TemplateCategory.PAYMENT.value,
                "template": "Payment received! Thanks {customer_name}. ${amount} paid for {service_type}. Receipt sent to {email}. Pleasure working with you!",
                "variables": ["customer_name", "amount", "service_type", "email"],
                "fallback": "Payment received! Thanks for your business. Receipt sent to your email."
            },
            
            # General Templates
            "need_more_info": {
                "category": TemplateCategory.GENERAL.value,
                "template": "I'd love to help! Could you provide more details about {topic}? The more info you give me, the better I can assist you.",
                "variables": ["topic"],
                "fallback": "I'd love to help! Could you provide more details? The more info you give me, the better I can assist."
            },
            "transfer_to_human": {
                "category": TemplateCategory.GENERAL.value,
                "template": "I'm connecting you with our human team for specialized help with {issue}. Expect a call within {timeframe}.",
                "variables": ["issue", "timeframe"],
                "fallback": "I'm connecting you with our human team for specialized help. Expect a call soon."
            },
            "weather_delay": {
                "category": TemplateCategory.GENERAL.value,
                "template": "Weather alert! {customer_name}, your {time} appointment is delayed due to {weather_condition}. New time: {new_time}. Sorry for inconvenience!",
                "variables": ["customer_name", "time", "weather_condition", "new_time"],
                "fallback": "Weather alert! Your appointment is delayed due to weather. We'll contact you with new time."
            }
        }
        
        # Load from file if exists, otherwise use defaults
        templates_file = self.templates_dir / "sms_templates.json"
        if templates_file.exists():
            try:
                with open(templates_file, 'r') as f:
                    loaded_templates = json.load(f)
                # Merge with defaults, keeping customizations
                for key, value in default_templates.items():
                    if key not in loaded_templates:
                        loaded_templates[key] = value
                return loaded_templates
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        # Save defaults
        with open(templates_file, 'w') as f:
            json.dump(default_templates, f, indent=2)
        
        return default_templates
    
    def _load_quick_replies(self) -> Dict[str, List[str]]:
        """Load quick reply patterns"""
        return {
            "yes": ["y", "yes", "yeah", "yep", "ok", "okay", "sure", "confirm", "confirmed", "👍", "✅"],
            "no": ["n", "no", "nope", "nah", "cancel", "cancelled", "not interested", "👎", "❌"],
            "reschedule": ["r", "reschedule", "change", "move", "different time", "postpone", "later"],
            "emergency": ["urgent", "emergency", "asap", "help", "911", "now", "immediately"],
            "info": ["info", "information", "details", "tell me more", "explain", "what", "how"],
            "thanks": ["thanks", "thank you", "thx", "appreciate", "grateful", "👍", "🙏"]
        }
    
    def _build_intent_mapping(self) -> Dict[str, List[str]]:
        """Build mapping from intents to template names"""
        return {
            "greeting": ["general_greeting", "welcome_new_customer", "returning_customer"],
            "schedule_appointment": ["appointment_scheduling", "appointment_confirmation"],
            "get_quote": ["quote_request_response", "quote_provided"],
            "emergency_service": ["emergency_response", "emergency_followup"],
            "confirm_yes": ["yes_confirmation"],
            "reschedule": ["reschedule_confirmation"],
            "cancel": ["cancellation_confirmation"],
            "after_hours": ["after_hours", "holiday_hours"],
            "payment": ["payment_reminder", "payment_received"],
            "followup": ["service_completion", "feedback_request"],
            "need_info": ["need_more_info"],
            "general": ["need_more_info", "transfer_to_human"]
        }
    
    def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific template by name"""
        return self.templates.get(template_name)
    
    def fill_template(self, template_name: str, variables: Dict[str, Any] = None,
                     use_fallback: bool = True) -> str:
        """Fill template with variables"""
        if variables is None:
            variables = {}
        
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        
        try:
            # Get template text
            template_text = template["template"]
            
            # Replace variables
            for var, value in variables.items():
                placeholder = f"{{{var}}}"
                template_text = template_text.replace(placeholder, str(value))
            
            # Check for unfilled variables
            missing_vars = re.findall(r'\{(\w+)\}', template_text)
            
            if missing_vars and use_fallback and "fallback" in template:
                # Use fallback if variables are missing
                return template["fallback"]
            elif missing_vars:
                # Fill with empty string or raise error
                for var in missing_vars:
                    template_text = template_text.replace(f"{{{var}}}", "")
            
            # Clean up extra spaces
            template_text = re.sub(r'\s+', ' ', template_text).strip()
            
            return template_text
            
        except Exception as e:
            if use_fallback and "fallback" in template:
                return template["fallback"]
            else:
                raise ValueError(f"Error filling template '{template_name}': {e}")
    
    def classify_quick_reply(self, message: str) -> Optional[str]:
        """Classify message as a quick reply type"""
        message_clean = message.lower().strip()
        
        # Check each quick reply category
        for reply_type, patterns in self.quick_replies.items():
            if any(pattern in message_clean for pattern in patterns):
                return reply_type
        
        return None
    
    def get_template_for_intent(self, intent: str, variables: Dict[str, Any] = None,
                              prefer_specific: bool = True) -> str:
        """Get best template for an intent"""
        if variables is None:
            variables = {}
        
        # Get possible templates for intent
        template_names = self.intent_templates.get(intent, ["need_more_info"])
        
        if prefer_specific and len(template_names) > 1:
            # Try to pick most specific template based on available variables
            best_template = self._select_best_template(template_names, variables)
        else:
            # Use first template
            best_template = template_names[0]
        
        return self.fill_template(best_template, variables)
    
    def get_template_for_quick_reply(self, reply_type: str, variables: Dict[str, Any] = None) -> str:
        """Get appropriate template response for quick reply"""
        if variables is None:
            variables = {}
        
        # Map quick reply types to intents
        reply_intent_map = {
            "yes": "confirm_yes",
            "no": "need_info",
            "reschedule": "reschedule", 
            "emergency": "emergency_service",
            "info": "need_info",
            "thanks": "followup"
        }
        
        intent = reply_intent_map.get(reply_type, "general")
        return self.get_template_for_intent(intent, variables)
    
    def suggest_templates_for_context(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Suggest appropriate templates based on conversation context"""
        suggestions = []
        
        state = context.get('state', 'initial')
        intent = context.get('intent', 'general')
        urgency = context.get('urgency', 'low')
        
        # State-based suggestions
        if state == 'scheduling':
            suggestions.extend([
                {"name": "appointment_confirmation", "reason": "Customer is scheduling"},
                {"name": "appointment_scheduling", "reason": "Offer time slots"}
            ])
        elif state == 'gathering_info':
            suggestions.extend([
                {"name": "need_more_info", "reason": "Need more details"},
                {"name": "quote_request_response", "reason": "Gathering quote info"}
            ])
        
        # Intent-based suggestions
        if intent == 'emergency_service':
            suggestions.extend([
                {"name": "emergency_response", "reason": "Emergency detected"}
            ])
        elif intent == 'get_quote':
            suggestions.extend([
                {"name": "quote_request_response", "reason": "Quote requested"},
                {"name": "quote_provided", "reason": "Provide quote"}
            ])
        
        # Urgency-based suggestions
        if urgency == 'high':
            suggestions.insert(0, {"name": "emergency_response", "reason": "High urgency"})
        
        # Remove duplicates while preserving order
        seen = set()
        unique_suggestions = []
        for suggestion in suggestions:
            if suggestion["name"] not in seen:
                seen.add(suggestion["name"])
                unique_suggestions.append(suggestion)
        
        return unique_suggestions[:5]  # Return top 5
    
    def _select_best_template(self, template_names: List[str], variables: Dict[str, Any]) -> str:
        """Select best template based on available variables"""
        best_template = template_names[0]
        best_score = 0
        
        for template_name in template_names:
            template = self.get_template(template_name)
            if not template:
                continue
            
            # Score based on how many required variables we have
            required_vars = template.get("variables", [])
            available_vars = set(variables.keys())
            required_set = set(required_vars)
            
            score = len(required_set.intersection(available_vars))
            
            if score > best_score:
                best_score = score
                best_template = template_name
        
        return best_template
    
    def validate_template(self, template_name: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """Validate template and variables"""
        if variables is None:
            variables = {}
        
        template = self.get_template(template_name)
        if not template:
            return {"valid": False, "error": f"Template '{template_name}' not found"}
        
        required_vars = template.get("variables", [])
        missing_vars = [var for var in required_vars if var not in variables]
        
        try:
            filled_text = self.fill_template(template_name, variables, use_fallback=False)
            return {
                "valid": True,
                "text": filled_text,
                "length": len(filled_text),
                "sms_parts": (len(filled_text) // 160) + 1,
                "missing_variables": missing_vars,
                "has_fallback": "fallback" in template
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "missing_variables": missing_vars,
                "has_fallback": "fallback" in template
            }
    
    def add_template(self, name: str, category: str, template: str, 
                    variables: List[str] = None, fallback: str = None) -> bool:
        """Add a new template"""
        try:
            self.templates[name] = {
                "category": category,
                "template": template,
                "variables": variables or [],
                "fallback": fallback
            }
            self._save_templates()
            return True
        except Exception as e:
            print(f"Error adding template: {e}")
            return False
    
    def update_template(self, name: str, **kwargs) -> bool:
        """Update existing template"""
        try:
            if name not in self.templates:
                return False
            
            self.templates[name].update(kwargs)
            self._save_templates()
            return True
        except Exception as e:
            print(f"Error updating template: {e}")
            return False
    
    def delete_template(self, name: str) -> bool:
        """Delete a template"""
        try:
            if name not in self.templates:
                return False
            
            del self.templates[name]
            self._save_templates()
            return True
        except Exception as e:
            print(f"Error deleting template: {e}")
            return False
    
    def get_templates_by_category(self, category: str) -> Dict[str, Dict[str, Any]]:
        """Get all templates in a category"""
        return {
            name: template for name, template in self.templates.items()
            if template.get("category") == category
        }
    
    def list_categories(self) -> List[str]:
        """List all template categories"""
        categories = set()
        for template in self.templates.values():
            categories.add(template.get("category", "general"))
        return sorted(categories)
    
    def get_random_template(self, category: str = None) -> Optional[str]:
        """Get a random template name, optionally from specific category"""
        if category:
            templates = self.get_templates_by_category(category)
            if templates:
                return random.choice(list(templates.keys()))
        else:
            if self.templates:
                return random.choice(list(self.templates.keys()))
        return None
    
    def search_templates(self, query: str) -> List[Dict[str, Any]]:
        """Search templates by content or name"""
        results = []
        query_lower = query.lower()
        
        for name, template in self.templates.items():
            score = 0
            
            # Check name match
            if query_lower in name.lower():
                score += 10
            
            # Check template content match
            if query_lower in template.get("template", "").lower():
                score += 5
            
            # Check category match
            if query_lower in template.get("category", "").lower():
                score += 3
            
            # Check variables match
            for var in template.get("variables", []):
                if query_lower in var.lower():
                    score += 2
            
            if score > 0:
                results.append({
                    "name": name,
                    "template": template,
                    "relevance_score": score
                })
        
        # Sort by relevance
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results
    
    def get_template_stats(self) -> Dict[str, Any]:
        """Get statistics about templates"""
        stats = {
            "total_templates": len(self.templates),
            "categories": {},
            "average_length": 0,
            "templates_with_fallback": 0,
            "most_variables": 0
        }
        
        total_length = 0
        
        for template in self.templates.values():
            # Category counts
            category = template.get("category", "general")
            stats["categories"][category] = stats["categories"].get(category, 0) + 1
            
            # Length statistics
            template_length = len(template.get("template", ""))
            total_length += template_length
            
            # Fallback count
            if "fallback" in template:
                stats["templates_with_fallback"] += 1
            
            # Variable count
            var_count = len(template.get("variables", []))
            stats["most_variables"] = max(stats["most_variables"], var_count)
        
        if stats["total_templates"] > 0:
            stats["average_length"] = total_length / stats["total_templates"]
        
        return stats
    
    def _save_templates(self):
        """Save templates to file"""
        templates_file = self.templates_dir / "sms_templates.json"
        try:
            with open(templates_file, 'w') as f:
                json.dump(self.templates, f, indent=2)
        except Exception as e:
            print(f"Error saving templates: {e}")

# Global instance
_template_system = None

def get_template_system() -> SMSTemplateSystem:
    """Get singleton template system instance"""
    global _template_system
    if _template_system is None:
        _template_system = SMSTemplateSystem()
    return _template_system
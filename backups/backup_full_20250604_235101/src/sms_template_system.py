"""
SMS Template System - Manages response templates
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
import re

class SMSTemplateSystem:
    def __init__(self):
        self.template_dir = Path("src/templates/sms")
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.templates = self._load_templates()
        
    def _load_templates(self) -> Dict[str, Dict]:
        """Load all SMS templates"""
        templates = {
            "appointment_confirmation": {
                "template": "Hi {customer_name}, this confirms your {service_type} appointment on {date} at {time}. Reply Y to confirm or call us to reschedule.",
                "variables": ["customer_name", "service_type", "date", "time"],
                "category": "scheduling"
            },
            "appointment_reminder": {
                "template": "Reminder: {customer_name}, you have a {service_type} appointment tomorrow at {time}. Reply C to cancel or R to reschedule.",
                "variables": ["customer_name", "service_type", "time"],
                "category": "scheduling"
            },
            "quote_response": {
                "template": "Hi {customer_name}, for {service_description} the estimated cost is ${min_price}-${max_price}. This includes {included_services}. Would you like to schedule?",
                "variables": ["customer_name", "service_description", "min_price", "max_price", "included_services"],
                "category": "sales"
            },
            "service_complete": {
                "template": "Hi {customer_name}, your {service_type} has been completed. Your invoice total is ${amount}. Thank you for choosing 757 Handy!",
                "variables": ["customer_name", "service_type", "amount"],
                "category": "billing"
            },
            "emergency_response": {
                "template": "🚨 URGENT: {customer_name}, we received your emergency about {issue_type}. Our team is dispatching immediately. ETA: {eta}. Stay safe!",
                "variables": ["customer_name", "issue_type", "eta"],
                "category": "emergency"
            },
            "business_hours_response": {
                "template": "Hi! Thanks for contacting 757 Handy. Our office hours are 8AM-6PM Mon-Fri. For emergencies, reply URGENT. We'll respond first thing tomorrow!",
                "variables": [],
                "category": "automation"
            },
            "initial_greeting": {
                "template": "Hi {customer_name}! Thanks for contacting 757 Handy. How can I help you today? For quotes, appointments, or service questions, just let me know!",
                "variables": ["customer_name"],
                "category": "greeting"
            },
            "follow_up": {
                "template": "Hi {customer_name}, following up on your {service_type} service. How was everything? We value your feedback! Reply with any concerns.",
                "variables": ["customer_name", "service_type"],
                "category": "follow_up"
            },
            "payment_reminder": {
                "template": "Hi {customer_name}, friendly reminder: ${amount} is due for your {service_type} completed on {date}. Pay online or call us. Thanks!",
                "variables": ["customer_name", "amount", "service_type", "date"],
                "category": "billing"
            },
            "weather_delay": {
                "template": "{customer_name}, weather delay! Your {time} appointment moved to {new_time} for safety. Sorry for any inconvenience!",
                "variables": ["customer_name", "time", "new_time"],
                "category": "scheduling"
            },
            "tech_arrival": {
                "template": "{customer_name}, {tech_name} is {eta} minutes away for your {service_type}! He'll call if any issues finding you.",
                "variables": ["customer_name", "tech_name", "eta", "service_type"],
                "category": "scheduling"
            },
            "quick_replies": {
                "yes_variations": ["Y", "Yes", "YES", "Ok", "OK", "Sure", "Confirm", "👍", "Yep", "Yup", "Absolutely"],
                "no_variations": ["N", "No", "NO", "Cancel", "Nope", "👎", "Nah", "Not interested"],
                "reschedule_variations": ["R", "Reschedule", "Change", "Different time", "Move", "Postpone"],
                "emergency_variations": ["URGENT", "EMERGENCY", "HELP", "911", "ASAP", "NOW"],
                "templates": {
                    "confirm_yes": "Great! Your appointment is confirmed. We'll see you then! You'll get a reminder 24hrs before.",
                    "confirm_no": "No problem. Would you like to reschedule for another time? Just let me know what works better.",
                    "need_more_info": "I'd be happy to help! Could you provide more details about what you need?",
                    "emergency_escalation": "🚨 Emergency received! I'm immediately notifying our dispatch team. Expect a call within 15 minutes.",
                    "reschedule_request": "I'll help you reschedule. What dates and times work best for you?",
                    "general_help": "I'm here to help! For fastest service, tell me: 1) What you need fixed 2) When you're available 3) Your address"
                }
            },
            "sentiment_responses": {
                "positive": [
                    "Wonderful! We're so glad you're happy with our service! 🌟",
                    "Thank you for the kind words! It means a lot to our team! 😊",
                    "Fantastic! We love happy customers! Thanks for choosing us!"
                ],
                "negative": [
                    "I sincerely apologize. Let me get our manager to address this immediately. What's the best number to reach you?",
                    "I'm sorry to hear that. We want to make this right. Can you share more details so we can fix this?",
                    "That's not the experience we want you to have. Let me escalate this and have someone call you within the hour."
                ],
                "neutral": [
                    "Thanks for the feedback! Is there anything specific we can improve?",
                    "We appreciate your response. How can we better serve you in the future?",
                    "Thank you for letting us know. We're always looking to improve our service."
                ]
            }
        }
        
        # Save default templates if file doesn't exist
        template_file = self.template_dir / "sms_templates.json"
        if not template_file.exists():
            template_file.write_text(json.dumps(templates, indent=2))
        else:
            # Load existing templates and merge with defaults
            try:
                existing_templates = json.loads(template_file.read_text())
                # Merge with defaults, keeping existing customizations
                for key, value in templates.items():
                    if key not in existing_templates:
                        existing_templates[key] = value
                templates = existing_templates
            except (json.JSONDecodeError, FileNotFoundError):
                # If file is corrupted, use defaults
                template_file.write_text(json.dumps(templates, indent=2))
            
        return templates
    
    def get_template(self, template_name: str) -> Optional[Dict]:
        """Get a specific template"""
        return self.templates.get(template_name)
    
    def fill_template(self, template_name: str, variables: Dict[str, str]) -> str:
        """Fill a template with variables"""
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        
        message = template["template"]
        
        # Replace all variables
        for var, value in variables.items():
            placeholder = f"{{{var}}}"
            message = message.replace(placeholder, str(value))
        
        # Check for missing variables
        missing_vars = re.findall(r'\{(\w+)\}', message)
        if missing_vars:
            # For optional variables, replace with empty string
            for var in missing_vars:
                if var in ["customer_name"]:
                    message = message.replace(f"{{{var}}}", "")
                else:
                    raise ValueError(f"Missing required variables: {missing_vars}")
        
        # Clean up any double spaces
        message = re.sub(r'\s+', ' ', message).strip()
        
        return message
    
    def classify_quick_reply(self, message: str) -> Optional[str]:
        """Classify if message is a quick reply"""
        message_lower = message.lower().strip()
        
        quick_replies = self.templates.get("quick_replies", {})
        
        # Check emergency variations first (highest priority)
        if any(v.lower() in message_lower for v in quick_replies.get("emergency_variations", [])):
            return "emergency"
        
        # Check yes variations
        if message_lower in [v.lower() for v in quick_replies.get("yes_variations", [])]:
            return "yes"
        
        # Check no variations
        if message_lower in [v.lower() for v in quick_replies.get("no_variations", [])]:
            return "no"
        
        # Check reschedule variations
        if any(v.lower() in message_lower for v in quick_replies.get("reschedule_variations", [])):
            return "reschedule"
        
        return None
    
    def get_quick_reply_response(self, reply_type: str) -> str:
        """Get appropriate response for quick reply"""
        quick_replies = self.templates.get("quick_replies", {})
        templates = quick_replies.get("templates", {})
        
        response_map = {
            "yes": templates.get("confirm_yes", "Thank you for confirming!"),
            "no": templates.get("confirm_no", "Understood. How can we help?"),
            "reschedule": templates.get("reschedule_request", "I'll help you reschedule. What dates work best for you?"),
            "emergency": templates.get("emergency_escalation", "Emergency received! Dispatching help immediately."),
            "general": templates.get("general_help", "How can I help you today?")
        }
        
        return response_map.get(reply_type, templates.get("need_more_info", "How can I help you today?"))
    
    def get_sentiment_response(self, sentiment: str) -> str:
        """Get response based on sentiment analysis"""
        sentiment_responses = self.templates.get("sentiment_responses", {})
        responses = sentiment_responses.get(sentiment, sentiment_responses.get("neutral", []))
        
        if responses:
            import random
            return random.choice(responses)
        
        return "Thank you for your feedback!"
    
    def classify_message_intent(self, message: str) -> str:
        """Classify the intent of an incoming message"""
        message_lower = message.lower()
        
        # Emergency keywords
        emergency_words = ['emergency', 'urgent', 'leak', 'flood', 'electrical', 'gas', 'fire', 'broken', 'not working']
        if any(word in message_lower for word in emergency_words):
            return 'emergency'
        
        # Appointment keywords
        appointment_words = ['appointment', 'schedule', 'book', 'available', 'when can', 'time slot']
        if any(word in message_lower for word in appointment_words):
            return 'appointment'
        
        # Quote keywords
        quote_words = ['quote', 'price', 'cost', 'estimate', 'how much', 'pricing', 'rate']
        if any(word in message_lower for word in quote_words):
            return 'quote'
        
        # Service inquiry keywords
        service_words = ['repair', 'fix', 'install', 'replace', 'maintenance', 'service', 'handyman']
        if any(word in message_lower for word in service_words):
            return 'service_inquiry'
        
        # Greeting keywords
        greeting_words = ['hello', 'hi', 'hey', 'good morning', 'good afternoon']
        if any(word in message_lower for word in greeting_words):
            return 'greeting'
        
        # Question keywords
        question_words = ['?', 'what', 'when', 'where', 'how', 'why', 'can you']
        if any(word in message_lower for word in question_words):
            return 'question'
        
        return 'general'
    
    def get_template_for_intent(self, intent: str, variables: Dict[str, str] = None) -> str:
        """Get appropriate template response for classified intent"""
        if variables is None:
            variables = {}
        
        intent_template_map = {
            'emergency': 'emergency_response',
            'appointment': 'appointment_confirmation',
            'quote': 'quote_response',
            'greeting': 'initial_greeting',
            'service_inquiry': 'general_help',
            'general': 'general_help'
        }
        
        template_name = intent_template_map.get(intent)
        if template_name and template_name in self.templates:
            try:
                return self.fill_template(template_name, variables)
            except ValueError:
                # If template filling fails, return quick reply
                return self.get_quick_reply_response('general')
        
        return self.get_quick_reply_response('general')
    
    def add_template(self, name: str, template: str, variables: List[str], category: str):
        """Add a new template"""
        self.templates[name] = {
            "template": template,
            "variables": variables,
            "category": category
        }
        self._save_templates()
    
    def update_template(self, name: str, **kwargs):
        """Update an existing template"""
        if name in self.templates:
            self.templates[name].update(kwargs)
            self._save_templates()
        else:
            raise ValueError(f"Template '{name}' not found")
    
    def delete_template(self, name: str):
        """Delete a template"""
        if name in self.templates:
            del self.templates[name]
            self._save_templates()
        else:
            raise ValueError(f"Template '{name}' not found")
    
    def get_templates_by_category(self, category: str) -> Dict[str, Dict]:
        """Get all templates in a specific category"""
        return {
            name: template for name, template in self.templates.items()
            if template.get('category') == category
        }
    
    def list_all_templates(self) -> List[str]:
        """List all available template names"""
        return list(self.templates.keys())
    
    def validate_template(self, template_name: str, variables: Dict[str, str]) -> Dict[str, any]:
        """Validate a template with given variables"""
        template = self.get_template(template_name)
        if not template:
            return {"valid": False, "error": f"Template '{template_name}' not found"}
        
        required_vars = template.get("variables", [])
        missing_vars = [var for var in required_vars if var not in variables]
        
        if missing_vars:
            return {
                "valid": False, 
                "error": f"Missing variables: {missing_vars}",
                "required": required_vars,
                "provided": list(variables.keys())
            }
        
        try:
            filled_message = self.fill_template(template_name, variables)
            return {
                "valid": True,
                "message": filled_message,
                "length": len(filled_message),
                "sms_count": (len(filled_message) // 160) + 1
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    def _save_templates(self):
        """Save templates to file"""
        template_file = self.template_dir / "sms_templates.json"
        try:
            template_file.write_text(json.dumps(self.templates, indent=2))
        except Exception as e:
            print(f"Error saving templates: {e}")
    
    def get_template_stats(self) -> Dict:
        """Get statistics about templates"""
        categories = {}
        total_templates = len(self.templates)
        
        for template in self.templates.values():
            category = template.get('category', 'uncategorized')
            categories[category] = categories.get(category, 0) + 1
        
        return {
            'total_templates': total_templates,
            'categories': categories,
            'average_variables': sum(len(t.get('variables', [])) for t in self.templates.values()) / total_templates if total_templates > 0 else 0
        }
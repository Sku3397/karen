"""
Template Storage System for Karen AI Secretary
Manages SMS templates with version control and persistence
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import hashlib
import shutil
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class TemplateVersion:
    """Represents a template version"""
    version: str
    timestamp: str
    user: str
    changes: Dict[str, Any]
    checksum: str

class TemplateStorage:
    """
    Enhanced template storage system with version control and persistence
    """
    
    def __init__(self, storage_path: str = "templates/sms_templates.json"):
        """
        Initialize template storage
        
        Args:
            storage_path: Path to the JSON file for storing templates
        """
        self.storage_path = Path(storage_path)
        self.backup_dir = self.storage_path.parent / "backups"
        self.version_file = self.storage_path.parent / "template_versions.json"
        
        # Ensure directories exist
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize storage
        self.templates = {}
        self.versions = {}
        self._load_templates()
        self._load_versions()
        
        logger.info(f"Template storage initialized at {self.storage_path}")
    
    def _generate_checksum(self, data: Dict) -> str:
        """Generate MD5 checksum for template data"""
        content = json.dumps(data, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()
    
    def _load_templates(self) -> None:
        """Load templates from JSON file"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    self.templates = json.load(f)
                logger.info(f"Loaded {len(self.templates)} templates from {self.storage_path}")
            else:
                # Initialize with default templates
                self.templates = self._get_default_templates()
                self._save_templates()
                logger.info("Initialized with default templates")
        except Exception as e:
            logger.error(f"Error loading templates: {e}", exc_info=True)
            self.templates = self._get_default_templates()
    
    def _load_versions(self) -> None:
        """Load version history from JSON file"""
        try:
            if self.version_file.exists():
                with open(self.version_file, 'r', encoding='utf-8') as f:
                    version_data = json.load(f)
                    self.versions = {
                        template_name: [
                            TemplateVersion(**v) for v in versions
                        ] for template_name, versions in version_data.items()
                    }
                logger.info(f"Loaded version history for {len(self.versions)} templates")
            else:
                self.versions = {}
        except Exception as e:
            logger.error(f"Error loading versions: {e}", exc_info=True)
            self.versions = {}
    
    def _save_templates(self) -> None:
        """Save templates to JSON file with backup"""
        try:
            # Create backup before saving
            if self.storage_path.exists():
                backup_filename = f"sms_templates_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                backup_path = self.backup_dir / backup_filename
                shutil.copy2(self.storage_path, backup_path)
                logger.debug(f"Created backup at {backup_path}")
            
            # Save current templates
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(self.templates)} templates to {self.storage_path}")
            
        except Exception as e:
            logger.error(f"Error saving templates: {e}", exc_info=True)
            raise
    
    def _save_versions(self) -> None:
        """Save version history to JSON file"""
        try:
            version_data = {
                template_name: [
                    {
                        'version': v.version,
                        'timestamp': v.timestamp,
                        'user': v.user,
                        'changes': v.changes,
                        'checksum': v.checksum
                    } for v in versions
                ] for template_name, versions in self.versions.items()
            }
            
            with open(self.version_file, 'w', encoding='utf-8') as f:
                json.dump(version_data, f, indent=2, ensure_ascii=False)
                
            logger.debug("Saved version history")
            
        except Exception as e:
            logger.error(f"Error saving versions: {e}", exc_info=True)
    
    def _get_default_templates(self) -> Dict[str, Dict]:
        """Return default SMS templates for all intent types"""
        timestamp = datetime.now().isoformat()
        
        return {
            # Greeting Templates
            "welcome_new_customer": {
                "template": "Hi {customer_name}! Welcome to 757 Handy. I'm Karen, your AI assistant. How can I help you today?",
                "variables": ["customer_name"],
                "category": "greeting",
                "description": "Welcome message for new customers",
                "fallback": "Hi! Welcome to 757 Handy. I'm Karen, your AI assistant. How can I help you today?",
                "created_at": timestamp,
                "updated_at": timestamp
            },
            "general_greeting": {
                "template": "Hello {customer_name}! Thanks for contacting 757 Handy. What can I help you with today?",
                "variables": ["customer_name"],
                "category": "greeting",
                "description": "Standard greeting template",
                "fallback": "Hello! Thanks for contacting 757 Handy. What can I help you with today?",
                "created_at": timestamp,
                "updated_at": timestamp
            },
            "returning_customer": {
                "template": "Hi {customer_name}! Great to hear from you again. How can I help you today?",
                "variables": ["customer_name"],
                "category": "greeting",
                "description": "Greeting for returning customers",
                "fallback": "Hi! Great to hear from you again. How can I help you today?",
                "created_at": timestamp,
                "updated_at": timestamp
            },
            
            # Appointment/Scheduling Templates
            "appointment_confirmation": {
                "template": "✅ Confirmed! {customer_name}, your {service_type} appointment is scheduled for {date} at {time}. Address: {address}. Reply Y to confirm or C to change.",
                "variables": ["customer_name", "service_type", "date", "time", "address"],
                "category": "scheduling",
                "description": "Appointment confirmation with details",
                "fallback": "✅ Your appointment is confirmed! We'll send details shortly.",
                "created_at": timestamp,
                "updated_at": timestamp
            },
            "appointment_reminder": {
                "template": "📅 Reminder: {customer_name}, you have a {service_type} appointment tomorrow at {time}. Our tech {tech_name} will arrive then. Questions?",
                "variables": ["customer_name", "service_type", "time", "tech_name"],
                "category": "scheduling",
                "description": "Appointment reminder notification",
                "fallback": "📅 Reminder: You have a service appointment tomorrow. Our tech will contact you.",
                "created_at": timestamp,
                "updated_at": timestamp
            },
            "appointment_scheduling": {
                "template": "I'd be happy to schedule your {service_type}! I have these times available: {available_times}. Which works best for you?",
                "variables": ["service_type", "available_times"],
                "category": "scheduling",
                "description": "Offering available appointment times",
                "fallback": "I'd be happy to schedule your service! What times work best for you?",
                "created_at": timestamp,
                "updated_at": timestamp
            },
            "tech_arrival": {
                "template": "🚛 {tech_name} is {eta_minutes} minutes away for your {service_type} appointment! Please be available. His contact: {tech_phone}",
                "variables": ["tech_name", "eta_minutes", "service_type", "tech_phone"],
                "category": "scheduling",
                "description": "Technician arrival notification",
                "fallback": "🚛 Our technician is on the way! Please be available.",
                "created_at": timestamp,
                "updated_at": timestamp
            },
            
            # Quote/Sales Templates
            "quote_request_response": {
                "template": "I'd be happy to provide a quote for {service_description}! To give you an accurate estimate, I need: 1) Your address 2) Photos if possible 3) When you need it done",
                "variables": ["service_description"],
                "category": "sales",
                "description": "Response to quote requests with information needed",
                "fallback": "I'd be happy to provide a quote! Can you describe what you need done and your address?",
                "created_at": timestamp,
                "updated_at": timestamp
            },
            "quote_provided": {
                "template": "💰 Quote for {customer_name}: {service_description} - Estimated ${min_cost}-${max_cost}. Includes {what_included}. Valid 30 days. Book now?",
                "variables": ["customer_name", "service_description", "min_cost", "max_cost", "what_included"],
                "category": "sales",
                "description": "Quote delivery with pricing details",
                "fallback": "💰 Here's your quote! I'll send the detailed estimate shortly.",
                "created_at": timestamp,
                "updated_at": timestamp
            },
            "quote_followup": {
                "template": "Hi {customer_name}! Following up on your {service_type} quote from {days_ago} days ago. Any questions? Ready to schedule?",
                "variables": ["customer_name", "service_type", "days_ago"],
                "category": "sales",
                "description": "Quote follow-up message",
                "fallback": "Hi! Following up on your recent quote. Any questions? Ready to schedule?",
                "created_at": timestamp,
                "updated_at": timestamp
            },
            
            # Emergency Templates
            "emergency_response": {
                "template": "🚨 EMERGENCY received! {customer_name}, I'm dispatching our emergency team to {address} immediately. ETA: {eta}. Stay safe!",
                "variables": ["customer_name", "address", "eta"],
                "category": "emergency",
                "description": "Emergency response with immediate dispatch",
                "fallback": "🚨 EMERGENCY received! I'm dispatching our emergency team immediately. Stay safe!",
                "created_at": timestamp,
                "updated_at": timestamp
            },
            "emergency_followup": {
                "template": "Emergency update: Our tech {tech_name} is en route to your {issue_type} emergency. ETA: {eta}. Direct contact: {tech_phone}",
                "variables": ["tech_name", "issue_type", "eta", "tech_phone"],
                "category": "emergency",
                "description": "Emergency follow-up with technician details",
                "fallback": "Emergency update: Our technician is on the way. You'll receive contact info shortly.",
                "created_at": timestamp,
                "updated_at": timestamp
            },
            
            # Confirmation Templates
            "yes_confirmation": {
                "template": "Perfect! {customer_name}, I've confirmed your request. {next_steps}",
                "variables": ["customer_name", "next_steps"],
                "category": "confirmation",
                "description": "Positive confirmation response",
                "fallback": "Perfect! I've confirmed your request. You'll hear from us shortly.",
                "created_at": timestamp,
                "updated_at": timestamp
            },
            "reschedule_confirmation": {
                "template": "No problem! I'll help you reschedule your {service_type}. What dates/times work better for you?",
                "variables": ["service_type"],
                "category": "confirmation",
                "description": "Reschedule assistance response",
                "fallback": "No problem! I'll help you reschedule. What dates/times work better for you?",
                "created_at": timestamp,
                "updated_at": timestamp
            },
            "cancellation_confirmation": {
                "template": "Understood, {customer_name}. I've cancelled your {service_type} appointment for {date}. Hope to help you in the future!",
                "variables": ["customer_name", "service_type", "date"],
                "category": "confirmation",
                "description": "Cancellation confirmation",
                "fallback": "Understood. I've cancelled your appointment. Hope to help you in the future!",
                "created_at": timestamp,
                "updated_at": timestamp
            },
            
            # Business Hours/Automation Templates
            "business_hours_response": {
                "template": "Thanks for contacting 757 Handy! Our office hours are {business_hours}. For emergencies, reply URGENT. We'll respond first thing tomorrow!",
                "variables": ["business_hours"],
                "category": "automation",
                "description": "After-hours automatic response",
                "fallback": "Thanks for contacting 757 Handy! Our office hours are 8AM-6PM Mon-Fri. For emergencies, reply URGENT.",
                "created_at": timestamp,
                "updated_at": timestamp
            },
            "holiday_hours": {
                "template": "Happy {holiday}! We're closed today but will respond to your message on {return_date}. For emergencies, reply URGENT.",
                "variables": ["holiday", "return_date"],
                "category": "automation",
                "description": "Holiday hours notification",
                "fallback": "We're closed for the holiday but will respond soon. For emergencies, reply URGENT.",
                "created_at": timestamp,
                "updated_at": timestamp
            },
            
            # Follow-up Templates
            "service_completion": {
                "template": "✅ Service complete! {customer_name}, your {service_type} is finished. Total: ${amount}. How was {tech_name}'s work? Rate 1-5:",
                "variables": ["customer_name", "service_type", "amount", "tech_name"],
                "category": "followup",
                "description": "Service completion with feedback request",
                "fallback": "✅ Service complete! How was our work? Please rate 1-5 and share any feedback.",
                "created_at": timestamp,
                "updated_at": timestamp
            },
            "feedback_request": {
                "template": "Hi {customer_name}! How was your {service_type} experience? Your feedback helps us improve. Reply with any comments or concerns.",
                "variables": ["customer_name", "service_type"],
                "category": "followup",
                "description": "General feedback request",
                "fallback": "Hi! How was your service experience? Your feedback helps us improve.",
                "created_at": timestamp,
                "updated_at": timestamp
            },
            "referral_request": {
                "template": "Glad you're happy with our service, {customer_name}! Know someone who needs {service_type} work? You both get $25 off when they mention you!",
                "variables": ["customer_name", "service_type"],
                "category": "followup",
                "description": "Referral incentive message",
                "fallback": "Glad you're happy with our service! Refer a friend and you both get $25 off!",
                "created_at": timestamp,
                "updated_at": timestamp
            },
            
            # Payment/Billing Templates
            "payment_reminder": {
                "template": "Friendly reminder: {customer_name}, ${amount} is due for {service_type} completed on {service_date}. Pay online: {payment_link}",
                "variables": ["customer_name", "amount", "service_type", "service_date", "payment_link"],
                "category": "billing",
                "description": "Payment reminder with online payment link",
                "fallback": "Friendly reminder: Payment is due for your recent service. Please contact us to complete payment.",
                "created_at": timestamp,
                "updated_at": timestamp
            },
            "payment_received": {
                "template": "Payment received! Thanks {customer_name}. ${amount} paid for {service_type}. Receipt sent to {email}. Pleasure working with you!",
                "variables": ["customer_name", "amount", "service_type", "email"],
                "category": "billing",
                "description": "Payment confirmation message",
                "fallback": "Payment received! Thanks for your business. Receipt sent to your email.",
                "created_at": timestamp,
                "updated_at": timestamp
            },
            
            # General/Information Templates
            "need_more_info": {
                "template": "I'd love to help! Could you provide more details about {topic}? The more info you give me, the better I can assist you.",
                "variables": ["topic"],
                "category": "general",
                "description": "Request for more information",
                "fallback": "I'd love to help! Could you provide more details? The more info you give me, the better I can assist.",
                "created_at": timestamp,
                "updated_at": timestamp
            },
            "transfer_to_human": {
                "template": "I'm connecting you with our human team for specialized help with {issue}. Expect a call within {timeframe}.",
                "variables": ["issue", "timeframe"],
                "category": "general",
                "description": "Transfer to human agent",
                "fallback": "I'm connecting you with our human team for specialized help. Expect a call soon.",
                "created_at": timestamp,
                "updated_at": timestamp
            },
            "weather_delay": {
                "template": "Weather alert! {customer_name}, your {time} appointment is delayed due to {weather_condition}. New time: {new_time}. Sorry for inconvenience!",
                "variables": ["customer_name", "time", "weather_condition", "new_time"],
                "category": "general",
                "description": "Weather-related delay notification",
                "fallback": "Weather alert! Your appointment is delayed due to weather. We'll contact you with new time.",
                "created_at": timestamp,
                "updated_at": timestamp
            }
        }
    
    def _create_version(self, template_name: str, old_template: Dict, new_template: Dict, user: str = "system") -> None:
        """Create a new version entry for template changes"""
        try:
            # Determine changes
            changes = {}
            for key in set(old_template.keys()) | set(new_template.keys()):
                if old_template.get(key) != new_template.get(key):
                    changes[key] = {
                        'old': old_template.get(key),
                        'new': new_template.get(key)
                    }
            
            # Create version entry
            version = TemplateVersion(
                version=f"v{len(self.versions.get(template_name, [])) + 1}",
                timestamp=datetime.now().isoformat(),
                user=user,
                changes=changes,
                checksum=self._generate_checksum(new_template)
            )
            
            # Add to version history
            if template_name not in self.versions:
                self.versions[template_name] = []
            self.versions[template_name].append(version)
            
            # Keep only last 10 versions per template
            if len(self.versions[template_name]) > 10:
                self.versions[template_name] = self.versions[template_name][-10:]
            
            self._save_versions()
            logger.info(f"Created version {version.version} for template '{template_name}'")
            
        except Exception as e:
            logger.error(f"Error creating version for {template_name}: {e}", exc_info=True)
    
    def save_template(self, name: str, template_data: Dict[str, Any], user: str = "system") -> bool:
        """
        Save a template with version control
        
        Args:
            name: Template name/identifier
            template_data: Template data dictionary
            user: User making the change
            
        Returns:
            bool: True if saved successfully
        """
        try:
            # Add metadata
            now = datetime.now().isoformat()
            old_template = self.templates.get(name, {})
            
            new_template = template_data.copy()
            new_template.update({
                'updated_at': now,
                'updated_by': user
            })
            
            # Add created_at if new template
            if name not in self.templates:
                new_template['created_at'] = now
                new_template['created_by'] = user
            
            # Create version before updating
            if old_template:
                self._create_version(name, old_template, new_template, user)
            
            # Update template
            self.templates[name] = new_template
            self._save_templates()
            
            logger.info(f"Successfully saved template '{name}' by user '{user}'")
            return True
            
        except Exception as e:
            logger.error(f"Error saving template '{name}': {e}", exc_info=True)
            return False
    
    def load_template(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Load a specific template by name
        
        Args:
            name: Template name/identifier
            
        Returns:
            Template data or None if not found
        """
        template = self.templates.get(name)
        if template:
            logger.debug(f"Loaded template '{name}'")
            return template.copy()
        else:
            logger.warning(f"Template '{name}' not found")
            return None
    
    def load_all_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Load all templates
        
        Returns:
            Dictionary of all templates
        """
        logger.debug(f"Loaded all {len(self.templates)} templates")
        return self.templates.copy()
    
    def delete_template(self, name: str, user: str = "system") -> bool:
        """
        Delete a template with version tracking
        
        Args:
            name: Template name to delete
            user: User performing deletion
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            if name in self.templates:
                # Create final version entry for deletion
                deleted_template = self.templates[name].copy()
                deleted_template['deleted_at'] = datetime.now().isoformat()
                deleted_template['deleted_by'] = user
                
                self._create_version(name, self.templates[name], deleted_template, user)
                
                del self.templates[name]
                self._save_templates()
                
                logger.info(f"Successfully deleted template '{name}' by user '{user}'")
                return True
            else:
                logger.warning(f"Template '{name}' not found for deletion")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting template '{name}': {e}", exc_info=True)
            return False
    
    def get_template_versions(self, name: str) -> List[TemplateVersion]:
        """Get version history for a template"""
        return self.versions.get(name, [])
    
    def rollback_template(self, name: str, version: str, user: str = "system") -> bool:
        """
        Rollback a template to a previous version
        
        Args:
            name: Template name
            version: Version to rollback to
            user: User performing rollback
            
        Returns:
            bool: True if rollback successful
        """
        try:
            versions = self.versions.get(name, [])
            target_version = None
            
            for v in versions:
                if v.version == version:
                    target_version = v
                    break
            
            if not target_version:
                logger.error(f"Version {version} not found for template {name}")
                return False
            
            # Get the template state at that version by applying changes in reverse
            # This is a simplified implementation - in production you might store full snapshots
            logger.warning(f"Rollback for template '{name}' to version '{version}' requested but not fully implemented")
            return False
            
        except Exception as e:
            logger.error(f"Error rolling back template '{name}' to version '{version}': {e}", exc_info=True)
            return False
    
    def list_categories(self) -> List[str]:
        """List all template categories"""
        categories = set()
        for template in self.templates.values():
            categories.add(template.get('category', 'uncategorized'))
        return sorted(categories)
    
    def get_template_stats(self) -> Dict[str, Any]:
        """Get statistics about stored templates"""
        categories = {}
        total_templates = len(self.templates)
        total_versions = sum(len(versions) for versions in self.versions.values())
        
        for template in self.templates.values():
            category = template.get('category', 'uncategorized')
            categories[category] = categories.get(category, 0) + 1
        
        return {
            'total_templates': total_templates,
            'total_versions': total_versions,
            'categories': categories,
            'average_variables': sum(len(t.get('variables', [])) for t in self.templates.values()) / total_templates if total_templates > 0 else 0,
            'storage_path': str(self.storage_path),
            'backup_dir': str(self.backup_dir)
        }
    
    def get_template_statistics(self) -> Dict[str, Any]:
        """Alias for get_template_stats for compatibility"""
        return self.get_template_stats()
    
    def search_templates(self, query: str) -> List[Dict[str, Any]]:
        """Search templates by name, content, or category"""
        results = []
        query_lower = query.lower()
        
        for name, template in self.templates.items():
            score = 0
            
            # Check name match
            if query_lower in name.lower():
                score += 10
            
            # Check template content match
            if query_lower in template.get('template', '').lower():
                score += 5
            
            # Check category match
            if query_lower in template.get('category', '').lower():
                score += 3
            
            # Check description match
            if query_lower in template.get('description', '').lower():
                score += 2
            
            # Check variables match
            for var in template.get('variables', []):
                if query_lower in var.lower():
                    score += 1
            
            if score > 0:
                results.append({
                    'name': name,
                    'template': template,
                    'relevance_score': score
                })
        
        # Sort by relevance
        results.sort(key=lambda x: x['relevance_score'], reverse=True)
        return results
    
    def validate_template(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate template data structure
        
        Args:
            template_data: Template data to validate
            
        Returns:
            Validation result with success status and errors
        """
        errors = []
        
        # Required fields
        required_fields = ['template', 'variables', 'category']
        for field in required_fields:
            if field not in template_data:
                errors.append(f"Missing required field: {field}")
        
        # Type validation
        if 'template' in template_data and not isinstance(template_data['template'], str):
            errors.append("Template must be a string")
        
        if 'variables' in template_data and not isinstance(template_data['variables'], list):
            errors.append("Variables must be a list")
        
        if 'category' in template_data and not isinstance(template_data['category'], str):
            errors.append("Category must be a string")
        
        # Template variable validation
        if 'template' in template_data and 'variables' in template_data:
            template_text = template_data['template']
            declared_vars = set(template_data['variables'])
            
            # Find variables used in template
            import re
            used_vars = set(re.findall(r'\{(\w+)\}', template_text))
            
            # Check for undeclared variables
            undeclared = used_vars - declared_vars
            if undeclared:
                errors.append(f"Template uses undeclared variables: {list(undeclared)}")
            
            # Check for unused declared variables
            unused = declared_vars - used_vars
            if unused:
                errors.append(f"Declared but unused variables: {list(unused)}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def export_templates(self, export_path: str, include_versions: bool = False) -> bool:
        """
        Export templates to a file
        
        Args:
            export_path: Path to export file
            include_versions: Whether to include version history
            
        Returns:
            bool: True if export successful
        """
        try:
            export_data = {
                'templates': self.templates,
                'exported_at': datetime.now().isoformat(),
                'export_version': '1.0'
            }
            
            if include_versions:
                export_data['versions'] = {
                    template_name: [
                        {
                            'version': v.version,
                            'timestamp': v.timestamp,
                            'user': v.user,
                            'changes': v.changes,
                            'checksum': v.checksum
                        } for v in versions
                    ] for template_name, versions in self.versions.items()
                }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Successfully exported templates to {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting templates: {e}", exc_info=True)
            return False
    
    def import_templates(self, import_path: str, merge: bool = True, user: str = "system") -> bool:
        """
        Import templates from a file
        
        Args:
            import_path: Path to import file
            merge: Whether to merge with existing templates or replace
            user: User performing import
            
        Returns:
            bool: True if import successful
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            imported_templates = import_data.get('templates', {})
            
            if not merge:
                # Replace all templates
                self.templates = {}
            
            # Import templates
            for name, template_data in imported_templates.items():
                self.save_template(name, template_data, user)
            
            logger.info(f"Successfully imported {len(imported_templates)} templates from {import_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error importing templates: {e}", exc_info=True)
            return False
    
    def cleanup_old_backups(self, keep_days: int = 30) -> int:
        """
        Clean up old backup files
        
        Args:
            keep_days: Number of days to keep backups
            
        Returns:
            Number of files deleted
        """
        try:
            cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
            deleted_count = 0
            
            for backup_file in self.backup_dir.glob("sms_templates_backup_*.json"):
                if backup_file.stat().st_mtime < cutoff_time:
                    backup_file.unlink()
                    deleted_count += 1
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old backup files")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up backups: {e}", exc_info=True)
            return 0


# Global instance for easy access
template_storage = TemplateStorage()

def get_template_storage() -> TemplateStorage:
    """Get the global template storage instance"""
    return template_storage
#!/usr/bin/env python3
"""
Enhanced NLP Integration for Karen AI

This module integrates the enhanced NLP capabilities with Karen's existing
email processing, SMS, and agent communication systems.

Features:
1. Service entity extraction with confidence scoring
2. Intelligent quote generation based on detected services
3. Multi-language support (English/Spanish)
4. Customer preference learning and memory
5. Context-aware response generation
"""

import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path

try:
    from .nlp_enhancements import HandymanNLPEnhancer, ServiceEntity, PriceEntity, CustomerPreference
    from .config import Config
except ImportError:
    # Fallback for direct execution
    from nlp_enhancements import HandymanNLPEnhancer, ServiceEntity, PriceEntity, CustomerPreference
    try:
        from config import Config
    except ImportError:
        # Create a minimal config class
        class Config:
            def __init__(self):
                pass

logger = logging.getLogger(__name__)

class EnhancedNLPIntegration:
    """Enhanced NLP integration for Karen AI system"""
    
    def __init__(self):
        self.enhancer = HandymanNLPEnhancer()
        self.config = Config()
        self.customer_data_file = Path("data/customer_preferences.json")
        self.conversation_data_file = Path("data/conversation_contexts.json")
        
        # Ensure data directory exists
        self.customer_data_file.parent.mkdir(exist_ok=True)
        
        # Load existing data
        self._load_customer_data()
        
    def _load_customer_data(self):
        """Load saved customer preferences and conversation contexts"""
        try:
            if self.customer_data_file.exists():
                with open(self.customer_data_file, 'r') as f:
                    data = json.load(f)
                    # Reconstruct customer preferences
                    for customer_id, pref_data in data.get('preferences', {}).items():
                        # Convert back to CustomerPreference object
                        pref = CustomerPreference(customer_id=customer_id)
                        for key, value in pref_data.items():
                            if hasattr(pref, key):
                                setattr(pref, key, value)
                        self.enhancer.customer_preferences[customer_id] = pref
                        
            if self.conversation_data_file.exists():
                with open(self.conversation_data_file, 'r') as f:
                    self.enhancer.conversation_context = json.load(f)
                    
        except Exception as e:
            logger.warning(f"Could not load customer data: {e}")
    
    def _save_customer_data(self):
        """Save customer preferences and conversation contexts"""
        try:
            # Save preferences
            preferences_data = {}
            for customer_id, pref in self.enhancer.customer_preferences.items():
                preferences_data[customer_id] = {
                    'preferred_times': pref.preferred_times,
                    'service_history': pref.service_history,
                    'communication_style': pref.communication_style,
                    'language_preference': pref.language_preference,
                    'price_sensitivity': pref.price_sensitivity,
                    'preferred_contractors': pref.preferred_contractors,
                    'budget_range': pref.budget_range,
                    'response_time_preference': pref.response_time_preference,
                    'contact_method_preference': pref.contact_method_preference,
                    'satisfaction_history': pref.satisfaction_history
                }
            
            with open(self.customer_data_file, 'w') as f:
                json.dump({'preferences': preferences_data}, f, indent=2)
                
            # Save conversation contexts  
            with open(self.conversation_data_file, 'w') as f:
                json.dump(dict(self.enhancer.conversation_context), f, indent=2)
                
        except Exception as e:
            logger.error(f"Could not save customer data: {e}")

    def process_email_content(self, email_content: str, sender_email: str) -> Dict[str, Any]:
        """
        Process email content with enhanced NLP
        
        Args:
            email_content: The email message content
            sender_email: Sender's email address (used as customer ID)
            
        Returns:
            Enhanced analysis results including services, quotes, and suggestions
        """
        logger.info(f"Processing email from {sender_email}")
        
        # Process with enhanced NLP
        result = self.enhancer.process_enhanced_message(email_content, sender_email)
        
        # Enhanced analysis for email context
        enhanced_result = {
            **result,
            'email_context': {
                'sender': sender_email,
                'timestamp': datetime.now().isoformat(),
                'medium': 'email'
            },
            'response_strategy': self._determine_response_strategy(result),
            'urgency_score': self._calculate_urgency_score(result),
            'recommended_actions': self._get_recommended_actions(result)
        }
        
        # Update conversation context
        if result['service_entities']:
            self.enhancer.update_conversation_context(
                sender_email,
                email_content,
                "Email processed with enhanced NLP",
                result['service_entities']
            )
        
        # Save updated data
        self._save_customer_data()
        
        return enhanced_result

    def process_sms_content(self, sms_content: str, phone_number: str) -> Dict[str, Any]:
        """
        Process SMS content with enhanced NLP
        
        Args:
            sms_content: The SMS message content
            phone_number: Sender's phone number (used as customer ID)
            
        Returns:
            Enhanced analysis results optimized for SMS responses
        """
        logger.info(f"Processing SMS from {phone_number}")
        
        # Process with enhanced NLP
        result = self.enhancer.process_enhanced_message(sms_content, phone_number)
        
        # SMS-specific enhancements
        enhanced_result = {
            **result,
            'sms_context': {
                'phone': phone_number,
                'timestamp': datetime.now().isoformat(),
                'medium': 'sms',
                'character_count': len(sms_content)
            },
            'response_strategy': self._determine_sms_response_strategy(result),
            'urgency_score': self._calculate_urgency_score(result),
            'suggested_sms_response': self._generate_sms_response(result)
        }
        
        # Learn from SMS interaction
        self.enhancer.learn_customer_preferences(phone_number, {
            'contact_method_preference': 'sms',
            'message_length': len(sms_content),
            'detected_language': result['detected_language']
        })
        
        # Save updated data
        self._save_customer_data()
        
        return enhanced_result

    def _determine_response_strategy(self, nlp_result: Dict[str, Any]) -> str:
        """Determine the best response strategy based on NLP analysis"""
        
        # Emergency situations
        if any(entity.urgency == 'high' for entity in nlp_result['service_entities']):
            return 'immediate_response'
        
        # Quote requests
        if nlp_result['generated_quote'] or nlp_result['price_entities']:
            return 'quote_focused'
        
        # Multi-service requests
        if len(nlp_result['service_entities']) > 1:
            return 'comprehensive_consultation'
        
        # Spanish language
        if nlp_result['detected_language'] == 'es':
            return 'spanish_response'
        
        # Default
        return 'standard_response'

    def _determine_sms_response_strategy(self, nlp_result: Dict[str, Any]) -> str:
        """Determine SMS-specific response strategy"""
        
        # Emergency - immediate phone call
        if any(entity.urgency == 'high' for entity in nlp_result['service_entities']):
            return 'emergency_callback'
        
        # Quote request - send brief estimate
        if nlp_result['generated_quote']:
            return 'brief_quote'
        
        # Multi-service - schedule consultation
        if len(nlp_result['service_entities']) > 1:
            return 'schedule_consultation'
        
        return 'standard_sms'

    def _calculate_urgency_score(self, nlp_result: Dict[str, Any]) -> int:
        """Calculate urgency score from 1-10"""
        score = 1
        
        for entity in nlp_result['service_entities']:
            if entity.urgency == 'high':
                score += 4
            elif entity.urgency == 'medium':
                score += 2
            else:
                score += 1
        
        # Emergency keywords boost
        emergency_keywords = ['flood', 'burst', 'overflow', 'sparks', 'fire', 'danger']
        # This would need the original message, simplified for now
        
        return min(score, 10)

    def _get_recommended_actions(self, nlp_result: Dict[str, Any]) -> List[str]:
        """Get recommended actions based on analysis"""
        actions = []
        
        # High urgency services
        high_urgency_services = [e for e in nlp_result['service_entities'] if e.urgency == 'high']
        if high_urgency_services:
            actions.append("Schedule emergency service call within 2 hours")
            actions.append("Send safety instructions if applicable")
        
        # Quote requests
        if nlp_result['generated_quote']:
            actions.append("Send detailed quote with service breakdown")
            actions.append("Include availability calendar")
        
        # Multi-service opportunities
        if len(nlp_result['service_entities']) > 1:
            actions.append("Offer bundled service discount")
            actions.append("Schedule comprehensive site visit")
        
        # Language-specific actions
        if nlp_result['detected_language'] == 'es':
            actions.append("Respond in Spanish")
            actions.append("Assign Spanish-speaking technician if available")
        
        return actions

    def _generate_sms_response(self, nlp_result: Dict[str, Any]) -> str:
        """Generate appropriate SMS response"""
        
        # Emergency response
        if any(entity.urgency == 'high' for entity in nlp_result['service_entities']):
            if nlp_result['detected_language'] == 'es':
                return "¡EMERGENCIA! Te llamaremos en 5 minutos. Mantén segura el área."
            return "EMERGENCY! We'll call you in 5 minutes. Keep area safe."
        
        # Quote response
        if nlp_result['generated_quote']:
            quote = nlp_result['generated_quote']
            if nlp_result['detected_language'] == 'es':
                return f"Estimación: ${quote['total_estimate']:.0f}. ¿Cuándo es conveniente para ti?"
            return f"Estimate: ${quote['total_estimate']:.0f}. When works best for you?"
        
        # Service acknowledgment
        if nlp_result['service_entities']:
            service = nlp_result['service_entities'][0]
            if nlp_result['detected_language'] == 'es':
                return f"Recibido: {service.service_type}. Te contactaremos pronto."
            return f"Got it: {service.service_type} service. We'll contact you soon."
        
        # Default
        if nlp_result['detected_language'] == 'es':
            return "Mensaje recibido. Responderemos pronto."
        return "Message received. We'll respond soon."

    def get_customer_insights(self, customer_id: str) -> Dict[str, Any]:
        """Get comprehensive customer insights"""
        
        insights = {
            'customer_id': customer_id,
            'has_history': customer_id in self.enhancer.customer_preferences,
            'conversation_count': len(self.enhancer.conversation_context.get(customer_id, [])),
            'preferences': {},
            'service_patterns': {},
            'recommendations': []
        }
        
        if customer_id in self.enhancer.customer_preferences:
            pref = self.enhancer.customer_preferences[customer_id]
            insights['preferences'] = {
                'language': pref.language_preference,
                'communication_style': pref.communication_style,
                'price_sensitivity': pref.price_sensitivity,
                'preferred_contact': pref.contact_method_preference,
                'response_time': pref.response_time_preference
            }
            
            # Analyze service patterns
            if pref.service_history:
                from collections import Counter
                service_counts = Counter(pref.service_history)
                insights['service_patterns'] = {
                    'most_common': service_counts.most_common(3),
                    'total_services': len(pref.service_history),
                    'unique_services': len(set(pref.service_history))
                }
                
                # Generate recommendations
                if len(pref.service_history) > 2:
                    insights['recommendations'].append("Offer maintenance package")
                
                if pref.price_sensitivity == 'high':
                    insights['recommendations'].append("Emphasize value and discounts")
                    
                if pref.language_preference == 'es':
                    insights['recommendations'].append("Ensure Spanish-speaking technician")
        
        return insights

    def generate_response_template(self, nlp_result: Dict[str, Any], 
                                 response_type: str = 'email') -> str:
        """Generate response template based on NLP analysis"""
        
        strategy = nlp_result.get('response_strategy', 'standard_response')
        language = nlp_result.get('detected_language', 'en')
        
        templates = {
            'immediate_response': {
                'en': """
Dear Customer,

Thank you for contacting 757 Handy. I understand you have an urgent {service_type} situation that requires immediate attention.

We are dispatching a technician to address your emergency. You can expect:
• Emergency service call within 2 hours
• Technician will contact you directly
• Initial assessment: ${quote}

For your safety, please {safety_instructions}.

Best regards,
Karen - 757 Handy Assistant
""",
                'es': """
Estimado Cliente,

Gracias por contactar 757 Handy. Entiendo que tiene una situación urgente de {service_type} que requiere atención inmediata.

Estamos enviando un técnico para atender su emergencia. Puede esperar:
• Llamada de servicio de emergencia dentro de 2 horas  
• El técnico se contactará directamente
• Evaluación inicial: ${quote}

Para su seguridad, por favor {safety_instructions}.

Saludos cordiales,
Karen - Asistente de 757 Handy
"""
            },
            'quote_focused': {
                'en': """
Dear Customer,

Thank you for your service request. Based on your description, I've prepared the following estimate:

{quote_breakdown}

This quote includes:
• Professional service technician
• All standard materials
• Service guarantee

Would you like to schedule this service? I have availability {availability}.

Best regards,
Karen - 757 Handy Assistant
""",
                'es': """
Estimado Cliente,

Gracias por su solicitud de servicio. Basado en su descripción, he preparado la siguiente estimación:

{quote_breakdown}

Esta cotización incluye:
• Técnico profesional de servicio
• Todos los materiales estándar
• Garantía de servicio

¿Le gustaría programar este servicio? Tengo disponibilidad {availability}.

Saludos cordiales,
Karen - Asistente de 757 Handy
"""
            }
        }
        
        template = templates.get(strategy, templates['quote_focused'])[language]
        
        # Fill in template variables
        if nlp_result['service_entities']:
            service_type = nlp_result['service_entities'][0].service_type
            template = template.replace('{service_type}', service_type)
        
        if nlp_result['generated_quote']:
            quote = nlp_result['generated_quote']['total_estimate']
            template = template.replace('{quote}', f"{quote:.0f}")
            
            # Generate quote breakdown
            breakdown = []
            for service in nlp_result['generated_quote']['service_breakdown']:
                breakdown.append(f"• {service['service_type']}: ${service['estimated_cost']:.0f}")
            template = template.replace('{quote_breakdown}', '\n'.join(breakdown))
        
        return template.strip()


# Factory function for easy integration
def create_enhanced_nlp_processor() -> EnhancedNLPIntegration:
    """Create an enhanced NLP processor instance"""
    return EnhancedNLPIntegration()


# Example usage for testing
if __name__ == "__main__":
    processor = create_enhanced_nlp_processor()
    
    # Test email processing
    email_content = """
    Hello! I have an emergency plumbing issue in my kitchen. 
    The sink is leaking badly and water is getting on the floor.
    I need someone to come out today. What would this cost?
    """
    
    result = processor.process_email_content(email_content, "customer@example.com")
    
    print("🚀 Enhanced NLP Integration Test")
    print("=" * 40)
    print(f"Language: {result['detected_language']}")
    print(f"Services: {len(result['service_entities'])}")
    print(f"Strategy: {result['response_strategy']}")
    print(f"Urgency: {result['urgency_score']}/10")
    
    if result['generated_quote']:
        print(f"Quote: ${result['generated_quote']['total_estimate']:.2f}")
    
    print("\nRecommended Actions:")
    for action in result['recommended_actions']:
        print(f"  • {action}")
    
    print("\nGenerated Response:")
    response = processor.generate_response_template(result)
    print(response[:200] + "..." if len(response) > 200 else response)
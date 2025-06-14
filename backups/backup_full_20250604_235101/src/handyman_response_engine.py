"""
Handyman Response Engine - Intelligent email response system for handyman business
"""
import logging
import re
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import json
import asyncio # Added for asyncio.to_thread

try:
    from .nlp_enhancements import HandymanNLPEnhancer
    NLP_AVAILABLE = True
except ImportError:
    logger.warning("NLP enhancements not available. Install dependencies: pip install spacy")
    NLP_AVAILABLE = False

logger = logging.getLogger(__name__)

class HandymanResponseEngine:
    """Enhanced response engine specifically designed for handyman business communications"""
    
    def __init__(self, business_name: str = "Beach Handyman", 
                 service_area: str = "Virginia Beach area",
                 phone: str = "757-354-4577",
                 llm_client: Optional[Any] = None):
        self.business_name = business_name
        self.service_area = service_area
        self.phone = phone
        self.business_hours = "Monday-Friday 8AM-6PM, Saturday 8AM-4PM"
        self.llm_client = llm_client
        
        # Initialize enhanced NLP processor
        self.nlp_enhancer = None
        if NLP_AVAILABLE:
            try:
                self.nlp_enhancer = HandymanNLPEnhancer()
                logger.info("Enhanced NLP processor initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize NLP enhancer: {e}")
                self.nlp_enhancer = None
        
        # Common handyman services
        self.services = {
            'plumbing': ['plumb', 'leak', 'drain', 'faucet', 'toilet', 'pipe', 'water'],
            'electrical': ['electric', 'outlet', 'switch', 'light', 'wiring', 'breaker', 'power'],
            'hvac': ['heat', 'cool', 'ac', 'air condition', 'thermostat', 'vent', 'hvac'],
            'carpentry': ['wood', 'cabinet', 'door', 'window', 'trim', 'deck', 'fence'],
            'drywall': ['drywall', 'wall', 'ceiling', 'patch', 'hole', 'crack'],
            'painting': ['paint', 'primer', 'brush', 'roller', 'color'],
            'flooring': ['floor', 'tile', 'carpet', 'vinyl', 'hardwood', 'laminate'],
            'general': ['fix', 'repair', 'install', 'replace', 'maintenance', 'handyman']
        }
        
        # Emergency keywords
        self.emergency_keywords = [
            'emergency', 'urgent', 'asap', 'immediately', 'flood', 'flooding',
            'burst pipe', 'no power', 'electrical fire', 'gas leak', 'ceiling leak'
        ]

    def classify_email_type(self, subject: str, body: str, customer_id: Optional[str] = None) -> Dict[str, Any]:
        """Classify the email to determine the best response approach"""
        content = (subject + " " + body).lower()
        full_text = subject + " " + body
        
        # Basic classification (fallback)
        classification = {
            'is_emergency': any(keyword in content for keyword in self.emergency_keywords),
            'services_mentioned': [],
            'is_quote_request': any(word in content for word in ['quote', 'estimate', 'cost', 'price', 'how much']),
            'is_appointment_request': any(word in content for word in ['schedule', 'appointment', 'when', 'available', 'book time', 'see you']),
            'is_general_inquiry': True,  # Default to true, will be refined
            'tone': 'professional',  # Default tone
            'language': 'en',  # Default language
            'extracted_entities': [],
            'price_entities': [],
            'generated_quote': None,
            'response_suggestions': []
        }
        
        # Use enhanced NLP if available
        if self.nlp_enhancer:
            try:
                nlp_result = self.nlp_enhancer.process_enhanced_message(full_text, customer_id)
                
                # Update classification with NLP results
                classification['language'] = nlp_result['detected_language']
                classification['extracted_entities'] = nlp_result['service_entities']
                classification['price_entities'] = nlp_result['price_entities']
                classification['generated_quote'] = nlp_result['generated_quote']
                classification['response_suggestions'] = nlp_result['response_suggestions']
                
                # Update services mentioned based on extracted entities
                for entity in nlp_result['service_entities']:
                    if entity.service_type not in classification['services_mentioned']:
                        classification['services_mentioned'].append(entity.service_type)
                
                # Update urgency based on NLP analysis
                for entity in nlp_result['service_entities']:
                    if entity.urgency == 'high':
                        classification['is_emergency'] = True
                        break
                
                logger.info(f"Enhanced NLP classification completed. Language: {classification['language']}, "
                          f"Entities: {len(classification['extracted_entities'])}")
                
            except Exception as e:
                logger.warning(f"NLP enhancement failed, using basic classification: {e}")
        
        # Fallback to basic service detection if NLP didn't find services
        if not classification['services_mentioned']:
            for service_type, keywords in self.services.items():
                if any(keyword in content for keyword in keywords):
                    classification['services_mentioned'].append(service_type)
        
        # Determine if it's a general inquiry or specific request
        if classification['services_mentioned'] or classification['is_quote_request'] or classification['is_appointment_request']:
            classification['is_general_inquiry'] = False
            
        return classification

    def generate_enhanced_prompt(self, email_from: str, email_subject: str, 
                                email_body: str, classification: Dict[str, Any]) -> str:
        """Generate an enhanced prompt for the LLM based on email classification"""
        
        current_time = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
        
        base_prompt = f"""You are Karen, the AI assistant for {self.business_name}, a professional handyman service in the {self.service_area}.

BUSINESS INFORMATION:
- Business: {self.business_name}
- Service Area: {self.service_area}
- Phone: {self.phone}
- Hours: {self.business_hours}
- Current Time: {current_time}

RESPONSE GUIDELINES:
1. Always be professional, friendly, and helpful
2. Use the customer's name if provided in the email
3. Reference specific services mentioned in their inquiry
4. Provide relevant business information (phone, hours, service area)
5. Keep responses concise but informative (2-4 paragraphs max)
6. Always end with a clear call to action
7. Use proper grammar and professional formatting

"""

        # Add specific instructions based on classification
        if classification['is_emergency']:
            base_prompt += """
🚨 EMERGENCY RESPONSE PROTOCOL:
- This appears to be an EMERGENCY situation
- Prioritize immediate assistance and safety
- Provide emergency contact information
- Suggest temporary safety measures if applicable
- Express urgency and understanding

"""

        if classification['is_quote_request']:
            base_prompt += """
QUOTE REQUEST PROTOCOL:
- Acknowledge their quote request professionally
- Explain that accurate quotes require an in-person assessment
- Mention we provide free estimates
- Ask for their location and best contact method
- Suggest a phone call for faster scheduling

"""

        if classification['is_appointment_request']:
            base_prompt += """
APPOINTMENT SCHEDULING PROTOCOL:
- Acknowledge their scheduling request
- Reference our business hours
- Ask for their preferred date/time and location
- Mention our flexibility for emergency situations
- Provide phone number for faster scheduling

"""

        if classification['services_mentioned']:
            services_text = ", ".join(classification['services_mentioned'])
            base_prompt += f"""
SERVICES MENTIONED: {services_text}
- Reference your expertise in these specific areas
- Mention relevant experience or specializations
- Provide service-specific information if helpful

"""
        
        # Add NLP-enhanced information
        if classification.get('extracted_entities'):
            base_prompt += """
ENHANCED SERVICE ANALYSIS:
"""
            for entity in classification['extracted_entities']:
                base_prompt += f"- {entity.service_type.title()}: {entity.description} (Urgency: {entity.urgency})\n"
                if entity.estimated_duration:
                    base_prompt += f"  Estimated duration: {entity.estimated_duration}\n"
                if entity.materials_needed:
                    base_prompt += f"  Materials may include: {', '.join(entity.materials_needed)}\n"
            base_prompt += "\n"
        
        # Add quote information if available
        if classification.get('generated_quote'):
            quote = classification['generated_quote']
            base_prompt += f"""
GENERATED QUOTE ESTIMATE: ${quote['total_estimate']:.2f}
- Use this as a reference for pricing discussions
- Mention that final pricing depends on assessment
- Quote valid until: {quote['valid_until'][:10]}

"""
        
        # Add language-specific instructions
        if classification.get('language') == 'es':
            base_prompt += """
LANGUAGE NOTE: Customer appears to prefer Spanish
- Respond in Spanish or offer bilingual service
- Use professional Spanish business terminology
- Mention Spanish-speaking staff availability

"""
        
        # Add contextual suggestions
        if classification.get('response_suggestions'):
            suggestions = classification['response_suggestions'][:2]  # Top 2 suggestions
            base_prompt += f"""
RESPONSE SUGGESTIONS:
{chr(10).join(f"- {suggestion}" for suggestion in suggestions)}

"""

        base_prompt += f"""
EMAIL TO RESPOND TO:
From: {email_from}
Subject: {email_subject}

Email Content:
{email_body}

GENERATE RESPONSE:
Write a professional email response as Karen from {self.business_name}. Include appropriate business information and a clear next step for the customer."""

        return base_prompt

    async def generate_response_async(self, email_from: str, email_subject: str, 
                               email_body: str, customer_id: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """Generate an enhanced response using the handyman-specific engine"""
        
        if not self.llm_client:
            logger.error("LLMClient not initialized in HandymanResponseEngine. Cannot generate AI response.")
            classification = self.classify_email_type(email_subject, email_body, customer_id)
            return self._generate_fallback_response(email_from, classification), classification

        classification = self.classify_email_type(email_subject, email_body, customer_id)
        enhanced_prompt = self.generate_enhanced_prompt(
            email_from, email_subject, email_body, classification
        )
        try:
            # Generate response using LLM, running the synchronous method in a separate thread
            response_text = await asyncio.to_thread(
                self.llm_client.generate_text, # The synchronous method to call
                enhanced_prompt # The argument to pass to generate_text
            )
            
            # Handle language preferences and translation
            if self.nlp_enhancer and classification.get('language') == 'es':
                try:
                    # Translate key parts if needed (basic implementation)
                    response_text = self.nlp_enhancer.translate_response(response_text, 'es')
                except Exception as e:
                    logger.warning(f"Translation failed: {e}")
            
            # Add signature if not present
            signature_keywords = ['karen', self.business_name.lower(), 'best regards', self.phone]
            if not any(sig in response_text.lower() for sig in signature_keywords):
                if classification.get('language') == 'es':
                    response_text += f"\n\nSaludos cordiales,\nKaren\n{self.business_name}\n{self.phone}"
                else:
                    response_text += f"\n\nBest regards,\nKaren\n{self.business_name}\n{self.phone}"
            
            # Update conversation context if NLP enhancer is available
            if self.nlp_enhancer and customer_id and classification.get('extracted_entities'):
                try:
                    self.nlp_enhancer.update_conversation_context(
                        customer_id, 
                        email_subject + " " + email_body,
                        response_text,
                        classification['extracted_entities']
                    )
                except Exception as e:
                    logger.warning(f"Failed to update conversation context: {e}")
            
            logger.info(f"Enhanced response generated. Classification: {classification}")
            return response_text, classification
            
        except Exception as e:
            logger.error(f"Error generating enhanced response with LLM: {e}", exc_info=True)
            fallback = self._generate_fallback_response(email_from, classification)
            return fallback, classification

    def _generate_fallback_response(self, email_from: str, classification: Dict[str, Any]) -> str:
        """Generate a fallback response if LLM fails"""
        
        if classification['is_emergency']:
            return f"""Thank you for contacting {self.business_name}.

I understand this appears to be an urgent situation. Please call us immediately at {self.phone} for emergency assistance.

If this is a life-threatening emergency, please call 911 first.

We're here to help and will respond as quickly as possible.

Best regards,
Karen
{self.business_name}
{self.phone}"""

        elif classification['is_quote_request']:
            return f"""Thank you for your interest in {self.business_name}!

I'd be happy to provide you with a quote for your project. To give you the most accurate estimate, we offer free in-person assessments in the {self.service_area}.

Please call us at {self.phone} to schedule a convenient time, or reply with:
- Your location
- Best phone number to reach you
- Preferred days/times for the assessment

We look forward to helping with your project!

Best regards,
Karen
{self.business_name}
{self.phone}"""

        else:
            return f"""Thank you for contacting {self.business_name}!

We've received your inquiry and will respond as soon as possible. For faster service, please call us at {self.phone}.

Our business hours are {self.business_hours}, and we service the {self.service_area}.

Best regards,
Karen
{self.business_name}
{self.phone}"""

    def should_notify_admin_immediately(self, classification: Dict[str, Any]) -> bool:
        """Determine if admin should be notified immediately"""
        return classification['is_emergency']

    def get_priority_level(self, classification: Dict[str, Any]) -> str:
        """Get priority level for the email"""
        if classification['is_emergency']:
            return "HIGH"
        elif classification['is_quote_request'] or classification['is_appointment_request']:
            return "MEDIUM"
        else:
            return "LOW"

    async def determine_intent(self, email_body: str, email_subject: str) -> str:
        """Determines the primary intent of the email using classification (can be expanded with LLM if needed)."""
        content = f"Subject: {email_subject}\nBody: {email_body}"
        prompt = f"Based on the following email content, what is the primary intent? Choose ONE: schedule_appointment, quote_request, general_inquiry, emergency_inquiry, unknown.\n\nEmail:\n{content}\n\nIntent:"
        if not self.llm_client:
            logger.warning("LLMClient not available for intent determination.")
            return "unknown"
        try:
            intent_response = await asyncio.to_thread(self.llm_client.generate_text, prompt)
            intent = intent_response.strip().lower().replace(".","")
            # Add more robust parsing if needed
            if "schedule_appointment" in intent: return "schedule_appointment"
            if "quote_request" in intent: return "quote_request"
            if "general_inquiry" in intent: return "general_inquiry"
            if "emergency_inquiry" in intent: return "emergency_inquiry"
            logger.warning(f"Could not parse intent from LLM response: '{intent_response}'. Defaulting to unknown.")
            return "unknown"
        except Exception as e:
            logger.error(f"Error during intent determination: {e}", exc_info=True)
            return "unknown"

    async def extract_appointment_details(self, email_body: str, email_subject: str) -> Optional[Dict[str, Any]]:
        """Uses LLM to extract appointment details from an email."""
        if not self.llm_client:
            logger.error("LLMClient not available in HandymanResponseEngine for extracting appointment details.")
            return None

        current_iso_date = datetime.now(timezone.utc).isoformat()

        extraction_prompt = f"""
You are an expert assistant skilled at extracting appointment details from customer emails.
Current date for reference: {current_iso_date}.
Analyze the following email content and extract relevant information for scheduling an appointment.

Email Subject: {email_subject}
Email Body:
--- START EMAIL BODY ---
{email_body}
--- END EMAIL BODY ---

Extract the following details if present. If a detail is not explicitly mentioned, use null for its value.
Provide the output in JSON format with the following keys:
- "requested_date": (string) The specific date requested (e.g., "tomorrow", "next Tuesday", "July 15th", "2024-07-15"). If multiple, pick the most likely or first one. If a day of the week, infer the next occurrence unless year is specified.
- "requested_time": (string) The specific time requested (e.g., "morning", "afternoon", "3 PM", "15:00"). 
- "preferred_days": (list of strings) e.g. ["Monday", "Wednesday"]
- "preferred_time_window": (string) e.g., "any weekday morning", "weekend afternoons"
- "service_description": (string) A brief description of the service needed or the reason for the appointment.
- "estimated_duration_hours": (float) If the user mentions a duration or implies it (e.g., "a couple of hours" -> 2.0, "all day" -> 8.0). Default to 1.0 if a service is mentioned but no duration.
- "flexibility": (string) Any comments on flexibility (e.g., "flexible on time", "only available after 5 PM").

Example JSON Output:
{
  "requested_date": "tomorrow",
  "requested_time": "afternoon",
  "preferred_days": null,
  "preferred_time_window": "weekday afternoons",
  "service_description": "fix a leaky faucet in the kitchen",
  "estimated_duration_hours": 1.5,
  "flexibility": "can do Wednesday instead if Tuesday afternoon is booked"
}

If no specific date/time is mentioned but they ask for availability, set requested_date and requested_time to null.
Focus on extracting information for a *new* appointment. Do not extract details if the email is clearly a follow-up, cancellation, or confirmation of an *existing* appointment unless it proposes a new time.
Output ONLY the JSON object.
"""
        response_text_for_error_logging = "" # Initialize for use in except block
        try:
            logger.debug(f"Sending prompt to LLM for appointment detail extraction: {extraction_prompt[:300]}...")
            
            # Correctly call the synchronous llm_client.generate_text via asyncio.to_thread
            response_text = await asyncio.to_thread(
                self.llm_client.generate_text, # The synchronous method
                extraction_prompt             # The argument
            )
            response_text_for_error_logging = response_text # Store for potential error logging
            
            logger.debug(f"LLM response for extraction: {response_text}")
            
            # Clean the response to get only the JSON part
            match = re.search(r'\{(.*?)\}', response_text, re.DOTALL) # Keep existing regex for single JSON object, or adjust if array is possible
            if match:
                json_str_cleaned = "{" + match.group(1) + "}"
                try:
                    details = json.loads(json_str_cleaned)
                    logger.info(f"Successfully extracted appointment details: {details}")
                    # Ensure estimated_duration_hours is a float, default to 1.0 if not present or invalid
                    duration = details.get('estimated_duration_hours')
                    if isinstance(duration, (int, float)) and duration > 0:
                        details['estimated_duration_hours'] = float(duration)
                    else:
                        details['estimated_duration_hours'] = 1.0 # Default if not present, or invalid type/value
                    return details
                except json.JSONDecodeError as je:
                    logger.error(f"JSONDecodeError parsing appointment details: '{je}'. Raw string: '{json_str_cleaned}'")
                    return None
            else:
                logger.warning(f"No JSON object found in LLM output for appointment details: {response_text}")
                return None
        except json.JSONDecodeError as e: # This specific catch might be redundant if json_str_cleaned is used above
            logger.error(f"Failed to decode JSON from LLM response for appointment extraction: {e}. Response was: {response_text_for_error_logging}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Error during LLM call for appointment extraction: {e}. Response text (if available): {response_text_for_error_logging}", exc_info=True)
            return None 
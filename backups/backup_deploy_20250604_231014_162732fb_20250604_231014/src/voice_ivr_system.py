#!/usr/bin/env python3
"""
Advanced IVR (Interactive Voice Response) System for 757 Handy
Handles sophisticated menu navigation, voice recognition, and call routing

Author: Phone Engineer Agent
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from twilio.twiml.voice_response import VoiceResponse, Gather, Say, Play

logger = logging.getLogger(__name__)

class MenuOption(Enum):
    """Menu options with professional descriptions"""
    SCHEDULING = ("1", "schedule", "Schedule an appointment for home repairs or maintenance")
    QUOTES = ("2", "quote", "Request a free estimate for your project")
    EMERGENCY = ("3", "emergency", "Connect to emergency repair services")
    CUSTOMER_SERVICE = ("4", "support", "Speak with our customer service team")
    BILLING = ("5", "billing", "Payment and billing inquiries")
    HOURS_LOCATION = ("6", "hours", "Business hours and location information")
    REPEAT_MENU = ("9", "repeat", "Repeat this menu")
    OPERATOR = ("0", "operator", "Speak with an operator")

@dataclass
class VoicePrompt:
    """Professional voice prompt configuration"""
    text: str
    voice: str = 'Polly.Joanna'
    language: str = 'en-US'
    rate: str = 'medium'
    volume: str = '+0dB'
    
    def to_ssml(self) -> str:
        """Convert to SSML for enhanced voice control"""
        return f'<speak><prosody rate="{self.rate}" volume="{self.volume}">{self.text}</prosody></speak>'

@dataclass
class CallContext:
    """Track caller context and journey"""
    call_sid: str
    caller_id: str
    current_menu: str = 'main'
    previous_menus: List[str] = None
    attempts: int = 0
    language_preference: str = 'en'
    customer_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.previous_menus is None:
            self.previous_menus = []
        if self.customer_data is None:
            self.customer_data = {}

class VoiceIVRSystem:
    """
    Sophisticated IVR system with:
    - Multi-level menu navigation
    - Speech recognition with DTMF fallback
    - Context-aware responses
    - Professional voice prompts
    - Smart routing based on caller history
    """
    
    def __init__(self):
        self.company_name = "757 Handy"
        self.call_contexts: Dict[str, CallContext] = {}
        
        # Professional voice prompts
        self.prompts = {
            'welcome': VoicePrompt(
                text=f"Thank you for calling {self.company_name}, Hampton Roads' premier home improvement experts. We're here to make your home better."
            ),
            'main_menu': VoicePrompt(
                text=("Please select from the following options: "
                     "For appointment scheduling, say 'schedule' or press 1. "
                     "For a free estimate, say 'quote' or press 2. "
                     "For emergency repairs, say 'emergency' or press 3. "
                     "For customer service, say 'support' or press 4. "
                     "For billing questions, say 'billing' or press 5. "
                     "For hours and location, press 6. "
                     "To repeat this menu, press 9, or say 'repeat'. "
                     "To speak with an operator at any time, press 0.")
            ),
            'scheduling_menu': VoicePrompt(
                text=("Let's schedule your appointment. "
                     "For plumbing services, press 1. "
                     "For electrical work, press 2. "
                     "For carpentry and repairs, press 3. "
                     "For HVAC services, press 4. "
                     "For general maintenance, press 5. "
                     "To speak with our scheduling specialist, press 0.")
            ),
            'quote_menu': VoicePrompt(
                text=("We'd be happy to provide a free estimate. "
                     "For bathroom remodeling, press 1. "
                     "For kitchen renovations, press 2. "
                     "For deck or patio work, press 3. "
                     "For roofing estimates, press 4. "
                     "For other projects, press 5. "
                     "To describe your project to our estimator, press 0.")
            ),
            'invalid_input': VoicePrompt(
                text="I didn't understand your selection. Let me repeat your options."
            ),
            'too_many_attempts': VoicePrompt(
                text="I'm having trouble understanding your selection. Let me connect you with one of our friendly representatives who can help you directly."
            ),
            'transferring': VoicePrompt(
                text="Please hold while I connect you with the right person to help you. Thank you for your patience."
            )
        }
        
        # Menu structure
        self.menus = {
            'main': {
                'prompt': self.prompts['main_menu'],
                'options': {
                    '1': {'action': 'submenu', 'target': 'scheduling'},
                    '2': {'action': 'submenu', 'target': 'quotes'},
                    '3': {'action': 'transfer', 'target': 'emergency'},
                    '4': {'action': 'transfer', 'target': 'customer_service'},
                    '5': {'action': 'transfer', 'target': 'billing'},
                    '6': {'action': 'info', 'target': 'hours_location'},
                    '9': {'action': 'repeat', 'target': 'main'},
                    '0': {'action': 'transfer', 'target': 'operator'}
                },
                'speech_mappings': {
                    'schedule': '1', 'appointment': '1', 'book': '1',
                    'quote': '2', 'estimate': '2', 'price': '2', 'cost': '2',
                    'emergency': '3', 'urgent': '3', 'help': '3',
                    'support': '4', 'service': '4', 'customer': '4',
                    'billing': '5', 'payment': '5', 'invoice': '5', 'bill': '5',
                    'hours': '6', 'location': '6', 'address': '6',
                    'repeat': '9', 'menu': '9',
                    'operator': '0', 'person': '0', 'human': '0'
                }
            },
            'scheduling': {
                'prompt': self.prompts['scheduling_menu'],
                'options': {
                    '1': {'action': 'transfer', 'target': 'plumbing_scheduler'},
                    '2': {'action': 'transfer', 'target': 'electrical_scheduler'},
                    '3': {'action': 'transfer', 'target': 'carpentry_scheduler'},
                    '4': {'action': 'transfer', 'target': 'hvac_scheduler'},
                    '5': {'action': 'transfer', 'target': 'maintenance_scheduler'},
                    '0': {'action': 'transfer', 'target': 'scheduling_specialist'},
                    '9': {'action': 'submenu', 'target': 'main'},
                },
                'speech_mappings': {
                    'plumbing': '1', 'plumber': '1', 'pipes': '1', 'leak': '1', 'toilet': '1', 'sink': '1',
                    'electrical': '2', 'electric': '2', 'wiring': '2', 'outlet': '2', 'lights': '2',
                    'carpentry': '3', 'carpenter': '3', 'wood': '3', 'repair': '3', 'fix': '3',
                    'hvac': '4', 'heating': '4', 'cooling': '4', 'air': '4', 'furnace': '4',
                    'maintenance': '5', 'general': '5', 'handyman': '5',
                    'specialist': '0', 'person': '0'
                }
            },
            'quotes': {
                'prompt': self.prompts['quote_menu'],
                'options': {
                    '1': {'action': 'transfer', 'target': 'bathroom_estimator'},
                    '2': {'action': 'transfer', 'target': 'kitchen_estimator'},
                    '3': {'action': 'transfer', 'target': 'outdoor_estimator'},
                    '4': {'action': 'transfer', 'target': 'roofing_estimator'},
                    '5': {'action': 'transfer', 'target': 'general_estimator'},
                    '0': {'action': 'transfer', 'target': 'estimator'},
                    '9': {'action': 'submenu', 'target': 'main'},
                },
                'speech_mappings': {
                    'bathroom': '1', 'bath': '1', 'shower': '1', 'vanity': '1',
                    'kitchen': '2', 'cabinet': '2', 'countertop': '2',
                    'deck': '3', 'patio': '3', 'outdoor': '3', 'fence': '3',
                    'roof': '4', 'roofing': '4', 'shingles': '4', 'gutter': '4',
                    'other': '5', 'different': '5', 'custom': '5',
                    'estimator': '0', 'person': '0'
                }
            }
        }
        
        logger.info("VoiceIVRSystem initialized with professional menu structure")
    
    def get_call_context(self, call_sid: str, caller_id: str) -> CallContext:
        """Get or create call context for tracking"""
        if call_sid not in self.call_contexts:
            self.call_contexts[call_sid] = CallContext(call_sid, caller_id)
        return self.call_contexts[call_sid]
    
    def process_input(self, call_sid: str, caller_id: str, digits: str = None, 
                     speech_result: str = None, current_menu: str = 'main') -> Dict[str, Any]:
        """
        Process caller input (DTMF or speech) and return appropriate action
        
        Returns:
            Dict with 'action', 'target', 'twiml_response', and 'context'
        """
        context = self.get_call_context(call_sid, caller_id)
        context.current_menu = current_menu
        context.attempts += 1
        
        # Get menu configuration
        menu_config = self.menus.get(current_menu, self.menus['main'])
        
        # Determine selection from input
        selection = self._determine_selection(digits, speech_result, menu_config)
        
        logger.info(f"Call {call_sid}: Menu={current_menu}, Input=DTMF:{digits}/Speech:{speech_result}, Selection={selection}")
        
        # Handle selection
        if selection and selection in menu_config['options']:
            option = menu_config['options'][selection]
            context.attempts = 0  # Reset attempts on valid input
            
            return {
                'action': option['action'],
                'target': option['target'],
                'selection': selection,
                'context': context,
                'twiml_response': self._generate_action_response(option, context)
            }
        else:
            # Invalid input handling
            return self._handle_invalid_input(context, menu_config)
    
    def _determine_selection(self, digits: str, speech_result: str, menu_config: Dict) -> Optional[str]:
        """Determine menu selection from DTMF digits or speech"""
        
        # Try DTMF first (most reliable)
        if digits and digits in menu_config['options']:
            return digits
        
        # Try speech recognition
        if speech_result and 'speech_mappings' in menu_config:
            speech_lower = speech_result.lower().strip()
            
            # Check for exact matches first
            if speech_lower in menu_config['speech_mappings']:
                return menu_config['speech_mappings'][speech_lower]
            
            # Check for partial matches
            for keyword, option in menu_config['speech_mappings'].items():
                if keyword in speech_lower:
                    return option
        
        return None
    
    def _handle_invalid_input(self, context: CallContext, menu_config: Dict) -> Dict[str, Any]:
        """Handle invalid input with progressive assistance"""
        
        if context.attempts >= 3:
            # Too many attempts - transfer to human
            response = VoiceResponse()
            response.say(self.prompts['too_many_attempts'].text, 
                        voice=self.prompts['too_many_attempts'].voice)
            
            return {
                'action': 'transfer',
                'target': 'operator',
                'selection': None,
                'context': context,
                'twiml_response': response
            }
        else:
            # Repeat menu with helpful guidance
            response = VoiceResponse()
            
            if context.attempts == 1:
                response.say(self.prompts['invalid_input'].text, 
                           voice=self.prompts['invalid_input'].voice)
            else:
                response.say("Let me try that again. You can either press a number on your keypad or speak your choice clearly.", 
                           voice='Polly.Joanna')
            
            # Add the menu with enhanced guidance
            gather = self._create_menu_gather(context.current_menu, enhanced=True)
            response.append(gather)
            
            # Fallback to operator
            response.say("If you're still having trouble, please hold and I'll connect you with an operator.", 
                       voice='Polly.Joanna')
            response.redirect('/voice/transfer-to-operator')
            
            return {
                'action': 'retry',
                'target': context.current_menu,
                'selection': None,
                'context': context,
                'twiml_response': response
            }
    
    def _generate_action_response(self, option: Dict, context: CallContext) -> VoiceResponse:
        """Generate appropriate TwiML response for the selected action"""
        response = VoiceResponse()
        
        if option['action'] == 'submenu':
            # Navigate to submenu
            context.previous_menus.append(context.current_menu)
            context.current_menu = option['target']
            
            menu_config = self.menus[option['target']]
            response.say(menu_config['prompt'].text, voice=menu_config['prompt'].voice)
            
            gather = self._create_menu_gather(option['target'])
            response.append(gather)
            
            # Fallback
            response.redirect('/voice/transfer-to-operator')
            
        elif option['action'] == 'repeat':
            # Repeat current menu
            menu_config = self.menus[option['target']]
            response.say(menu_config['prompt'].text, voice=menu_config['prompt'].voice)
            
            gather = self._create_menu_gather(option['target'])
            response.append(gather)
            
        elif option['action'] == 'transfer':
            # Transfer to appropriate department
            response.say(self.prompts['transferring'].text, 
                       voice=self.prompts['transferring'].voice)
            response.redirect(f'/voice/transfer-to-{option["target"]}')
            
        elif option['action'] == 'info':
            # Provide information
            response.redirect(f'/voice/info-{option["target"]}')
        
        return response
    
    def _create_menu_gather(self, menu_name: str, enhanced: bool = False) -> Gather:
        """Create a Gather element for menu input"""
        gather = Gather(
            input='dtmf speech',
            timeout=5 if enhanced else 4,
            speechTimeout='auto',
            speechModel='experimental_conversations',
            enhanced=enhanced,
            action=f'/voice/handle-menu?menu={menu_name}',
            method='POST',
            numDigits=1,
            finishOnKey='#'
        )
        
        if enhanced:
            # More detailed instructions for confused callers
            menu_config = self.menus[menu_name]
            enhanced_text = f"I can understand if you speak clearly or press the number keys. {menu_config['prompt'].text}"
            gather.say(enhanced_text, voice='Polly.Joanna')
        
        return gather
    
    def generate_main_menu_twiml(self, call_sid: str, caller_id: str) -> VoiceResponse:
        """Generate the main menu TwiML response"""
        context = self.get_call_context(call_sid, caller_id)
        response = VoiceResponse()
        
        # Welcome message
        response.say(self.prompts['welcome'].text, voice=self.prompts['welcome'].voice)
        
        # Main menu
        response.say(self.prompts['main_menu'].text, voice=self.prompts['main_menu'].voice)
        
        # Gather input
        gather = self._create_menu_gather('main')
        response.append(gather)
        
        # Default fallback
        response.redirect('/voice/transfer-to-operator')
        
        return response
    
    def generate_hours_info(self) -> VoiceResponse:
        """Generate business hours and location information"""
        response = VoiceResponse()
        
        hours_info = (
            f"{self.company_name} is open Monday through Friday from 8 AM to 6 PM, "
            f"and Saturday from 9 AM to 4 PM. We're closed on Sundays. "
            f"We're located in the Hampton Roads area and serve Norfolk, Virginia Beach, "
            f"Chesapeake, Hampton, Newport News, and surrounding areas. "
            f"For emergency services, we're available 24/7 with an additional service fee. "
            f"You can also visit our website at 757handy.com or follow us on social media."
        )
        
        response.say(hours_info, voice='Polly.Joanna')
        
        # Return to main menu option
        gather = Gather(
            input='dtmf',
            timeout=5,
            action='/voice/handle-menu?menu=main',
            method='POST',
            numDigits=1
        )
        gather.say("Press 1 to return to the main menu, or stay on the line to speak with an operator.", 
                  voice='Polly.Joanna')
        response.append(gather)
        
        response.redirect('/voice/transfer-to-operator')
        
        return response
    
    def get_call_analytics(self) -> Dict[str, Any]:
        """Get analytics on call patterns and menu usage"""
        analytics = {
            'total_calls': len(self.call_contexts),
            'menu_selections': {},
            'completion_rates': {},
            'average_attempts': 0,
            'most_popular_options': []
        }
        
        if not self.call_contexts:
            return analytics
        
        total_attempts = 0
        for context in self.call_contexts.values():
            total_attempts += context.attempts
            
            # Track menu usage
            for menu in [context.current_menu] + context.previous_menus:
                if menu not in analytics['menu_selections']:
                    analytics['menu_selections'][menu] = 0
                analytics['menu_selections'][menu] += 1
        
        analytics['average_attempts'] = total_attempts / len(self.call_contexts)
        
        # Most popular menu selections
        sorted_menus = sorted(analytics['menu_selections'].items(), 
                            key=lambda x: x[1], reverse=True)
        analytics['most_popular_options'] = sorted_menus[:5]
        
        return analytics
    
    def cleanup_old_contexts(self, hours: int = 24):
        """Clean up old call contexts to prevent memory leaks"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        old_contexts = []
        for call_sid, context in self.call_contexts.items():
            # Assuming context has a timestamp (would need to add this)
            # For now, just limit total contexts
            if len(self.call_contexts) > 1000:
                old_contexts.append(call_sid)
        
        for call_sid in old_contexts[:500]:  # Remove oldest half
            del self.call_contexts[call_sid]
        
        logger.info(f"Cleaned up {len(old_contexts)} old call contexts")

if __name__ == "__main__":
    # Test the IVR system
    ivr = VoiceIVRSystem()
    
    # Simulate a call flow
    test_call = "CA1234567890"
    test_caller = "+15551234567"
    
    # Test main menu
    result = ivr.process_input(test_call, test_caller, digits="1", current_menu="main")
    print(f"Main menu selection 1: {result['action']} -> {result['target']}")
    
    # Test speech input
    result = ivr.process_input(test_call, test_caller, speech_result="I need a quote", current_menu="main")
    print(f"Speech 'quote': {result['action']} -> {result['target']}")
    
    # Test invalid input
    result = ivr.process_input(test_call, test_caller, digits="99", current_menu="main")
    print(f"Invalid input: {result['action']}")
    
    # Get analytics
    analytics = ivr.get_call_analytics()
    print(f"Analytics: {analytics}")
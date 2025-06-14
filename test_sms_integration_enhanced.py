#!/usr/bin/env python3
"""
Enhanced SMS Integration Test
Tests the complete SMS system with configuration, NLP, and response generation
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import components
from src.sms_config import SMSConfig, ServiceType, MessagePriority, ResponseTimeType
from src.handyman_sms_engine import HandymanSMSEngine
from src.nlp_enhancements import SMSNLPEngine
from src.llm_client import LLMClient

def setup_logging():
    """Setup comprehensive logging for testing."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f'sms_integration_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        ]
    )
    return logging.getLogger(__name__)

def test_sms_configuration():
    """Test SMS configuration system."""
    print("\n" + "="*60)
    print("TESTING SMS CONFIGURATION SYSTEM")
    print("="*60)
    
    config = SMSConfig()
    
    test_messages = [
        ("Emergency! Pipe burst in basement!", ServiceType.EMERGENCY, MessagePriority.EMERGENCY),
        ("Need plumber for leaky faucet", ServiceType.PLUMBING, MessagePriority.HIGH),
        ("Quote for bathroom remodel please", ServiceType.QUOTE_REQUEST, MessagePriority.NORMAL),
        ("Schedule HVAC maintenance", ServiceType.SCHEDULING, MessagePriority.NORMAL),
        ("Handyman needed for general repairs", ServiceType.GENERAL_HANDYMAN, MessagePriority.NORMAL)
    ]
    
    results = []
    for message, expected_service, expected_priority in test_messages:
        service_type = config.classify_service_type(message)
        priority = config.get_priority_for_service(service_type, message)
        response_config = config.get_response_time_config(service_type)
        template_config = config.get_template_for_service(service_type)
        
        result = {
            'message': message,
            'expected_service': expected_service,
            'actual_service': service_type,
            'expected_priority': expected_priority,
            'actual_priority': priority,
            'response_time': response_config['target_minutes'],
            'template': template_config['primary_template'],
            'should_auto_respond': config.should_auto_respond(service_type, priority)
        }
        
        results.append(result)
        
        print(f"\nMessage: '{message}'")
        print(f"  Service Type: {service_type.value} (expected: {expected_service.value})")
        print(f"  Priority: {priority.value} (expected: {expected_priority.value})")
        print(f"  Response Time: {response_config['target_minutes']} minutes")
        print(f"  Template: {template_config['primary_template']}")
        print(f"  Auto-respond: {config.should_auto_respond(service_type, priority)}")
        
        # Validation
        service_match = "✅" if service_type == expected_service else "❌"
        priority_match = "✅" if priority == expected_priority else "❌"
        print(f"  Validation: Service {service_match} Priority {priority_match}")
    
    return results

async def test_nlp_enhancement():
    """Test SMS NLP enhancements."""
    print("\n" + "="*60)
    print("TESTING SMS NLP ENHANCEMENTS")
    print("="*60)
    
    try:
        nlp_engine = SMSNLPEngine()
    except Exception as e:
        print(f"Failed to initialize NLP engine: {e}")
        return []
    
    test_messages = [
        "emergency! pipe burst rn need help asap!",
        "thx for fixing my sink yesterday 👍 great job",
        "tmrw afternoon appt still good? pls confirm",
        "hvac not working w/ kids at home 😢",
        "quote 4 bathroom remodel w/ tile work pls",
        "yes confirm",
        "STOP",
        "wtf this is taking 2 long! angry customer here 😡"
    ]
    
    results = []
    for message in test_messages:
        try:
            # Test abbreviation expansion
            expanded = nlp_engine.expand_sms_abbreviations(message)
            
            # Full SMS analysis
            nlp_result, service_type, priority = await nlp_engine.analyze_sms(message)
            
            # Get response urgency
            urgency_config = nlp_engine.get_response_urgency(service_type, priority, nlp_result.sentiment)
            
            result = {
                'original': message,
                'expanded': expanded,
                'intent': nlp_result.intent.value,
                'service_type': service_type.value,
                'priority': priority.value,
                'sentiment': nlp_result.sentiment.value,
                'is_urgent': nlp_result.is_urgent,
                'confidence': nlp_result.confidence,
                'keywords': nlp_result.keywords,
                'entities': [e.to_dict() for e in nlp_result.entities],
                'target_response_minutes': urgency_config['target_minutes'],
                'escalate_to_human': urgency_config.get('escalate_to_human', False)
            }
            
            results.append(result)
            
            print(f"\nOriginal: '{message}'")
            print(f"Expanded: '{expanded}'")
            print(f"Intent: {nlp_result.intent.value}")
            print(f"Service: {service_type.value}")
            print(f"Priority: {priority.value}")
            print(f"Sentiment: {nlp_result.sentiment.value}")
            print(f"Urgent: {nlp_result.is_urgent}")
            print(f"Confidence: {nlp_result.confidence:.2f}")
            print(f"Keywords: {', '.join(nlp_result.keywords[:5])}")  # First 5 keywords
            print(f"Response Time: {urgency_config['target_minutes']} minutes")
            print(f"Escalate: {urgency_config.get('escalate_to_human', False)}")
            
        except Exception as e:
            print(f"Error analyzing '{message}': {e}")
            results.append({'error': str(e), 'message': message})
    
    return results

async def test_sms_engine_integration():
    """Test SMS engine with configuration integration."""
    print("\n" + "="*60)
    print("TESTING SMS ENGINE INTEGRATION")
    print("="*60)
    
    try:
        # Initialize without LLM for testing
        sms_engine = HandymanSMSEngine(llm_client=None)
    except Exception as e:
        print(f"Failed to initialize SMS engine: {e}")
        return []
    
    test_scenarios = [
        {
            'phone': '+15551234567',
            'message': 'Emergency! No heat and kids at home!',
            'expected_urgency': 'critical'
        },
        {
            'phone': '+15551234568',
            'message': 'Quote for deck repair pls',
            'expected_urgency': 'medium'
        },
        {
            'phone': '+15551234569',
            'message': 'yes',
            'expected_urgency': 'medium'
        },
        {
            'phone': '+15551234570',
            'message': 'tmrw 2pm electrical appt ok?',
            'expected_urgency': 'medium'
        },
        {
            'phone': '+15551234571',
            'message': 'STOP',
            'expected_urgency': 'low'
        }
    ]
    
    results = []
    for scenario in test_scenarios:
        phone = scenario['phone']
        message = scenario['message']
        expected_urgency = scenario['expected_urgency']
        
        try:
            # Test classification
            classification = sms_engine.classify_sms_type(phone, message)
            
            # Test fallback response generation
            fallback_response = sms_engine._generate_sms_fallback_response(phone, message, classification)
            
            # Test template recommendation
            service_type = classification.get('service_type', ServiceType.GENERAL_HANDYMAN)
            template_config = sms_engine.get_template_recommendation(service_type)
            
            result = {
                'phone': phone,
                'message': message,
                'classification': classification,
                'fallback_response': fallback_response,
                'response_length': len(fallback_response),
                'template_recommendation': template_config,
                'expected_urgency': expected_urgency,
                'actual_urgency': classification.get('estimated_urgency', 'unknown')
            }
            
            results.append(result)
            
            print(f"\nPhone: {phone}")
            print(f"Message: '{message}'")
            print(f"Service Type: {classification.get('service_type', 'N/A')}")
            print(f"Priority: {classification.get('priority', 'N/A')}")
            print(f"Urgency: {classification.get('estimated_urgency', 'N/A')} (expected: {expected_urgency})")
            print(f"Auto-respond: {classification.get('should_auto_respond', False)}")
            print(f"Fallback Response ({len(fallback_response)} chars): '{fallback_response}'")
            print(f"Template: {template_config.get('primary_template', 'N/A')}")
            
            # Validation
            urgency_match = "✅" if classification.get('estimated_urgency') == expected_urgency else "❌"
            length_ok = "✅" if len(fallback_response) <= 160 else "⚠️ "
            print(f"Validation: Urgency {urgency_match} Length {length_ok}")
            
        except Exception as e:
            print(f"Error processing scenario: {e}")
            results.append({'error': str(e), 'scenario': scenario})
    
    return results

async def test_end_to_end_flow():
    """Test complete end-to-end SMS processing flow."""
    print("\n" + "="*60)
    print("TESTING END-TO-END SMS FLOW")
    print("="*60)
    
    try:
        # Initialize components
        config = SMSConfig()
        nlp_engine = SMSNLPEngine()
        sms_engine = HandymanSMSEngine(llm_client=None)
        
        print("✅ All components initialized successfully")
        
    except Exception as e:
        print(f"❌ Component initialization failed: {e}")
        return []
    
    # Real-world scenarios
    scenarios = [
        {
            'name': 'Emergency Plumbing',
            'phone': '+17575551001',
            'message': 'HELP! Burst pipe flooding basement rn!',
            'context': {'time': 'after_hours', 'customer_type': 'new'}
        },
        {
            'name': 'Appointment Confirmation',
            'phone': '+17575551002',
            'message': 'yes confirm tmrw 2pm',
            'context': {'time': 'business_hours', 'customer_type': 'existing'}
        },
        {
            'name': 'Quote Request',
            'phone': '+17575551003',
            'message': 'how much 2 fix kitchen faucet? thx',
            'context': {'time': 'business_hours', 'customer_type': 'new'}
        },
        {
            'name': 'Service Inquiry',
            'phone': '+17575551004',
            'message': 'do u do hvac maintenance? need annual service',
            'context': {'time': 'business_hours', 'customer_type': 'unknown'}
        }
    ]
    
    results = []
    for scenario in scenarios:
        print(f"\n--- {scenario['name']} ---")
        
        try:
            phone = scenario['phone']
            message = scenario['message']
            context = scenario['context']
            
            # Step 1: SMS Configuration Analysis
            service_type = config.classify_service_type(message)
            priority = config.get_priority_for_service(service_type, message)
            should_auto_respond = config.should_auto_respond(service_type, priority)
            
            # Step 2: NLP Analysis
            nlp_result, nlp_service_type, nlp_priority = await nlp_engine.analyze_sms(message, context)
            
            # Step 3: SMS Engine Processing
            classification = sms_engine.classify_sms_type(phone, message)
            fallback_response = sms_engine._generate_sms_fallback_response(phone, message, classification)
            
            # Step 4: Response Time Calculation
            urgency_config = nlp_engine.get_response_urgency(service_type, priority, nlp_result.sentiment)
            
            result = {
                'scenario': scenario['name'],
                'phone': phone,
                'message': message,
                'context': context,
                'config_analysis': {
                    'service_type': service_type.value,
                    'priority': priority.value,
                    'should_auto_respond': should_auto_respond
                },
                'nlp_analysis': {
                    'intent': nlp_result.intent.value,
                    'service_type': nlp_service_type.value,
                    'priority': nlp_priority.value,
                    'sentiment': nlp_result.sentiment.value,
                    'confidence': nlp_result.confidence
                },
                'engine_response': {
                    'classification': classification,
                    'fallback_response': fallback_response,
                    'response_length': len(fallback_response)
                },
                'urgency_config': urgency_config
            }
            
            results.append(result)
            
            # Display results
            print(f"Message: '{message}'")
            print(f"Config: {service_type.value} | {priority.value} | Auto: {should_auto_respond}")
            print(f"NLP: {nlp_result.intent.value} | {nlp_result.sentiment.value} | Conf: {nlp_result.confidence:.2f}")
            print(f"Response ({len(fallback_response)}): '{fallback_response}'")
            print(f"Target Time: {urgency_config['target_minutes']} min | Escalate: {urgency_config.get('escalate_to_human', False)}")
            
            # Consistency check
            config_service_match = service_type == nlp_service_type
            config_priority_match = priority == nlp_priority
            consistency = "✅" if config_service_match and config_priority_match else "⚠️ "
            print(f"Consistency: {consistency} Service: {config_service_match} Priority: {config_priority_match}")
            
        except Exception as e:
            print(f"❌ Error in scenario '{scenario['name']}': {e}")
            results.append({'error': str(e), 'scenario': scenario})
    
    return results

def generate_test_report(all_results: Dict[str, List[Any]]):
    """Generate comprehensive test report."""
    print("\n" + "="*60)
    print("TEST REPORT SUMMARY")
    print("="*60)
    
    total_tests = 0
    passed_tests = 0
    
    for test_name, results in all_results.items():
        print(f"\n{test_name.upper()}:")
        
        if not results:
            print("  ❌ No results (component failure)")
            continue
        
        test_count = len([r for r in results if 'error' not in r])
        error_count = len([r for r in results if 'error' in r])
        
        total_tests += len(results)
        passed_tests += test_count
        
        print(f"  Total: {len(results)} | Passed: {test_count} | Errors: {error_count}")
        
        if error_count > 0:
            print("  Errors encountered:")
            for result in results:
                if 'error' in result:
                    print(f"    - {result['error']}")
    
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    print(f"\nOVERALL SUCCESS RATE: {success_rate:.1f}% ({passed_tests}/{total_tests})")
    
    if success_rate >= 90:
        print("🎉 EXCELLENT: SMS integration is working well!")
    elif success_rate >= 75:
        print("✅ GOOD: SMS integration is functional with minor issues")
    elif success_rate >= 50:
        print("⚠️  FAIR: SMS integration needs improvements")
    else:
        print("❌ POOR: SMS integration has significant issues")

async def main():
    """Run comprehensive SMS integration tests."""
    logger = setup_logging()
    
    print("🚀 Starting Enhanced SMS Integration Tests")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    all_results = {}
    
    try:
        # Test 1: SMS Configuration System
        logger.info("Testing SMS Configuration System")
        all_results['sms_configuration'] = test_sms_configuration()
        
        # Test 2: NLP Enhancements
        logger.info("Testing SMS NLP Enhancements")
        all_results['nlp_enhancement'] = await test_nlp_enhancement()
        
        # Test 3: SMS Engine Integration
        logger.info("Testing SMS Engine Integration")
        all_results['sms_engine'] = await test_sms_engine_integration()
        
        # Test 4: End-to-End Flow
        logger.info("Testing End-to-End Flow")
        all_results['end_to_end'] = await test_end_to_end_flow()
        
        # Generate comprehensive report
        generate_test_report(all_results)
        
    except Exception as e:
        logger.error(f"Test execution failed: {e}", exc_info=True)
        print(f"❌ Test execution failed: {e}")
    
    print(f"\n✅ Testing completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == '__main__':
    asyncio.run(main()) 
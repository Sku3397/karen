#!/usr/bin/env python3
"""
Core SMS Integration Test
Tests the SMS configuration system and handyman SMS engine integration
"""

import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import core components
from src.sms_config import SMSConfig, ServiceType, MessagePriority, ResponseTimeType
from src.handyman_sms_engine import HandymanSMSEngine

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
        ("Handyman needed for general repairs", ServiceType.GENERAL_HANDYMAN, MessagePriority.NORMAL),
        ("Electrical outlet not working", ServiceType.ELECTRICAL, MessagePriority.HIGH),
        ("How much to paint bedroom?", ServiceType.QUOTE_REQUEST, MessagePriority.NORMAL),
        ("yes", ServiceType.GENERAL_HANDYMAN, MessagePriority.NORMAL)
    ]
    
    passed = 0
    total = len(test_messages)
    
    for i, (message, expected_service, expected_priority) in enumerate(test_messages, 1):
        print(f"\nTest {i}/{total}: '{message}'")
        
        try:
            service_type = config.classify_service_type(message)
            priority = config.get_priority_for_service(service_type, message)
            response_config = config.get_response_time_config(service_type)
            template_config = config.get_template_for_service(service_type)
            should_auto_respond = config.should_auto_respond(service_type, priority)
            
            print(f"  Service Type: {service_type.value}")
            print(f"  Priority: {priority.value}")
            print(f"  Response Time: {response_config['target_minutes']} minutes")
            print(f"  Template: {template_config['primary_template']}")
            print(f"  Auto-respond: {should_auto_respond}")
            
            # Validation
            service_match = service_type == expected_service
            priority_match = priority == expected_priority
            
            if service_match and priority_match:
                print(f"  Result: ✅ PASS")
                passed += 1
            else:
                print(f"  Result: ❌ FAIL")
                if not service_match:
                    print(f"    Expected service: {expected_service.value}, got: {service_type.value}")
                if not priority_match:
                    print(f"    Expected priority: {expected_priority.value}, got: {priority.value}")
                    
        except Exception as e:
            print(f"  Result: ❌ ERROR - {e}")
    
    print(f"\nSMS Configuration Test Results: {passed}/{total} passed ({passed/total*100:.1f}%)")
    return passed == total

def test_sms_engine_integration():
    """Test SMS engine with configuration integration."""
    print("\n" + "="*60)
    print("TESTING SMS ENGINE INTEGRATION")
    print("="*60)
    
    try:
        # Initialize without LLM for testing
        sms_engine = HandymanSMSEngine(llm_client=None)
        print("✅ SMS Engine initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize SMS engine: {e}")
        return False
    
    test_scenarios = [
        {
            'name': 'Emergency Plumbing',
            'phone': '+15551234567',
            'message': 'Emergency! No heat and kids at home!',
            'expected_service': ServiceType.EMERGENCY,
            'expected_urgency': 'critical'
        },
        {
            'name': 'Quote Request',
            'phone': '+15551234568',
            'message': 'Quote for deck repair please',
            'expected_service': ServiceType.QUOTE_REQUEST,
            'expected_urgency': 'medium'
        },
        {
            'name': 'Quick Response',
            'phone': '+15551234569',
            'message': 'yes',
            'expected_service': ServiceType.GENERAL_HANDYMAN,
            'expected_urgency': 'medium'
        },
        {
            'name': 'Scheduling',
            'phone': '+15551234570',
            'message': 'tomorrow 2pm electrical appointment ok?',
            'expected_service': ServiceType.ELECTRICAL,
            'expected_urgency': 'high'
        },
        {
            'name': 'Unsubscribe',
            'phone': '+15551234571',
            'message': 'STOP',
            'expected_service': ServiceType.GENERAL_HANDYMAN,
            'expected_urgency': 'low'
        }
    ]
    
    passed = 0
    total = len(test_scenarios)
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\nTest {i}/{total}: {scenario['name']}")
        
        try:
            phone = scenario['phone']
            message = scenario['message']
            
            # Test classification
            classification = sms_engine.classify_sms_type(phone, message)
            
            # Test fallback response generation
            fallback_response = sms_engine._generate_sms_fallback_response(phone, message, classification)
            
            # Test template recommendation
            service_type = classification.get('service_type', ServiceType.GENERAL_HANDYMAN)
            template_config = sms_engine.get_template_recommendation(service_type)
            
            print(f"  Message: '{message}'")
            print(f"  Service Type: {service_type.value}")
            print(f"  Priority: {classification.get('priority', 'N/A')}")
            print(f"  Urgency: {classification.get('estimated_urgency', 'N/A')}")
            print(f"  Auto-respond: {classification.get('should_auto_respond', False)}")
            print(f"  Response ({len(fallback_response)} chars): '{fallback_response}'")
            print(f"  Template: {template_config.get('primary_template', 'N/A')}")
            
            # Validation
            response_valid = len(fallback_response) > 0 and len(fallback_response) <= 160
            has_service_type = 'service_type' in classification
            has_priority = 'priority' in classification
            
            if response_valid and has_service_type and has_priority:
                print(f"  Result: ✅ PASS")
                passed += 1
            else:
                print(f"  Result: ❌ FAIL")
                if not response_valid:
                    print(f"    Invalid response length: {len(fallback_response)}")
                if not has_service_type:
                    print(f"    Missing service type in classification")
                if not has_priority:
                    print(f"    Missing priority in classification")
            
        except Exception as e:
            print(f"  Result: ❌ ERROR - {e}")
    
    print(f"\nSMS Engine Test Results: {passed}/{total} passed ({passed/total*100:.1f}%)")
    return passed == total

def test_integration_flow():
    """Test the complete integration flow between components."""
    print("\n" + "="*60)
    print("TESTING INTEGRATION FLOW")
    print("="*60)
    
    try:
        config = SMSConfig()
        sms_engine = HandymanSMSEngine(llm_client=None)
        print("✅ All components initialized")
    except Exception as e:
        print(f"❌ Component initialization failed: {e}")
        return False
    
    # Test real-world scenarios
    scenarios = [
        {
            'name': 'Emergency with abbreviations',
            'phone': '+17575551001',
            'message': 'help! burst pipe flooding basement asap!',
            'expected_response_time': 5  # Should be immediate
        },
        {
            'name': 'Appointment confirmation',
            'phone': '+17575551002',
            'message': 'yes confirm tomorrow 2pm',
            'expected_quick_response': True
        },
        {
            'name': 'Quote with service details',
            'phone': '+17575551003',
            'message': 'how much to fix kitchen faucet leak?',
            'expected_service': ServiceType.PLUMBING
        },
        {
            'name': 'HVAC emergency',
            'phone': '+17575551004',
            'message': 'no heat in house with baby!',
            'expected_priority': MessagePriority.EMERGENCY
        }
    ]
    
    passed = 0
    total = len(scenarios)
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\nIntegration Test {i}/{total}: {scenario['name']}")
        
        try:
            phone = scenario['phone']
            message = scenario['message']
            
            # Step 1: Configuration analysis
            config_service = config.classify_service_type(message)
            config_priority = config.get_priority_for_service(config_service, message)
            config_response = config.get_response_time_config(config_service)
            
            # Step 2: Engine processing
            engine_classification = sms_engine.classify_sms_type(phone, message)
            engine_response = sms_engine._generate_sms_fallback_response(phone, message, engine_classification)
            
            # Step 3: Consistency check
            engine_service = engine_classification.get('service_type')
            engine_priority = engine_classification.get('priority')
            
            print(f"  Message: '{message}'")
            print(f"  Config Service: {config_service.value}")
            print(f"  Engine Service: {engine_service.value if engine_service else 'N/A'}")
            print(f"  Config Priority: {config_priority.value}")
            print(f"  Engine Priority: {engine_priority.value if engine_priority else 'N/A'}")
            print(f"  Response Time: {config_response['target_minutes']} minutes")
            print(f"  Response: '{engine_response[:50]}{'...' if len(engine_response) > 50 else ''}'")
            
            # Validation
            service_consistent = config_service == engine_service
            priority_consistent = config_priority == engine_priority
            response_valid = len(engine_response) > 0 and len(engine_response) <= 160
            
            # Check scenario-specific expectations
            scenario_valid = True
            if 'expected_response_time' in scenario:
                expected_time = scenario['expected_response_time']
                actual_time = config_response['target_minutes']
                scenario_valid = actual_time <= expected_time
                print(f"  Response Time Check: {actual_time} <= {expected_time} = {scenario_valid}")
            
            if 'expected_quick_response' in scenario:
                is_quick = engine_classification.get('is_quick_response', False)
                scenario_valid = is_quick == scenario['expected_quick_response']
                print(f"  Quick Response Check: {is_quick} = {scenario_valid}")
            
            if 'expected_service' in scenario:
                expected_service = scenario['expected_service']
                scenario_valid = config_service == expected_service
                print(f"  Service Check: {config_service.value} == {expected_service.value} = {scenario_valid}")
            
            if 'expected_priority' in scenario:
                expected_priority = scenario['expected_priority']
                scenario_valid = config_priority == expected_priority
                print(f"  Priority Check: {config_priority.value} == {expected_priority.value} = {scenario_valid}")
            
            if service_consistent and priority_consistent and response_valid and scenario_valid:
                print(f"  Result: ✅ PASS")
                passed += 1
            else:
                print(f"  Result: ❌ FAIL")
                if not service_consistent:
                    print(f"    Service inconsistency")
                if not priority_consistent:
                    print(f"    Priority inconsistency")
                if not response_valid:
                    print(f"    Invalid response")
                if not scenario_valid:
                    print(f"    Scenario expectation not met")
            
        except Exception as e:
            print(f"  Result: ❌ ERROR - {e}")
    
    print(f"\nIntegration Flow Test Results: {passed}/{total} passed ({passed/total*100:.1f}%)")
    return passed == total

def main():
    """Run core SMS integration tests."""
    print("🚀 Starting Core SMS Integration Tests")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all tests
    results = []
    
    print("\n" + "🔧 Testing SMS Configuration System...")
    results.append(test_sms_configuration())
    
    print("\n" + "🔧 Testing SMS Engine Integration...")
    results.append(test_sms_engine_integration())
    
    print("\n" + "🔧 Testing Integration Flow...")
    results.append(test_integration_flow())
    
    # Generate summary
    passed_tests = sum(results)
    total_tests = len(results)
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print("\n" + "="*60)
    print("FINAL TEST SUMMARY")
    print("="*60)
    print(f"Tests Passed: {passed_tests}/{total_tests}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if success_rate == 100:
        print("🎉 EXCELLENT: All SMS integration tests passed!")
        print("   ✅ SMS Configuration System working correctly")
        print("   ✅ SMS Engine integration successful")
        print("   ✅ Component integration flow validated")
    elif success_rate >= 75:
        print("✅ GOOD: Most SMS integration tests passed")
        print("   Some minor issues detected, but system is functional")
    elif success_rate >= 50:
        print("⚠️  FAIR: Half of SMS integration tests passed")
        print("   System needs significant improvements")
    else:
        print("❌ POOR: SMS integration has major issues")
        print("   System requires substantial fixes")
    
    print(f"\n✅ Testing completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return success_rate >= 75

if __name__ == '__main__':
    main() 
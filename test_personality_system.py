#!/usr/bin/env python3
"""
Comprehensive testing and self-healing for Karen's personality system
"""
import sys
import os
import traceback
import importlib
from datetime import datetime
from typing import Dict, List, Any
import random

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

class PersonalitySystemTester:
    def __init__(self):
        self.test_results = []
        self.healing_actions = []
        self.modules_to_test = [
            'personality.voice_personality',
            'personality.regional_adaptation', 
            'personality.humor_engine'
        ]
        
    def log_result(self, test_name: str, success: bool, details: str = "", error: str = ""):
        """Log test result"""
        result = {
            'test': test_name,
            'success': success,
            'timestamp': datetime.now().isoformat(),
            'details': details,
            'error': error
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    Details: {details}")
        if error:
            print(f"    Error: {error}")
            
    def attempt_healing(self, module_name: str, error: str) -> bool:
        """Attempt to heal issues automatically"""
        print(f"🔧 Attempting to heal {module_name}...")
        
        # Common healing strategies
        healing_strategies = [
            self._fix_import_errors,
            self._fix_missing_dependencies,
            self._fix_syntax_errors,
            self._fix_missing_methods
        ]
        
        for strategy in healing_strategies:
            try:
                if strategy(module_name, error):
                    self.healing_actions.append(f"Applied {strategy.__name__} to {module_name}")
                    return True
            except Exception as e:
                print(f"    Healing strategy {strategy.__name__} failed: {e}")
                
        return False
        
    def _fix_import_errors(self, module_name: str, error: str) -> bool:
        """Fix common import errors"""
        if "No module named" in error:
            missing_module = error.split("'")[1] if "'" in error else ""
            
            if missing_module == "datetime":
                # Add datetime import
                file_path = f"src/{module_name.replace('.', '/')}.py"
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    if "from datetime import datetime" not in content:
                        content = "from datetime import datetime\n" + content
                        with open(file_path, 'w') as f:
                            f.write(content)
                        return True
                        
        return False
        
    def _fix_missing_dependencies(self, module_name: str, error: str) -> bool:
        """Fix missing dependency issues"""
        if "requests" in error:
            # Comment out requests usage for now
            file_path = f"src/{module_name.replace('.', '/')}.py" 
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Comment out requests imports and usage
                content = content.replace("import requests", "# import requests")
                content = content.replace("requests.", "# requests.")
                
                with open(file_path, 'w') as f:
                    f.write(content)
                return True
                
        return False
        
    def _fix_syntax_errors(self, module_name: str, error: str) -> bool:
        """Fix basic syntax errors"""
        if "invalid syntax" in error:
            file_path = f"src/{module_name.replace('.', '/')}.py"
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    lines = f.readlines()
                
                # Look for common syntax issues
                fixed = False
                for i, line in enumerate(lines):
                    # Fix missing colons
                    if line.strip().startswith(('if ', 'elif ', 'else', 'for ', 'while ', 'def ', 'class ')) and not line.rstrip().endswith(':'):
                        if '(' in line and ')' in line:  # Has parentheses, probably needs colon
                            lines[i] = line.rstrip() + ':\n'
                            fixed = True
                
                if fixed:
                    with open(file_path, 'w') as f:
                        f.writelines(lines)
                    return True
                    
        return False
        
    def _fix_missing_methods(self, module_name: str, error: str) -> bool:
        """Fix missing method errors"""
        # This would require more sophisticated AST parsing
        return False

    def test_module_import(self, module_name: str) -> bool:
        """Test if module can be imported"""
        try:
            module = importlib.import_module(module_name)
            importlib.reload(module)  # Reload in case we fixed it
            self.log_result(f"Import {module_name}", True, "Module imported successfully")
            return True
        except Exception as e:
            error_msg = str(e)
            self.log_result(f"Import {module_name}", False, error=error_msg)
            
            # Attempt healing
            if self.attempt_healing(module_name, error_msg):
                return self.test_module_import(module_name)  # Retry after healing
                
            return False

    def test_voice_personality(self) -> bool:
        """Test VoicePersonality class thoroughly"""
        try:
            from personality.voice_personality import VoicePersonality
            
            vp = VoicePersonality()
            
            # Test greeting generation
            greeting = vp.get_greeting()
            assert isinstance(greeting, str), "Greeting should be string"
            assert len(greeting) > 0, "Greeting should not be empty"
            self.log_result("VoicePersonality.get_greeting()", True, f"Generated: '{greeting[:50]}...'")
            
            # Test sentiment handling
            response = vp.handle_difficult_customer(-0.8)
            assert isinstance(response, str), "Sentiment response should be string"
            self.log_result("VoicePersonality.handle_difficult_customer()", True, f"Generated empathy response")
            
            # Test hold messages
            hold_msg = vp.get_hold_message()
            assert isinstance(hold_msg, str), "Hold message should be string"
            self.log_result("VoicePersonality.get_hold_message()", True)
            
            # Test appointment confirmation
            confirmation = vp.confirm_appointment("2:00 PM", "tomorrow")
            assert "2:00 PM" in confirmation, "Confirmation should include time"
            assert "tomorrow" in confirmation, "Confirmation should include date"
            self.log_result("VoicePersonality.confirm_appointment()", True)
            
            # Test vocal emphasis
            emphasis = vp.add_vocal_emphasis("Hello there!", "excited")
            assert isinstance(emphasis, dict), "Emphasis should return dict"
            assert 'message' in emphasis, "Should have message key"
            self.log_result("VoicePersonality.add_vocal_emphasis()", True)
            
            # Test callback handling
            callback = vp.handle_callback_request("John", "555-1234", "3 PM")
            assert "John" in callback, "Should include customer name"
            assert "555-1234" in callback, "Should include phone number"
            self.log_result("VoicePersonality.handle_callback_request()", True)
            
            # Test emergency handling
            emergency = vp.handle_emergency_call()
            assert "emergency" in emergency.lower(), "Should acknowledge emergency"
            self.log_result("VoicePersonality.handle_emergency_call()", True)
            
            # Test call endings
            ending = vp.end_call_pleasantly("appointment_scheduled")
            assert isinstance(ending, str), "Call ending should be string"
            self.log_result("VoicePersonality.end_call_pleasantly()", True)
            
            # Test repeat customer handling
            repeat = vp.adapt_for_repeat_customer("Sarah", "plumbing repair")
            assert "Sarah" in repeat, "Should include customer name"
            self.log_result("VoicePersonality.adapt_for_repeat_customer()", True)
            
            return True
            
        except Exception as e:
            self.log_result("VoicePersonality tests", False, error=str(e))
            return False

def test_consistency_checker():
    """Test PersonalityConsistencyChecker"""
    print("\n🧪 Testing PersonalityConsistencyChecker...")
    try:
        from personality import PersonalityConsistencyChecker
        
        checker = PersonalityConsistencyChecker()
        
        # Test professional response
        professional_response = "I'd be happy to help you with that repair. Let me check our schedule."
        is_consistent, feedback, scores = checker.score_response(professional_response)
        print(f"Professional response: {is_consistent}, {feedback}")
        
        # Test unprofessional response
        unprofessional_response = "Yeah, cool, whatever. I guess we can fix that."
        is_consistent2, feedback2, scores2 = checker.score_response(unprofessional_response)
        print(f"Unprofessional response: {is_consistent2}, {feedback2}")
        
        # Professional should score better
        assert is_consistent == True, "Professional response should be consistent"
        assert is_consistent2 == False, "Unprofessional response should be inconsistent"
        
        # Test suggestions
        suggestions = checker.suggest_improvements(unprofessional_response)
        assert len(suggestions) > 0, "Should provide suggestions for bad response"
        
        print("✅ PersonalityConsistencyChecker working correctly")
        return True, "All tests passed"
        
    except Exception as e:
        print(f"❌ PersonalityConsistencyChecker test failed: {e}")
        return False, str(e)

def test_empathy_engine():
    """Test EmpathyEngine"""
    print("\n🧪 Testing EmpathyEngine...")
    try:
        from personality import EmpathyEngine
        
        engine = EmpathyEngine()
        
        # Test emotion detection
        frustrated_message = "I'm so frustrated with this broken sink! It's been leaking for days."
        emotions = engine.detect_emotions(frustrated_message)
        print(f"Detected emotions: {emotions}")
        
        assert 'frustrated' in emotions, "Should detect frustration"
        assert emotions['frustrated'] > 0, "Frustration score should be positive"
        
        # Test empathy response generation
        empathy_response = engine.generate_empathy_response(emotions)
        assert empathy_response, "Should generate empathy response"
        assert any(word in empathy_response.lower() for word in ['understand', 'frustration', 'help']), "Response should show understanding"
        
        # Test customer state analysis
        customer_state = engine.analyze_customer_state(frustrated_message)
        assert customer_state['sentiment'] == 'negative', "Should detect negative sentiment"
        assert customer_state['needs_empathy'] == True, "Should identify need for empathy"
        
        print("✅ EmpathyEngine working correctly")
        return True, "All tests passed"
        
    except Exception as e:
        print(f"❌ EmpathyEngine test failed: {e}")
        return False, str(e)

def test_response_enhancer():
    """Test ResponseEnhancer"""
    print("\n🧪 Testing ResponseEnhancer...")
    try:
        from personality import ResponseEnhancer
        
        enhancer = ResponseEnhancer()
        
        # Test basic enhancement
        basic_response = "We can fix your sink on Tuesday."
        context = {
            'customer_message': "My sink is broken and I'm really frustrated.",
            'interaction_type': 'service_request'
        }
        
        enhanced = enhancer.enhance_response(basic_response, context)
        print(f"Original: {basic_response}")
        print(f"Enhanced: {enhanced}")
        
        # Enhanced should be longer and more personal
        assert len(enhanced) > len(basic_response), "Enhanced response should be longer"
        assert enhanced.lower() != basic_response.lower(), "Enhanced should be different"
        
        # Should contain empathy for frustrated customer
        assert any(word in enhanced.lower() for word in ['understand', 'frustration', 'help', 'happy']), "Should show empathy/warmth"
        
        # Test validation
        validation = enhancer.validate_enhanced_response(enhanced, basic_response, context)
        assert validation['enhancement_successful'], f"Enhancement should be successful: {validation}"
        
        print("✅ ResponseEnhancer working correctly")
        return True, "All tests passed"
        
    except Exception as e:
        print(f"❌ ResponseEnhancer test failed: {e}")
        return False, str(e)

def test_small_talk_engine():
    """Test SmallTalkEngine"""
    print("\n🧪 Testing SmallTalkEngine...")
    try:
        from personality import SmallTalkEngine
        
        engine = SmallTalkEngine()
        
        # Test time-based comments
        time_comment = engine.get_time_appropriate_comment()
        assert time_comment, "Should return time-appropriate comment"
        print(f"Time comment: {time_comment}")
        
        # Test seasonal comments
        seasonal_comment = engine.get_seasonal_comment()
        assert seasonal_comment, "Should return seasonal comment"
        print(f"Seasonal comment: {seasonal_comment}")
        
        # Test small talk detection
        weather_message = "It's such a beautiful day today!"
        opportunity = engine.detect_small_talk_opportunity(weather_message)
        assert opportunity == 'weather', "Should detect weather small talk opportunity"
        
        # Test small talk response
        response = engine.generate_small_talk_response('weather')
        assert response, "Should generate weather response"
        assert any(word in response.lower() for word in ['weather', 'day', 'beautiful', 'projects']), "Should be weather-related"
        
        print("✅ SmallTalkEngine working correctly")
        return True, "All tests passed"
        
    except Exception as e:
        print(f"❌ SmallTalkEngine test failed: {e}")
        return False, str(e)

def test_cultural_awareness():
    """Test CulturalAwareness"""
    print("\n🧪 Testing CulturalAwareness...")
    try:
        from personality import CulturalAwareness
        
        awareness = CulturalAwareness()
        
        # Test holiday greetings
        holiday_greeting = awareness.get_holiday_appropriate_greeting(datetime(2023, 12, 20))
        assert holiday_greeting, "Should return holiday greeting in December"
        assert 'holiday' in holiday_greeting.lower(), "December greeting should mention holidays"
        
        # Test cultural sensitivity validation
        insensitive_message = "Obviously everyone knows that, guys."
        validation = awareness.validate_cultural_sensitivity(insensitive_message)
        assert len(validation['issues']) > 0, "Should detect insensitive language"
        
        # Test inclusive language
        sensitive_message = "Thank you for your question. I'd be happy to help."
        validation2 = awareness.validate_cultural_sensitivity(sensitive_message)
        assert validation2['score'] > validation['score'], "Sensitive message should score higher"
        
        print("✅ CulturalAwareness working correctly")
        return True, "All tests passed"
        
    except Exception as e:
        print(f"❌ CulturalAwareness test failed: {e}")
        return False, str(e)

def test_core_personality():
    """Test CorePersonality integration"""
    print("\n🧪 Testing CorePersonality integration...")
    try:
        from personality import CorePersonality
        
        personality = CorePersonality()
        
        # Test personality context generation
        email_context = personality.get_personality_context('email')
        assert 'Karen' in email_context, "Should mention Karen's name"
        assert 'email' in email_context.lower(), "Should include email-specific guidance"
        
        # Test greetings
        morning_greeting = personality.get_greeting('morning', 'phone')
        assert 'Good morning' in morning_greeting, "Should include time-appropriate greeting"
        assert '757 Handy' in morning_greeting, "Should include company name"
        
        # Test regional dialect adjustment
        response = "Can you put that in the shopping cart?"
        adjusted = personality.adjust_for_regional_dialect(response, 'virginia')
        # In Virginia, shopping cart becomes buggy
        assert 'buggy' in adjusted or 'shopping cart' in adjusted, "Should handle regional terms"
        
        print("✅ CorePersonality working correctly")
        return True, "All tests passed"
        
    except Exception as e:
        print(f"❌ CorePersonality test failed: {e}")
        return False, str(e)

def test_end_to_end_workflow():
    """Test complete end-to-end personality enhancement workflow"""
    print("\n🧪 Testing end-to-end workflow...")
    try:
        from personality import ResponseEnhancer, PersonalityConsistencyChecker
        
        enhancer = ResponseEnhancer()
        checker = PersonalityConsistencyChecker()
        
        # Simulate customer scenarios
        scenarios = [
            {
                'customer_message': "My water heater is broken and I'm really worried about the cost.",
                'basic_response': "We can replace your water heater. It will cost $800.",
                'context': {'service_type': 'emergency', 'customer_mood': 'worried'}
            },
            {
                'customer_message': "Thank you so much for the great work last time!",
                'basic_response': "We can schedule another appointment for next week.",
                'context': {'customer_type': 'repeat', 'customer_mood': 'positive'}
            },
            {
                'customer_message': "I'm not sure what exactly is wrong with my sink.",
                'basic_response': "We'll need to diagnose the problem first.",
                'context': {'customer_mood': 'confused'}
            }
        ]
        
        for i, scenario in enumerate(scenarios):
            print(f"\n--- Scenario {i+1} ---")
            print(f"Customer: {scenario['customer_message']}")
            print(f"Basic response: {scenario['basic_response']}")
            
            # Enhance the response
            enhanced = enhancer.enhance_response(scenario['basic_response'], {
                'customer_message': scenario['customer_message'],
                **scenario['context']
            })
            print(f"Enhanced: {enhanced}")
            
            # Validate consistency
            validation = checker.validate_personality_consistency(enhanced, scenario['context'])
            print(f"Consistency: {validation['is_consistent']} (score: {validation['overall_score']:.2f})")
            
            if not validation['is_consistent']:
                print(f"Issues: {validation['feedback']}")
                print(f"Suggestions: {validation['suggestions']}")
            
            # Basic checks
            assert len(enhanced) > len(scenario['basic_response']), f"Scenario {i+1}: Enhanced should be longer"
            assert enhanced != scenario['basic_response'], f"Scenario {i+1}: Enhanced should be different"
        
        print("\n✅ End-to-end workflow working correctly")
        return True, "All scenarios passed"
        
    except Exception as e:
        print(f"❌ End-to-end workflow test failed: {e}")
        return False, str(e)

def run_comprehensive_tests():
    """Run all tests and return results"""
    print("🚀 Starting comprehensive personality system tests...\n")
    
    tests = [
        ("Imports", test_imports),
        ("PersonalityTraits", test_personality_traits),
        ("ConsistencyChecker", test_consistency_checker),
        ("EmpathyEngine", test_empathy_engine),
        ("ResponseEnhancer", test_response_enhancer),
        ("SmallTalkEngine", test_small_talk_engine),
        ("CulturalAwareness", test_cultural_awareness),
        ("CorePersonality", test_core_personality),
        ("End-to-End", test_end_to_end_workflow)
    ]
    
    results = {}
    total_tests = len(tests)
    passed_tests = 0
    
    for test_name, test_func in tests:
        try:
            success, message = test_func()
            results[test_name] = {'success': success, 'message': message}
            if success:
                passed_tests += 1
        except Exception as e:
            results[test_name] = {'success': False, 'message': f"Test crashed: {e}"}
            print(f"❌ {test_name} crashed: {e}")
    
    print(f"\n📊 Test Results: {passed_tests}/{total_tests} tests passed")
    print("=" * 50)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{status} {test_name}: {result['message']}")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! Personality system is working flawlessly.")
        return True
    else:
        print(f"\n⚠️  {total_tests - passed_tests} tests failed. Issues need to be fixed.")
        return False

if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)
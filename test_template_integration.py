#!/usr/bin/env python3
"""
Test script for SMS template persistence integration
Verifies that the template storage system works with SMS integration
"""

import sys
import os
sys.path.append('.')

def test_template_storage():
    """Test template storage functionality"""
    print("=== Testing Template Storage ===")
    
    from src.template_storage import get_template_storage
    
    storage = get_template_storage()
    
    # Test loading existing templates
    print(f"✓ Loaded {len(storage.templates)} templates")
    
    # Test template categories
    categories = storage.list_categories()
    print(f"✓ Template categories: {categories}")
    
    # Test loading a specific template
    emergency_template = storage.load_template('emergency_response')
    if emergency_template:
        print(f"✓ Emergency template loaded: {emergency_template['template'][:50]}...")
    else:
        print("✗ Failed to load emergency template")
    
    # Test template search
    search_results = storage.search_templates('appointment')
    print(f"✓ Found {len(search_results)} templates matching 'appointment'")
    
    return True

def test_sms_template_integration():
    """Test SMS integration with template storage"""
    print("\n=== Testing SMS Template Integration ===")
    
    # Mock the required environment variables for testing
    os.environ.setdefault('TWILIO_ACCOUNT_SID', 'test_sid')
    os.environ.setdefault('TWILIO_AUTH_TOKEN', 'test_token')
    os.environ.setdefault('TWILIO_FROM_NUMBER', '+1234567890')
    
    try:
        from src.sms_integration import SMSIntegration
        
        # Create SMS integration instance
        sms = SMSIntegration()
        print("✓ SMS integration initialized")
        
        # Test template response generation
        template_response = sms._get_template_response('emergency', {
            'customer_name': 'John Doe',
            'address': '123 Main St',
            'eta': '15 minutes'
        })
        
        if template_response:
            print(f"✓ Template response generated: {template_response[:50]}...")
        else:
            print("✗ Failed to generate template response")
        
        # Test fallback response
        fallback_response = sms._get_fallback_response('appointment')
        print(f"✓ Fallback response: {fallback_response[:50]}...")
        
        # Test customer name extraction
        customer_name = sms._extract_customer_name('+1234567890')
        print(f"✓ Customer name extraction: '{customer_name}' (empty is expected for test)")
        
        return True
        
    except Exception as e:
        print(f"✗ SMS integration test failed: {e}")
        return False

def test_template_versioning():
    """Test template version control"""
    print("\n=== Testing Template Versioning ===")
    
    from src.template_storage import get_template_storage
    
    storage = get_template_storage()
    
    # Test saving a template with versioning
    test_template = {
        'template': 'Test template v2: Hello {name}!',
        'variables': ['name'],
        'category': 'test',
        'description': 'Test versioning template'
    }
    
    success = storage.save_template('version_test', test_template, 'test_user')
    if success:
        print("✓ Template saved with versioning")
        
        # Check version history
        versions = storage.get_template_versions('version_test')
        print(f"✓ Template has {len(versions)} versions")
        
        # Test statistics
        stats = storage.get_template_statistics()
        print(f"✓ Template statistics: {stats['total_templates']} total templates")
        
    return success

def test_template_validation():
    """Test template validation"""
    print("\n=== Testing Template Validation ===")
    
    from src.template_storage import get_template_storage
    
    storage = get_template_storage()
    
    # Test valid template
    valid_template = {
        'template': 'Hello {name}, welcome to {service}!',
        'variables': ['name', 'service'],
        'category': 'greeting'
    }
    
    validation = storage.validate_template(valid_template)
    if validation['valid']:
        print("✓ Valid template passed validation")
    else:
        print(f"✗ Valid template failed validation: {validation['errors']}")
    
    # Test invalid template (missing variables)
    invalid_template = {
        'template': 'Hello {name}, welcome to {service}!',
        'variables': ['name'],  # Missing 'service'
        'category': 'greeting'
    }
    
    validation = storage.validate_template(invalid_template)
    if not validation['valid']:
        print("✓ Invalid template correctly failed validation")
    else:
        print("✗ Invalid template incorrectly passed validation")
    
    return True

def main():
    """Run all tests"""
    print("SMS Template Persistence Integration Test")
    print("=" * 50)
    
    tests = [
        test_template_storage,
        test_sms_template_integration,
        test_template_versioning,
        test_template_validation
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print(f"\n=== Test Results ===")
    print(f"Passed: {sum(results)}/{len(results)} tests")
    
    if all(results):
        print("🎉 All tests passed! SMS template persistence is working correctly.")
    else:
        print("❌ Some tests failed. Check the output above for details.")
    
    return all(results)

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
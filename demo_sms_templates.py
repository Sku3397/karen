#!/usr/bin/env python3
"""
SMS Template System Demo
Demonstrates the complete SMS template persistence system
"""

import sys
sys.path.append('.')

from src.template_storage import get_template_storage

def demo_template_storage():
    """Demonstrate template storage capabilities"""
    print("🏪 SMS Template Storage System Demo")
    print("=" * 50)
    
    # Get template storage instance
    storage = get_template_storage()
    
    print(f"\n📊 Template Statistics:")
    stats = storage.get_template_statistics()
    print(f"   Total templates: {stats['total_templates']}")
    print(f"   Categories: {', '.join(storage.list_categories())}")
    print(f"   Average variables per template: {stats['average_variables']:.1f}")
    
    # Show templates by category
    print(f"\n📁 Templates by Category:")
    for category in storage.list_categories():
        templates = [name for name, template in storage.templates.items() 
                    if template.get('category') == category]
        print(f"   {category}: {len(templates)} templates")
        for template_name in templates[:2]:  # Show first 2 in each category
            template = storage.load_template(template_name)
            if template:
                print(f"     • {template_name}: {template['template'][:60]}...")
    
    return storage

def demo_template_usage(storage):
    """Demonstrate template usage"""
    print(f"\n📝 Template Usage Examples:")
    
    # Example 1: Emergency response
    print(f"\n🚨 Emergency Response:")
    emergency_template = storage.load_template('emergency_response')
    if emergency_template:
        # Fill template with variables
        message = emergency_template['template']
        variables = {
            'customer_name': 'John Smith',
            'issue_type': 'burst pipe',
            'eta': '20 minutes'
        }
        
        for var, value in variables.items():
            message = message.replace(f'{{{var}}}', value)
        
        print(f"   Template: {emergency_template['template']}")
        print(f"   Variables: {variables}")
        print(f"   Result: {message}")
    
    # Example 2: Appointment confirmation  
    print(f"\n📅 Appointment Confirmation:")
    appointment_template = storage.load_template('appointment_confirmation')
    if appointment_template:
        variables = {
            'customer_name': 'Sarah Johnson',
            'service_type': 'plumbing repair',
            'date': 'June 5th',
            'time': '2:00 PM'
        }
        
        message = appointment_template['template']
        for var, value in variables.items():
            message = message.replace(f'{{{var}}}', value)
        
        print(f"   Result: {message}")
    
    # Example 3: Using fallback
    print(f"\n🛡️ Fallback Example:")
    template = storage.load_template('emergency_response')
    if template and 'fallback' in template:
        print(f"   Fallback: {template['fallback']}")

def demo_template_management(storage):
    """Demonstrate template management"""
    print(f"\n🔧 Template Management:")
    
    # Create a new template
    new_template = {
        'template': 'Hi {customer_name}! Your {service_type} quote is ready. Total: ${amount}. Valid for 30 days. Book now?',
        'variables': ['customer_name', 'service_type', 'amount'],
        'category': 'sales',
        'description': 'Quote delivery template with pricing',
        'fallback': 'Your quote is ready! Contact us to review the details.'
    }
    
    success = storage.save_template('quote_delivery', new_template, 'demo_user')
    if success:
        print(f"   ✓ Created new template: quote_delivery")
        
        # Load and test the new template
        loaded = storage.load_template('quote_delivery')
        if loaded:
            test_variables = {
                'customer_name': 'Mike Wilson',
                'service_type': 'bathroom renovation',
                'amount': '2,500'
            }
            
            message = loaded['template']
            for var, value in test_variables.items():
                message = message.replace(f'{{{var}}}', value)
            
            print(f"   Test result: {message}")
    
    # Search templates
    print(f"\n🔍 Template Search:")
    search_results = storage.search_templates('quote')
    print(f"   Found {len(search_results)} templates matching 'quote':")
    for result in search_results:
        print(f"     • {result['name']} (relevance: {result['relevance_score']})")

def demo_template_validation(storage):
    """Demonstrate template validation"""
    print(f"\n✅ Template Validation:")
    
    # Valid template
    valid_template = {
        'template': 'Hello {name}, your appointment is at {time}.',
        'variables': ['name', 'time'],
        'category': 'scheduling'
    }
    
    validation = storage.validate_template(valid_template)
    print(f"   Valid template check: {'✓ Passed' if validation['valid'] else '✗ Failed'}")
    
    # Invalid template (missing variable declaration)
    invalid_template = {
        'template': 'Hello {name}, your appointment is at {time}.',
        'variables': ['name'],  # Missing 'time'
        'category': 'scheduling'
    }
    
    validation = storage.validate_template(invalid_template)
    print(f"   Invalid template check: {'✓ Correctly failed' if not validation['valid'] else '✗ Incorrectly passed'}")
    if not validation['valid']:
        print(f"     Errors: {validation['errors']}")

def main():
    """Run the complete demo"""
    try:
        # Core functionality
        storage = demo_template_storage()
        
        # Usage examples
        demo_template_usage(storage)
        
        # Management features
        demo_template_management(storage)
        
        # Validation
        demo_template_validation(storage)
        
        print(f"\n🎉 Demo completed successfully!")
        print(f"💡 The SMS template system is ready for production use.")
        print(f"🔗 Integration with SMS sending is available via SMSIntegration.send_template_sms()")
        
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
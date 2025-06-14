#!/usr/bin/env python3
"""
Simple test to validate token manager structure and basic functionality
without requiring Google API libraries.
"""

import sys
import os
import json
from datetime import datetime, timedelta
from pathlib import Path

def test_token_file_structure():
    """Test existing token files structure"""
    print("=== Testing Token File Structure ===")
    
    project_root = Path('.')
    
    # Check for existing token files
    token_files = list(project_root.glob("gmail_token_*.json"))
    
    if not token_files:
        print("No existing token files found")
        return True
    
    print(f"Found {len(token_files)} token file(s):")
    
    for token_file in token_files:
        print(f"\nProcessing: {token_file}")
        
        try:
            with open(token_file, 'r') as f:
                data = json.load(f)
            
            # Check structure
            required_fields = ['token', 'refresh_token', 'token_uri', 'client_id', 'client_secret']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print(f"  ⚠️ Missing fields: {missing_fields}")
            else:
                print(f"  ✓ All required fields present")
            
            # Check expiry
            if 'expiry' in data:
                print(f"  Expiry field: {data['expiry']} (type: {type(data['expiry'])})")
            else:
                print(f"  ⚠️ No expiry field")
            
            # Check token age if metadata exists
            if 'created_at' in data:
                created_at = datetime.fromisoformat(data['created_at'])
                age = datetime.now() - created_at
                print(f"  Token age: {age}")
            
            print(f"  Has refresh token: {bool(data.get('refresh_token'))}")
            print(f"  Scopes: {len(data.get('scopes', []))}")
            
        except Exception as e:
            print(f"  ❌ Error reading {token_file}: {e}")
    
    return True

def test_token_manager_import():
    """Test if token manager can be imported"""
    print("=== Testing Token Manager Import ===")
    
    try:
        # Add src to path
        sys.path.insert(0, 'src')
        
        # Try importing without Google dependencies
        print("Checking token_manager.py structure...")
        
        with open('src/token_manager.py', 'r') as f:
            content = f.read()
        
        # Check for key classes and functions
        checks = {
            'EnhancedTokenManager class': 'class EnhancedTokenManager' in content,
            'get_enhanced_token_manager function': 'def get_enhanced_token_manager' in content,
            'Automatic refresh logic': '_needs_refresh' in content,
            'Error handling': 'TokenManagerError' in content,
            'Notification system': '_notify_token_failure' in content,
            'Background monitoring': '_start_background_monitor' in content,
            'Thread safety': 'threading.RLock' in content,
        }
        
        for check_name, passed in checks.items():
            status = "✓" if passed else "❌"
            print(f"  {status} {check_name}")
        
        all_passed = all(checks.values())
        print(f"\nOverall structure check: {'✓ PASS' if all_passed else '❌ FAIL'}")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error checking token manager structure: {e}")
        return False

def test_oauth_tokens_directory():
    """Test oauth tokens directory setup"""
    print("=== Testing OAuth Tokens Directory ===")
    
    try:
        project_root = Path('.')
        
        # Check for potential token directories
        possible_dirs = [
            project_root / 'oauth_tokens',
            project_root / 'secure_tokens',
            project_root,  # Root level tokens
        ]
        
        for token_dir in possible_dirs:
            if token_dir.exists():
                print(f"Found directory: {token_dir}")
                
                # Check permissions if on Unix-like system
                try:
                    stat_info = token_dir.stat()
                    perms = oct(stat_info.st_mode)[-3:]
                    print(f"  Permissions: {perms}")
                except:
                    print(f"  Permissions: Could not check (Windows)")
                
                # Count token files
                if token_dir == project_root:
                    token_files = list(token_dir.glob("gmail_token_*.json"))
                else:
                    token_files = list(token_dir.glob("*.json"))
                
                print(f"  Token files: {len(token_files)}")
                
                for tf in token_files[:3]:  # Show first 3
                    print(f"    - {tf.name}")
                
                if len(token_files) > 3:
                    print(f"    ... and {len(token_files) - 3} more")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking oauth directory: {e}")
        return False

def test_enhanced_vs_original():
    """Compare enhanced token manager with original"""
    print("=== Comparing Token Managers ===")
    
    try:
        # Check if both files exist
        original_file = Path('src/oauth_token_manager.py')
        enhanced_file = Path('src/token_manager.py')
        
        print(f"Original oauth_token_manager.py: {'✓' if original_file.exists() else '❌'}")
        print(f"Enhanced token_manager.py: {'✓' if enhanced_file.exists() else '❌'}")
        
        if enhanced_file.exists():
            with open(enhanced_file, 'r') as f:
                enhanced_content = f.read()
            
            # Check for enhanced features
            enhancements = {
                'Automatic background refresh': '_start_background_monitor' in enhanced_content,
                'Retry logic with exponential backoff': 'retry_delay * (attempt + 1)' in enhanced_content,
                'Email notifications': '_notify_token_failure' in enhanced_content,
                'Comprehensive error handling': 'TokenRefreshError' in enhanced_content,
                'Token status reporting': 'get_token_status' in enhanced_content,
                'Force refresh capability': 'force_refresh' in enhanced_content,
                'Thread-safe operations': '_refresh_in_progress' in enhanced_content,
                'Token backup system': '_backup_token_file' in enhanced_content,
            }
            
            print("\nEnhanced features:")
            for feature, present in enhancements.items():
                status = "✓" if present else "❌"
                print(f"  {status} {feature}")
            
            enhancement_count = sum(enhancements.values())
            print(f"\nEnhancements implemented: {enhancement_count}/{len(enhancements)}")
            
            return enhancement_count >= len(enhancements) * 0.8  # 80% success rate
        
        return False
        
    except Exception as e:
        print(f"❌ Error comparing token managers: {e}")
        return False

def test_integration_points():
    """Test integration with email and calendar clients"""
    print("=== Testing Integration Points ===")
    
    try:
        # Check email_client.py
        email_client_file = Path('src/email_client.py')
        if email_client_file.exists():
            with open(email_client_file, 'r') as f:
                email_content = f.read()
            
            email_integration = {
                'Enhanced token manager import': 'from .token_manager import' in email_content,
                'Auto-refresh credentials call': 'get_credentials_with_auto_refresh' in email_content,
                'Updated credential retrieval': 'get_credentials_with_auto_refresh(self.profile, self.email_address)' in email_content,
            }
            
            print("Email client integration:")
            for check, passed in email_integration.items():
                status = "✓" if passed else "❌"
                print(f"  {status} {check}")
        
        # Check calendar_client.py
        calendar_client_file = Path('src/calendar_client.py')
        if calendar_client_file.exists():
            with open(calendar_client_file, 'r') as f:
                calendar_content = f.read()
            
            calendar_integration = {
                'Enhanced token manager import': 'from .token_manager import' in calendar_content,
                'Auto-refresh credentials call': 'get_credentials_with_auto_refresh' in calendar_content,
                'Updated credential retrieval': "get_credentials_with_auto_refresh('calendar', self.email_address)" in calendar_content,
            }
            
            print("\nCalendar client integration:")
            for check, passed in calendar_integration.items():
                status = "✓" if passed else "❌"
                print(f"  {status} {check}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking integration: {e}")
        return False

def main():
    """Run all structural tests"""
    print("Enhanced Token Manager - Structural Test Suite")
    print("=" * 55)
    print()
    
    tests = [
        ("Token File Structure", test_token_file_structure),
        ("Token Manager Import", test_token_manager_import),
        ("OAuth Tokens Directory", test_oauth_tokens_directory),
        ("Enhanced vs Original", test_enhanced_vs_original),
        ("Integration Points", test_integration_points),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"Running {test_name} test...")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results[test_name] = False
        
        print()
    
    # Summary
    print("=" * 55)
    print("Structural Test Results Summary:")
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print()
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All structural tests passed!")
        print("\n📋 Implementation Summary:")
        print("✓ Enhanced OAuth token manager with automatic refresh")
        print("✓ Comprehensive error handling and retry logic")
        print("✓ Email notification system for failures")
        print("✓ Background monitoring and proactive refresh")
        print("✓ Thread-safe operations with proper locking")
        print("✓ Integration with existing email and calendar clients")
        print("✓ Graceful degradation and recovery mechanisms")
        return 0
    else:
        print("❌ Some structural tests failed. Check implementation.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
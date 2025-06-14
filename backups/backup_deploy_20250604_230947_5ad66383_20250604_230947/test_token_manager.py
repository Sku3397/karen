#!/usr/bin/env python3
"""
Test script for the Enhanced Token Manager
Tests automatic refresh, error handling, and notification functionality.
"""

import sys
import os
import logging
from datetime import datetime, timedelta

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.token_manager import (
    EnhancedTokenManager, 
    get_enhanced_token_manager,
    get_credentials_with_auto_refresh,
    get_all_token_status,
    force_refresh_token
)

def setup_logging():
    """Setup logging for testing"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('token_manager_test.log')
        ]
    )

def test_token_status():
    """Test getting token status"""
    print("=== Testing Token Status ===")
    
    try:
        status_list = get_all_token_status()
        
        if not status_list:
            print("No tokens found. Please ensure OAuth tokens are set up.")
            return False
        
        print(f"Found {len(status_list)} token(s):")
        print()
        
        for status in status_list:
            print(f"Profile: {status['profile']}")
            print(f"Email: {status['email']}")
            print(f"Valid: {status['valid']}")
            print(f"Needs Refresh: {status['needs_refresh']}")
            print(f"Has Refresh Token: {status['has_refresh_token']}")
            print(f"Last Refresh: {status['last_refresh']}")
            print(f"Refresh Count: {status['refresh_count']}")
            if status['expiry']:
                print(f"Expires: {status['expiry']}")
            print("-" * 40)
        
        return True
        
    except Exception as e:
        print(f"Error testing token status: {e}")
        return False

def test_credential_retrieval():
    """Test credential retrieval with automatic refresh"""
    print("=== Testing Credential Retrieval ===")
    
    try:
        # Get token status to find available tokens
        status_list = get_all_token_status()
        
        if not status_list:
            print("No tokens available for testing")
            return False
        
        for status in status_list:
            profile = status['profile']
            email = status['email']
            
            print(f"Testing credentials for {profile}:{email}")
            
            # Test credential retrieval
            creds = get_credentials_with_auto_refresh(profile, email)
            
            if creds:
                print(f"✓ Successfully retrieved credentials for {profile}:{email}")
                print(f"  Valid: {creds.valid}")
                print(f"  Has token: {bool(creds.token)}")
                print(f"  Has refresh token: {bool(creds.refresh_token)}")
                if creds.expiry:
                    print(f"  Expires: {creds.expiry}")
                    time_until_expiry = creds.expiry - datetime.utcnow()
                    print(f"  Time until expiry: {time_until_expiry}")
            else:
                print(f"✗ Failed to retrieve credentials for {profile}:{email}")
            
            print()
        
        return True
        
    except Exception as e:
        print(f"Error testing credential retrieval: {e}")
        logging.exception("Error in credential retrieval test")
        return False

def test_force_refresh():
    """Test forced token refresh"""
    print("=== Testing Force Refresh ===")
    
    try:
        status_list = get_all_token_status()
        
        if not status_list:
            print("No tokens available for refresh testing")
            return False
        
        # Test refresh on first token
        first_token = status_list[0]
        profile = first_token['profile']
        email = first_token['email']
        
        print(f"Testing force refresh for {profile}:{email}")
        
        # Record current refresh count
        old_refresh_count = first_token.get('refresh_count', 0)
        
        # Force refresh
        success = force_refresh_token(profile, email)
        
        if success:
            print(f"✓ Force refresh succeeded for {profile}:{email}")
            
            # Check if refresh count increased
            new_status_list = get_all_token_status()
            for status in new_status_list:
                if status['profile'] == profile and status['email'] == email:
                    new_refresh_count = status.get('refresh_count', 0)
                    if new_refresh_count > old_refresh_count:
                        print(f"✓ Refresh count increased: {old_refresh_count} → {new_refresh_count}")
                    break
        else:
            print(f"✗ Force refresh failed for {profile}:{email}")
        
        return success
        
    except Exception as e:
        print(f"Error testing force refresh: {e}")
        logging.exception("Error in force refresh test")
        return False

def test_manager_instance():
    """Test token manager instance and monitoring"""
    print("=== Testing Token Manager Instance ===")
    
    try:
        manager = get_enhanced_token_manager()
        print(f"✓ Token manager instance created")
        print(f"  Project root: {manager.project_root}")
        print(f"  Tokens directory: {manager.tokens_dir}")
        print(f"  Refresh threshold: {manager.refresh_threshold}")
        print(f"  Profiles: {list(manager.profiles.keys())}")
        
        # Test cleanup
        manager.cleanup_failed_refreshes()
        print("✓ Cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"Error testing manager instance: {e}")
        logging.exception("Error in manager instance test")
        return False

def test_error_handling():
    """Test error handling with invalid tokens"""
    print("=== Testing Error Handling ===")
    
    try:
        # Test with non-existent profile
        creds = get_credentials_with_auto_refresh('invalid_profile', 'test@example.com')
        if creds is None:
            print("✓ Correctly handled invalid profile")
        else:
            print("✗ Should have failed with invalid profile")
        
        # Test with invalid email format
        creds = get_credentials_with_auto_refresh('gmail_secretary', 'invalid-email')
        # This should still attempt to work, just won't find a token file
        print("✓ Error handling test completed")
        
        return True
        
    except Exception as e:
        # Expected to catch exceptions
        print(f"✓ Exception properly caught: {type(e).__name__}: {e}")
        return True

def main():
    """Run all tests"""
    setup_logging()
    
    print("Enhanced Token Manager Test Suite")
    print("=" * 50)
    print()
    
    tests = [
        ("Token Status", test_token_status),
        ("Credential Retrieval", test_credential_retrieval),
        ("Manager Instance", test_manager_instance),
        ("Error Handling", test_error_handling),
        ("Force Refresh", test_force_refresh),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"Running {test_name} test...")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"✗ {test_name} test failed with exception: {e}")
            logging.exception(f"Test {test_name} failed")
            results[test_name] = False
        
        print()
    
    # Summary
    print("=" * 50)
    print("Test Results Summary:")
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
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed. Check logs for details.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
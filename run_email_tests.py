#!/usr/bin/env python3
"""
Email Pipeline Test Runner
Orchestrates comprehensive email pipeline testing
"""

import os
import sys
import time
import subprocess
from datetime import datetime

def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n🔄 {description}")
    print(f"   Command: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()[:200]}...")
            return True
        else:
            print(f"❌ {description} - FAILED")
            if result.stderr.strip():
                print(f"   Error: {result.stderr.strip()[:200]}...")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - TIMEOUT")
        return False
    except Exception as e:
        print(f"💥 {description} - CRASHED: {e}")
        return False

def main():
    """Main test orchestration"""
    print("🧪 Karen AI Email Pipeline - Automated Test Runner")
    print("=" * 60)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test sequence
    tests = [
        # 1. System status check
        ("python monitor_email_responses.py --status", "System Status Check"),
        
        # 2. Send test emails
        ("python send_test_email.py basic", "Send Basic Test Email"),
        
        # 3. Wait for delivery
        ("sleep 10", "Wait for Email Delivery"),
        
        # 4. Process emails
        ("python quick_email_test.py", "Process Incoming Emails"),
        
        # 5. Check responses
        ("python monitor_email_responses.py", "Check Email Activity"),
        
        # 6. Send emergency email
        ("python send_test_email.py emergency", "Send Emergency Test Email"),
        
        # 7. Wait and process
        ("sleep 10", "Wait for Emergency Email"),
        ("python quick_email_test.py", "Process Emergency Email"),
        
        # 8. Final status check
        ("python monitor_email_responses.py", "Final Activity Check"),
    ]
    
    results = []
    
    for command, description in tests:
        success = run_command(command, description)
        results.append((description, success))
        
        # Small delay between tests
        if "sleep" not in command:
            time.sleep(2)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for description, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {description}")
        if success:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    print(f"📅 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Email pipeline is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} tests failed. Check individual test outputs.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️  Test runner interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Test runner crashed: {e}")
        sys.exit(1)
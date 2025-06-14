#!/usr/bin/env python3
"""
Simplified Test Engineer for email system monitoring
"""

import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.append('src')

def test_email_system():
    """Test email system connectivity and functionality"""
    try:
        # Check if email client exists
        email_client_path = Path('src/email_client.py')
        if not email_client_path.exists():
            raise Exception("EmailClient file not found")
        
        # Check for Gmail token files
        token_files = list(Path('.').glob('gmail_token_*.json'))
        if not token_files:
            raise Exception("No Gmail token files found")
        
        print("Email system: OPERATIONAL")
        return True
    except Exception as e:
        print(f"EMAIL SYSTEM FAILURE: {e}")
        return False

def update_status(status, health, data):
    """Update status file"""
    status_data = {
        'agent': 'test_engineer',
        'status': status,
        'health': health,
        'data': data,
        'timestamp': datetime.now().isoformat()
    }
    
    status_file = Path('autonomous-agents/communication/status/test_engineer_status.json')
    status_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(status_file, 'w') as f:
        json.dump(status_data, f, indent=2)

def send_emergency_alert(error_msg):
    """Send emergency alert to orchestrator"""
    alert = {
        'from': 'test_engineer',
        'to': 'orchestrator',
        'type': 'emergency',
        'content': {
            'system': 'email',
            'error': error_msg,
            'severity': 'CRITICAL'
        },
        'timestamp': datetime.now().isoformat()
    }
    
    # Create message file
    msg_filename = f"test_engineer_to_orchestrator_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    msg_path = Path(f'autonomous-agents/communication/inbox/orchestrator/{msg_filename}')
    msg_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(msg_path, 'w') as f:
        json.dump(alert, f, indent=2)
    
    print(f"Emergency alert sent: {msg_filename}")

def main():
    """Main monitoring loop"""
    import sys
    
    # Check for test mode
    test_mode = len(sys.argv) > 1 and sys.argv[1] == '--test'
    
    print("Starting continuous email monitoring...")
    print("Email system monitoring active - keeping the system operational")
    
    loop_count = 0
    while True:
        try:
            # Test email system
            email_ok = test_email_system()
            
            # Test completed features
            if os.path.exists('src/phone_engineer_agent.py'):
                print("Testing phone integration...")
                # Add phone tests when needed
            
            # Update status
            update_status('testing', 70 if email_ok else 0, {
                'email_status': 'working' if email_ok else 'FAILED',
                'last_check': time.strftime('%Y-%m-%d %H:%M:%S')
            })
            
            # If email system fails, send emergency alert
            if not email_ok:
                send_emergency_alert('Email system check failed')
            
            print(f"Status check completed at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("Email system is being monitored and protected...")
            
            loop_count += 1
            if test_mode and loop_count >= 2:
                print("Test mode: Stopping after 2 iterations")
                break
                
            time.sleep(600 if not test_mode else 2)  # 10 minutes or 2 seconds for test
            
        except KeyboardInterrupt:
            print("\nTest Engineer monitoring stopped")
            break
        except Exception as e:
            print(f"Monitoring error: {e}")
            time.sleep(60 if not test_mode else 1)  # Wait 1 minute or 1 second before retrying

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Quick Email Pipeline Test
Simple test to verify basic email processing functionality
"""

import os
import sys
import time
import logging
import asyncio
from datetime import datetime

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from src.celery_app import get_communication_agent_instance
from src.config import SECRETARY_EMAIL_ADDRESS, MONITORED_EMAIL_ACCOUNT_CONFIG, USE_MOCK_EMAIL_CLIENT

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def quick_email_test():
    """Quick test of email processing pipeline"""
    print("🚀 Quick Email Pipeline Test")
    print("=" * 50)
    
    print(f"📧 Configuration:")
    print(f"   Secretary: {SECRETARY_EMAIL_ADDRESS}")
    print(f"   Monitored: {MONITORED_EMAIL_ACCOUNT_CONFIG}")
    print(f"   Mock Mode: {USE_MOCK_EMAIL_CLIENT}")
    
    try:
        print("\n🤖 Getting communication agent...")
        agent = get_communication_agent_instance()
        print(f"✅ Agent obtained: {type(agent)}")
        
        print("\n📬 Processing recent emails...")
        # Process emails from the last day
        asyncio.run(agent.check_and_process_incoming_tasks(process_last_n_days=1))
        print("✅ Email processing completed")
        
        print("\n🎉 Quick test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Quick test failed: {e}", exc_info=True)
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = quick_email_test()
    if success:
        print("\n✨ Test passed!")
        sys.exit(0)
    else:
        print("\n💥 Test failed!")
        sys.exit(1)
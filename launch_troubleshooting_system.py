#!/usr/bin/env python3
"""
Launch script for the Integrated Troubleshooting System

This script provides a simple entry point to start the collaborative
troubleshooting system for Karen AI's multi-agent MCP development.
"""

import sys
import signal
import logging
from pathlib import Path

# Add the workspace to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from integrated_troubleshooting_launcher import IntegratedTroubleshootingSystem

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info("Received shutdown signal, stopping troubleshooting system...")
    global troubleshooting_system
    if troubleshooting_system:
        troubleshooting_system.stop()
    sys.exit(0)

def main():
    """Main entry point"""
    global troubleshooting_system
    
    logger.info("=" * 60)
    logger.info("KAREN AI COLLABORATIVE TROUBLESHOOTING SYSTEM")
    logger.info("=" * 60)
    logger.info("Starting multi-agent troubleshooting coordination...")
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    troubleshooting_system = None
    
    try:
        # Create and start the troubleshooting system
        troubleshooting_system = IntegratedTroubleshootingSystem()
        troubleshooting_system.start()
        
        logger.info("✅ Troubleshooting system started successfully!")
        logger.info("")
        logger.info("Available Services:")
        logger.info("• Multi-agent issue coordination")
        logger.info("• Conflict-free resource management") 
        logger.info("• Testing environment orchestration")
        logger.info("• Knowledge base and pattern matching")
        logger.info("• Solution sharing and validation")
        logger.info("")
        logger.info("Agents can now:")
        logger.info("• Report issues → troubleshooting_orchestrator")
        logger.info("• Request help → send help_request message")
        logger.info("• Share solutions → use solution_share type")
        logger.info("• Coordinate testing → request environment reservation")
        logger.info("")
        logger.info("System running... Press Ctrl+C to stop")
        
        # Keep the system running
        try:
            while troubleshooting_system.running:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            pass
            
    except Exception as e:
        logger.error(f"Failed to start troubleshooting system: {e}")
        return 1
    finally:
        if troubleshooting_system:
            troubleshooting_system.stop()
            
    logger.info("Troubleshooting system stopped gracefully")
    return 0

if __name__ == "__main__":
    exit(main())
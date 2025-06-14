#!/usr/bin/env python3
"""
Launch script for the SMS Engineer Agent.
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add project root and src to sys.path to allow imports from src
try:
    PROJECT_ROOT = Path(__file__).resolve().parent
    SRC_DIR = PROJECT_ROOT / 'src'
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))

    from sms_engineer_agent import SMSEngineerAgent
    from dotenv import load_dotenv
except ImportError as e:
    # This block might be problematic if PROJECT_ROOT or SRC_DIR are not defined due to an early error
    # However, Path resolution should generally work.
    print(f"Error importing necessary modules: {e}")
    # Safely print paths if they exist
    project_root_defined = 'PROJECT_ROOT' in locals() or 'PROJECT_ROOT' in globals()
    src_dir_defined = 'SRC_DIR' in locals() or 'SRC_DIR' in globals()
    print(f"PROJECT_ROOT defined: {project_root_defined}, SRC_DIR defined: {src_dir_defined}")
    if project_root_defined: print(f"PROJECT_ROOT: {PROJECT_ROOT}")
    if src_dir_defined: print(f"SRC_DIR: {SRC_DIR}") 
    print(f"sys.path: {sys.path}")
    print("Please ensure that src/sms_engineer_agent.py exists and all dependencies are installed.")
    sys.exit(1)

def main():
    """Initializes and starts the SMSEngineerAgent."""
    # Load environment variables from .env file in the project root
    env_path = PROJECT_ROOT / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print(f"Loaded environment variables from {env_path}")
    else:
        print(f".env file not found at {env_path}. Agent might not have all configurations.")

    # Configure basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout
    )
    logger = logging.getLogger(__name__)
    logger.info("🚀 Launching SMS Engineer Agent...")

    agent = SMSEngineerAgent()

    try:
        logger.info("Starting SMS Engineer Agent in asynchronous processing mode...")
        asyncio.run(agent.start_processing())
    except KeyboardInterrupt:
        logger.info("🔌 SMS Engineer Agent shutdown requested via KeyboardInterrupt.")
        agent.stop()
    except Exception as e:
        logger.error(f"💥 SMS Engineer Agent encountered a fatal error: {e}", exc_info=True)
        agent.stop()
    finally:
        logger.info("👋 SMS Engineer Agent has stopped.")

if __name__ == "__main__":
    main() 
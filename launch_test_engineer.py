#!/usr/bin/env python3
"""
Launch script for the Test Engineer Agent.
"""
import logging
import os
import sys
from pathlib import Path

# Add project root and src to sys.path to allow imports
try:
    PROJECT_ROOT = Path(__file__).resolve().parent
    SRC_DIR = PROJECT_ROOT / 'src'
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))

    from test_engineer import main as test_engineer_main
    from dotenv import load_dotenv
    from src.agent_activity_logger import AgentActivityLogger
except ImportError as e:
    print(f"Error importing necessary modules: {e}")
    project_root_defined = 'PROJECT_ROOT' in locals() or 'PROJECT_ROOT' in globals()
    src_dir_defined = 'SRC_DIR' in locals() or 'SRC_DIR' in globals()
    print(f"PROJECT_ROOT defined: {project_root_defined}, SRC_DIR defined: {src_dir_defined}")
    if project_root_defined: print(f"PROJECT_ROOT: {PROJECT_ROOT}")
    if src_dir_defined: print(f"SRC_DIR: {SRC_DIR}")
    print(f"sys.path: {sys.path}")
    print("Please ensure src/test_engineer.py exists.")
    sys.exit(1)

def main():
    """Initializes and starts the TestEngineerAgent."""
    env_path = PROJECT_ROOT / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print(f"Loaded environment variables from {env_path}")
    else:
        print(f".env file not found at {env_path}. Agent might not have all configurations.")

    # Basic logging configuration (test_engineer.py might have its own more specific logging)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout
    )
    logger = logging.getLogger("LaunchTestEngineer")
    logger.info("🚀 Launching Test Engineer Agent...")

    try:
        test_engineer_main() # This will typically run a loop or a long-running process
    except KeyboardInterrupt:
        logger.info("🔌 Test Engineer Agent shutdown requested via KeyboardInterrupt.")
    except Exception as e:
        logger.error(f"💥 Test Engineer Agent encountered a fatal error: {e}", exc_info=True)
    finally:
        logger.info("👋 Test Engineer Agent has stopped.")

if __name__ == "__main__":
    main() 
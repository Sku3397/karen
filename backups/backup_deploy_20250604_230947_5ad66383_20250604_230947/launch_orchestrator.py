#!/usr/bin/env python3
"""
Launch script for the Orchestrator Agent.
"""
import sys
import os

# Ensure the script can find the 'orchestrator_active.py' module
# Assuming orchestrator_active.py is in the same directory or on PYTHONPATH

try:
    from orchestrator_active import main as orchestrator_main
except ImportError as e:
    print(f"Error: Could not import orchestrator_main from orchestrator_active: {e}")
    print("Make sure orchestrator_active.py is in the project root or accessible via PYTHONPATH.")
    # Attempt to add project root to sys.path as a fallback
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    try:
        from orchestrator_active import main as orchestrator_main
        print(f"Successfully imported orchestrator_main after adding {project_root} to sys.path.")
    except ImportError as e2:
        print(f"Error even after adding project root to sys.path: {e2}")
        sys.exit(1)


if __name__ == "__main__":
    print("🚀 Launching Orchestrator Agent...")
    # The orchestrator_active.py script handles its own src path adjustments.
    exit_code = orchestrator_main()
    sys.exit(exit_code) 
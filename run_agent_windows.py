#!/usr/bin/env python3
"""
Run Agent Windows Script
------------------------
Launches a specified agent in a new PowerShell window.
Reads agent configuration from 'autonomous-agents/shared-knowledge/agents_config.json'.
Useful for development and monitoring individual agents on Windows.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# --- Path Setup ---
# This script (run_agent_windows.py) is at the Project Root.
PROJECT_ROOT = Path(__file__).resolve().parent
AUTONOMOUS_AGENTS_DIR = PROJECT_ROOT / "autonomous-agents"
SHARED_KNOWLEDGE_DIR = AUTONOMOUS_AGENTS_DIR / "shared-knowledge"
AGENTS_CONFIG_PATH = SHARED_KNOWLEDGE_DIR / "agents_config.json"

def get_project_python_interpreter(config_preference="default") -> str:
    """
    Detects and returns the path to the project's Python interpreter.
    Similar to logic in launch_agents.py and start_session.py.
    """
    if config_preference and config_preference != "default":
        p_path = Path(config_preference)
        if p_path.is_file() and os.access(p_path, os.X_OK):
            # If it's an absolute path or a path relative to project root that resolves
            if p_path.is_absolute():
                return str(p_path)
            resolved_path = (PROJECT_ROOT / p_path).resolve()
            if resolved_path.exists() and os.access(resolved_path, os.X_OK):
                 return str(resolved_path)
        print(f"[RunAgent] Warning: Specified python interpreter '{config_preference}' not found or not executable. Falling back.")

    # Try project .venv (common for Poetry, etc.)
    venv_scripts_dir = PROJECT_ROOT / ".venv" / ("Scripts" if os.name == 'nt' else "bin")
    venv_python_exe = venv_scripts_dir / ("python.exe" if os.name == 'nt' else "python")
    if venv_python_exe.exists() and os.access(venv_python_exe, os.X_OK):
        return str(venv_python_exe)

    # Try project venv (common for venv module)
    venv_alt_scripts_dir = PROJECT_ROOT / "venv" / ("Scripts" if os.name == 'nt' else "bin")
    venv_alt_python_exe = venv_alt_scripts_dir / ("python.exe" if os.name == 'nt' else "python")
    if venv_alt_python_exe.exists() and os.access(venv_alt_python_exe, os.X_OK):
        return str(venv_alt_python_exe)

    # Fallback to the Python interpreter running this script
    return sys.executable

def load_agent_config(agent_name_to_find: str) -> dict | None:
    """Loads agent configurations and returns the config for the specified agent."""
    if not AGENTS_CONFIG_PATH.exists():
        print(f"[RunAgent] Error: Agent configuration file not found at {AGENTS_CONFIG_PATH}")
        return None
    try:
        config_data = json.loads(AGENTS_CONFIG_PATH.read_text(encoding='utf-8'))
        for agent_config in config_data.get("agents", []):
            if agent_config.get("name") == agent_name_to_find:
                return agent_config
        print(f"[RunAgent] Error: Agent '{agent_name_to_find}' not found in {AGENTS_CONFIG_PATH}")
        return None
    except json.JSONDecodeError:
        print(f"[RunAgent] Error: Could not parse agent configuration file {AGENTS_CONFIG_PATH}")
        return None
    except Exception as e:
        print(f"[RunAgent] Error loading agent config for '{agent_name_to_find}': {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Launch a specific agent in a new PowerShell window on Windows.")
    parser.add_argument("agent_name", help="The name of the agent to launch (must be defined in agents_config.json).")
    args = parser.parse_args()

    agent_name = args.agent_name
    print(f"[RunAgent] Attempting to launch agent: '{agent_name}'...")

    agent_config = load_agent_config(agent_name)
    if not agent_config:
        return

    script_path_rel = agent_config.get("script_path")
    if not script_path_rel:
        print(f"[RunAgent] Error: Agent '{agent_name}' configuration is missing 'script_path'.")
        return

    script_abs_path = (PROJECT_ROOT / script_path_rel).resolve()
    if not script_abs_path.exists():
        print(f"[RunAgent] Error: Agent script for '{agent_name}' not found at expected path: {script_abs_path}")
        return

    python_interpreter_pref = agent_config.get("python_interpreter", "default")
    python_exe_to_use = get_project_python_interpreter(python_interpreter_pref)
    
    agent_script_args = agent_config.get("args", [])

    # Construct the command to be run inside the new PowerShell window
    # Using list form for subprocess is generally safer with paths containing spaces
    command_parts = [python_exe_to_use, str(script_abs_path)] + agent_script_args
    
    # Escape arguments for PowerShell if necessary, though Popen usually handles this well for the direct command.
    # For the -Command part, quoting might be needed if args have spaces or special PS chars.
    # Simpler approach: pass the command as a list to Popen, and PowerShell will execute it.
    
    # The command string for PowerShell's -Command argument
    # Ensure paths with spaces are quoted for PowerShell execution context
    ps_command_elements = [f'"{part}"' if " " in part else part for part in command_parts]
    full_ps_command = f"& {{{' '.join(ps_command_elements)}; Write-Host \"Agent script finished. Press Enter to close window.\"; Read-Host}}"

    # Construct the 'start' command for PowerShell
    # Using 'start powershell' launches a new window.
    # -NoExit keeps the window open if the script exits quickly or errors.
    # -Command executes the specified command.
    # The title of the window will be "Agent: <AgentName>"
    
    # Note: subprocess.Popen with shell=False is preferred.
    # `start` is a cmd.exe built-in, so we can use cmd /c start ...
    # Or, more directly, call powershell.exe with arguments to start a new window.
    # Using `start` via `cmd /c` is a common way to detach and open a new window.
    
    # Updated: Using CREATE_NEW_CONSOLE with powershell.exe directly
    # This gives more control and avoids cmd.exe layer.
    
    new_window_command = [
        "powershell.exe",
        "-NoExit",          # Keep window open after command finishes
        "-Command",
        full_ps_command
    ]

    print(f"[RunAgent] Launching agent '{agent_name}' in a new PowerShell window.")
    print(f"[RunAgent]   Interpreter: {python_exe_to_use}")
    print(f"[RunAgent]   Script: {script_abs_path}")
    if agent_script_args:
        print(f"[RunAgent]   Arguments: {agent_script_args}")
    print(f"[RunAgent]   PowerShell Command: {' '.join(new_window_command)}") # For logging

    try:
        # For Windows, subprocess.CREATE_NEW_CONSOLE flag opens a new console window
        # The process running this script (run_agent_windows.py) will not wait for it.
        subprocess.Popen(new_window_command, creationflags=subprocess.CREATE_NEW_CONSOLE)
        print(f"[RunAgent] Agent '{agent_name}' launched successfully.")
    except FileNotFoundError:
        print(f"[RunAgent] Error: powershell.exe not found. Ensure PowerShell is installed and in your PATH.")
    except Exception as e:
        print(f"[RunAgent] Error launching agent '{agent_name}' in new window: {e}")

if __name__ == "__main__":
    if os.name != 'nt':
        print("Warning: This script is primarily intended for Windows to launch agents in new PowerShell windows.")
        print("On non-Windows systems, it will attempt to run, but behavior may differ (e.g., no new window without 'start' or similar).")
        # Fallback or exit? For now, let it proceed but it won't achieve the 'new window' goal as directly.
        # A more cross-platform approach might use 'gnome-terminal', 'xterm', 'open -a Terminal' etc.
        # but that's beyond the current "run_agent_windows.py" scope.

    main() 
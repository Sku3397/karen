#!/usr/bin/env python3
import json
import logging
import os
from pathlib import Path

# Assuming src is in PYTHONPATH or this script is run in a way that src.orchestrator is discoverable.
# If running directly from project root with 'python src/start_orchestrator_and_load_tasks.py',
# this import might need adjustment or PYTHONPATH setup.
# For simplicity, assuming direct import works if src is a package.
try:
    from .orchestrator import AgentOrchestrator, AgentType, TaskPriority
except ImportError:
    # Fallback for running as top-level script if src is not directly in pythonpath
    # This is a common pattern for scripts inside a package.
    import sys
    # Add project root to path to allow importing from src
    PROJECT_ROOT_GUESS = Path(__file__).resolve().parent.parent
    sys.path.append(str(PROJECT_ROOT_GUESS))
    from src.orchestrator import AgentOrchestrator, AgentType, TaskPriority


# Configure basic logging for the runner script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TASKS_FILE_PATH = Path(__file__).resolve().parent.parent / "tasks" / "eigencode_assigned_tasks.json"
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def load_and_dispatch_tasks(orchestrator: AgentOrchestrator):
    logger.info(f"Attempting to load tasks from: {TASKS_FILE_PATH}")
    if not TASKS_FILE_PATH.exists():
        logger.error(f"CRITICAL: Tasks file not found at {TASKS_FILE_PATH}. Orchestrator will not be loaded with Eigencode tasks.")
        return

    try:
        with open(TASKS_FILE_PATH, 'r', encoding='utf-8') as f:
            tasks_data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {TASKS_FILE_PATH}: {e}")
        return
    except Exception as e:
        logger.error(f"Error reading tasks file {TASKS_FILE_PATH}: {e}")
        return

    if not isinstance(tasks_data, list):
        logger.error(f"Tasks data in {TASKS_FILE_PATH} is not a list. Skipping task loading.")
        return

    logger.info(f"Found {len(tasks_data)} tasks in {TASKS_FILE_PATH}.")
    loaded_count = 0
    for task_item in tasks_data:
        try:
            description = task_item.get("description")
            source_file = task_item.get("source_file", "N/A")
            task_id_hint = task_item.get("task_id", "UnknownID") # For logging

            # AgentType mapping - Eigencode tasks are general, assign to Archaeologist for now if not specified
            # Or, we might need a new 'EigencodeTaskProcessorAgent' or map based on category.
            # For now, let's try to infer or default.
            # This mapping might need to be more sophisticated.
            category = task_item.get("category", "").lower()
            assigned_agent_type_str = "ARCHAEOLOGIST" # Default

            if "sms" in category or "sms" in source_file:
                assigned_agent_type_str = "SMS_ENGINEER"
            elif "phone" in category or "voice" in category or "phone" in source_file or "voice" in source_file:
                assigned_agent_type_str = "PHONE_ENGINEER"
            elif "memory" in category or "memory" in source_file or "customer_profile" in source_file:
                assigned_agent_type_str = "MEMORY_ENGINEER"
            elif "test" in category or "test" in source_file:
                assigned_agent_type_str = "TEST_ENGINEER"
            # Add more mappings as needed, e.g., for personality, analytics, coordination

            try:
                agent_type = AgentType[assigned_agent_type_str]
            except KeyError:
                logger.warning(f"Task {task_id_hint}: Unknown agent type '{assigned_agent_type_str}' inferred for category '{category}'. Defaulting to ARCHAEOLOGIST.")
                agent_type = AgentType.ARCHAEOLOGIST
            
            priority_str = task_item.get("priority", "medium").upper()
            try:
                priority = TaskPriority[priority_str]
            except KeyError:
                logger.warning(f"Task {task_id_hint}: Unknown priority '{priority_str}'. Defaulting to MEDIUM.")
                priority = TaskPriority.MEDIUM

            params = {
                "original_task_id": task_item.get("task_id"),
                "source_file": source_file,
                "status_from_eigencode": task_item.get("status"), # 'new'
                "notes_from_eigencode": task_item.get("notes"),
                "category_from_eigencode": task_item.get("category")
            }
            if task_item.get("source_file"): # If it's about an existing file
                 params["target_file_path"] = str( (PROJECT_ROOT / task_item["source_file"]).resolve() )


            # Task type for orchestrator: could be 'code_analysis_item', 'file_creation_request', 'implementation_task'
            # Based on the task from Eigencode, this is likely an 'implementation_task' or 'fix_issue'
            task_type = "process_eigencode_task" # Generic task type for agents to handle

            # If the task is to create a non-existent file, set task_type accordingly
            if "create" in description.lower() and task_item.get("source_file") and not (PROJECT_ROOT / task_item["source_file"]).exists():
                task_type = "create_file_task"
                params["target_file_path"] = str( (PROJECT_ROOT / task_item["source_file"]).resolve() )
                params["initial_content_suggestion"] = f"# TODO: Implement content for {task_item['source_file']} based on Eigencode task: {description}"


            task_full_description = f"Eigencode Task ({task_id_hint}): {description}. Source: {source_file}"
            
            orchestrator.create_task(
                agent_type=agent_type,
                task_type=task_type,
                description=task_full_description,
                priority=priority,
                params=params
            )
            loaded_count += 1
        except Exception as e:
            logger.error(f"Failed to create orchestrator task for Eigencode item {task_item.get('task_id', 'N/A')}: {e}", exc_info=True)
            
    logger.info(f"Successfully loaded {loaded_count} tasks into the orchestrator's queue.")

def main():
    logger.info("Starting Orchestrator and loading Eigencode tasks...")
    
    # Ensure necessary directories for orchestrator logging exist (it does this itself, but belt and braces)
    (Path(__file__).resolve().parent.parent / "logs" / "orchestrator").mkdir(parents=True, exist_ok=True)

    orchestrator = AgentOrchestrator()
    
    # Load tasks from the Eigencode-generated JSON file
    load_and_dispatch_tasks(orchestrator)
    
    logger.info("Orchestrator initialized and tasks loaded. Background threads should be processing.")
    logger.info("This script will now keep running to keep the orchestrator alive.")
    logger.info("Press Ctrl+C to stop the orchestrator and this script.")
    
    try:
        # Keep the main thread alive, orchestrator runs in background threads
        while True:
            time.sleep(60) # Keep alive, check status or perform other main thread tasks if needed
            # Example: orchestrator.get_system_overview() or print queue size
            # logger.debug(f"Orchestrator task queue size: {orchestrator.task_queue.qsize()}")
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Shutting down orchestrator runner...")
    finally:
        logger.info("Orchestrator runner finished.")

if __name__ == "__main__":
    main() 
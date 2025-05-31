import pytest
import os
# import sys # No longer needed here, conftest.py handles it
import subprocess
import time
import signal
import logging # For logging within the test

# # Add project root to sys.path to allow src imports # No longer needed here
# PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) # No longer needed here
# sys.path.insert(0, PROJECT_ROOT) # No longer needed here

# Attempt to import EmailClient and config values
# These imports assume that when APP_ENV is set, the config module
# correctly loads all necessary values from the main .env file.
try:
    from src.email_client import EmailClient
    # config.py should have loaded ADMIN_EMAIL_ADDRESS and SECRETARY_EMAIL_ADDRESS from the environment
    from src.config import ADMIN_EMAIL_ADDRESS, SECRETARY_EMAIL_ADDRESS 
except ImportError as e:
    # This allows the file to be parsable by pytest for collection even if src or config is problematic initially
    # The actual test run will then fail more gracefully if these are truly unavailable.
    logging.error(f"Could not import necessary modules from src: {e}. Test will likely fail.")
    EmailClient = None
    ADMIN_EMAIL_ADDRESS = "fallback_admin@example.com" # Fallback to prevent crash before test run
    SECRETARY_EMAIL_ADDRESS = "fallback_secretary@example.com"

logger = logging.getLogger(__name__) # Test-specific logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')

# Determine the project root and python executable from .venv
PROJECT_ROOT_FOR_EXEC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if os.name == 'nt': # Windows
    PYTHON_EXEC = os.path.join(PROJECT_ROOT_FOR_EXEC, ".venv", "Scripts", "python.exe")
else: # Linux/macOS
    PYTHON_EXEC = os.path.join(PROJECT_ROOT_FOR_EXEC, ".venv", "bin", "python")

# Helper function to manage subprocesses
def start_service(command, name, working_dir="."):
    logger.info(f"Starting {name} with command: {' '.join(command)} in {working_dir}")
    # Set APP_ENV for the subprocess environment as well
    env = os.environ.copy()
    env["APP_ENV"] = "interactive_test" 
    # Ensure PYTHONPATH includes src for Celery worker/beat if they are not run as modules
    # This might be needed if 'src.celery_app' can't be found by the celery command otherwise.
    # current_pythonpath = env.get("PYTHONPATH", "")
    # project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")) # tests/ -> project_root/
    # src_path = os.path.join(project_root, "src")
    # if src_path not in current_pythonpath:
    #    env["PYTHONPATH"] = f"{src_path}{os.pathsep}{current_pythonpath}"
    # logger.info(f"PYTHONPATH for {name}: {env.get('PYTHONPATH')}")

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, cwd=working_dir)
    time.sleep(8) # Increased wait time for services to start, especially Celery
    if process.poll() is not None: # Check if process terminated early
        stdout, stderr = process.communicate()
        logger.error(f"ERROR: {name} failed to start. Return code: {process.returncode}")
        logger.error(f"STDOUT:\n{stdout}")
        logger.error(f"STDERR:\n{stderr}")
        raise RuntimeError(f"{name} failed to start. Check logs for details.")
    logger.info(f"{name} started successfully with PID: {process.pid}")
    return process

@pytest.mark.interactive
def test_run_interactive_secretary_session(capsys):
    original_app_env = os.environ.get("APP_ENV")
    # Set APP_ENV for the current pytest process. This ensures config.py loads correctly.
    os.environ["APP_ENV"] = "interactive_test"
    logger.info("Set APP_ENV to interactive_test for the pytest process.")

    # Crucially, reload the config module and dependent modules if they cache config at import time.
    # This is a common challenge. A robust way is to ensure config is re-read or to structure
    # apps (like FastAPI, Celery) to be initialized *after* env is set.
    # For this test, we assume that setting os.environ["APP_ENV"] before imports 
    # at the top of *this file* (if they were inside the function) or at the start of config.py is sufficient.
    # The `start_service` helper also sets APP_ENV for subprocesses.

    # Re-import or access configured values AFTER APP_ENV is set to ensure they are from the correct .env context
    # This relies on src.config.py correctly re-evaluating os.getenv() when it's imported or its variables accessed.
    from src.config import ADMIN_EMAIL_ADDRESS as CURRENT_ADMIN_EMAIL
    from src.config import SECRETARY_EMAIL_ADDRESS as CURRENT_SECRETARY_EMAIL
    logger.info(f"Using ADMIN_EMAIL_ADDRESS: {CURRENT_ADMIN_EMAIL}")
    logger.info(f"Using SECRETARY_EMAIL_ADDRESS (to be monitored): {CURRENT_SECRETARY_EMAIL}")

    if not EmailClient:
        pytest.fail("EmailClient could not be imported. Check src/email_client.py and its dependencies.")
    if not CURRENT_ADMIN_EMAIL or not CURRENT_SECRETARY_EMAIL or "fallback" in CURRENT_ADMIN_EMAIL:
        pytest.fail("Admin or Secretary email addresses not loaded correctly. Check config and .env setup.")

    processes = []
    # project_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")) # Already defined as PROJECT_ROOT_FOR_EXEC

    try:
        # 1. Start FastAPI Application (Uvicorn)
        # Uvicorn running main.py should pick up APP_ENV from its environment
        # Add --reload for hot-reloading of FastAPI app code
        fastapi_cmd = [PYTHON_EXEC, "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
        processes.append(start_service(fastapi_cmd, "FastAPI", working_dir=PROJECT_ROOT_FOR_EXEC))

        # 2. Start Celery Worker
        # Invoke celery as a module: python -m celery
        celery_worker_cmd = [PYTHON_EXEC, "-m", "celery", "-A", "src.celery_app.app", "worker", "-l", "INFO", "-P", "solo", "--autoreload"]
        processes.append(start_service(celery_worker_cmd, "Celery Worker", working_dir=PROJECT_ROOT_FOR_EXEC))

        # 3. Start Celery Beat Scheduler
        # Invoke celery as a module: python -m celery
        celery_beat_cmd = [PYTHON_EXEC, "-m", "celery", "-A", "src.celery_app.app", "beat", "-l", "INFO", "--schedule", "./celerybeat-schedule-interactive-test"]
        processes.append(start_service(celery_beat_cmd, "Celery Beat", working_dir=PROJECT_ROOT_FOR_EXEC))

        logger.info("All services for interactive test started.")

        # 4. Send Initial Notification Email to Admin
        try:
            logger.info(f"Attempting to send notification email to {CURRENT_ADMIN_EMAIL} from {CURRENT_SECRETARY_EMAIL}")
            # EmailClient is instantiated here, it should use config loaded by APP_ENV=interactive_test
            # which means it uses the SECRETARY_EMAIL_ADDRESS from the main .env file and its OAuth tokens
            email_service = EmailClient(email_address=CURRENT_SECRETARY_EMAIL) 
            subject = "Handyman Secretary AI Interactive Test: Monitoring Initiated"
            body = (f"The Handyman Secretary AI interactive test environment is now active.\n"
                    f"Secretary AI is monitoring: {CURRENT_SECRETARY_EMAIL}\n"
                    f"You can now send test emails to this address.\n\n"
                    f"FastAPI: http://localhost:8000\n"
                    f"This test session is running. You can stop it in your IDE/terminal (e.g., Ctrl+C in the pytest runner).")
            # The send_email method in EmailClient expects 'to', 'subject', 'body'
            email_service.send_email(to=CURRENT_ADMIN_EMAIL, subject=subject, body=body)
            logger.info(f"Notification email supposedly sent to {CURRENT_ADMIN_EMAIL}.")
        except Exception as e:
            logger.error(f"ERROR: Failed to send notification email: {e}", exc_info=True)
            pytest.fail(f"Failed to send notification email: {e}")

        # 5. Keep Test Running for Admin Interaction
        logger.info("\n" + "="*70)
        logger.info("Handyman Secretary AI Interactive Test is RUNNING.")
        logger.info(f"FastAPI available at: http://localhost:8000")
        logger.info(f"Secretary AI is monitoring emails for: {CURRENT_SECRETARY_EMAIL}")
        logger.info(f"Admin notifications will be sent to: {CURRENT_ADMIN_EMAIL}")
        logger.info("You can now send emails to the secretary AI to test its abilities.")
        logger.info("The Cursor agent will monitor performance and logs.")
        logger.info("Press Ctrl+C in the terminal/IDE running pytest to stop this test.")
        logger.info("="*70 + "\n")

        while True:
            time.sleep(5) # Keep the main test thread alive, check for subprocess health
            for p_idx, p in enumerate(processes):
                if p.poll() is not None:
                    stdout, stderr = p.communicate()
                    service_name = p.args # Or a more descriptive name passed to start_service
                    logger.error(f"SERVICE CRASHED: {service_name} (PID: {p.pid}) exited with code {p.returncode}.")
                    logger.error(f"  STDOUT:\n{stdout}")
                    logger.error(f"  STDERR:\n{stderr}")
                    pytest.fail(f"Service {service_name} crashed during interactive test. Check logs.")
            # Add any other live monitoring/checks here if needed

    except Exception as e:
        logger.error(f"An error occurred during interactive test setup or execution: {e}", exc_info=True)
        pytest.fail(str(e))
    finally:
        logger.info("Initiating shutdown of interactive test services...")
        for p in reversed(processes):
            service_name_args = p.args
            logger.info(f"Stopping {service_name_args} (PID: {p.pid})...")
            # Send SIGINT (Ctrl+C) first for graceful shutdown, as Uvicorn/Celery might trap it
            try:
                if os.name == 'nt': # Windows does not support sending SIGINT this way well for subprocesses
                    p.terminate() # For Windows, SIGTERM is more common for direct termination
                else:
                    p.send_signal(signal.SIGINT)
                p.wait(timeout=15) # Increased timeout for graceful shutdown
                logger.info(f"Process {p.pid} ({service_name_args}) terminated gracefully.")
            except subprocess.TimeoutExpired:
                logger.warning(f"Process {p.pid} ({service_name_args}) did not respond to SIGINT/terminate. Sending SIGKILL...")
                p.kill()
                logger.info(f"Process {p.pid} ({service_name_args}) killed.")
            except Exception as e_term:
                 logger.error(f"Error during termination of {p.pid} ({service_name_args}): {e_term}")

        if original_app_env is None:
            if "APP_ENV" in os.environ: # Check before deleting
                del os.environ["APP_ENV"]
                logger.info("Removed APP_ENV from environment.")
        else:
            os.environ["APP_ENV"] = original_app_env
            logger.info(f"Restored APP_ENV to: {original_app_env}")
        
        logger.info("Interactive test session processes stopped.")
        # Clean up the temporary Celery Beat schedule file
        schedule_file = os.path.join(PROJECT_ROOT_FOR_EXEC, "celerybeat-schedule-interactive-test")
        if os.path.exists(schedule_file):
            try:
                os.remove(schedule_file)
                logger.info(f"Removed Celery Beat schedule file: {schedule_file}")
            except OSError as e_remove:
                logger.warning(f"Could not remove Celery Beat schedule file {schedule_file}: {e_remove}") 
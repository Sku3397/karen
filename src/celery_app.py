# APP_ENV needs to be known before config is imported, which itself loads .env files.
# So, ensure APP_ENV is set in the environment *before* Celery worker/beat starts.
# The modified config.py will handle loading the correct .env file.

import os # Moved os import higher
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta
import asyncio # Added for asyncio.run

# --- Early .env loading for Celery context ---
# Determine project root assuming this file is in src/
PROJECT_ROOT_FOR_CELERY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN_ENV_PATH_FOR_CELERY = os.path.join(PROJECT_ROOT_FOR_CELERY, '.env')

# Get a logger for this early loading phase
_celery_early_logger = logging.getLogger('celery_early_config')
_celery_early_logger.setLevel(logging.DEBUG)
_early_handler = logging.StreamHandler()
_early_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
_celery_early_logger.addHandler(_early_handler)

_celery_early_logger.info(f"CELERY_APP.PY: Attempting to load .env file from: {MAIN_ENV_PATH_FOR_CELERY}")
if os.path.exists(MAIN_ENV_PATH_FOR_CELERY):
    loaded_env = load_dotenv(dotenv_path=MAIN_ENV_PATH_FOR_CELERY, override=True) # Override to be sure
    _celery_early_logger.info(f"CELERY_APP.PY: Loaded .env file: {MAIN_ENV_PATH_FOR_CELERY}, result: {loaded_env}")
    # Log a few key variables to confirm they are loaded as expected by Celery
    _celery_early_logger.info(f"CELERY_APP.PY: CELERY_BROKER_URL from os.getenv after load: {os.getenv('CELERY_BROKER_URL')}")
    _celery_early_logger.info(f"CELERY_APP.PY: SECRETARY_EMAIL_ADDRESS from os.getenv after load: {os.getenv('SECRETARY_EMAIL_ADDRESS')}")
else:
    _celery_early_logger.warning(f"CELERY_APP.PY: Main .env file NOT FOUND at: {MAIN_ENV_PATH_FOR_CELERY}")

_celery_early_logger.removeHandler(_early_handler) # Clean up handler
# --- End Early .env loading ---

from celery import Celery, signals
from celery.schedules import crontab
# import os # Already imported
# import logging # Already imported
# from datetime import datetime, timedelta # Already imported

# Import your application's configuration and agents
# Adjust paths as necessary based on your project structure

# config will now load the correct .env file based on APP_ENV
# We will rely on the above early load_dotenv for Celery's direct needs.
# Other modules will still import config.py which has its own sophisticated .env loading logic.
from . import config # Use relative import for config

from .communication_agent.agent import CommunicationAgent # Assuming this path
# Import the actual task_manager instance from its module
from .task_manager_agent import task_manager as actual_task_manager_instance # Assuming this path

# Import MockEmailClient if using it for tests
# The decision to use MockEmailClient should ideally be in config, not directly here.
# For now, will rely on config.USE_MOCK_EMAIL_CLIENT if it exists.
USE_MOCK_EMAIL_CLIENT = getattr(config, 'USE_MOCK_EMAIL_CLIENT', False)
if USE_MOCK_EMAIL_CLIENT:
    from .mock_email_client import MockEmailClient

# Setup basic logging configuration for this module
# This will apply to logs emitted directly from celery_app.py
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# ^-- This might be conflicting. Celery signals should handle configuration for Celery loggers.
logger = logging.getLogger(__name__)

print("PRINT: CELERY_APP.PY - About to create Celery app instance", flush=True)
# Celery broker and backend URLs are now sourced from config module (or directly from os.getenv due to early load)
celery_app = Celery(
    'ai_handyman_tasks',
    broker=os.getenv('CELERY_BROKER_URL'), # Use getenv directly after early load
    backend=os.getenv('CELERY_RESULT_BACKEND'), # Use getenv directly
    include=['src.celery_app']  # Point to this module to find tasks
)

# Optional Celery configuration, see Celery docs for more options
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],  # Ignore other content
    result_serializer='json',
    timezone=os.getenv('TZ', 'UTC'), # Use TZ from env or default to UTC
    enable_utc=True,
    worker_hijack_root_logger=False,  # Allow custom logging configuration
    # Add beat_schedule_filename for test isolation if not using DB scheduler
    # beat_schedule_filename = 'celerybeat-schedule-interactive-test' if config.APP_ENV == 'interactive_test' else 'celerybeat-schedule'
)

# Celery Logging Configuration
CELERY_LOG_FMT = "[%(asctime)s: %(levelname)s/%(processName)s][%(name)s] %(message)s"
CELERY_TASK_LOG_FMT = "[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s"

# Add specific configuration for celery.app.trace as per GitHub issue #4734 recommendation
if not logging.getLogger('celery.app.trace').handlers:
    # If no handlers are configured for celery.app.trace, add a basic one and ensure propagation.
    # This is to make sure its logs, and potentially by extension task logs, make it out.
    trace_logger = logging.getLogger('celery.app.trace')
    trace_logger.setLevel(logging.INFO) # Or DEBUG if more verbosity is needed from trace
    trace_logger.propagate = True
    # Optionally, add a handler if it's not getting picked up by root logger configuration elsewhere
    # console_handler = logging.StreamHandler()
    # console_handler.setFormatter(logging.Formatter(CELERY_LOG_FMT))
    # trace_logger.addHandler(console_handler)

@signals.after_setup_logger.connect
def setup_celery_logger(logger, **kwargs):
    """Configure Celery's root logger."""
    formatter = logging.Formatter(CELERY_LOG_FMT)
    for handler in logger.handlers:
        handler.setFormatter(formatter)
    logger.setLevel(logging.DEBUG) # Set to DEBUG
    logger.propagate = True # Ensure propagation

@signals.after_setup_task_logger.connect
def setup_celery_task_logger(logger, **kwargs):
    """Configure Celery's task logger."""
    formatter = logging.Formatter(CELERY_TASK_LOG_FMT)
    for handler in logger.handlers:
        handler.setFormatter(formatter)
    logger.setLevel(logging.DEBUG) # Set to DEBUG
    logger.propagate = True # Ensure propagation

# Initialize CommunicationAgent 
_communication_agent_instance = None

def get_communication_agent_instance():
    global _communication_agent_instance
    if _communication_agent_instance is None:
        logger.debug("Creating new CommunicationAgent instance in get_communication_agent_instance().")
        
        # Config for Karen's sending email account (karensecretaryai@gmail.com)
        sending_email_config = {
            'SECRETARY_EMAIL_ADDRESS': os.getenv('SECRETARY_EMAIL_ADDRESS'),
            'SECRETARY_TOKEN_PATH': os.getenv('SECRETARY_TOKEN_PATH', 'gmail_token_karen.json') # Default if not in .env
            # SMTP/IMAP server/port/password are not used by the current EmailClient with Gmail API
        }
        logger.debug(f"Sending email config: {sending_email_config.get('SECRETARY_EMAIL_ADDRESS')}, Token: {sending_email_config.get('SECRETARY_TOKEN_PATH')}")

        # Config for the monitored email account (hello@757handy.com)
        monitoring_email_config = {
            'MONITORED_EMAIL_ACCOUNT': os.getenv('MONITORED_EMAIL_ACCOUNT'),
            'MONITORED_EMAIL_TOKEN_PATH': os.getenv('MONITORED_EMAIL_TOKEN_PATH', 'gmail_token_monitor.json') # Default
        }
        logger.debug(f"Monitoring email config: {monitoring_email_config.get('MONITORED_EMAIL_ACCOUNT')}, Token: {monitoring_email_config.get('MONITORED_EMAIL_TOKEN_PATH')}")

        sms_cfg_to_use = {
            'account_sid': os.getenv('TWILIO_ACCOUNT_SID'),
            'auth_token': os.getenv('TWILIO_AUTH_TOKEN'),
            'from_number': os.getenv('TWILIO_FROM_NUMBER')
        }
        print(f"PRINT_DEBUG_AGENT_INSTANCE: sms_cfg_to_use from os.getenv: {sms_cfg_to_use.get('account_sid')}", flush=True)

        transcription_cfg_to_use = {
            'language_code': os.getenv('SPEECH_LANGUAGE_CODE', 'en-US')
        }
        print(f"PRINT_DEBUG_AGENT_INSTANCE: transcription_cfg_to_use from os.getenv: {transcription_cfg_to_use.get('language_code')}", flush=True)
        
        task_manager_to_use = actual_task_manager_instance # This should be fine as it's an imported instance

        print("PRINT_DEBUG_AGENT_INSTANCE: About to instantiate CommunicationAgent (using os.getenv based config).", flush=True)
        _communication_agent_instance = CommunicationAgent(
            sending_email_cfg=sending_email_config,      # Pass sending config
            monitoring_email_cfg=monitoring_email_config, # Pass monitoring config
            sms_cfg=sms_cfg_to_use, 
            transcription_cfg=transcription_cfg_to_use, 
            admin_email=os.getenv('ADMIN_EMAIL_ADDRESS'), # Get directly
            task_manager_instance=task_manager_to_use 
        )
    return _communication_agent_instance

@celery_app.task(name='src.celery_app.add')
def add(x, y):
    logger.info(f"Executing add task with arguments: {x}, {y}")
    result = x + y
    logger.info(f"Result of add task: {result}")
    return result

@celery_app.task(name='check_emails_task', ignore_result=True)
def check_secretary_emails_task():
    print("PRINT_DEBUG: \u09af\u09cc\u0997RE-INTRODUCING get_communication_agent_instance() CALL \u09af\u09cc\u0997", flush=True)
    logger.info("Celery task: \u09af\u09cc\u0997RE-INTRODUCING get_communication_agent_instance() CALL \u09af\u09cc\u0997")
    try:
        print("PRINT_DEBUG: \u09af\u09cc\u0997TRY BLOCK ENTERED \u09af\u09cc\u0997", flush=True)
        logger.debug("Attempting to get CommunicationAgent instance...")
        agent = get_communication_agent_instance()
        print(f"PRINT_DEBUG: \u09af\u09cc\u0997CommunicationAgent instance obtained: {type(agent)} \u09af\u09cc\u0997", flush=True)
        logger.info(f"CommunicationAgent instance obtained: {type(agent)}.")
        logger.info("Calling asyncio.run(agent.check_and_process_incoming_tasks()) for last 1 day")
        # Running the async method within the synchronous Celery task
        asyncio.run(agent.check_and_process_incoming_tasks(process_last_n_days=1)) 
        logger.info("Finished asyncio.run(agent.check_and_process_incoming_tasks())")
    except Exception as e:
        print(f"PRINT_DEBUG: \u09af\u09cc\u0997EXCEPTION in check_secretary_emails_task: {e} \u09af\u09cc\u0997", flush=True)
        logger.error(f"Error in check_secretary_emails_task: {e}", exc_info=True)
        raise # Re-raise the exception so Celery can mark the task as failed if needed
    logger.info("Celery task: \u09af\u09cc\u0997FINISHED (after get_communication_agent_instance call) \u09af\u09cc\u0997")

@celery_app.task(name='check_instruction_emails_task', ignore_result=True)
def check_instruction_emails_task_runner(): # Renamed to avoid conflict with a potential future module name
    logger.info("Celery task: \u09af\u09cc\u0997RUNNING check_instruction_emails_task_runner \u09af\u09cc\u0997")
    try:
        agent = get_communication_agent_instance()
        logger.info("Calling agent.check_and_process_instruction_emails() for last 1 day")
        # By default, it checks last 1 day and UNSEEN only, which is good for instructions.
        agent.check_and_process_instruction_emails(process_last_n_days=1) 
        logger.info("Finished agent.check_and_process_instruction_emails()")
    except Exception as e:
        logger.error(f"Error in check_instruction_emails_task_runner: {e}", exc_info=True)
        raise
    logger.info("Celery task: \u09af\u09cc\u0997FINISHED check_instruction_emails_task_runner \u09af\u09cc\u0997")

# Define a periodic task schedule (e.g., run every 5 minutes)
# This schedule will be active if Celery beat is run with this app.
# celery_app.conf.beat_schedule = {
#     'check-secretary-emails-every-1-minute': { # Changed to 1 minute for faster testing feedback
#         'task': 'check_emails_task', # Name is 'check_emails_task'
#         'schedule': crontab(minute='*/1'),  # Run every 1 minute
#     },
#     'check-instruction-emails-every-2-minutes': { 
#         'task': 'check_instruction_emails_task', # This is the name of the task defined above
#         'schedule': crontab(minute='*/2'),  # Run every 2 minutes
#     },
# }

# --- Autonomous Testing Rig (Keep for other tests, but not primary for this interactive one) ---
def run_autonomous_test_suite():
    """Runs a suite of autonomous tests using the MockEmailClient."""
    # This part needs to be aware of the APP_ENV or a specific test config
    # to decide if it should use MockEmailClient.
    # For now, assuming a global USE_MOCK_EMAIL_CLIENT might be set by test setup.
    
    # For current interactive test, USE_MOCK_EMAIL_CLIENT should be False.
    # This suite is likely for unit/integration tests that *do* want mocks.
    current_use_mock = getattr(config, 'USE_MOCK_EMAIL_CLIENT_FOR_AUTONOMOUS_TESTS', False)

    if not current_use_mock: # Check a more specific config flag if available
        logger.error("AUTONOMOUS TESTS with MockEmailClient are not enabled in current config.")
        # print("ERROR: Autonomous tests require USE_MOCK_EMAIL_CLIENT_FOR_AUTONOMOUS_TESTS=True in config/.env")
        return False

    logger.info("Starting Autonomous Test Suite with MockEmailClient...")
    # ... (rest of the autonomous test suite using MockEmailClient)
    # This section would need careful review to ensure it uses a mock client
    # passed in or configured, rather than assuming the global one.
    # For example, it might instantiate its own CommunicationAgent with a MockEmailClient.

    # Simplified for brevity for now.
    print("Autonomous test suite with MockEmailClient would run here if enabled.")
    return True


# Ensure celery_app is aliased as 'app' if the pytest celery commands use -A src.celery_app.app
app = celery_app


if __name__ == '__main__':
    # This allows running the Celery worker directly using:
    # python -m src.celery_app worker -l info -B
    # OR running the test suite (if USE_MOCK_EMAIL_CLIENT is True in .env):
    # python -m src.celery_app test
    import sys
    # import os # os is already imported at the top
    # from dotenv import load_dotenv # Moved to top
    # load_dotenv() # Moved to top
    
    # The debug prints can be removed or commented out now if we are confident
    # print(f"Initial os.getenv('USE_MOCK_EMAIL_CLIENT'): {os.getenv('USE_MOCK_EMAIL_CLIENT')}")
    # dotenv_loaded = load_dotenv() # This would be redundant if already loaded at top
    # print(f"dotenv.load_dotenv() returned: {dotenv_loaded}") 
    # print(f"After load_dotenv(), os.getenv('USE_MOCK_EMAIL_CLIENT'): {os.getenv('USE_MOCK_EMAIL_CLIENT')}")

    # USE_MOCK_EMAIL_CLIENT is directly imported from .config now, no need for FRESH_ alias
    print(f"USE_MOCK_EMAIL_CLIENT from src.config (after top-level load_dotenv): {USE_MOCK_EMAIL_CLIENT}")
    print(f"Type of USE_MOCK_EMAIL_CLIENT: {type(USE_MOCK_EMAIL_CLIENT)}")

    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        if not USE_MOCK_EMAIL_CLIENT: # Use the directly imported one
            print("TEST SUITE ABORTING: USE_MOCK_EMAIL_CLIENT is False or not True.")
            # print(f"Final check - os.getenv('USE_MOCK_EMAIL_CLIENT') before exit: {os.getenv('USE_MOCK_EMAIL_CLIENT')}")
            sys.exit(1)
        run_autonomous_test_suite()
    else:
        # When starting worker, the -l option will also affect log level.
        # The signal handlers above ensure DEBUG for Celery's own loggers.
        celery_app.start() 
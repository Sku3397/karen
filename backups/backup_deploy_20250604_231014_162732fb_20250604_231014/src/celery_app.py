# APP_ENV needs to be known before config is imported, which itself loads .env files.
# So, ensure APP_ENV is set in the environment *before* Celery worker/beat starts.
# The modified config.py will handle loading the correct .env file.

import os # Moved os import higher
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta
import asyncio # Added for asyncio.run
from src.orchestrator import get_orchestrator_instance # Add this import

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

# Import AgentCommunication
from src.agent_communication import AgentCommunication

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

# --- New Agent-Related Tasks ---

# Import for Orchestrator
from .orchestrator import get_orchestrator_instance # Ensure this import is present

# Import SMS tasks
from .celery_sms_tasks import check_sms_task, test_sms_system

@celery_app.task(name='trigger_orchestrator_action_task', bind=True, ignore_result=True)
def trigger_orchestrator_action_task(self, action_name: str = 'check_all_agent_health', params: dict = None):
    """
    Triggers a specified action on the OrchestratorAgent.
    Default action is 'check_all_agent_health'.
    Future actions could include 'execute_workflow' with params.
    """
    task_logger = self.get_logger()
    comm = AgentCommunication('orchestrator_trigger_task') # Use a specific ID for this task's communication
    task_logger.info(f"Executing trigger_orchestrator_action_task for action: {action_name}")

    try:
        comm.update_status('starting_orchestrator_action', 10, {'action': action_name, 'task_id': self.request.id})
        
        orchestrator = get_orchestrator_instance()
        task_logger.info(f"Orchestrator instance obtained: {orchestrator}")

        if action_name == 'check_all_agent_health':
            task_logger.info("Calling orchestrator.check_all_agent_health()")
            health_status = orchestrator.check_all_agent_health()
            task_logger.info(f"Orchestrator check_all_agent_health completed. Status: {health_status}")
            comm.update_status('completed_health_check', 100, {'action': action_name, 'health_status': health_status, 'task_id': self.request.id})
        elif action_name == 'execute_workflow' and params and 'workflow_name' in params:
            workflow_name = params.get('workflow_name')
            workflow_params = params.get('workflow_params', {})
            task_logger.info(f"Calling orchestrator.execute_workflow(workflow_name='{workflow_name}', params={workflow_params})")
            workflow_result = orchestrator.execute_workflow(workflow_name=workflow_name, params=workflow_params)
            task_logger.info(f"Orchestrator execute_workflow completed. Result: {workflow_result}")
            comm.update_status('completed_workflow_execution', 100, {'action': action_name, 'workflow_name': workflow_name, 'result': workflow_result, 'task_id': self.request.id})
        else:
            task_logger.warning(f"Unknown or unsupported action_name: {action_name} or missing params for execute_workflow.")
            comm.update_status('failed_action_not_supported', 100, {'action': action_name, 'error': 'Action not supported or invalid params', 'task_id': self.request.id})
            return

        task_logger.info(f"Successfully executed orchestrator action: {action_name}")

    except Exception as e:
        task_logger.error(f"Error in trigger_orchestrator_action_task for action {action_name}: {e}", exc_info=True)
        comm.update_status('error_in_orchestrator_action', 100, {'action': action_name, 'error': str(e), 'task_id': self.request.id})
        raise # Re-raise for Celery to see it as failed

@celery_app.task(name='archaeologist_periodic_scan_task', bind=True, ignore_result=True)
def archaeologist_periodic_scan_task(self):
    """Code archaeologist agent that maps existing system"""
    task_logger = self.get_logger()
    comm = AgentCommunication('archaeologist')
    task_logger.info("Executing archaeologist_periodic_scan_task: System mapping and analysis.")
    
    try:
        comm.update_status('analyzing', 10, {'phase': 'starting', 'task_id': self.request.id})
        
        messages = comm.read_messages()
        for msg in messages:
            task_logger.info(f"Archaeologist received: {msg.get('type')} from {msg.get('from')} - Content: {msg.get('content')}")

        # TODO: Implement actual archaeologist agent logic
        # Example:
        # archaeologist_instance = get_archaeologist_agent_instance() # Needs to be defined
        # asyncio.run(archaeologist_instance.perform_system_scan())
        task_logger.info("Archaeologist: Performing mock system scan...")
        comm.update_status('analyzing', 50, {'phase': 'scanning filesystem', 'task_id': self.request.id})
        # Simulate work
        import time
        time.sleep(5) # Simulate scan time
        
        comm.share_knowledge('code_patterns', {
            'discovered_by': 'archaeologist',
            'pattern_type': 'error_handling',
            'description': 'try/except with logging via task_logger or module logger',
            'example_location': 'src/celery_app.py'
        })
        comm.share_knowledge('system_info', {
            'celery_version': celery_app.conf.CELERY_VERSION if hasattr(celery_app.conf, 'CELERY_VERSION') else 'unknown',
            'broker_url': celery_app.conf.broker_url,
        })

        comm.send_message('sms_engineer', 'analysis_complete', {
            'patterns_documented': True,
            'templates_created': False, # Mock value
            'report_id': f"archaeology_report_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        })
        
        comm.update_status('completed', 100, {'phase': 'done', 'task_id': self.request.id})
        task_logger.info("Archaeologist: System scan completed and findings shared.")
        print("PRINT_DEBUG: archaeologist_periodic_scan_task executed successfully.", flush=True)

    except Exception as e:
        task_logger.error(f"Error in archaeologist_periodic_scan_task: {e}", exc_info=True)
        comm.update_status('error', 0, {'error': str(e), 'task_id': self.request.id, 'details': 'Failed during periodic scan'})
        # raise # Re-raise if Celery should retry or mark as failure explicitly based on strategy

@celery_app.task(name='sms_event_handler_task', bind=True, ignore_result=True)
def sms_event_handler_task(self, payload: dict):
    """Handles incoming SMS events."""
    task_logger = self.get_logger()
    comm = AgentCommunication('sms_engineer')
    task_logger.info(f"Executing sms_event_handler_task with payload: {payload}")

    try:
        comm.update_status('processing_sms', 10, {'phase': 'received_payload', 'task_id': self.request.id, 'payload_keys': list(payload.keys())})
        
        messages = comm.read_messages()
        for msg in messages:
            task_logger.info(f"SMS Engineer received: {msg.get('type')} from {msg.get('from')} - Content: {msg.get('content')}")
            if msg.get('type') == 'analysis_complete':
                task_logger.info(f"SMS Engineer: Noted analysis complete from {msg.get('from')}")

        # TODO: Implement actual SMS event handling logic using an sms_engineer agent
        # Example:
        # sms_engineer_instance = get_sms_engineer_agent_instance() # Needs to be defined
        # asyncio.run(sms_engineer_instance.process_incoming_sms(payload))
        task_logger.info(f"SMS Engineer: Processing SMS payload: {payload.get('sms_content', 'N/A')}")
        comm.update_status('processing_sms', 70, {'phase': 'generating_reply', 'task_id': self.request.id})
        # Simulate work
        import time
        time.sleep(3)

        # Example: sending a message to another agent or confirming action
        comm.send_message('memory_engineer', 'new_sms_interaction', {
            'sms_payload': payload,
            'status': 'processed_by_sms_engineer'
        })
        
        comm.update_status('completed', 100, {'phase': 'sms_processed', 'task_id': self.request.id})
        task_logger.info(f"SMS Engineer: SMS event processed: {payload.get('message_sid', 'N/A')}")
        print(f"PRINT_DEBUG: sms_event_handler_task executed successfully for payload: {payload}", flush=True)

    except Exception as e:
        task_logger.error(f"Error in sms_event_handler_task: {e}", exc_info=True)
        comm.update_status('error', 0, {'error': str(e), 'task_id': self.request.id, 'payload': payload})
        # raise

@celery_app.task(name='voice_event_handler_task', bind=True, ignore_result=True)
def voice_event_handler_task(self, payload: dict):
    """Handles incoming voice/call events."""
    task_logger = self.get_logger()
    comm = AgentCommunication('phone_engineer')
    task_logger.info(f"Executing voice_event_handler_task with payload: {payload}")

    try:
        comm.update_status('processing_voice', 10, {'phase': 'received_payload', 'task_id': self.request.id, 'call_sid': payload.get('call_sid')})
        
        messages = comm.read_messages()
        for msg in messages:
            task_logger.info(f"Phone Engineer received: {msg.get('type')} from {msg.get('from')} - Content: {msg.get('content')}")

        # TODO: Implement actual voice event handling logic
        # Example:
        # phone_engineer_instance = get_phone_engineer_agent_instance() # Needs to be defined
        # asyncio.run(phone_engineer_instance.process_incoming_voice(payload))
        task_logger.info(f"Phone Engineer: Processing voice payload for call SID: {payload.get('call_sid', 'N/A')}")
        comm.update_status('processing_voice', 70, {'phase': 'transcribing_call', 'task_id': self.request.id})
        import time
        time.sleep(7) # Simulate transcription and processing

        comm.send_message('memory_engineer', 'new_voice_interaction', {
            'voice_payload': payload,
            'transcription_status': 'simulated_success',
            'status': 'processed_by_phone_engineer'
        })

        comm.update_status('completed', 100, {'phase': 'voice_processed', 'task_id': self.request.id})
        task_logger.info(f"Phone Engineer: Voice event processed for call SID: {payload.get('call_sid', 'N/A')}")
        print(f"PRINT_DEBUG: voice_event_handler_task executed successfully for payload: {payload}", flush=True)

    except Exception as e:
        task_logger.error(f"Error in voice_event_handler_task: {e}", exc_info=True)
        comm.update_status('error', 0, {'error': str(e), 'task_id': self.request.id, 'payload': payload})
        # raise

@celery_app.task(name='memory_maintenance_task', bind=True, ignore_result=True)
def memory_maintenance_task(self):
    """Consolidates and manages conversation memory."""
    task_logger = self.get_logger()
    comm = AgentCommunication('memory_engineer')
    task_logger.info("Executing memory_maintenance_task.")

    try:
        comm.update_status('maintenance', 10, {'phase': 'starting_memory_maintenance', 'task_id': self.request.id})
        
        messages = comm.read_messages()
        for msg in messages:
            task_logger.info(f"Memory Engineer received: {msg.get('type')} from {msg.get('from')} - Content: {msg.get('content')}")
            # Example: process new_sms_interaction or new_voice_interaction messages
            if msg.get('type') in ['new_sms_interaction', 'new_voice_interaction']:
                task_logger.info(f"Memory Engineer: Processing {msg.get('type')} from {msg.get('from')}")
                # Add to knowledge base or internal memory structures

        # TODO: Implement actual memory maintenance logic
        # Example:
        # memory_engineer_instance = get_memory_engineer_agent_instance() # Needs to be defined
        # asyncio.run(memory_engineer_instance.perform_maintenance())
        task_logger.info("Memory Engineer: Performing memory consolidation and indexing...")
        comm.update_status('maintenance', 60, {'phase': 'consolidating_data', 'task_id': self.request.id})
        import time
        time.sleep(10) # Simulate maintenance work

        comm.share_knowledge('memory_summary', {
            'last_updated': datetime.now().isoformat(),
            'interactions_processed_in_run': len(messages), # Example metric
            'summary_quality': 'simulated_high'
        })
        
        comm.update_status('completed', 100, {'phase': 'memory_maintenance_done', 'task_id': self.request.id})
        task_logger.info("Memory Engineer: Memory maintenance task completed.")
        print("PRINT_DEBUG: memory_maintenance_task executed successfully.", flush=True)

    except Exception as e:
        task_logger.error(f"Error in memory_maintenance_task: {e}", exc_info=True)
        comm.update_status('error', 0, {'error': str(e), 'task_id': self.request.id})
        # raise

@celery_app.task(name='qa_tests_runner_task', bind=True, ignore_result=True)
def qa_tests_runner_task(self):
    """Runs automated quality assurance tests."""
    task_logger = self.get_logger()
    comm = AgentCommunication('test_engineer')
    task_logger.info("Executing qa_tests_runner_task.")

    try:
        comm.update_status('testing', 10, {'phase': 'initializing_tests', 'task_id': self.request.id})
        
        messages = comm.read_messages()
        for msg in messages:
            task_logger.info(f"Test Engineer received: {msg.get('type')} from {msg.get('from')} - Content: {msg.get('content')}")
            # Could receive triggers or configurations for tests

        # TODO: Implement actual QA test execution logic
        # Example:
        # test_engineer_instance = get_test_engineer_agent_instance() # Needs to be defined
        # asyncio.run(test_engineer_instance.run_all_tests())
        task_logger.info("Test Engineer: Starting test suites...")
        comm.update_status('testing', 50, {'phase': 'running_core_tests', 'task_id': self.request.id})
        import time
        time.sleep(15) # Simulate test execution

        test_results = {'passed': 100, 'failed': 2, 'skipped': 5, 'pass_rate': 100*100/(100+2)} # Mock results
        comm.share_knowledge('test_run_summary', {
            'run_id': f"qa_run_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'results': test_results,
            'coverage': 'simulated_75_percent'
        })
        
        comm.send_message('orchestrator', 'test_results_available', { # Assuming an orchestrator agent
            'summary': test_results,
            'details_link': f"/reports/qa/run_{datetime.now().strftime('%Y%m%d%H%M%S')}.html" # Mock link
        })

        comm.update_status('completed', 100, {'phase': 'qa_tests_done', 'task_id': self.request.id, 'results_summary': test_results})
        task_logger.info("Test Engineer: QA tests completed and results shared.")
        print("PRINT_DEBUG: qa_tests_runner_task executed successfully.", flush=True)

    except Exception as e:
        task_logger.error(f"Error in qa_tests_runner_task: {e}", exc_info=True)
        comm.update_status('error', 0, {'error': str(e), 'task_id': self.request.id})
        # raise

# --- New Monitoring Tasks ---
@celery_app.task(name='monitor_celery_logs_task', ignore_result=True)
def monitor_celery_logs_task():
    logger.info("Executing monitor_celery_logs_task.")
    # TODO: Implement logic to check celery_worker_debug_logs_new.txt and celery_beat_logs_new.txt
    # This could involve checking file size, modification time, or scanning for errors.
    # For simplicity, just logging for now.
    worker_log_path = os.path.join(PROJECT_ROOT_FOR_CELERY, 'celery_worker_debug_logs_new.txt')
    beat_log_path = os.path.join(PROJECT_ROOT_FOR_CELERY, 'celery_beat_logs_new.txt')
    logger.debug(f"Checking Celery worker log: {worker_log_path}")
    logger.debug(f"Checking Celery beat log: {beat_log_path}")
    print(f"PRINT_DEBUG: monitor_celery_logs_task executed. Worker log: {worker_log_path}, Beat log: {beat_log_path}", flush=True)

@celery_app.task(name='monitor_agent_platform_logs_task', ignore_result=True)
def monitor_agent_platform_logs_task():
    logger.info("Executing monitor_agent_platform_logs_task.")
    agent_logs_dir = os.path.join(PROJECT_ROOT_FOR_CELERY, 'multi-agent-logs') # As per user request
    # TODO: Implement logic to check logs in /multi-agent-logs/
    # This could involve checking file counts, sizes, modification times, or scanning for errors.
    logger.debug(f"Checking agent platform logs in: {agent_logs_dir}")
    if not os.path.exists(agent_logs_dir):
        logger.warning(f"Agent logs directory {agent_logs_dir} does not exist.")
    else:
        # Example: list files, check modification times, etc.
        pass
    print(f"PRINT_DEBUG: monitor_agent_platform_logs_task executed for dir: {agent_logs_dir}", flush=True)

@celery_app.task(name='monitor_redis_queues_task', ignore_result=True)
def monitor_redis_queues_task():
    logger.info("Executing monitor_redis_queues_task.")
    try:
        redis_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
        # The redis library is already in requirements.txt
        import redis
        r = redis.from_url(redis_url)
        # Celery default queue is usually 'celery' but can be changed.
        # Check common queues; this might need to be more dynamic based on actual app usage.
        queues_to_check = ['celery'] # Default Celery queue
        # Add other known queues if necessary, e.g., based on task_routes or config.
        # For tasks defined in celery_integration.existing_tasks, if they use specific queues.
        # The orchestrator config mentions "fetch_new_emails", "process_email_with_llm", "send_karen_reply"
        # Assuming they use the default queue for now unless specified otherwise.

        queue_lengths = {}
        for q_name in queues_to_check:
            try:
                length = r.llen(q_name)
                queue_lengths[q_name] = length
                logger.info(f"Redis queue '{q_name}' length: {length}")
            except Exception as e:
                logger.error(f"Error checking Redis queue '{q_name}': {e}", exc_info=True)
        
        if not queue_lengths:
            logger.warning("No Redis queues were checked or an error occurred for all.")

    except ImportError:
        logger.error("Redis library not installed. Cannot monitor Redis queues.")
    except Exception as e:
        logger.error(f"Error connecting to Redis or monitoring queues: {e}", exc_info=True)
    print(f"PRINT_DEBUG: monitor_redis_queues_task executed. Checked: {list(queue_lengths.keys()) if 'queue_lengths' in locals() else 'None'}", flush=True)


@celery_app.task(name='monitor_gmail_api_quota_task', ignore_result=True)
def monitor_gmail_api_quota_task():
    logger.info("Executing monitor_gmail_api_quota_task.")
    # This task serves as a reminder. Actual Gmail API quota monitoring is complex
    # and best handled via Google Cloud Monitoring or specific client library features.
    logger.warning("REMINDER: Periodically check Google Cloud Console for Gmail API quota usage.")
    # Optionally, provide a direct link if known and stable:
    # logger.info("Link to Google Cloud API Quotas: https://console.cloud.google.com/apis/dashboard")
    print("PRINT_DEBUG: monitor_gmail_api_quota_task executed (manual check reminder).", flush=True)

@celery_app.task(name='trigger_orchestrator_action', bind=True)
def trigger_orchestrator_action(self, action='check_health'):
    """Manually trigger orchestrator actions"""
    try:
        orchestrator = get_orchestrator_instance()
        if action == 'check_health':
            orchestrator.check_all_agent_health()
        elif action == 'execute_workflow':
            orchestrator.execute_workflow()
        return f"Orchestrator action '{action}' completed"
    except Exception as e:
        logger.error(f"Orchestrator action failed: {e}")
        raise

# Define a periodic task schedule
celery_app.conf.beat_schedule = {
    # Existing email check tasks (adjust schedules as needed based on actual `email_check_interval`)
    'check-secretary-emails-every-2-minutes': {
        'task': 'check_emails_task', # Name of the task defined earlier
        'schedule': crontab(minute='*/2'),
    },
    'check-instruction-emails-every-5-minutes': {
        'task': 'check_instruction_emails_task', # Name of the task defined earlier
        'schedule': crontab(minute='*/5'),
    },

    # New Agent-Related Periodic Tasks
    'archaeologist-scan-every-6-hours': {
        'task': 'archaeologist_periodic_scan_task',
        'schedule': crontab(minute=0, hour='*/6'), # Every 6 hours
    },
    'memory-maintenance-daily': {
        'task': 'memory_maintenance_task',
        'schedule': crontab(minute=0, hour=3), # Daily at 3:00 AM
    },
    'qa-tests-runner-hourly': {
        'task': 'qa_tests_runner_task',
        'schedule': crontab(minute=30, hour='*'), # Every hour at 30 minutes past the hour
    },

    # SMS Processing Tasks
    'check-sms-every-2-minutes': {
        'task': 'check_sms_task',
        'schedule': crontab(minute='*/2'),  # Every 2 minutes, matching email schedule
    },
    'test-sms-system-daily': {
        'task': 'test_sms_system', 
        'schedule': crontab(hour=9, minute=15),  # Daily at 9:15 AM
    },

    # New Monitoring Periodic Tasks
    'monitor-celery-logs-every-15-mins': {
        'task': 'monitor_celery_logs_task',
        'schedule': crontab(minute='*/15'),
    },
    'monitor-agent-platform-logs-every-17-mins': { # Offset slightly
        'task': 'monitor_agent_platform_logs_task',
        'schedule': crontab(minute='*/17'),
    },
    'monitor-redis-queues-every-10-mins': {
        'task': 'monitor_redis_queues_task',
        'schedule': crontab(minute='*/10'),
    },
    'monitor-gmail-api-quota-every-12-hours': {
        'task': 'monitor_gmail_api_quota_task',
        'schedule': crontab(minute=0, hour='*/12'), # Every 12 hours
    },
}

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
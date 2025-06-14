# Configuration for Orchestrator Agent
import os
from dotenv import load_dotenv
import logging
import time # For timestamping initial log

# --- Enhanced Entry Logging ---
# Get a logger instance specifically for this initial block
_config_initial_logger = logging.getLogger('config_initialization')
_config_initial_logger.setLevel(logging.DEBUG) # Ensure it captures debug
# Basic handler for this very early log, in case root logger isn't configured yet
_temp_handler = logging.StreamHandler()
_temp_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
_config_initial_logger.addHandler(_temp_handler)
_config_initial_logger.info(f"--- src.config.py TOP LEVEL EXECUTION START ({time.time()}) ---")
_config_initial_logger.info(f"Initial os.getcwd(): {os.getcwd()}")
_config_initial_logger.info(f"__file__: {__file__}")
_config_initial_logger.removeHandler(_temp_handler) # Remove temporary handler
# --- End Enhanced Entry Logging ---

# If DJANGO_SETTINGS_MODULE is set, Django needs to be configured before other imports
# that might depend on its settings (like django_celery_beat models indirectly via celery_app)
if os.getenv("DJANGO_SETTINGS_MODULE"):
    try:
        import django
        django.setup()
        logging.getLogger(__name__).info(f"Django settings configured using DJANGO_SETTINGS_MODULE: {os.getenv('DJANGO_SETTINGS_MODULE')}")
    except ImportError:
        logging.getLogger(__name__).warning("DJANGO_SETTINGS_MODULE is set, but Django is not installed. Skipping django.setup().")
    except Exception as e:
        logging.getLogger(__name__).error(f"Error during django.setup(): {e}", exc_info=True)

# Determine which .env file to load
APP_ENV = os.getenv("APP_ENV")
logger = logging.getLogger(__name__)

# Construct the path to the project root directory
# Assuming config.py is in src/, so project root is one level up
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if APP_ENV == "interactive_test":
    dotenv_path = os.path.join(PROJECT_ROOT, '.env.interactive_test')
    logger.info(f"AIHS APP_ENV is 'interactive_test', attempting to load specific .env: {dotenv_path}")
    # First, load .env.interactive_test to get APP_ENV itself and any specific overrides
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path=dotenv_path, override=True)
        logger.info(f"Successfully loaded overrides from: {dotenv_path}")
        # Now, ensure the main .env is also loaded so other variables are available
        # The initial APP_ENV=interactive_test from the system or pytest will ensure this block is run.
        # Then, load the main .env file for all other variables.
        # Variables from .env.interactive_test (like a test-specific CELERY_BROKER_URL if we were using one)
        # would override those from the main .env due to the 'override=True' above.
        # However, given the user's clarification, .env.interactive_test *only* contains APP_ENV.
        # So, we load the main .env for all actual configuration values.
        main_dotenv_path = os.path.join(PROJECT_ROOT, '.env')
        if os.path.exists(main_dotenv_path):
            load_dotenv(dotenv_path=main_dotenv_path, override=False)
            logger.info(f"Successfully loaded main configuration from: {main_dotenv_path} for interactive_test context.")
        else:
            logger.warning(f"Warning: Main .env file not found at {main_dotenv_path} during interactive_test setup.")
    else:
        logger.warning(f"Warning: Interactive test .env file not found at {dotenv_path}. Falling back to default .env loading.")
        # Fallback to loading the main .env if .env.interactive_test is somehow not found
        main_dotenv_path = os.path.join(PROJECT_ROOT, '.env')
        if os.path.exists(main_dotenv_path):
            load_dotenv(dotenv_path=main_dotenv_path)
            logger.info(f"Successfully loaded main configuration from: {main_dotenv_path} (fallback).")
        else:
            logger.warning(f"Warning: Main .env file not found at {main_dotenv_path} (fallback).")
else:
    # Default behavior: load the main .env file
    dotenv_path = os.path.join(PROJECT_ROOT, '.env')
    logger.info(f"AIHS APP_ENV is not 'interactive_test' (value: {APP_ENV}), loading default environment from: {dotenv_path}")
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path=dotenv_path)
        logger.info(f"Successfully loaded default environment from: {dotenv_path}")
    else:
        logger.warning(f"Warning: Default .env file not found at {dotenv_path}")


# Pub/Sub topics for agent communication
PUBSUB_PROJECT_ID = os.getenv('PUBSUB_PROJECT_ID', 'your-gcp-project-id')
ORCHESTRATOR_TOPIC = os.getenv('ORCHESTRATOR_TOPIC', 'orchestrator-commands')
AGENT_TOPICS = {
    'scheduling': os.getenv('SCHEDULING_TOPIC', 'scheduling-requests'),
    'payment': os.getenv('PAYMENT_TOPIC', 'payment-requests'),
    'voice': os.getenv('VOICE_TOPIC', 'voice-requests')
}

# Firestore collection names
FIRESTORE_CLIENT_HISTORY = 'client_history'
FIRESTORE_AGENT_STATE = 'agent_states'
FIRESTORE_WORKFLOWS = 'workflows'

# Email Agent Configuration
SECRETARY_EMAIL_SMTP_SERVER = os.getenv('SECRETARY_EMAIL_SMTP_SERVER')
SECRETARY_EMAIL_SMTP_PORT = int(os.getenv('SECRETARY_EMAIL_SMTP_PORT', 587))
SECRETARY_EMAIL_IMAP_SERVER = os.getenv('SECRETARY_EMAIL_IMAP_SERVER')
SECRETARY_EMAIL_IMAP_PORT = int(os.getenv('SECRETARY_EMAIL_IMAP_PORT', 993))
SECRETARY_EMAIL_ADDRESS = os.getenv('SECRETARY_EMAIL_ADDRESS') # karensecretaryai@gmail.com (for sending test/receiving instructions)
SECRETARY_EMAIL_PASSWORD = os.getenv('SECRETARY_EMAIL_PASSWORD') # Likely unused with OAuth
SECRETARY_TOKEN_PATH_ENV_VAR = os.getenv('SECRETARY_TOKEN_PATH', 'gmail_token_karen.json')
SECRETARY_TOKEN_PATH_CONFIG = os.path.join(PROJECT_ROOT, SECRETARY_TOKEN_PATH_ENV_VAR.split('#')[0].strip()) # Token for karensecretaryai@gmail.com

MONITORED_EMAIL_ACCOUNT_CONFIG = os.getenv('MONITORED_EMAIL_ACCOUNT') # hello@757handy.com (for primary monitoring and sending)
MONITORED_EMAIL_TOKEN_PATH_ENV_VAR = os.getenv('MONITORED_EMAIL_TOKEN_PATH', 'gmail_token_monitor.json')
MONITORED_EMAIL_TOKEN_PATH_CONFIG = os.path.join(PROJECT_ROOT, MONITORED_EMAIL_TOKEN_PATH_ENV_VAR.split('#')[0].strip()) # Token for hello@757handy.com

ADMIN_EMAIL_ADDRESS = os.getenv('ADMIN_EMAIL_ADDRESS')

# Gemini API Key
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# SendGrid API Key (if used for sending, an alternative to direct SMTP)
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')

# Celery Configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND')

# Firebase Admin SDK Key Path
FIREBASE_SERVICE_ACCOUNT_KEY_PATH = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY_PATH')

# Mock client setting (for testing)
USE_MOCK_EMAIL_CLIENT = os.getenv('USE_MOCK_EMAIL_CLIENT', 'False').lower() == 'true'

# Path to the Google OAuth client secrets file (for all Google services ideally)
GOOGLE_APP_CREDENTIALS_PATH = os.getenv('GOOGLE_APP_CREDENTIALS_PATH', 'credentials.json')

# Token path specifically for hello@757handy.com's Google Calendar access
GOOGLE_CALENDAR_TOKEN_PATH = os.getenv('GOOGLE_CALENDAR_TOKEN_PATH_HELLO', 'gmail_token_hello_calendar.json')

# It's good practice to log critical configs if they are missing, or provide fallbacks
if not SECRETARY_EMAIL_ADDRESS:
    logger.error("CRITICAL: SECRETARY_EMAIL_ADDRESS is not set in the environment.")
if not MONITORED_EMAIL_ACCOUNT_CONFIG: # Added check
    logger.error("CRITICAL: MONITORED_EMAIL_ACCOUNT is not set in the environment. Primary email functions will fail.")
if not GEMINI_API_KEY:
    logger.warning("WARNING: GEMINI_API_KEY is not set in the environment. AI features will fail.")
if not CELERY_BROKER_URL:
    logger.warning("WARNING: CELERY_BROKER_URL is not set. Celery tasks may not function.")

if not FIREBASE_SERVICE_ACCOUNT_KEY_PATH:
    logger.warning("WARNING: FIREBASE_SERVICE_ACCOUNT_KEY_PATH is not set in the environment. Firebase Admin SDK might not initialize correctly if GOOGLE_APPLICATION_CREDENTIALS is not set either.")

# For clarity, let's define ADMIN_EMAIL and SECRETARY_EMAIL as requested in the prompt's test script
ADMIN_EMAIL = ADMIN_EMAIL_ADDRESS
SECRETARY_EMAIL = SECRETARY_EMAIL_ADDRESS # This refers to karensecretaryai@gmail.com
PRIMARY_KAREN_EMAIL = MONITORED_EMAIL_ACCOUNT_CONFIG # This will be hello@757handy.com

# Memory System Configuration
USE_MEMORY_SYSTEM = os.getenv('USE_MEMORY_SYSTEM', 'False').lower() == 'true'

# --- Celery Configuration ---
# If True, the main application will not attempt to start Celery worker and beat.
# This is useful if Redis is not available or Celery is managed separately.
SKIP_CELERY_STARTUP = os.getenv("SKIP_CELERY_STARTUP", "True").lower() == "true"

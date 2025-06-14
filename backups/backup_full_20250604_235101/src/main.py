"""
Main FastAPI application for the AI Handyman Secretary Assistant.
Combines all agent functionalities into a unified API.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
from fastapi import APIRouter # Added for clarity if used for mocks
import firebase_admin
from firebase_admin import credentials, firestore
import os
import subprocess # Added for starting Celery worker
import threading # Added for running worker in a separate thread
import sys # Added to get Python executable
import time # Added for sleep in startup for logging clarity
import logging.config # Added for dictionary config

# Attempt to import EmailClient and config
try:
    from .email_client import EmailClient
    from . import config # Use relative import for config within the same package
    EMAIL_SYSTEM_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import EmailClient or config: {e}. Startup email will not be sent.")
    EmailClient = None # type: ignore
    config = None # type: ignore
    EMAIL_SYSTEM_AVAILABLE = False

# Import endpoint routers
# Simplified imports - assuming these modules exist and export a 'router'
try:
    from .endpoints import users, appointments, communications, knowledge, billing, inventory, tasks, memory
except ImportError as e:
    print(f"Warning: Could not import some endpoint modules: {e}. Using mock routers.")
    users = type('MockRouter', (), {'router': APIRouter(tags=["mock"])})()
    appointments = type('MockRouter', (), {'router': APIRouter(tags=["mock"])})()
    communications = type('MockRouter', (), {'router': APIRouter(tags=["mock"])})()
    knowledge = type('MockRouter', (), {'router': APIRouter(tags=["mock"])})()
    billing = type('MockRouter', (), {'router': APIRouter(tags=["mock"])})()
    inventory = type('MockRouter', (), {'router': APIRouter(tags=["mock"])})()
    tasks = type('MockRouter', (), {'router': APIRouter(tags=["mock"])})()
    memory = type('MockRouter', (), {'router': APIRouter(tags=["mock"])})()


# Import the Task Manager Agent's router
try:
    from .task_manager_agent import router as task_manager_router
    TASK_MANAGER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import TaskManagerAgent router: {e}")
    task_manager_router = APIRouter(prefix="/tasks", tags=["tasks_mock"]) # Mock router
    TASK_MANAGER_AVAILABLE = False

# Configure logging
# Use dictionary configuration for more control
logging_config = {
    'version': 1,
    'disable_existing_loggers': False, # Keep existing loggers
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'level': 'DEBUG', # Set console handler level to DEBUG
            'stream': 'ext://sys.stdout', # Explicitly use stdout
        },
        # File handler configuration (optional, based on need)
        # 'file': {
        #     'class': 'logging.FileHandler',
        #     'formatter': 'standard',
        #     'level': 'DEBUG',
        #     'filename': 'application.log',
        # },
    },
    'loggers': {
        '': { # Root logger
            'handlers': ['console'], # Add console handler to root
            'level': 'INFO', # Set root logger level to INFO
            'propagate': True
        },
        'uvicorn': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False # Prevent uvicorn logs from being duplicated by root
        },
        'uvicorn.error': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False
        },
        'src.email_client': { # Explicitly configure email_client logger
            'handlers': ['console'],
            'level': 'DEBUG', # Ensure DEBUG messages from email client are shown
            'propagate': False # Prevent duplication
        }
    },
}

try:
    logging.config.dictConfig(logging_config)
except Exception as e:
    print(f"Error configuring logging: {e}")

logger = logging.getLogger(__name__) # Get logger after config

# Initialize Firebase Admin SDK (if not already initialized)
# Ensure GOOGLE_APPLICATION_CREDENTIALS environment variable is set to the path of your service account key file
try:
    if not firebase_admin._apps:
        if config and config.FIREBASE_SERVICE_ACCOUNT_KEY_PATH:
            cred = credentials.Certificate(config.FIREBASE_SERVICE_ACCOUNT_KEY_PATH)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialized successfully.")
        elif os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            # If path is not in config, try to initialize with default env var
            firebase_admin.initialize_app()
            logger.info("Firebase Admin SDK initialized successfully using GOOGLE_APPLICATION_CREDENTIALS.")
        else:
            logger.warning("Firebase service account key path not found in config and GOOGLE_APPLICATION_CREDENTIALS not set. Firebase Admin SDK not initialized.")
except Exception as e:
    logger.error(f"Failed to initialize Firebase Admin SDK: {e}")


# Create main FastAPI app
app = FastAPI(
    title="AI Handyman Secretary Assistant",
    description="Comprehensive AI assistant for handyman services",
    version="1.0.0"
)

# --- Celery Worker Auto-start ---
celery_worker_process = None
celery_beat_process = None # Added for Celery Beat

def start_celery_worker():
    """Starts the Celery worker in a separate process."""
    global celery_worker_process
    try:
        # Construct the command to run the Celery worker
        # Ensure PYTHONPATH is set correctly if needed, or that src is in Python's path
        # Using sys.executable to ensure the correct Python interpreter is used
        python_executable = sys.executable
        # Assuming celery_app.py is in the 'src' directory and 'src' is in PYTHONPATH
        # or the command is run from the project root.
        # Adding project root to PYTHONPATH explicitly for robustness
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env = os.environ.copy()
        env["PYTHONPATH"] = project_root + os.pathsep + env.get("PYTHONPATH", "")
        
        worker_command = [
            python_executable, "-m", "celery", "-A", "src.celery_app:celery_app", "worker",
            "-l", "INFO", # Or DEBUG
            "--pool=solo", # Necessary on Windows for Celery 5.x
            "--without-heartbeat",
            "--without-gossip",
            "--without-mingle"
        ]
        logger.info(f"Starting Celery worker with command: {' '.join(worker_command)}")
        # For Windows, use creationflags to avoid new console window if desired,
        # but for logging to file, a visible window might not be an issue.
        # subprocess.CREATE_NO_WINDOW (requires import subprocess)
        # Redirect output to a file for the worker as well
        # with open("celery_worker_from_main_logs.txt", "wb") as log_file:
        #     celery_worker_process = subprocess.Popen(worker_command, stdout=log_file, stderr=subprocess.STDOUT, env=env)
        # Don't redirect output to file for now, let it go to console for easier debugging
        celery_worker_process = subprocess.Popen(worker_command, env=env)
        logger.info(f"Celery worker started with PID: {celery_worker_process.pid}")
    except Exception as e:
        logger.error(f"Failed to start Celery worker: {e}", exc_info=True)

def stop_celery_worker():
    """Stops the Celery worker if it's running."""
    global celery_worker_process
    if celery_worker_process:
        logger.info("Stopping Celery worker...")
        celery_worker_process.terminate()
        try:
            celery_worker_process.wait(timeout=10) # Wait for 10 seconds
            logger.info("Celery worker terminated.")
        except subprocess.TimeoutExpired:
            logger.warning("Celery worker did not terminate in time, killing...")
            celery_worker_process.kill()
            logger.info("Celery worker killed.")
        celery_worker_process = None

def start_celery_beat():
    """Starts the Celery Beat scheduler in a separate process."""
    global celery_beat_process
    try:
        python_executable = sys.executable
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env = os.environ.copy()
        env["PYTHONPATH"] = project_root + os.pathsep + env.get("PYTHONPATH", "")
        
        # Using django_celery_beat.schedulers:DatabaseScheduler based on project clues
        # Ensure django_celery_beat is installed (should be in requirements.txt)
        beat_command = [
            python_executable, "-m", "celery", "-A", "src.celery_app:celery_app", "beat",
            "-l", "INFO", # Or DEBUG
            "--scheduler", "django_celery_beat.schedulers:DatabaseScheduler",
            "--pidfile=", # Empty string for pidfile to avoid issues if it's not cleaned up
        ]
        logger.info(f"Starting Celery Beat with command: {' '.join(beat_command)}")
        # Log to a separate file for beat
        # with open("celery_beat_from_main_logs.txt", "wb") as log_file:
        #     celery_beat_process = subprocess.Popen(beat_command, stdout=log_file, stderr=subprocess.STDOUT, env=env)
        # Don't redirect output to file for now, let it go to console for easier debugging
        celery_beat_process = subprocess.Popen(beat_command, env=env)
        logger.info(f"Celery Beat started with PID: {celery_beat_process.pid}")
    except Exception as e:
        logger.error(f"Failed to start Celery Beat: {e}", exc_info=True)

def stop_celery_beat():
    """Stops the Celery Beat scheduler if it's running."""
    global celery_beat_process
    if celery_beat_process:
        logger.info("Stopping Celery Beat...")
        celery_beat_process.terminate()
        try:
            celery_beat_process.wait(timeout=10)
            logger.info("Celery Beat terminated.")
        except subprocess.TimeoutExpired:
            logger.warning("Celery Beat did not terminate in time, killing...")
            celery_beat_process.kill()
            logger.info("Celery Beat killed.")
        celery_beat_process = None
# --- End Celery Worker Auto-start ---


@app.on_event("startup")
async def startup_event():
    # --- TEMPORARY DEBUG PRINT --- # Keep this comment to mark the section
    # All temporary debug lines are removed from here.
    # --- END TEMPORARY DEBUG PRINT ---

    logger.info("Application startup: AI Handyman Secretary Assistant is online.")
    
    # Add a small delay to allow logging to initialize
    time.sleep(2) # Added a small delay
    logger.info("POST-SLEEP: Continuing startup...") # New log

    if not config.SKIP_CELERY_STARTUP:
        # Start Celery Worker
        logger.info("PRE-WORKER-THREAD: Attempting to start Celery worker thread...") # New log
        worker_thread = threading.Thread(target=start_celery_worker, daemon=True)
        worker_thread.start()
        logger.info("POST-WORKER-THREAD: Celery worker thread started.") # New log

        # Start Celery Beat
        logger.info("PRE-BEAT-THREAD: Attempting to start Celery beat thread...") # New log
        beat_thread = threading.Thread(target=start_celery_beat, daemon=True)
        beat_thread.start()
        logger.info("POST-BEAT-THREAD: Celery beat thread started.") # New log
    else:
        logger.info("SKIP_CELERY_STARTUP is True. Celery worker and beat will not be started by main app.")
    
    # --- Add one-time instruction check on startup for the last hour ---
    logger.info("Attempting to schedule one-time instruction email check for the last hour.")
    try:
        # We need a CommunicationAgent instance. This will use get_communication_agent_instance
        # from celery_app, which should be initialized by now or on first call.
        from .celery_app import get_communication_agent_instance as get_agent_for_startup
        
        def run_startup_instruction_check():
            try:
                logger.info("STARTUP TASK: Getting agent instance for instruction check...")
                agent = get_agent_for_startup()
                if agent:
                    logger.info("STARTUP TASK: Agent instance retrieved. Checking instruction emails (newer_than='1h', ignoring UNSEEN status for this check)...")
                    agent.check_and_process_instruction_emails(newer_than_duration="1h", override_search_criteria_for_duration_fetch=True)
                    logger.info("STARTUP TASK: Finished one-time instruction email check for the last hour.")
                else:
                    logger.error("STARTUP TASK: Failed to get CommunicationAgent instance. Cannot check instruction emails.")
            except Exception as e_startup_check:
                logger.error(f"STARTUP TASK: Error during one-time instruction email check: {e_startup_check}", exc_info=True)

        startup_instruction_check_thread = threading.Thread(target=run_startup_instruction_check, daemon=True)
        startup_instruction_check_thread.start()
        logger.info("One-time instruction email check thread started.")

    except ImportError as e_import_agent:
        logger.error(f"Failed to import get_communication_agent_instance for startup check: {e_import_agent}")
    except Exception as e_startup_task_setup:
        logger.error(f"Failed to set up one-time instruction email check: {e_startup_task_setup}")
    # --- End one-time instruction check ---

    # Check for primary email account and its token path for startup notification
    if EMAIL_SYSTEM_AVAILABLE and config and config.ADMIN_EMAIL_ADDRESS and \
       config.MONITORED_EMAIL_ACCOUNT_CONFIG and config.MONITORED_EMAIL_TOKEN_PATH_CONFIG:
        try:
            # Added logging before EmailClient initialization
            logger.info(f"Attempting to initialize EmailClient for monitored account: {config.MONITORED_EMAIL_ACCOUNT_CONFIG}")
            email_client_monitor = EmailClient(
                email_address=config.MONITORED_EMAIL_ACCOUNT_CONFIG, 
                token_file_path=config.MONITORED_EMAIL_TOKEN_PATH_CONFIG
            )
            logger.info(f"EmailClient initialized successfully for monitored account: {config.MONITORED_EMAIL_ACCOUNT_CONFIG}")

            subject = "AI Secretary Online Notification"
            body = f"The AI Handyman Secretary Assistant (monitoring {config.MONITORED_EMAIL_ACCOUNT_CONFIG}) has started and is now online."
            logger.info(f"Attempting to send startup notification email to {config.ADMIN_EMAIL_ADDRESS} from {config.MONITORED_EMAIL_ACCOUNT_CONFIG}")
            email_client_monitor.send_email(
                to=config.ADMIN_EMAIL_ADDRESS,
                subject=subject,
                body=body
            )
            logger.info(f"Startup notification email sent successfully to {config.ADMIN_EMAIL_ADDRESS}.")
        except Exception as e:
            logger.error(f"Failed to send startup email from {config.MONITORED_EMAIL_ACCOUNT_CONFIG}: {e}", exc_info=True) # Log traceback
    else:
        logger.warning("Email system, admin email, or primary monitored account/token path configurations are not fully available. Startup email will not be sent.")

    # --- STARTUP SELF-TEST ---
    if EMAIL_SYSTEM_AVAILABLE and config and \
       config.SECRETARY_EMAIL_ADDRESS and config.SECRETARY_TOKEN_PATH_CONFIG and \
       config.MONITORED_EMAIL_ACCOUNT_CONFIG:
        logger.info("--- Initiating Startup Self-Test Email ---")
        try:
            logger.info(f"Attempting to initialize EmailClient for instruction account (sender for self-test): {config.SECRETARY_EMAIL_ADDRESS}")
            email_client_secretary = EmailClient(
                email_address=config.SECRETARY_EMAIL_ADDRESS,
                token_file_path=config.SECRETARY_TOKEN_PATH_CONFIG
            )
            logger.info(f"EmailClient initialized successfully for instruction account: {config.SECRETARY_EMAIL_ADDRESS}")

            test_subject = "Service Inquiry - Kitchen & Small Roof Repair" # New Subject
            test_body = (                                                  # New Body
                "Hi Beach Handyman,\n\n"
                "I have a couple of questions about your services.\n"
                "1. Do you handle kitchen remodels?\n"
                "2. I also have a small roofing issue, probably less than 50 sq ft. Is that something you can look at?\n"
                "3. Lastly, do you offer free estimates for work?\n\n"
                "Looking forward to your response.\n\n"
                "Thanks,\n"
                "A. Potential Customer"
            )
            
            logger.info(f"Sending self-test email from {config.SECRETARY_EMAIL_ADDRESS} to {config.MONITORED_EMAIL_ACCOUNT_CONFIG} with subject: '{test_subject}'")
            success = email_client_secretary.send_email(
                to=config.MONITORED_EMAIL_ACCOUNT_CONFIG,
                subject=test_subject,
                body=test_body
            )
            if success:
                logger.info(f"Startup self-test email successfully dispatched from {config.SECRETARY_EMAIL_ADDRESS} to {config.MONITORED_EMAIL_ACCOUNT_CONFIG}.")
            else:
                logger.error(f"Failed to send startup self-test email from {config.SECRETARY_EMAIL_ADDRESS} to {config.MONITORED_EMAIL_ACCOUNT_CONFIG}.")

        except Exception as e:
            logger.error(f"Failed to execute startup self-test: Could not initialize EmailClient for {config.SECRETARY_EMAIL_ADDRESS} or send email. Error: {e}", exc_info=True)
    else:
        logger.warning("Startup self-test email not sent. Required configurations (secretary email/token, monitored email) are not fully available.")
    # --- END STARTUP SELF-TEST ---


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown: AI Handyman Secretary Assistant is shutting down.")
    if not config.SKIP_CELERY_STARTUP:
        stop_celery_worker()
        stop_celery_beat()
    else:
        logger.info("SKIP_CELERY_STARTUP is True. Skipping Celery worker and beat shutdown.")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include endpoint routers
app.include_router(users.router, prefix="/api/v1", tags=["users"])
app.include_router(tasks.router, prefix="/api/v1", tags=["tasks"])
app.include_router(appointments.router, prefix="/api/v1", tags=["appointments"])
app.include_router(communications.router, prefix="/api/v1", tags=["communications"])
app.include_router(knowledge.router, prefix="/api/v1", tags=["knowledge"])
app.include_router(billing.router, prefix="/api/v1", tags=["billing"])
app.include_router(inventory.router, prefix="/api/v1", tags=["inventory"])

# Include the Task Manager Agent's router
if TASK_MANAGER_AVAILABLE:
    app.include_router(task_manager_router, prefix="/api/v1") # Prefix already in task_manager_agent's router
else:
    app.include_router(task_manager_router, prefix="/api/v1") # Include mock router

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "AI Handyman Secretary Assistant API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    # Basic health check: returns 200 if the FastAPI app is running
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="debug")
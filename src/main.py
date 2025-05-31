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
    from .endpoints import users, appointments, communications, knowledge, billing, inventory, tasks
except ImportError as e:
    print(f"Warning: Could not import some endpoint modules: {e}. Using mock routers.")
    users = type('MockRouter', (), {'router': APIRouter(tags=["mock"])})()
    appointments = type('MockRouter', (), {'router': APIRouter(tags=["mock"])})()
    communications = type('MockRouter', (), {'router': APIRouter(tags=["mock"])})()
    knowledge = type('MockRouter', (), {'router': APIRouter(tags=["mock"])})()
    billing = type('MockRouter', (), {'router': APIRouter(tags=["mock"])})()
    inventory = type('MockRouter', (), {'router': APIRouter(tags=["mock"])})()
    tasks = type('MockRouter', (), {'router': APIRouter(tags=["mock"])})()


# Import the Task Manager Agent's router
try:
    from .task_manager_agent import router as task_manager_router
    TASK_MANAGER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import TaskManagerAgent router: {e}")
    task_manager_router = APIRouter(prefix="/tasks", tags=["tasks_mock"]) # Mock router
    TASK_MANAGER_AVAILABLE = False


# Configure logging
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# stream_handler = logging.StreamHandler() # Optional: if direct stdout needed before uvicorn
# stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
# logger.addHandler(stream_handler)

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
        with open("celery_worker_from_main_logs.txt", "wb") as log_file:
            celery_worker_process = subprocess.Popen(worker_command, stdout=log_file, stderr=subprocess.STDOUT, env=env)
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
# --- End Celery Worker Auto-start ---


@app.on_event("startup")
async def startup_event():
    logger.info("Application startup: AI Handyman Secretary Assistant is online.")
    
    # Start Celery Worker
    # Run in a separate thread to not block FastAPI startup
    worker_thread = threading.Thread(target=start_celery_worker, daemon=True)
    worker_thread.start()
    
    if EMAIL_SYSTEM_AVAILABLE and config and config.ADMIN_EMAIL_ADDRESS and config.SECRETARY_EMAIL_ADDRESS:
        try:
            email_client = EmailClient(email_address=config.SECRETARY_EMAIL_ADDRESS)
            subject = "AI Secretary Online Notification"
            body = "The AI Handyman Secretary Assistant has started and is now monitoring emails."
            logger.info(f"Attempting to send startup notification email to {config.ADMIN_EMAIL_ADDRESS} from {config.SECRETARY_EMAIL_ADDRESS}")
            email_client.send_email(
                to=config.ADMIN_EMAIL_ADDRESS,
                subject=subject,
                body=body
            )
            logger.info(f"Startup notification email sent successfully to {config.ADMIN_EMAIL_ADDRESS}.")
        except Exception as e:
            logger.error(f"Failed to send startup email: {e}", exc_info=True) # Log traceback
    else:
        logger.warning("Email system or required email configurations are not available. Startup email will not be sent.")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown: AI Handyman Secretary Assistant is shutting down.")
    stop_celery_worker()

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
        "status": "operational",
        "task_manager_available": TASK_MANAGER_AVAILABLE,
        "endpoints": {
            "users": "/api/v1/users",
            "tasks": "/api/v1/tasks" if TASK_MANAGER_AVAILABLE else "/api/v1/tasks_mock",
            "appointments": "/api/v1/appointments",
            "communications": "/api/v1/communications",
            "knowledge": "/api/v1/knowledge",
            "billing": "/api/v1/billing",
            "inventory": "/api/v1/inventory",
            # "task-manager": "/api/v1/task-manager" if AGENTS_AVAILABLE else "unavailable" # Updated
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "AI Handyman Secretary Assistant"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="debug")
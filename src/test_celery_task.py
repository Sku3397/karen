from .celery_app import add
import logging

# Configure basic logging to see output from this script
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info("Attempting to send 'add' task to Celery worker...")
    # Send the task. 
    # .delay() is a shortcut for .apply_async()
    try:
        task_result = add.delay(5, 7)
        logger.info(f"'add' task sent. Task ID: {task_result.id}")
        logger.info("Waiting for result (this might hang if worker is not processing)...")
        # Wait for the result with a timeout
        result = task_result.get(timeout=30) # Wait for 30 seconds
        logger.info(f"Result received: 5 + 7 = {result}")
    except Exception as e:
        logger.error(f"An error occurred while sending or getting task result: {e}", exc_info=True) 
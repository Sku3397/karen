# Retry decorators for transient failure handling
import time
import logging
from functools import wraps
from src.errors import TransientError
from src.logging_config import get_logger

def retry(max_attempts=3, backoff_factor=2, exceptions=(TransientError,)):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            attempt = 0
            delay = 1
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    logger.warning(f"Retry {attempt}/{max_attempts} for {func.__name__} due to: {e}")
                    if attempt == max_attempts:
                        logger.error(f"Max retries reached for {func.__name__}")
                        raise
                    time.sleep(delay)
                    delay *= backoff_factor
        return wrapper
    return decorator

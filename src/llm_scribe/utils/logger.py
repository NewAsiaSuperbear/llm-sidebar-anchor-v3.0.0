import logging
import os
import time
from functools import wraps

from llm_scribe.config import LOG_FILE


def setup_logger():
    """Configures the logging system for the application."""
    log_dir = os.path.dirname(LOG_FILE)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] [%(threadName)s] %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("LLMScribePro")

# Global logger instance
logger = setup_logger()

def perf_log(func):
    """Decorator to measure and log function execution time."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        duration = (end_time - start_time) * 1000 # Convert to ms
        if duration > 10: # Only log if it takes more than 10ms
            logger.info(f"PERF: {func.__name__} took {duration:.2f}ms")
        return result
    return wrapper

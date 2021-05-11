"""
timer.py

 Timer functions for timing LinuxForHealth connect functions.
"""
import logging
import functools
import time
from connect.config import get_settings


logger = logging.getLogger(__name__)


def timer(func):
    """Async decorator to print the elapsed runtime of the decorated function"""

    @functools.wraps(func)
    async def timer_wrapper(*args, **kwargs):
        settings = get_settings()
        if not settings.connect_timing_enabled:
            return

        start_time = time.time()
        result = await func(*args, **kwargs)
        run_time = time.time() - start_time
        logger.trace(f"{func.__name__}() elapsed time = {run_time:.7f}s")
        return result

    return timer_wrapper


def sync_timer(func):
    """Sync decorator to print the elapsed runtime of the decorated function"""

    @functools.wraps(func)
    def timer_wrapper(*args, **kwargs):
        settings = get_settings()
        if not settings.connect_timing_enabled:
            return

        start_time = time.time()
        result = func(*args, **kwargs)
        run_time = time.time() - start_time
        logger.trace(f"{func.__name__}() elapsed time = {run_time:.7f}s")
        return result

    return timer_wrapper

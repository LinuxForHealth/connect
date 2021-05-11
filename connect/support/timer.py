"""
timer.py

 Timer functions for timing LinuxForHealth connect functions.
"""
import inspect
import logging
import functools
import time
from connect.config import get_settings


logger = logging.getLogger(__name__)


def timer(func):
    """Decorator to print the elapsed runtime of the decorated function"""

    @functools.wraps(func)
    async def timer_wrapper(*args, **kwargs):
        settings = get_settings()
        if settings.connect_timing_enabled:
            start_time = time.time()

        if inspect.iscoroutinefunction(func):
            result = await func(*args, **kwargs)
        else:
            result = func(*args, **kwargs)

        if settings.connect_timing_enabled:
            run_time = time.time() - start_time
            logger.trace(f"{func.__name__}() elapsed time = {run_time:.7f}s")
        return result

    return timer_wrapper

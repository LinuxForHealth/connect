"""
timer.py

Timer functions for timing LinuxForHealth connect functions.
"""
import functools
import inspect
import logging
import time


logger = logging.getLogger(__name__)


def timer(func):
    """
    @timer decorator to print the elapsed runtime of the decorated function.

    Whether the function you are decorating is sync or async, you need to await
    the function when you use the @timer decorator.
    """

    @functools.wraps(func)
    async def timer_wrapper(*args, **kwargs):
        start_time = time.time()

        if inspect.iscoroutinefunction(func):
            result = await func(*args, **kwargs)
        else:
            result = func(*args, **kwargs)

        run_time = time.time() - start_time
        logger.trace(f"{func.__name__}() elapsed time = {run_time:.7f}s")
        return result

    return timer_wrapper

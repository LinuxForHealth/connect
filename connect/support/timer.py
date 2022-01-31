"""
timer.py

Timer functions for timing LinuxForHealth connect functions.
"""
import functools
import inspect
import json
import logging
import time
from connect.clients import nats
from connect.config import nats_timing_subject
from connect.support.encoding import ConnectEncoder


logger = logging.getLogger(__name__)


def timer(func):
    """
    @timer decorator to print the elapsed run time of the decorated function.

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

        js = await nats.get_jetstream_context()
        message = {"function": func.__name__, "elapsed_time": run_time}
        msg_str = json.dumps(message, cls=ConnectEncoder)
        await js.publish(nats_timing_subject, bytearray(msg_str, "utf-8"))

        return result

    return timer_wrapper

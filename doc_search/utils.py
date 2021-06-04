import functools
from typing import Optional, List, Tuple
from asyncio import get_running_loop, AbstractEventLoop

RESULTS = List[Tuple[str, str]]

def executor(loop: Optional[AbstractEventLoop] = None, executor=None):

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            partial = functools.partial(func, *args, **kwargs)
            loop = get_running_loop()
            return loop.run_in_executor(executor, partial)

        return wrapper
    return decorator

class RequestError(Exception):
    pass
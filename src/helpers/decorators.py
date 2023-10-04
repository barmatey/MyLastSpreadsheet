import time
import typing
from functools import wraps

from loguru import logger

T = typing.TypeVar("T")


def singleton(class_: T) -> T:
    instances = {}

    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return getinstance


def timeit(func):
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        logger.success(f'function {func.__name__} took {total_time * 1000:.0f}ms')
        return result

    return timeit_wrapper

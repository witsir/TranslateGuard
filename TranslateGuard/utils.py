import logging
import random
import time
from typing import Callable


from .base_exceptions import ErrorMsg, RetryException

logger = logging.getLogger(__name__)


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


def retry(
        func: Callable,
        e_type_list: list[ErrorMsg],
        initial_delay: float = 1,
        exponential_base: float = 2,
        jitter: bool = True,
        max_retries: int = 3
):
    """Retry a function with exponential backoff."""

    def wrapper(*args, **kwargs):
        # Initialize variables
        num_retries = 0
        delay = initial_delay
        type_list = tuple(e_type_list)
        # Loop until a successful response or max_retries is hit or an exception is raised
        while True:
            try:
                return func(*args, **kwargs)

            # Retry on specified errors
            except Exception as e:
                if e.error_type in type_list:
                    logger.warning(e)
                    num_retries += 1
                    if num_retries > max_retries:
                        logger.error(ErrorMsg.RetryError)
                        raise e
                    delay *= exponential_base * (1 + jitter * random.random())

                    time.sleep(delay)
                else:
                    raise RetryException(ErrorMsg.RetryError)
    return wrapper

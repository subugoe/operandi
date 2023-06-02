from ocrd_utils import initLogging


__all__ = [
    "safe_init_logging"
]

logging_initialized = False


def safe_init_logging() -> None:
    """
    wrapper around ocrd_utils.initLogging. It assures that ocrd_utils.initLogging is only called
    once. This function may be called multiple times
    """
    global logging_initialized
    if not logging_initialized:
        logging_initialized = True
        initLogging()

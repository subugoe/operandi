"""
Based on:
https://pawamoy.github.io/posts/unify-logging-for-a-gunicorn-uvicorn-app/
"""

from datetime import datetime
import logging
import loguru
import sys
from os import environ
from os.path import join
from pathlib import Path


__all__ = [
    "reconfigure_all_loggers",
    "get_log_file_path_prefix"
]


class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = loguru.logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where the logged message originated
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        loguru.logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def reconfigure_all_loggers(log_level: str, log_file_path: str):
    # Intercept everything at the root logger
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(logging.getLevelName(log_level))

    # Remove other loggers' handlers and propagate logs to root logger
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    loguru.logger.configure(
        handlers=[
            {"sink": sys.stdout},
            {"sink": log_file_path, "serialize": False}
        ]
    )


# Returns log path for the modules, if module is worker, returns prefix for logging
def get_log_file_path_prefix(module_type: str) -> str:
    modules_types = ["server", "harvester", "broker", "worker"]
    if module_type not in modules_types:
        raise ValueError(f"Unknown module type: {module_type}, should be one of {modules_types}")

    logging_rood_dir: str = environ.get("OPERANDI_LOGS_DIR", None)
    if not logging_rood_dir:
        raise ValueError("Environment variable not set: OPERANDI_LOGS_DIR")
    Path(logging_rood_dir).mkdir(mode=0o777, parents=True, exist_ok=True)
    # Path(logging_rood_dir).chmod(mode=0o777)

    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M")
    log_file_path_prefix = join(logging_rood_dir, f"{module_type}_{current_time}")
    return log_file_path_prefix

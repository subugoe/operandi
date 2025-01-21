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
from .constants import MODULE_TYPES


__all__ = [
    "get_log_file_path_prefix",
    "reconfigure_all_loggers"
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
        print(f"Resetting handlers, propagation True, reconfiguring the logger: {name}")
        current_logger = logging.getLogger(name)
        if "pika" in current_logger.name or "paramiko" in current_logger.name or "ocrd" in current_logger.name:
            print(f"Setting log level to WARNING of: {name}")
            current_logger.setLevel(level="WARNING")
        current_logger.handlers = []
        current_logger.propagate = True
    handlers = [
        {"sink": sys.stdout},
        {"sink": log_file_path, "serialize": False}
    ]
    print(f"Configured new handlers: {handlers}")
    loguru.logger.configure(handlers=handlers)


# Returns log path for the modules, if module is worker, returns prefix for logging
def get_log_file_path_prefix(module_type: str) -> str:
    if module_type not in MODULE_TYPES:
        raise ValueError(f"Unknown module type '{module_type}', should be one of '{MODULE_TYPES}'")
    logging_rood_dir: str = environ.get("OPERANDI_LOGS_DIR", None)
    if not logging_rood_dir:
        raise ValueError("Environment variable not set: OPERANDI_LOGS_DIR")
    Path(logging_rood_dir).mkdir(mode=0o777, parents=True, exist_ok=True)
    # Path(logging_rood_dir).chmod(mode=0o777)
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M")
    log_file_path_prefix = join(logging_rood_dir, f"{module_type}_{current_time}")
    return log_file_path_prefix

"""
Based on:
https://pawamoy.github.io/posts/unify-logging-for-a-gunicorn-uvicorn-app/
"""

import logging
import loguru
import sys


__all__ = [
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
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    loguru.logger.configure(
        handlers=[
            {"sink": sys.stdout},
            {"sink": log_file_path, "serialize": False}
        ]
    )

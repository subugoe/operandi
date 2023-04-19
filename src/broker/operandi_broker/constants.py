from datetime import datetime
from operandi_utils import (
    OPERANDI_LOGS_DIR
)

__all__ = [
    "LOG_LEVEL_BROKER",
    "LOG_LEVEL_WORKER",
    "LOG_FILE_PATH_BROKER",
    "LOG_FILE_PATH_WORKER"
]

LOG_LEVEL_BROKER: str = "INFO"
LOG_LEVEL_WORKER: str = "INFO"

current_time = datetime.now().strftime("%Y-%m-%d_%H-%M")
LOG_FILE_PATH_BROKER: str = f"{OPERANDI_LOGS_DIR}/broker_{current_time}.log"
LOG_FILE_PATH_WORKER: str = f"{OPERANDI_LOGS_DIR}/worker_{current_time}.log"

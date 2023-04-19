from datetime import datetime
from operandi_utils import OPERANDI_LOGS_DIR

__all__ = [
    "LOG_FILE_PATH",
    "LOG_LEVEL"
]

current_time = datetime.now().strftime("%Y-%m-%d_%H-%M")
LOG_FILE_PATH: str = f"{OPERANDI_LOGS_DIR}/server_{current_time}.log"
LOG_LEVEL: str = "INFO"

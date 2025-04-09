from logging import Logger
from operandi_utils import is_url_responsive


def check_server_responsiveness(logger: Logger, server_address: str):
    if not is_url_responsive(server_address):
        msg = f"The Operandi Server is not responding: {server_address}"
        logger.error(msg)
        raise ConnectionError(msg)

from os import environ

__all__ = [
    "OPERANDI_DB_NAME",
    "OPERANDI_DB_URL"
]

OPERANDI_DB_NAME: str = environ.get("OPERANDI_DB_NAME", "operandi_db")
OPERANDI_DB_URL: str = environ.get("OPERANDI_DB_URL")

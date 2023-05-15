from dotenv import load_dotenv
from os import getenv

__all__ = [
    'DB_NAME',
    'DB_URL'
]

load_dotenv()

DB_URL: str = getenv("OCRD_WEBAPI_DB_URL", "mongodb://localhost:27018")
DB_NAME: str = getenv("OCRD_WEBAPI_DB_NAME", "operandi-db")

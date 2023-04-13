from os import environ

__all__ = [
    "OCRD_WEBAPI_PASSWORD",
    "OCRD_WEBAPI_USERNAME"
]

OCRD_WEBAPI_USERNAME = environ.get("OCRD_WEBAPI_USERNAME", "test")
OCRD_WEBAPI_PASSWORD = environ.get("OCRD_WEBAPI_PASSWORD", "test")

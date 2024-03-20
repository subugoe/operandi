from os import environ
from requests import get as requests_get

OPERANDI_SERVER_URL = environ.get("OPERANDI_SERVER_URL")


def test_get_root_info():
    response = requests_get(f"{OPERANDI_SERVER_URL}/")
    assert response.status_code == 200
    assert response.json()["message"] == "The home page of the OPERANDI Server"

"""
def test_get_root_info(operandi):
    response = operandi.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "The home page of the OPERANDI Server"
"""
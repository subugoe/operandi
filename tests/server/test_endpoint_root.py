

def test_get_root_info(operandi_client):
    response = operandi_client.get('/')
    assert response.status_code == 200, "The status code is not 200"
    json = response.json()
    assert json['message'] == "The home page of the OPERANDI Server"

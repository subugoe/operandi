from pytest import mark
from .helpers_asserts import assert_response_status_code


@mark.asyncio
async def test_get_root_info(operandi):
    response = await operandi.get('/')
    assert_response_status_code(response.status_code, expected_floor=2)
    assert response.json()['message'] == "The home page of the OPERANDI Server"

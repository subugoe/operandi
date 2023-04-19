from requests import get


def is_url_responsive(url: str) -> bool:
    try:
        response = get(url, stream=True)
        if response.status_code // 100 == 2:
            return True
    except Exception as e:
        return False

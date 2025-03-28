from requests import post as requests_post

def send_bag_to_ola_hd(path_to_bag, username, password, endpoint) -> str:
    ola_hd_files = {"file": open(path_to_bag, "rb")}
    ola_hd_auth = (username, password)
    ola_hd_response = requests_post(url=endpoint, files=ola_hd_files, auth=ola_hd_auth)
    if ola_hd_response.status_code >= 400:
        ola_hd_response.raise_for_status()
    return ola_hd_response.json()["pid"]

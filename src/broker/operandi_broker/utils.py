import os
import requests
from clint.textui import progress


# Further simplifications possible
def download_mets_file(mets_url, ocrd_workspace_dir):
    if not os.path.exists(ocrd_workspace_dir):
        os.makedirs(ocrd_workspace_dir)
    filename = f"{ocrd_workspace_dir}/mets.xml"

    try:
        response = requests.get(mets_url, stream=True)
        if response.status_code == 200:
            with open(filename, 'wb') as file:
                # Unfortunately the responses from GDZ does not
                # contain content-length information in the response
                # header. The line below is a "bad" hack to find the
                # size of the mets file
                length = response.content.__sizeof__() - 33
                size = (length / 512) + 1
                # TODO: The progress bar is not working as expected
                # TODO: Consider to remove it completely
                for chunk in progress.bar(response.iter_content(chunk_size=512), expected_size=size):
                    if chunk:
                        file.write(chunk)
                        file.flush()
            return True
    except requests.exceptions.RequestException as e:
        return False


# TODO: Conceptual implementation, not tested in any way yet
def send_bag_to_ola_hd(path_to_bag) -> str:
    # Ola-HD dev instance,
    # available only when connected to GOENET
    url = 'http://141.5.99.53/api/bag'
    files = {'file': open(path_to_bag, 'rb')}
    params = {'isGt': False}
    # The credentials here are already publicly available inside the ola-hd repo
    # Ignore docker warnings about exposed credentials
    ola_hd_response = requests.post(url, files=files, data=params, auth=("admin", "JW24G.xR"))
    if ola_hd_response.status_code >= 400:
        ola_hd_response.raise_for_status()
    return ola_hd_response.json()['pid']

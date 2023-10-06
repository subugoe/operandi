
def test_post_workspace_zip(harvester, path_workspace1):
    workspace_id = harvester.post_workspace_zip(ocrd_zip_path=path_workspace1)
    assert workspace_id


def test_post_workspace_url(harvester):
    mets_url = "https://content.staatsbibliothek-berlin.de/dc/PPN631277528.mets.xml"
    file_grp = "DEFAULT"
    workspace_id = harvester.post_workspace_url(mets_url=mets_url, file_grp=file_grp)
    assert workspace_id

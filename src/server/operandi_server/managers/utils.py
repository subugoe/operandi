import bagit
from tempfile import NamedTemporaryFile
from uuid import uuid4
from zipfile import ZipFile

from ocrd import Resolver
from ocrd.workspace_bagger import WorkspaceBagger
from ocrd_validators.ocrd_zip_validator import OcrdZipValidator
from operandi_server.exceptions import WorkspaceNotValidException

__all__ = [
    "extract_bag_info",
    "generate_id",
    "validate_bag"
]


def generate_id(file_ext: str = None):
    # TODO: We should consider using
    #  uuid1 or uuid3 in the future
    # Generate a random ID (uuid4)
    generated_id = str(uuid4())
    if file_ext:
        generated_id += file_ext
    return generated_id


def extract_bag_info(bag_dest, workspace_dir) -> dict:
    workspace_bagger = WorkspaceBagger(Resolver())
    workspace_bagger.spill(bag_dest, workspace_dir)

    # TODO: work is done twice here: spill already extracts the bag-info.txt but throws it away.
    #  maybe workspace_bagger.spill can be changed to deliver the bag-info.txt here
    with ZipFile(bag_dest, 'r') as zip_fp:
        bag_info_bytes = zip_fp.read("bag-info.txt")
        with NamedTemporaryFile() as tmp_file:
            with open(tmp_file.name, 'wb') as f:
                f.write(bag_info_bytes)
            bag_info = bagit._load_tag_file(tmp_file.name)
    return bag_info


def validate_bag(bag_dest: str):
    try:
        valid_report = OcrdZipValidator(
            Resolver(),
            bag_dest
        ).validate(processes=1)
    except Exception as e:
        raise WorkspaceNotValidException(f"Error during workspace validation: {str(e)}") from e
    if valid_report and not valid_report.is_valid:
        raise WorkspaceNotValidException(valid_report.to_xml())

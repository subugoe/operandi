from ocrd_utils import initLogging

import bagit
from tempfile import NamedTemporaryFile
from typing import Union
from uuid import uuid4
from zipfile import ZipFile

from ocrd import Resolver
from ocrd.workspace import Workspace
from ocrd.workspace_bagger import WorkspaceBagger
from ocrd_validators.ocrd_zip_validator import OcrdZipValidator
from operandi_server.exceptions import WorkspaceNotValidException
from .constants import DEFAULT_METS_BASENAME

__all__ = [
    "extract_bag_info",
    "generate_id",
    "get_workspace_bag",
    "safe_init_logging",
    "validate_bag"
]

logging_initialized = False


def safe_init_logging() -> None:
    """
    wrapper around ocrd_utils.initLogging. It assures that ocrd_utils.initLogging is only called
    once. This function may be called multiple times
    """
    global logging_initialized
    if not logging_initialized:
        logging_initialized = True
        initLogging()


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


# TODO: Refine this and get rid of the low level os.path bullshits
def get_workspace_bag(db_workspace) -> Union[str, None]:
    """
    Create workspace bag.

    The resulting zip is stored in the workspaces' directory (`self._resource_dir`).
    The Workspace could have been changed so recreation of bag-files is necessary.
    Simply zipping is not sufficient.

    Args:
         db_workspace (DBWorkspace): database model of the workspace
    Returns:
        path to created bag
    """
    bag_dest = f"{db_workspace.workspace_dir}.zip"
    mets_basename = db_workspace.mets_basename
    if not mets_basename:
        mets_basename = DEFAULT_METS_BASENAME
    resolver = Resolver()
    WorkspaceBagger(resolver).bag(
        Workspace(
            resolver,
            directory=db_workspace.workspace_dir,
            mets_basename=mets_basename
        ),
        ocrd_identifier=db_workspace.ocrd_identifier,
        dest=bag_dest,
        ocrd_mets=mets_basename,
        # This must be 1, crashes for higher values
        processes=1
    )
    return bag_dest

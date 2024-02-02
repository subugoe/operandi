import bagit
from tempfile import NamedTemporaryFile
from typing import List, Union
from uuid import uuid4
from zipfile import ZipFile

from ocrd import Resolver
from ocrd.workspace import Workspace
from ocrd.workspace_bagger import WorkspaceBagger
from ocrd_utils import initLogging
from ocrd_validators.ocrd_zip_validator import OcrdZipValidator
from operandi_server.constants import DEFAULT_FILE_GRP, DEFAULT_METS_BASENAME
from operandi_server.exceptions import WorkspaceNotValidException


__all__ = [
    "create_workspace_bag_from_remote_url",
    "extract_bag_info",
    "generate_id",
    "get_ocrd_workspace_physical_pages",
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
    generated_id = str(uuid4())
    if file_ext:
        generated_id += file_ext
    return generated_id


def extract_bag_info(bag_dest, workspace_dir) -> dict:
    workspace_bagger = WorkspaceBagger(Resolver())
    workspace_bagger.spill(bag_dest, workspace_dir)

    # TODO: work is done twice here: spill already extracts the bag-info.txt but throws it away.
    #  maybe workspace_bagger.spill can be changed to deliver the bag-info.txt here
    with ZipFile(bag_dest, mode='r') as zip_fp:
        bag_info_bytes = zip_fp.read("bag-info.txt")
        with NamedTemporaryFile() as tmp_file:
            with open(tmp_file.name, mode="wb") as f:
                f.write(bag_info_bytes)
            bag_info = bagit._load_tag_file(tmp_file.name)
    return bag_info


def validate_bag(bag_dest: str):
    try:
        # Warning: do not set processes to a higher value than 1, it would crash the Uvicorn internals
        valid_report = OcrdZipValidator(Resolver(), bag_dest).validate(processes=1)
    except Exception as e:
        raise WorkspaceNotValidException(f"Error during workspace validation: {str(e)}") from e
    if valid_report and not valid_report.is_valid:
        raise WorkspaceNotValidException(valid_report.to_xml())


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
        # Warning: do not set processes to a higher value than 1, it would crash the Uvicorn internals
        processes=1
    )
    return bag_dest


def create_workspace_bag_from_remote_url(
    mets_url: str,
    workspace_id: str,
    bag_dest: str,
    mets_basename: str = DEFAULT_METS_BASENAME,
    preserve_file_grps: List[str] = None
) -> str:
    if not preserve_file_grps:
        preserve_file_grps = [DEFAULT_FILE_GRP]

    resolver = Resolver()
    # Create an OCR-D Workspace from a remote mets URL
    # without downloading the files referenced in the mets file
    workspace = resolver.workspace_from_url(
        mets_url=mets_url,
        clobber_mets=False,
        mets_basename=mets_basename,
        download=False
    )

    remove_groups = [x for x in workspace.mets.file_groups if x not in preserve_file_grps]
    for group in remove_groups:
        workspace.remove_file_group(group, recursive=True, force=True)
    workspace.save_mets()
    ws_files = workspace.find_files()
    for ws_file in ws_files:
        workspace.download_file(f=ws_file)

    # Resolves and downloads all file groups and files in the mets file
    WorkspaceBagger(resolver).bag(
        workspace,
        dest=bag_dest,
        ocrd_identifier=workspace_id,
        # Warning: do not set processes to a higher value than 1, it would crash the Uvicorn internals
        processes=1
    )
    return workspace.directory


def get_ocrd_workspace_physical_pages(mets_path: str) -> List[str]:
    return Resolver().workspace_from_url(mets_url=mets_path).mets.physical_pages

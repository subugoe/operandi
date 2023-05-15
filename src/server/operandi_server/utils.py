from os.path import join
from pathlib import Path
from typing import Union
import bagit
import tempfile
import uuid
import zipfile

from ocrd import Resolver
from ocrd.workspace import Workspace
from ocrd.workspace_bagger import WorkspaceBagger
from ocrd_utils import initLogging
from ocrd_validators.ocrd_zip_validator import OcrdZipValidator

from .constants import SERVER_URL
from .exceptions import WorkspaceNotValidException

__all__ = [
    "bagit_from_url",
    "extract_bag_dest",
    "extract_bag_info",
    "find_upwards",
    "generate_id",
    "read_bag_info_from_zip",
    "safe_init_logging"
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


# TODO: This is not used anymore, keeping still around for reference
def to_processor_job_url(processor_name: str, job_id: str) -> str:
    """
    create the url where the processor job is available e.g. http://localhost:8000/processor/ocrd-dummy/{job_id}

    does not verify that the processor or/and the processor-job exists
    """
    return f"{SERVER_URL}/processor/{processor_name}/{job_id}"


def extract_bag_info(zip_dest, workspace_dir) -> dict:
    try:
        resolver = Resolver()
        valid_report = OcrdZipValidator(resolver, zip_dest).validate(processes=1)
    except Exception as e:
        raise WorkspaceNotValidException(f"Error during workspace validation: {str(e)}") from e

    if valid_report is not None and not valid_report.is_valid:
        raise WorkspaceNotValidException(valid_report.to_xml())

    workspace_bagger = WorkspaceBagger(resolver)
    workspace_bagger.spill(zip_dest, workspace_dir)

    # TODO: work is done twice here: spill already extracts the bag-info.txt but throws it away.
    # maybe workspace_bagger.spill can be changed to deliver the bag-info.txt here
    bag_info = read_bag_info_from_zip(zip_dest)

    return bag_info


def extract_bag_dest(workspace_db, workspace_dir, bag_dest) -> None:
    mets = workspace_db.ocrd_mets or "mets.xml"
    identifier = workspace_db.ocrd_identifier
    resolver = Resolver()
    WorkspaceBagger(resolver).bag(
        Workspace(resolver, directory=workspace_dir, mets_basename=mets),
        dest=bag_dest,
        ocrd_identifier=identifier,
        ocrd_mets=mets,
    )


def generate_id(file_ext=None):
    # TODO: We should consider using
    #  uuid1 or uuid3 in the future
    # Generate a random ID (uuid4)
    generated_id = str(uuid.uuid4())
    if file_ext:
        generated_id += file_ext
    return generated_id


def read_bag_info_from_zip(path_to_zip) -> dict:
    """
    Extracts bag-info.txt from bagit-file and turns it into a dict

    Args:
        path_to_zip: path to bagit-file

    Returns:
        bag-info.txt from bagit as a dict
    """
    with zipfile.ZipFile(path_to_zip, 'r') as z:
        bag_info_bytes = z.read("bag-info.txt")
        with tempfile.NamedTemporaryFile() as tmp:
            with open(tmp.name, 'wb') as f:
                f.write(bag_info_bytes)
            return bagit._load_tag_file(tmp.name)


def find_upwards(filename, cwd: Path = None) -> Union[Path, None]:
    """
    search in current directory and all directories above for 'filename'
    """
    if cwd is None:
        cwd = Path.cwd()
    if cwd == Path(cwd.root) or cwd == cwd.parent:
        return None

    fullpath = cwd / filename
    return fullpath if fullpath.exists() else find_upwards(filename, cwd.parent)


# TODO: Provide separate functions for the steps below
def bagit_from_url(mets_url, mets_basename="mets.xml", dest=None, file_grp=None, ocrd_identifier=None):
    """
    Create OCRD-ZIP from a mets-URL.

    1. Downloads the mets file from the mets_url
    2. Downloads all files for the provided file_grp/s
    3. Creates an OCRD-ZIP

    Args:
        mets_url:                   url to a mets file
        mets_basename: (optional):  under which name is the downloaded mets saved
        dest: (optional):           parent directory of the mets file and the OCRD-ZIP file
        file_grp (optional):        file groups to download, downloads everything if not set
        ocrd_identifier (optional): Value for key 'Ocrd-Identifier' in bag-info.txt of created bag

    Returns:
        Path of the created zip bag
    """
    if dest is None:
        dest = "/tmp/ocrd_webapi_bags"
    if ocrd_identifier is None:
        ocrd_identifier = f"ocrd-{generate_id()}"

    bag_dest = join(dest, f"{ocrd_identifier}.zip")
    resolver = Resolver()
    # Create an OCR-D Workspace from a mets URL
    # without downloading the files referenced in the mets file
    workspace = resolver.workspace_from_url(mets_url,
                                            dest,
                                            clobber_mets=False,
                                            mets_basename=mets_basename,
                                            download=False)

    if file_grp:
        # Remove unnecessary file groups from the mets file to reduce the size
        remove_groups = [x for x in workspace.mets.file_groups if x not in file_grp]
        for g in remove_groups:
            workspace.remove_file_group(g, recursive=True, force=True)
        workspace.save_mets()

    # The ocrd workspace bagger automatically downloads the files/groups
    WorkspaceBagger(resolver).bag(workspace, dest=bag_dest, ocrd_identifier=ocrd_identifier)

    return bag_dest

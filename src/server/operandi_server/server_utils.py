from logging import Logger
from os import environ
from os.path import join
from pathlib import Path
from shutil import copyfile
from typing import List

from operandi_utils import get_nf_wfs_dir, get_ocrd_process_wfs_dir
from operandi_utils.constants import AccountType
from operandi_utils.database import db_create_workflow
from operandi_utils.oton import OTONConverter
from operandi_server.files_manager import LFMInstance
from operandi_server.routers.user_utils import create_user_if_not_available
from operandi_server.routers.workflow_utils import nf_script_extract_metadata_with_handling


async def insert_default_accounts(logger: Logger):
    default_admin_user = environ.get("OPERANDI_SERVER_DEFAULT_USERNAME", None)
    default_admin_pass = environ.get("OPERANDI_SERVER_DEFAULT_PASSWORD", None)
    default_harvester_user = environ.get("OPERANDI_HARVESTER_DEFAULT_USERNAME", None)
    default_harvester_pass = environ.get("OPERANDI_HARVESTER_DEFAULT_PASSWORD", None)

    logger.info(f"Configuring default server admin account")
    if default_admin_user and default_admin_pass:
        await create_user_if_not_available(
            logger,
            username=default_admin_user,
            password=default_admin_pass,
            account_type=AccountType.ADMIN,
            institution_id="GWDG Goettingen",
            approved_user=True,
            details="Default admin account"
        )
        logger.info(f"Inserted default server account credentials")

    logger.info(f"Configuring default harvester account")
    if default_harvester_user and default_harvester_pass:
        await create_user_if_not_available(
            logger,
            username=default_harvester_user,
            password=default_harvester_pass,
            account_type=AccountType.HARVESTER,
            institution_id="SUB Goettingen",
            approved_user=True,
            details="Default harvester account"
        )
        logger.info(f"Inserted default harvester account credentials")

async def produce_production_workflows(
    logger: Logger,
    ocrd_process_wf_dir: Path = get_ocrd_process_wfs_dir(),
    production_nf_wfs_dir: Path = get_nf_wfs_dir()
):
    oton_converter = OTONConverter()
    for path in ocrd_process_wf_dir.iterdir():
        if not path.is_file():
            logger.info(f"Skipping non-file path: {path}")
            continue
        if path.suffix != '.txt':
            logger.info(f"Skipping non .txt extension file path: {path}")
            continue
        # path.stem -> file_name
        # path.name -> file_name.ext
        logger.info(f"Converting to Nextflow workflow the ocrd process workflow: {path}")
        output_path = Path(production_nf_wfs_dir, f"{path.stem}.nf")
        oton_converter.convert_oton(
            input_path=path, output_path=str(output_path), environment="apptainer", with_mets_server=False)
        logger.info(f"Converted to a Nextflow file without a mets server: {output_path}")
        output_path = Path(production_nf_wfs_dir, f"{path.stem}_with_MS.nf")
        oton_converter.convert_oton(
            input_path=path, output_path=str(output_path), environment="apptainer", with_mets_server=True)
        logger.info(f"Converted to a Nextflow file with a mets server: {output_path}")

async def insert_production_workflows(
    logger: Logger,
    production_nf_wfs_dir: Path = get_nf_wfs_dir()
) -> List[str]:
    wf_detail = "Workflow provided by the Operandi Server"
    logger.info(f"Inserting production workflows for Operandi from: {production_nf_wfs_dir}")
    production_workflows = []
    for path in production_nf_wfs_dir.iterdir():
        if not path.is_file():
            logger.info(f"Skipping non-file path: {path}")
            continue
        if path.suffix != '.nf':
            logger.info(f"Skipping non .nf extension file path: {path}")
            continue
        # path.stem -> file_name
        # path.name -> file_name.ext
        workflow_id, workflow_dir = LFMInstance.make_dir_workflow(workflow_id=path.stem, exists_ok=True)
        nf_script_dest = str(join(workflow_dir, path.name))
        copyfile(src=path, dst=nf_script_dest)
        nf_metadata = await nf_script_extract_metadata_with_handling(logger, nf_script_dest)
        logger.info(f"Inserting: {workflow_id}, metadata: {nf_metadata}, script path: {nf_script_dest}")
        await db_create_workflow(
            user_id="Operandi Server",
            workflow_id=workflow_id, workflow_dir=workflow_dir, workflow_script_path=nf_script_dest,
            workflow_script_base=path.name, uses_mets_server=nf_metadata["uses_mets_server"],
            executable_steps=nf_metadata["executable_steps"],
            producible_file_groups=nf_metadata["producible_file_groups"], details=wf_detail)
        production_workflows.append(workflow_id)
    return production_workflows

from datetime import datetime
from os.path import join
from shutil import rmtree, copytree
from tests.constants import (
    OPERANDI_TESTS_LOCAL_DIR_WORKFLOW_JOBS,
    OPERANDI_TESTS_LOCAL_DIR_WORKSPACES,
    OPERANDI_HPC_DIR_PROJECT,
    OPERANDI_TESTS_HPC_DIR_BATCH_SCRIPTS,
    OPERANDI_TESTS_HPC_DIR_SLURM_WORKSPACES
)
from tests.helpers_asserts import assert_exists_dir
from tests.helpers_utils import to_asset_path

current_time = datetime.now().strftime("%Y%m%d_%H%M")
ID_BATCH_SCRIPT = "test_submit_workflow_job.sh"
ID_WORKFLOW_JOB = f"test_workflow_job_{current_time}"
ID_WORKSPACE = f"data"

ID_WORKFLOW_JOB_DIR = join(OPERANDI_TESTS_HPC_DIR_SLURM_WORKSPACES, ID_WORKFLOW_JOB)
HPC_WORKSPACE_PATH = join(ID_WORKFLOW_JOB_DIR, ID_WORKSPACE)
HPC_BATCH_SCRIPT_PATH = join(OPERANDI_TESTS_HPC_DIR_BATCH_SCRIPTS, ID_BATCH_SCRIPT)


# TODO: Adapt to the previous changes to use zips
def _test_hpc_connector_clean(hpc_command_executor):
    # Remove the tests folder from the HPC environment
    hpc_command_executor.execute_blocking(f"bash -lc 'rm -rf {OPERANDI_HPC_DIR_PROJECT}'")


def _test_hpc_connector_put_directory(hpc_data_transfer):
    hpc_data_transfer.put_dir(
        local_src=join(to_asset_path("workspaces", "dummy_ws"), ID_WORKSPACE),
        remote_dst=HPC_WORKSPACE_PATH
    )


def test_hpc_connector_put_file_batch_script(hpc_data_transfer):
    # Transfer slurm batch script
    hpc_data_transfer.put_file(
        local_src=to_asset_path('batch_scripts', ID_BATCH_SCRIPT),
        remote_dst=HPC_BATCH_SCRIPT_PATH
    )


def _test_hpc_connector_put_file_nextflow_script(hpc_data_transfer, path_workflow1):
    # Transfer nextflow workflow
    hpc_data_transfer.put_file(
        local_src=path_workflow1,
        remote_dst=join(ID_WORKFLOW_JOB_DIR, "test_default_workflow.nf")
    )


def test_pack_and_put_slurm_workspace(hpc_data_transfer, path_workflow1):
    # Move the test asset to actual workspaces location
    workspace_dir = copytree(
        src=join(to_asset_path("workspaces", "dummy_ws"), ID_WORKSPACE),
        dst=join(OPERANDI_TESTS_LOCAL_DIR_WORKSPACES, ID_WORKSPACE)
    )

    hpc_data_transfer.pack_and_put_slurm_workspace(
        ocrd_workspace_dir=workspace_dir,
        workflow_job_id=ID_WORKFLOW_JOB,
        nextflow_script_path=path_workflow1,
        tempdir_prefix="test_slurm_workspace-"
    )


def test_hpc_connector_run_batch_script(hpc_command_executor, path_workflow1):
    batch_script_path = join(OPERANDI_TESTS_HPC_DIR_BATCH_SCRIPTS, ID_BATCH_SCRIPT)
    slurm_job_id = hpc_command_executor.trigger_slurm_job(
        batch_script_path=batch_script_path,
        workflow_job_id=ID_WORKFLOW_JOB,
        nextflow_script_path=path_workflow1,
        input_file_grp="OCR-D-IMG",
        workspace_id=ID_WORKSPACE,
        mets_basename="mets.xml",
        cpus=2,
        ram=8
    )
    finished_successfully = hpc_command_executor.poll_till_end_slurm_job_state(
        slurm_job_id=slurm_job_id,
        interval=5,
        timeout=300
    )
    assert finished_successfully


def test_get_and_unpack_slurm_workspace(hpc_data_transfer):
    hpc_data_transfer.get_and_unpack_slurm_workspace(
        ocrd_workspace_dir=join(OPERANDI_TESTS_LOCAL_DIR_WORKSPACES, ID_WORKSPACE),
        hpc_slurm_workspace_path=OPERANDI_TESTS_HPC_DIR_SLURM_WORKSPACES,
        workflow_job_dir=join(OPERANDI_TESTS_LOCAL_DIR_WORKFLOW_JOBS, ID_WORKFLOW_JOB)
    )


def _test_hpc_connector_get_directory(
        hpc_data_transfer,
        hpc_command_executor
):
    dir_src = ID_WORKFLOW_JOB_DIR
    dir_dest = join(OPERANDI_TESTS_LOCAL_DIR_WORKFLOW_JOBS, ID_WORKFLOW_JOB)

    # Remove the dir left from previous tests (if any)
    rmtree(dir_dest, ignore_errors=True)
    hpc_data_transfer.get_dir(
        remote_src=dir_src,
        local_dst=dir_dest
    )
    assert_exists_dir(dir_dest)

    # Remove the workflow job folder from the HPC storage
    hpc_command_executor.execute_blocking(f"bash -lc 'rm -rf {dir_src}'")

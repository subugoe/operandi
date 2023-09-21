from datetime import datetime
from os.path import join
from shutil import copytree
from tests.constants import (
    OPERANDI_TESTS_LOCAL_DIR_WORKFLOW_JOBS,
    OPERANDI_TESTS_LOCAL_DIR_WORKSPACES,
    OPERANDI_TESTS_HPC_DIR_BATCH_SCRIPTS,
    OPERANDI_TESTS_HPC_DIR_SLURM_WORKSPACES
)
from tests.helpers_asserts import assert_exists_dir, assert_exists_file
from tests.helpers_utils import to_asset_path

current_time = datetime.now().strftime("%Y%m%d_%H%M")
ID_WORKFLOW_JOB = f"test_wf_job_{current_time}"
ID_WORKSPACE = f"test_ws_{current_time}"

HPC_SLURM_WORKFLOW_JOB_DIR = join(OPERANDI_TESTS_HPC_DIR_SLURM_WORKSPACES, ID_WORKFLOW_JOB)
HPC_WORKSPACE_PATH = join(HPC_SLURM_WORKFLOW_JOB_DIR, ID_WORKSPACE)


def test_pack_and_put_slurm_workspace(hpc_data_transfer, path_workflow1):
    # Move the test asset to actual workspaces location
    local_workspace_dir = copytree(
        src=join(to_asset_path("workspaces", "dummy_ws"), "data"),
        dst=join(OPERANDI_TESTS_LOCAL_DIR_WORKSPACES, ID_WORKSPACE)
    )
    assert_exists_dir(local_workspace_dir)

    local_slurm_workspace_zip_path = hpc_data_transfer.create_slurm_workspace_zip(
        ocrd_workspace_dir=local_workspace_dir,
        workflow_job_dir=HPC_SLURM_WORKFLOW_JOB_DIR,
        nextflow_script_path=path_workflow1,
        tempdir_prefix="test_slurm_workspace-"
    )
    assert_exists_file(local_slurm_workspace_zip_path)

    hpc_dst_slurm_zip = hpc_data_transfer.put_slurm_workspace(
        local_src_slurm_zip=local_slurm_workspace_zip_path,
        hpc_slurm_workspaces_root=OPERANDI_TESTS_HPC_DIR_SLURM_WORKSPACES,
        workflow_job_dir=HPC_SLURM_WORKFLOW_JOB_DIR
    )

    # TODO: implement this
    # assert_exists_remote_file(hpc_dst_slurm_zip)


def test_hpc_connector_put_batch_script(hpc_data_transfer):
    batch_script_id = "test_submit_workflow_job.sh"
    hpc_batch_script_path = join(OPERANDI_TESTS_HPC_DIR_BATCH_SCRIPTS, batch_script_id)
    hpc_data_transfer.put_file(
        local_src=to_asset_path('batch_scripts', batch_script_id),
        remote_dst=hpc_batch_script_path
    )


def test_hpc_connector_run_batch_script(hpc_command_executor, path_workflow1):
    batch_script_id = "test_submit_workflow_job.sh"
    hpc_batch_script_path = join(OPERANDI_TESTS_HPC_DIR_BATCH_SCRIPTS, batch_script_id)
    slurm_job_id = hpc_command_executor.trigger_slurm_job(
        batch_script_path=hpc_batch_script_path,
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
        hpc_slurm_workspace_path=HPC_SLURM_WORKFLOW_JOB_DIR,
        workflow_job_dir=join(OPERANDI_TESTS_LOCAL_DIR_WORKFLOW_JOBS, ID_WORKFLOW_JOB)
    )

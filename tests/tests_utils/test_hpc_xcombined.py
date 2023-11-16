from datetime import datetime
from os import environ
from os.path import join
from shutil import copytree
from operandi_server.constants import (
    SERVER_WORKFLOW_JOBS_ROUTER,
    SERVER_WORKSPACES_ROUTER
)
from tests.helpers_asserts import assert_exists_dir, assert_exists_file
from tests.helpers_utils import to_asset_path

current_time = datetime.now().strftime("%Y%m%d_%H%M")
ID_WORKFLOW_JOB = f"test_wf_job_{current_time}"
ID_WORKSPACE = f"test_ws_{current_time}"


def test_pack_and_put_slurm_workspace(hpc_data_transfer, path_workflow1):
    # Move the test asset to actual workspaces location
    local_workspace_dir = copytree(
        src=join(to_asset_path(resource_type="workspaces", name="small_ws"), "data"),
        dst=join(
            environ.get("OPERANDI_SERVER_BASE_DIR"),
            SERVER_WORKSPACES_ROUTER,
            ID_WORKSPACE
        )
    )
    assert_exists_dir(local_workspace_dir)

    local_slurm_workspace_zip_path = hpc_data_transfer.create_slurm_workspace_zip(
        ocrd_workspace_dir=local_workspace_dir,
        workflow_job_id=ID_WORKFLOW_JOB,
        nextflow_script_path=path_workflow1,
        tempdir_prefix="test_slurm_workspace-"
    )
    assert_exists_file(local_slurm_workspace_zip_path)

    hpc_dst_slurm_zip = hpc_data_transfer.put_slurm_workspace(
        local_src_slurm_zip=local_slurm_workspace_zip_path,
        workflow_job_id=ID_WORKFLOW_JOB
    )

    # TODO: implement this
    # assert_exists_remote_file(hpc_dst_slurm_zip)


def test_hpc_connector_put_batch_script(hpc_data_transfer):
    batch_script_id = "submit_workflow_job.sh"
    hpc_batch_script_path = join(hpc_data_transfer.batch_scripts_dir, batch_script_id)
    hpc_data_transfer.put_file(
        local_src=to_asset_path(resource_type="batch_scripts", name=batch_script_id),
        remote_dst=hpc_batch_script_path
    )


def test_hpc_connector_run_batch_script(hpc_command_executor, path_workflow1):
    batch_script_id = "submit_workflow_job.sh"
    hpc_batch_script_path = join(hpc_command_executor.batch_scripts_dir, batch_script_id)
    slurm_job_id = hpc_command_executor.trigger_slurm_job(
        batch_script_path=hpc_batch_script_path,
        workflow_job_id=ID_WORKFLOW_JOB,
        nextflow_script_path=path_workflow1,
        input_file_grp="DEFAULT",
        workspace_id=ID_WORKSPACE,
        mets_basename="mets.xml",
        job_deadline_time="1:00:00",
        cpus=2,
        ram=8,
        nf_process_forks=2,
        ws_pages_amount=8
    )
    finished_successfully = hpc_command_executor.poll_till_end_slurm_job_state(
        slurm_job_id=slurm_job_id,
        interval=5,
        timeout=300
    )
    assert finished_successfully


def test_get_and_unpack_slurm_workspace(hpc_data_transfer):
    # TODO: Use a method that resolves with ID
    hpc_data_transfer.get_and_unpack_slurm_workspace(
        ocrd_workspace_dir=join(
            environ.get("OPERANDI_SERVER_BASE_DIR"),
            SERVER_WORKSPACES_ROUTER,
            ID_WORKSPACE
        ),
        workflow_job_dir=join(
            environ.get("OPERANDI_SERVER_BASE_DIR"),
            SERVER_WORKFLOW_JOBS_ROUTER,
            ID_WORKFLOW_JOB
        )
    )

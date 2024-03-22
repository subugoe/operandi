from datetime import datetime
from os import environ
from os.path import join
from shutil import copytree
from operandi_server.constants import SERVER_WORKFLOW_JOBS_ROUTER, SERVER_WORKSPACES_ROUTER
from tests.helpers_asserts import assert_exists_dir, assert_exists_file
from tests.helpers_utils import to_asset_path

OPERANDI_SERVER_BASE_DIR = environ.get("OPERANDI_SERVER_BASE_DIR")
BATCH_SCRIPT_ID = "submit_workflow_job.sh"

current_time = datetime.now().strftime("%Y%m%d_%H%M")
ID_WORKFLOW_JOB_WITH_MS = f"test_wf_job_ms_{current_time}"
ID_WORKSPACE_WITH_MS = f"test_ws_ms_{current_time}"
ID_WORKFLOW_JOB = f"test_wf_job_{current_time}"
ID_WORKSPACE = f"test_ws_{current_time}"


def test_hpc_connector_put_batch_script(hpc_data_transfer):
    hpc_batch_script_path = join(hpc_data_transfer.batch_scripts_dir, BATCH_SCRIPT_ID)
    hpc_data_transfer.put_file(
        local_src=to_asset_path(resource_type="batch_scripts", name=BATCH_SCRIPT_ID),
        remote_dst=hpc_batch_script_path
    )


def test_pack_and_put_slurm_workspace_with_ms(
    hpc_data_transfer, path_small_workspace_data_dir, template_workflow_with_ms
):
    # Move the test asset to actual workspaces location
    local_workspace_dir = copytree(
        src=path_small_workspace_data_dir,
        dst=join(OPERANDI_SERVER_BASE_DIR, SERVER_WORKSPACES_ROUTER, ID_WORKSPACE_WITH_MS)
    )
    assert_exists_dir(local_workspace_dir)

    local_slurm_workspace_zip_path = hpc_data_transfer.create_slurm_workspace_zip(
        ocrd_workspace_dir=local_workspace_dir,
        workflow_job_id=ID_WORKFLOW_JOB_WITH_MS,
        nextflow_script_path=template_workflow_with_ms,
        tempdir_prefix="test_slurm_workspace-"
    )
    assert_exists_file(local_slurm_workspace_zip_path)

    hpc_dst_slurm_zip = hpc_data_transfer.put_slurm_workspace(
        local_src_slurm_zip=local_slurm_workspace_zip_path,
        workflow_job_id=ID_WORKFLOW_JOB_WITH_MS
    )

    # TODO: implement this
    # assert_exists_remote_file(hpc_dst_slurm_zip)


def test_pack_and_put_slurm_workspace(
    hpc_data_transfer, path_small_workspace_data_dir, template_workflow_with_ms
):
    # Move the test asset to actual workspaces location
    local_workspace_dir = copytree(
        src=path_small_workspace_data_dir,
        dst=join(OPERANDI_SERVER_BASE_DIR, SERVER_WORKSPACES_ROUTER, ID_WORKSPACE)
    )
    assert_exists_dir(local_workspace_dir)

    local_slurm_workspace_zip_path = hpc_data_transfer.create_slurm_workspace_zip(
        ocrd_workspace_dir=local_workspace_dir,
        workflow_job_id=ID_WORKFLOW_JOB,
        nextflow_script_path=template_workflow_with_ms,
        tempdir_prefix="test_slurm_workspace-"
    )
    assert_exists_file(local_slurm_workspace_zip_path)

    hpc_dst_slurm_zip = hpc_data_transfer.put_slurm_workspace(
        local_src_slurm_zip=local_slurm_workspace_zip_path,
        workflow_job_id=ID_WORKFLOW_JOB
    )

    # TODO: implement this
    # assert_exists_remote_file(hpc_dst_slurm_zip)


def test_hpc_connector_run_batch_script_with_ms(hpc_command_executor, template_workflow_with_ms):
    hpc_batch_script_path = join(hpc_command_executor.batch_scripts_dir, BATCH_SCRIPT_ID)
    slurm_job_id = hpc_command_executor.trigger_slurm_job(
        batch_script_path=hpc_batch_script_path,
        workflow_job_id=ID_WORKFLOW_JOB_WITH_MS,
        nextflow_script_path=template_workflow_with_ms,
        input_file_grp="DEFAULT",
        workspace_id=ID_WORKSPACE_WITH_MS,
        mets_basename="mets.xml",
        job_deadline_time="1:00:00",
        cpus=3,
        ram=16,
        nf_process_forks=2,
        ws_pages_amount=8,
        use_mets_server=True
    )
    finished_successfully = hpc_command_executor.poll_till_end_slurm_job_state(
        slurm_job_id=slurm_job_id,
        interval=5,
        timeout=300
    )
    assert finished_successfully


def test_hpc_connector_run_batch_script(hpc_command_executor, template_workflow):
    hpc_batch_script_path = join(hpc_command_executor.batch_scripts_dir, BATCH_SCRIPT_ID)
    slurm_job_id = hpc_command_executor.trigger_slurm_job(
        batch_script_path=hpc_batch_script_path,
        workflow_job_id=ID_WORKFLOW_JOB,
        nextflow_script_path=template_workflow,
        input_file_grp="DEFAULT",
        workspace_id=ID_WORKSPACE,
        mets_basename="mets.xml",
        job_deadline_time="1:00:00",
        cpus=2,
        ram=16,
        nf_process_forks=2,
        ws_pages_amount=8,
        use_mets_server=False
    )
    finished_successfully = hpc_command_executor.poll_till_end_slurm_job_state(
        slurm_job_id=slurm_job_id,
        interval=5,
        timeout=300
    )
    assert finished_successfully


def test_get_and_unpack_slurm_workspace_with_ms(hpc_data_transfer):
    # TODO: Use a method that resolves with ID
    hpc_data_transfer.get_and_unpack_slurm_workspace(
        ocrd_workspace_dir=join(OPERANDI_SERVER_BASE_DIR, SERVER_WORKSPACES_ROUTER, ID_WORKSPACE_WITH_MS),
        workflow_job_dir=join(OPERANDI_SERVER_BASE_DIR, SERVER_WORKFLOW_JOBS_ROUTER, ID_WORKFLOW_JOB_WITH_MS)
    )


def test_get_and_unpack_slurm_workspace(hpc_data_transfer):
    # TODO: Use a method that resolves with ID
    hpc_data_transfer.get_and_unpack_slurm_workspace(
        ocrd_workspace_dir=join(OPERANDI_SERVER_BASE_DIR, SERVER_WORKSPACES_ROUTER, ID_WORKSPACE),
        workflow_job_dir=join(OPERANDI_SERVER_BASE_DIR, SERVER_WORKFLOW_JOBS_ROUTER, ID_WORKFLOW_JOB)
    )

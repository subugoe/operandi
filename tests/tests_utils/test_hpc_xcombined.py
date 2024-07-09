from datetime import datetime
from os import environ
from os.path import join
from shutil import copytree
from time import sleep
from operandi_server.constants import (
    DEFAULT_FILE_GRP, DEFAULT_METS_BASENAME, SERVER_WORKFLOW_JOBS_ROUTER, SERVER_WORKSPACES_ROUTER
)
from operandi_utils.hpc.constants import HPC_JOB_DEADLINE_TIME_TEST, HPC_JOB_DEFAULT_PARTITION, HPC_JOB_QOS_2H
from tests.helpers_asserts import assert_exists_dir, assert_exists_file

OPERANDI_SERVER_BASE_DIR = environ.get("OPERANDI_SERVER_BASE_DIR")
BATCH_SCRIPT_ID = "submit_workflow_job.sh"

current_time = datetime.now().strftime("%Y%m%d_%H%M")
ID_WORKFLOW_JOB_WITH_MS = f"test_wf_job_ms_{current_time}"
ID_WORKSPACE_WITH_MS = f"test_ws_ms_{current_time}"
ID_WORKFLOW_JOB = f"test_wf_job_{current_time}"
ID_WORKSPACE = f"test_ws_{current_time}"


def helper_pack_and_put_slurm_workspace(
    hpc_data_transfer, workflow_job_id: str, workspace_id: str, path_workflow: str, path_workspace_dir: str
):
    # Move the test asset to actual workspaces location
    dst_path = join(OPERANDI_SERVER_BASE_DIR, SERVER_WORKSPACES_ROUTER, workspace_id)
    local_workspace_dir = copytree(src=path_workspace_dir, dst=dst_path)
    assert_exists_dir(local_workspace_dir)

    local_slurm_workspace_zip_path = hpc_data_transfer.create_slurm_workspace_zip(
        ocrd_workspace_dir=local_workspace_dir, workflow_job_id=workflow_job_id, nextflow_script_path=path_workflow,
        tempdir_prefix="test_slurm_workspace-")
    assert_exists_file(local_slurm_workspace_zip_path)

    hpc_dst_slurm_zip = hpc_data_transfer.put_slurm_workspace(
        local_src_slurm_zip=local_slurm_workspace_zip_path, workflow_job_id=workflow_job_id)

    # TODO: implement this
    # assert_exists_remote_file(hpc_dst_slurm_zip)


def test_hpc_connector_put_batch_script(hpc_data_transfer, path_batch_script_submit_workflow_job):
    hpc_batch_script_path = join(hpc_data_transfer.batch_scripts_dir, BATCH_SCRIPT_ID)
    hpc_data_transfer.put_file(local_src=path_batch_script_submit_workflow_job, remote_dst=hpc_batch_script_path)


def test_pack_and_put_slurm_workspace(hpc_data_transfer, path_small_workspace_data_dir, template_workflow):
    helper_pack_and_put_slurm_workspace(
        hpc_data_transfer=hpc_data_transfer, workflow_job_id=ID_WORKFLOW_JOB, workspace_id=ID_WORKSPACE,
        path_workflow=template_workflow, path_workspace_dir=path_small_workspace_data_dir)


def test_pack_and_put_slurm_workspace_with_ms(
    hpc_data_transfer, path_small_workspace_data_dir, template_workflow_with_ms
):
    helper_pack_and_put_slurm_workspace(
        hpc_data_transfer=hpc_data_transfer, workflow_job_id=ID_WORKFLOW_JOB_WITH_MS, workspace_id=ID_WORKSPACE_WITH_MS,
        path_workflow=template_workflow_with_ms, path_workspace_dir=path_small_workspace_data_dir)


def test_hpc_connector_run_batch_script(hpc_command_executor, template_workflow):
    hpc_batch_script_path = join(hpc_command_executor.batch_scripts_dir, BATCH_SCRIPT_ID)
    slurm_job_id = hpc_command_executor.trigger_slurm_job(
        batch_script_path=hpc_batch_script_path, workflow_job_id=ID_WORKFLOW_JOB,
        nextflow_script_path=template_workflow, input_file_grp=DEFAULT_FILE_GRP, workspace_id=ID_WORKSPACE,
        mets_basename=DEFAULT_METS_BASENAME, nf_process_forks=2, ws_pages_amount=8, use_mets_server=False,
        file_groups_to_remove="", cpus=2, ram=16, job_deadline_time=HPC_JOB_DEADLINE_TIME_TEST,
        partition=HPC_JOB_DEFAULT_PARTITION, qos=HPC_JOB_QOS_2H)
    finished_successfully = hpc_command_executor.poll_till_end_slurm_job_state(
        slurm_job_id=slurm_job_id, interval=5, timeout=300)
    assert finished_successfully


def test_hpc_connector_run_batch_script_with_ms(hpc_command_executor, template_workflow_with_ms):
    hpc_batch_script_path = join(hpc_command_executor.batch_scripts_dir, BATCH_SCRIPT_ID)
    slurm_job_id = hpc_command_executor.trigger_slurm_job(
        batch_script_path=hpc_batch_script_path, workflow_job_id=ID_WORKFLOW_JOB_WITH_MS,
        nextflow_script_path=template_workflow_with_ms, input_file_grp=DEFAULT_FILE_GRP,
        workspace_id=ID_WORKSPACE_WITH_MS, mets_basename=DEFAULT_METS_BASENAME, nf_process_forks=2, ws_pages_amount=8,
        use_mets_server=True, file_groups_to_remove="", cpus=3, ram=16, job_deadline_time=HPC_JOB_DEADLINE_TIME_TEST,
        partition=HPC_JOB_DEFAULT_PARTITION, qos=HPC_JOB_QOS_2H)
    finished_successfully = hpc_command_executor.poll_till_end_slurm_job_state(
        slurm_job_id=slurm_job_id, interval=5, timeout=300)
    assert finished_successfully


def test_get_and_unpack_slurm_workspace(hpc_data_transfer):
    # Wait some time till the zip is created in the HPC
    sleep(45)
    hpc_data_transfer.get_and_unpack_slurm_workspace(
        ocrd_workspace_dir=join(OPERANDI_SERVER_BASE_DIR, SERVER_WORKSPACES_ROUTER, ID_WORKSPACE),
        workflow_job_dir=join(OPERANDI_SERVER_BASE_DIR, SERVER_WORKFLOW_JOBS_ROUTER, ID_WORKFLOW_JOB)
    )


def test_get_and_unpack_slurm_workspace_with_ms(hpc_data_transfer):
    # Wait some time till the zip is created in the HPC
    sleep(45)
    hpc_data_transfer.get_and_unpack_slurm_workspace(
        ocrd_workspace_dir=join(OPERANDI_SERVER_BASE_DIR, SERVER_WORKSPACES_ROUTER, ID_WORKSPACE_WITH_MS),
        workflow_job_dir=join(OPERANDI_SERVER_BASE_DIR, SERVER_WORKFLOW_JOBS_ROUTER, ID_WORKFLOW_JOB_WITH_MS)
    )

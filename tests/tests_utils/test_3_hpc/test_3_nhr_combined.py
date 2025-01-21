from datetime import datetime
from os import environ
from shutil import copytree
from pathlib import Path
from operandi_server.constants import (
    DEFAULT_FILE_GRP, DEFAULT_METS_BASENAME, SERVER_WORKFLOW_JOBS_ROUTER, SERVER_WORKSPACES_ROUTER
)
from operandi_utils.hpc.constants import (
    HPC_JOB_DEADLINE_TIME_TEST, HPC_NHR_JOB_TEST_PARTITION, HPC_JOB_QOS_SHORT
)
from tests.helpers_asserts import assert_exists_dir, assert_exists_file

OPERANDI_SERVER_BASE_DIR = environ.get("OPERANDI_SERVER_BASE_DIR")

current_time = datetime.now().strftime("%Y%m%d_%H%M%S%f")
ID_WORKFLOW_JOB_WITH_MS = f"test_wf_job_ms_{current_time}"
ID_WORKSPACE_WITH_MS = f"test_ws_ms_{current_time}"
ID_WORKFLOW_JOB = f"test_wf_job_{current_time}"
ID_WORKSPACE = f"test_ws_{current_time}"

def helper_pack_and_put_slurm_workspace(
    hpc_nhr_data_transfer, workflow_job_id: str, workspace_id: str, path_workflow: Path, path_workspace_dir: Path
):
    # Move the test asset to actual workspaces location
    dst_path = Path(OPERANDI_SERVER_BASE_DIR, SERVER_WORKSPACES_ROUTER, workspace_id)
    local_workspace_dir = copytree(src=path_workspace_dir, dst=dst_path)
    assert_exists_dir(str(local_workspace_dir))

    local_slurm_workspace_zip_path = hpc_nhr_data_transfer.create_slurm_workspace_zip(
        ocrd_workspace_dir=Path(local_workspace_dir), workflow_job_id=workflow_job_id,
        nextflow_script_path=path_workflow, tempdir_prefix="test_slurm_workspace-")
    assert_exists_file(str(local_slurm_workspace_zip_path))

    hpc_dst_slurm_zip = hpc_nhr_data_transfer.put_slurm_workspace(
        local_src_slurm_zip=local_slurm_workspace_zip_path, workflow_job_id=workflow_job_id)

    # TODO: implement this
    # assert_exists_remote_file(hpc_dst_slurm_zip)

    Path(local_slurm_workspace_zip_path).unlink(missing_ok=True)

def test_pack_and_put_slurm_workspace(hpc_nhr_data_transfer, path_small_workspace_data_dir, template_workflow):
    helper_pack_and_put_slurm_workspace(
        hpc_nhr_data_transfer=hpc_nhr_data_transfer, workflow_job_id=ID_WORKFLOW_JOB, workspace_id=ID_WORKSPACE,
        path_workflow=Path(template_workflow), path_workspace_dir=Path(path_small_workspace_data_dir)
    )


def test_pack_and_put_slurm_workspace_with_ms(
    hpc_nhr_data_transfer, path_small_workspace_data_dir, template_workflow_with_ms
):
    helper_pack_and_put_slurm_workspace(
        hpc_nhr_data_transfer=hpc_nhr_data_transfer, workflow_job_id=ID_WORKFLOW_JOB_WITH_MS,
        workspace_id=ID_WORKSPACE_WITH_MS, path_workflow=Path(template_workflow_with_ms),
        path_workspace_dir=Path(path_small_workspace_data_dir)
    )


def test_hpc_connector_run_batch_script(
    hpc_nhr_command_executor, hpc_nhr_data_transfer, template_workflow):
    slurm_job_id = hpc_nhr_command_executor.trigger_slurm_job(
        workflow_job_id=ID_WORKFLOW_JOB, nextflow_script_path=Path(template_workflow),
        input_file_grp=DEFAULT_FILE_GRP, workspace_id=ID_WORKSPACE,
        mets_basename=DEFAULT_METS_BASENAME, nf_process_forks=2, ws_pages_amount=8,
        use_mets_server=False, nf_executable_steps=["ocrd-cis-ocropy-binarize"],
        file_groups_to_remove="", cpus=2, ram=16, job_deadline_time=HPC_JOB_DEADLINE_TIME_TEST,
        partition=HPC_NHR_JOB_TEST_PARTITION, qos=HPC_JOB_QOS_SHORT)
    finished_successfully = hpc_nhr_command_executor.poll_till_end_slurm_job_state(
        slurm_job_id=slurm_job_id, interval=10, timeout=300)
    assert finished_successfully

    ws_dir = Path(OPERANDI_SERVER_BASE_DIR, SERVER_WORKSPACES_ROUTER, ID_WORKSPACE)
    wf_job_dir = Path(OPERANDI_SERVER_BASE_DIR, SERVER_WORKFLOW_JOBS_ROUTER, ID_WORKFLOW_JOB)
    hpc_nhr_data_transfer.get_and_unpack_slurm_workspace(ocrd_workspace_dir=ws_dir, workflow_job_dir=wf_job_dir)
    assert Path(ws_dir, "OCR-D-BIN").exists()
    assert wf_job_dir.exists()
    assert Path(wf_job_dir, "work").exists()
    assert Path(wf_job_dir, ID_WORKSPACE, "OCR-D-BIN").exists()
    assert Path(wf_job_dir, f"slurm-job-{slurm_job_id}.txt").exists()

def test_hpc_connector_run_batch_script_with_ms(
    hpc_nhr_command_executor, hpc_nhr_data_transfer, template_workflow_with_ms):
    slurm_job_id = hpc_nhr_command_executor.trigger_slurm_job(
        workflow_job_id=ID_WORKFLOW_JOB_WITH_MS, nextflow_script_path=Path(template_workflow_with_ms),
        input_file_grp=DEFAULT_FILE_GRP, workspace_id=ID_WORKSPACE_WITH_MS,
        mets_basename=DEFAULT_METS_BASENAME, nf_process_forks=2, ws_pages_amount=8,
        use_mets_server=True, nf_executable_steps=["ocrd-cis-ocropy-binarize"],
        file_groups_to_remove="", cpus=4, ram=16, job_deadline_time=HPC_JOB_DEADLINE_TIME_TEST,
        partition=HPC_NHR_JOB_TEST_PARTITION, qos=HPC_JOB_QOS_SHORT)
    finished_successfully = hpc_nhr_command_executor.poll_till_end_slurm_job_state(
        slurm_job_id=slurm_job_id, interval=10, timeout=300)
    assert finished_successfully

    ws_dir = Path(OPERANDI_SERVER_BASE_DIR, SERVER_WORKSPACES_ROUTER, ID_WORKSPACE_WITH_MS)
    wf_job_dir = Path(OPERANDI_SERVER_BASE_DIR, SERVER_WORKFLOW_JOBS_ROUTER, ID_WORKFLOW_JOB_WITH_MS)
    hpc_nhr_data_transfer.get_and_unpack_slurm_workspace(ocrd_workspace_dir=ws_dir, workflow_job_dir=wf_job_dir)
    assert Path(ws_dir, "OCR-D-BIN").exists()
    assert wf_job_dir.exists()
    assert Path(wf_job_dir, "work").exists()
    assert Path(wf_job_dir, ID_WORKSPACE_WITH_MS, "OCR-D-BIN").exists()
    assert Path(wf_job_dir, f"slurm-job-{slurm_job_id}.txt").exists()

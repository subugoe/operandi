from os.path import join
from shutil import rmtree
from tests.constants import (
    OPERANDI_TESTS_LOCAL_DIR_WORKFLOW_JOBS,
    OPERANDI_TESTS_HPC_DIR,
    OPERANDI_TESTS_HPC_DIR_BATCH_SCRIPTS,
    OPERANDI_TESTS_HPC_DIR_WORKFLOW_JOBS
)
from tests.helpers_asserts import assert_exists_dir
from tests.helpers_utils import to_asset_path

# current_time = datetime.now().strftime("%Y-%m-%d_%H-%M")
ID_BATCH_SCRIPT = "test_submit_workflow_job.sh"
ID_NEXTFLOW_SCRIPT = "test_default_workflow.nf"
ID_WORKFLOW_JOB = "test_default_workflow_job_id"
ID_WORKFLOW_JOB_DIR = join(OPERANDI_TESTS_HPC_DIR_WORKFLOW_JOBS, ID_WORKFLOW_JOB)


def test_hpc_connector_clean(hpc_command_executor):
    # Remove the tests folder from the HPC environment
    hpc_command_executor.execute_blocking(f"bash -lc 'rm -rf {OPERANDI_TESTS_HPC_DIR}'")


def test_hpc_connector_put_directory(hpc_data_transfer):
    hpc_data_transfer.put_directory(
        source=join(to_asset_path("workspaces", "dummy_ws"), "data"),
        destination=join(ID_WORKFLOW_JOB_DIR, "data")
    )


def test_hpc_connector_put_file_batch_script(hpc_data_transfer):
    # Transfer slurm batch script
    hpc_data_transfer.put_file(
        source=to_asset_path('batch_scripts', ID_BATCH_SCRIPT),
        destination=join(OPERANDI_TESTS_HPC_DIR_BATCH_SCRIPTS, ID_BATCH_SCRIPT)
    )


def test_hpc_connector_put_file_nextflow_script(hpc_data_transfer):
    # Transfer nextflow workflow
    hpc_data_transfer.put_file(
        source=to_asset_path('workflows', ID_NEXTFLOW_SCRIPT),
        destination=join(ID_WORKFLOW_JOB_DIR, ID_NEXTFLOW_SCRIPT)
    )


def test_hpc_connector_run_batch_script(hpc_command_executor):
    batch_script_path = join(OPERANDI_TESTS_HPC_DIR_BATCH_SCRIPTS, ID_BATCH_SCRIPT)
    slurm_job_id = hpc_command_executor.trigger_slurm_job(
        batch_script_path=batch_script_path,
        workflow_job_id=ID_WORKFLOW_JOB,
        nextflow_script_id=ID_NEXTFLOW_SCRIPT,
        input_file_grp="OCR-D-IMG"
    )
    finished_successfully = hpc_command_executor.poll_till_end_slurm_job_state(
        slurm_job_id=slurm_job_id,
        interval=5,
        timeout=300
    )
    assert finished_successfully


def test_hpc_connector_get_directory(
        hpc_data_transfer,
        hpc_command_executor
):
    dir_src = ID_WORKFLOW_JOB_DIR
    dir_dest = join(OPERANDI_TESTS_LOCAL_DIR_WORKFLOW_JOBS, ID_WORKFLOW_JOB)

    # Remove the dir left from previous tests (if any)
    rmtree(dir_dest, ignore_errors=True)
    hpc_data_transfer.get_directory(
        source=dir_src,
        destination=dir_dest
    )
    assert_exists_dir(dir_dest)

    # Remove the workflow job folder from the HPC storage
    hpc_command_executor.execute_blocking(f"bash -lc 'rm -rf {dir_src}'")

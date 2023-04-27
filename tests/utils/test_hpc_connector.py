from tests.constants import OPERANDI_TESTS_DIR
from tests.helpers_asserts import assert_exists_dir
from tests.helpers_utils import to_asset_path
from tests.utils.constants import OPERANDI_HPC_HOME_PATH


def test_hpc_connector_put_directory(fixture_hpc_io_transfer_connector):
    dir_src = to_asset_path('workspaces', 'dummy_ws/data')
    workflow_job_id = "test_workflow_job_id"
    dir_dest = f"{OPERANDI_HPC_HOME_PATH}/tests/workflow_jobs/{workflow_job_id}/data"
    fixture_hpc_io_transfer_connector.put_directory(source=dir_src, destination=dir_dest)


def test_hpc_connector_put_file(fixture_hpc_io_transfer_connector):
    # Transfer the slurm batch script
    batch_script_id = "test_submit_workflow_job.sh"
    file_src = to_asset_path('batch_scripts', batch_script_id)
    file_dest = f"{OPERANDI_HPC_HOME_PATH}/tests/batch_scripts/{batch_script_id}"
    fixture_hpc_io_transfer_connector.put_file(source=file_src, destination=file_dest)

    # Transfer the nextflow workflow
    workflow_job_id = "test_workflow_job_id"
    nextflow_script_id = "test_template_workflow.nf"
    file_src = to_asset_path('workflows', nextflow_script_id)
    file_dest = f"{OPERANDI_HPC_HOME_PATH}/tests/workflow_jobs/{workflow_job_id}/{nextflow_script_id}"
    fixture_hpc_io_transfer_connector.put_file(source=file_src, destination=file_dest)


def test_hpc_connector_run_batch_script(fixture_hpc_paramiko_connector):
    # current_time = datetime.now().strftime("%Y-%m-%d_%H-%M")
    batch_script_id = "test_submit_workflow_job.sh"
    batch_script_path = f"{OPERANDI_HPC_HOME_PATH}/tests/batch_scripts/{batch_script_id}"
    workflow_job_id = f"test_workflow_job_id"
    input_file_grp = "OCR-D-IMG"
    nextflow_script_id = "test_template_workflow.nf"

    slurm_job_id = fixture_hpc_paramiko_connector.trigger_slurm_job(
        batch_script_path=batch_script_path,
        workflow_job_id=workflow_job_id,
        nextflow_script_id=nextflow_script_id,
        input_file_grp=input_file_grp
    )
    finished_successfully = fixture_hpc_paramiko_connector.poll_till_end_slurm_job_state(
        slurm_job_id=slurm_job_id,
        interval=5,
        timeout=300
    )
    assert finished_successfully


def test_hpc_connector_get_directory(fixture_hpc_io_transfer_connector):
    workflow_job_id = f"test_workflow_job_id"
    dir_src = f"{OPERANDI_HPC_HOME_PATH}/tests/workflow_jobs/{workflow_job_id}"
    dir_dest = f"{OPERANDI_TESTS_DIR}/workflow_jobs/{workflow_job_id}"
    fixture_hpc_io_transfer_connector.get_directory(source=dir_src, destination=dir_dest)
    assert_exists_dir(dir_dest)

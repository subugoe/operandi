from datetime import datetime
from os.path import join
from time import sleep

current_time = datetime.now().strftime("%Y%m%d_%H%M%S%f")


def test_hpc_connector_executor_mk_dir(hpc_nhr_command_executor):
    test_dir_name = join(hpc_nhr_command_executor.project_root_dir_with_env, f"test_dir_{current_time}")
    sleep(0.5)
    output, err, return_code = hpc_nhr_command_executor.execute_blocking(command=f"bash -lc 'mkdir -p {test_dir_name}'")
    assert return_code == 0, err
    assert err == []
    assert output == []


def test_hpc_connector_executor_rm_dir_negative(hpc_nhr_command_executor):
    test_dir_name = join(hpc_nhr_command_executor.project_root_dir_with_env, f"test_dir_{current_time}")
    sleep(0.5)
    output, err, return_code = hpc_nhr_command_executor.execute_blocking(command=f"bash -lc 'rm {test_dir_name}'")
    assert return_code == 1
    # The test dir name will be part of the returned error message
    assert f'{test_dir_name}' in err[0]
    assert output == []


def test_hpc_connector_executor_rm_dir_positive(hpc_nhr_command_executor):
    test_dir_name = join(hpc_nhr_command_executor.project_root_dir_with_env, f"test_dir_{current_time}")
    sleep(0.5)
    output, err, return_code = hpc_nhr_command_executor.execute_blocking(command=f"bash -lc 'rm -rf {test_dir_name}'")
    assert return_code == 0
    assert err == []
    assert output == []


def test_hpc_connector_executor_cd_dir(hpc_nhr_command_executor):
    test_dir_name = join(hpc_nhr_command_executor.project_root_dir_with_env, f"test_dir_{current_time}")
    sleep(0.5)
    output, err, return_code = hpc_nhr_command_executor.execute_blocking(command=f"bash -lc 'cd {test_dir_name}'")
    assert return_code == 1
    # The test dir name will be part of the returned error message
    assert f'{test_dir_name}' in err[0]
    assert output == []


def _test_hpc_connector_executor_check_if_models_exists(hpc_nhr_command_executor):
    non_existing_models = {
        "ocrd-calamari-recognize": "non-existing-model",
        "non-existing-processor": "qurator-gt4histocr-1.0",
    }
    existing_models = {
        "ocrd-calamari-recognize": "qurator-gt4histocr-1.0",
        "ocrd-cis-ocropy-recognize": "LatinHist.pyrnn.gz",
        "ocrd-kraken-recognize": "typewriter.mlmodel",
        "ocrd-tesserocr-recognize": "Fraktur.traineddata"
    }

    for key, value in existing_models.items():
        assert hpc_nhr_command_executor.check_if_model_exists(ocrd_processor=key, model=value)
    for key, value in non_existing_models.items():
        assert not hpc_nhr_command_executor.check_if_model_exists(ocrd_processor=key, model=value)

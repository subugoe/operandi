from datetime import datetime
from os.path import join
from time import sleep

current_time = datetime.now().strftime("%Y%m%d_%H%M")


def test_hpc_connector_executor_mk_dir(hpc_nhr_command_executor):
    test_dir_name = join(hpc_nhr_command_executor.project_root_dir, f"test_dir_{current_time}")
    sleep(0.5)
    output, err, return_code = hpc_nhr_command_executor.execute_blocking(command=f"bash -lc 'mkdir -p {test_dir_name}'")
    assert return_code == 0, err
    assert err == []
    assert output == []


def test_hpc_connector_executor_rm_dir_negative(hpc_nhr_command_executor):
    test_dir_name = join(hpc_nhr_command_executor.project_root_dir, f"test_dir_{current_time}")
    sleep(0.5)
    output, err, return_code = hpc_nhr_command_executor.execute_blocking(command=f"bash -lc 'rm {test_dir_name}'")
    assert return_code == 1
    # The test dir name will be part of the returned error message
    assert f'{test_dir_name}' in err[0]
    assert output == []


def test_hpc_connector_executor_rm_dir_positive(hpc_nhr_command_executor):
    test_dir_name = join(hpc_nhr_command_executor.project_root_dir, f"test_dir_{current_time}")
    sleep(0.5)
    output, err, return_code = hpc_nhr_command_executor.execute_blocking(command=f"bash -lc 'rm -rf {test_dir_name}'")
    assert return_code == 0
    assert err == []
    assert output == []


def test_hpc_connector_executor_cd_dir(hpc_nhr_command_executor):
    test_dir_name = join(hpc_nhr_command_executor.project_root_dir, f"test_dir_{current_time}")
    sleep(0.5)
    output, err, return_code = hpc_nhr_command_executor.execute_blocking(command=f"bash -lc 'cd {test_dir_name}'")
    assert return_code == 1
    # The test dir name will be part of the returned error message
    assert f'{test_dir_name}' in err[0]
    assert output == []

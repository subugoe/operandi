from os.path import exists, join
import shlex
import subprocess
from re import search as regex_search
from typing import Union


# Must be further refined
class NextflowManager:
    def __init__(self, venv_path: str = None):
        # The virtual environment activation path where OCR-D processor are installed
        self.venv_path = venv_path
        # E.g., self.venv_path = "\$HOME/venv37-ocrd/bin/activate"
        # WARNING: PEP complains about the \$ escape sequence,
        # but this is the format that the Nextflow Executor expects

    @staticmethod
    def execute_workflow(
            nf_script_path: str,
            workspace_mets_path: str,
            job_dir: str,
            workspace_path: str = None,
            venv_path: str = None,
            input_group: str = None,
            in_background=True
    ):
        # TODO: Parse the rest of the possible workflow params
        # TODO: Use workflow_params to enable more flexible workflows
        nf_command = NextflowManager.build_nf_command(
            nf_script_path=nf_script_path,
            ws_mets_path=workspace_mets_path,
            ws_path=workspace_path,
            venv_path=venv_path,
            input_group=input_group,
            in_background=in_background
        )

        # Throws an exception if not successful
        return NextflowManager.__start_nf_process(nf_command, job_dir)

    @staticmethod
    def is_nf_available() -> Union[str, None]:
        # The path to Nextflow must be in $PATH
        # Otherwise, the full path must be provided

        # TODO: May be a good idea to define
        # the path to Nextflow somewhere else
        # (as a config or const parameter)
        ver_cmd = "nextflow -v"

        try:
            # Raises an exception if the subprocess fails
            ver_process = subprocess.run(shlex.split(ver_cmd),
                                         shell=False,
                                         check=True,
                                         stdout=subprocess.PIPE,
                                         universal_newlines=True)
        # Only the result is important not why it failed
        except Exception:
            return None

        regex_pattern = r"nextflow version\s*([\d.]+)"
        nf_version = regex_search(regex_pattern, ver_process.stdout).group(1)
        return nf_version

    @staticmethod
    def build_nf_command(
            nf_script_path: str,
            ws_mets_path: str,
            ws_path: str = None,
            venv_path: str = None,
            input_group: str = None,
            in_background: bool = True
    ) -> str:
        nf_command = "nextflow"
        # If set, executes the nf process in the background
        if in_background:
            nf_command += " -bg"
        nf_command += f" run {nf_script_path}"
        nf_command += f" --mets {ws_mets_path}"
        if ws_path:
            nf_command += f" --workspace_dir {ws_path}"
        # If None, the venv set inside the Nextflow script will be used
        if venv_path:
            nf_command += f" --venv {venv_path}"
        # If None, the input_group set inside the Nextflow script will be used
        if input_group:
            nf_command += f" --input_group {input_group}"
        nf_command += f" -with-report report.html"
        return nf_command

    @staticmethod
    def __start_nf_process(nf_command: str, job_dir: str):
        nf_out = f'{job_dir}/nextflow_out.txt'
        nf_err = f'{job_dir}/nextflow_err.txt'

        # TODO: Not sure if this is too much to be handled in a single
        #  try catch block structure.
        try:
            with open(nf_out, 'w+') as nf_out_file:
                with open(nf_err, 'w+') as nf_err_file:
                    # TODO: We will need better management of this, blocking is bad
                    # The parent process blocks till the subprocess returns.
                    # Raises an exception if the subprocess fails
                    nf_process = subprocess.run(shlex.split(nf_command),
                                                shell=False,
                                                check=True,
                                                cwd=job_dir,
                                                stdout=nf_out_file,
                                                stderr=nf_err_file,
                                                universal_newlines=True)
        # More detailed exception catches needed
        # E.g., was the exception due to IOError or subprocess.CalledProcessError
        except Exception as error:
            raise error
        return nf_process

    @staticmethod
    def is_nf_report(location_dir: str) -> Union[str, None]:
        report_path = join(location_dir, "report.html")
        if exists(report_path):
            return report_path
        return None

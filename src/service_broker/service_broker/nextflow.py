import subprocess
import shlex


def build_nf_command(nf_script_path, workspace_dir, save_to_olahd=False):
    nf_command = "nextflow -bg"  # -bg - run in the background
    nf_command += f" run {nf_script_path}"
    # When running an OCR-D docker container
    # It is enough to map the volume_dir.
    # Workspace path and mets path not needed
    nf_command += f" --volume_dir {workspace_dir}"
    # nf_command += f" --workspace {workspace_dir}/"
    # nf_command += f" --mets {workspace_dir}/mets.xml"
    if save_to_olahd:
        # TODO: read user and pw from file or env. Leave blank skips storing in olahd
        nf_command += " --olahd_username admin"
        nf_command += ' --olahd_endpoint "http://141.5.104.244/api"'
        nf_command += " --olahd_password JW24G.xR"
    nf_command += " -with-report"  # produce report.html
    return nf_command


def trigger_nf_process(nf_workspace_dir, nf_script_path, ocrd_workspace_dir):
    nf_command = build_nf_command(nf_script_path, ocrd_workspace_dir)
    nf_out = f"{nf_workspace_dir}/nf_out.txt"
    nf_err = f"{nf_workspace_dir}/nf_err.txt"

    # TODO: Not a big fan of the nested structure, fix this to open/close files separately
    # TODO: Exception handling related to fd should be then more clear
    with open(nf_out, 'w+') as nf_out_file:
        with open(nf_err, 'w+') as nf_err_file:
            # Raises an exception if the subprocess fails
            # TODO: Catch and process exceptions properly
            # TODO: For some reason '.call' works '.run' does not. Investigate it ...
            nf_process = subprocess.call(
                shlex.split(nf_command),
                # shell=False,
                # check=True,
                cwd=nf_workspace_dir,
                stdout=nf_out_file,
                stderr=nf_err_file
                # universal_newlines=True
            )
    return nf_process

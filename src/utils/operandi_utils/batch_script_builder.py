# This class is used to automatically generate
# batch scripts submitted to the HPC environment

# Check here for more detailed information:
# https://docs.gwdg.de/doku.php?id=en:services:application_services:high_performance_computing:running_jobs_slurm

# The default batch script used (previously) is available
# under service_broker/batch_scripts/base_script.sh

from typing import List
from .hpc_constants import OPERANDI_HPC_USERNAME


class BatchScriptBuilder:
    def __init__(self):
        pass

    # Note: All values defined with SBATCH directives are hard values.
    # E.g., when the memory is set to 6000 MB (--mem=6000MB) and
    # the job uses more than that - it will be killed by the manager.
    @staticmethod
    def build_directives(
            account: str = None,
            constraint: str = None,
            cpus_per_task: int = None,
            job_name: str = None,
            mail_type: str = None,
            mail_user: str = None,
            mem: str = None,
            mem_per_cpu: str = None,
            nodes: int = None,
            output: str = None,
            partition: str = None,
            time: str = None,
            qos: str = None,
    ):
        if bool(mem) and bool(mem_per_cpu):
            raise ValueError("Either `mem` or `mem_per_cpu` must be set, not both!")
        # TODO: Further checks required for exclusive combinations

        batch_directives = ""
        if account:
            # Project (not user) account the job should be charged to.
            batch_directives += f"#SBATCH --account={account}\n"
        if constraint:
            # Set to `scratch` if allocated nodes has to access the same location
            batch_directives += f"#SBATCH --constraint={constraint}\n"
        if cpus_per_task:
            # CPU cores per task
            batch_directives += f"#SBATCH --cpus-per-task={cpus_per_task}\n"
        if job_name:
            batch_directives += f"#SBATCH --job-name={job_name}\n"
        if mail_type:
            # Possible values: NONE, BEGIN, END, FAIL, ALL
            # E.g., END,FAIL - means sent an e-mail if job failed
            batch_directives += f"#SBATCH --mail-type={mail_type}\n"
        if mail_user:
            # Email address to send notifications to
            batch_directives += f"#SBATCH --mail-user={mail_user}\n"
        if mem:
            # Memory (RAM) per node. Number followed by unit prefix.
            # E.g., 5GB
            batch_directives += f"#SBATCH --mem={mem}\n"
        if mem_per_cpu:
            # Memory (RAM) per requested CPU core
            # E.g., 1500MB
            batch_directives += f"#SBATCH --mem-per-cpu={mem_per_cpu}\n"
        if nodes:
            batch_directives += f"#SBATCH --nodes={nodes}\n"
        if output:
            # Store the job output in “file” (otherwise written to slurm-<jobid>).
            # %J in the filename stands for the jobid.
            batch_directives += f"#SBATCH --output={output}\n"
        if partition:
            # Partition/queue in which to run the job.
            # GWDG supports: medium (default), fat, fat+, gpu
            batch_directives += f"#SBATCH --partition={partition}\n"
        if time:
            # Maximum runtime of the job.
            # If this time is exceeded the job is killed.
            # format: d-hh:mm:ss
            # GWDG max default: 2 days
            batch_directives += f"#SBATCH --time={time}\n"
        if qos:
            # GWDG supports: short (2 hours), long (5 days)
            # GWDG max default: 2 days
            batch_directives += f"#SBATCH --qos={qos}\n"
        return batch_directives

    @staticmethod
    def build_modules(clean: bool = True, modules: List = None):
        if not modules:
            raise ValueError("No modules passed to the module builder")
        modules_section = ""
        if clean:
            modules_section += f"module purge\n"
        for module in modules:
            modules_section += f"module load {module}\n"
        return modules_section

    # TODO: This must not be hard coded
    #  it is just my initial naive try to automize things
    @staticmethod
    def build_bash_commands(
            scratch_value: str = "scratch1",
            env_user: str = "${USER}",
            nf_script_name: str = "hpc_nextflow.nf"
    ):
        # This path depends on the HPC environment configuration
        # ${USER} is the env variable of the current user account
        # $1 is the first parameter passed to the script,
        # i.e., the workspace id
        mkdir_user_sh = BatchScriptBuilder.sh_mkdir_command(
            dir_path=f"/{scratch_value}/users/{env_user}"
        )
        mkdir_workspace_sh = BatchScriptBuilder.sh_mkdir_command(
            dir_path=f"/scratch1/users/{env_user}/$1"
        )
        cp_dir_workspace_sh = BatchScriptBuilder.sh_cp_dir_command(
            src_dir=f"/home/users/{env_user}/$1/bin",
            dst_dir=f"/{scratch_value}/users/{env_user}/$1"
        )
        rm_home_workspace_sh = BatchScriptBuilder.sh_rm_dir_command(
            dir_path=f"/home/users/{env_user}/$1"
        )
        cd_scratch_workspace_sh = BatchScriptBuilder.sh_cd_dir_command(
            dir_path=f"/{scratch_value}/users/{env_user}/$1/bin"
        )
        nextflow_run_sh = BatchScriptBuilder.sh_build_nf_command(
            # This is the default Nextflow script
            #  under service_broker/nextflow/scripts/hpc_nextflow.nf
            nf_script_name=nf_script_name,
            volume_dir=f"/{scratch_value}/users/{env_user}/$1/bin"
        )

        bash_commands = ""
        bash_commands += f"{mkdir_user_sh}\n"
        bash_commands += f"{mkdir_workspace_sh}\n"
        bash_commands += f"{cp_dir_workspace_sh}"
        bash_commands += f"{rm_home_workspace_sh}"
        bash_commands += f"{cd_scratch_workspace_sh}\n"
        bash_commands += f"{nextflow_run_sh}\n"
        return bash_commands

    @staticmethod
    def sh_mkdir_command(dir_path: str):
        # check if dir exists
        create_dir_command = f"if [ ! -d \"{dir_path}\" ]; then\n"
        # create if not
        create_dir_command += f"  mkdir \"{dir_path}\"\n"
        create_dir_command += "fi"
        return create_dir_command

    @staticmethod
    def sh_cp_dir_command(src_dir: str, dst_dir: str):
        return f"cp -rf {src_dir} {dst_dir}\n"

    @staticmethod
    def sh_rm_dir_command(dir_path: str):
        return f"rm -rf {dir_path}\n"

    @staticmethod
    def sh_cd_dir_command(dir_path: str):
        # If changing directory not successful, exit
        return f"cd {dir_path} || exit\n"

    @staticmethod
    def sh_build_nf_command(nf_script_name: str, volume_dir: str):
        nf_command = "nextflow run "
        nf_command += f"{nf_script_name} "
        nf_command += f"--volume-dir {volume_dir}"
        return nf_command

    @staticmethod
    def produce_batch_file(output_path: str):
        sbatch_directives = BatchScriptBuilder.build_directives(
            constraint="scratch",
            partition="medium",
            cpus_per_task=2,
            mem="32G",
            output=f"/home/users/{OPERANDI_HPC_USERNAME}/jobs_output/job-%J.txt"
        )
        sbatch_modules = BatchScriptBuilder.build_modules(
            clean=True,
            modules=['nextflow', 'singularity']
        )
        sbatch_bash_commands = BatchScriptBuilder.build_bash_commands(
            scratch_value="scratch1",
            nf_script_name="hpc_nextflow.nf"
        )

        with open(output_path, mode='w', encoding='utf-8') as batch_file:
            # Start by specifying the bash path
            batch_file.write("#!/bin/bash\n")
            # Write the sbatch directives
            batch_file.write(sbatch_directives)
            batch_file.write("\n")
            # Useful when debugging
            batch_file.write("hostname\n")
            batch_file.write("slurm_resources\n")
            batch_file.write("\n")
            # Write the modules section
            batch_file.write(sbatch_modules)
            batch_file.write("\n")
            # Write the bash section + Nextflow trigger command
            batch_file.write(sbatch_bash_commands)
            batch_file.write("\n")
            batch_file.write("# This script was automatically generated \
                             by the Service Broker - Batch Script Builder\n")
            batch_file.write("\n")

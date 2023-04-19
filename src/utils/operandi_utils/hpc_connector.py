import os
import SSHLibrary

from .hpc_constants import (
    OPERANDI_HPC_HOST,
    OPERANDI_HPC_USERNAME,
    OPERANDI_HPC_SSH_KEYPATH,
    OPERANDI_HPC_HOME_PATH
)


# The Service broker uses the SSHCommunication class
# to communicate with the HPC environment
# TODO: Implement appropriate error handling
class HPCConnector:
    def __init__(self, hpc_home_path: str = OPERANDI_HPC_HOME_PATH, scp="ON", scp_preserve_times=True, mode="0755"):
        # TODO: Handle the exceptions properly
        # E.g., when not connected to GOENET the SSH connection fails
        self.scp = scp
        self.scp_preserve_times = scp_preserve_times
        self.mode = mode
        self.hpc_home_path = hpc_home_path
        self.__ssh = SSHLibrary.SSHLibrary()

    def connect_to_hpc(
            self,
            host=OPERANDI_HPC_HOST,
            username=OPERANDI_HPC_USERNAME,
            key_path=OPERANDI_HPC_SSH_KEYPATH
    ):
        keyfile = self.__check_keyfile_existence(key_path)
        if not keyfile:
            print(f"Error: HPC key path does not exist or is not readable!")
            print(f"Checked path: \n{key_path}")
            exit(1)

        self.__ssh.open_connection(host=host)
        self.__ssh.login_with_public_key(
            username=username,
            keyfile=keyfile,
            allow_agent=True
        )

    @staticmethod
    def __check_keyfile_existence(hpc_key_path):
        if os.path.exists(hpc_key_path) and os.path.isfile(hpc_key_path):
            return hpc_key_path
        return None

    # TODO: Handle the output and return_code instead of just returning them
    # Execute blocking commands
    # Waiting for an output and return_code
    def execute_blocking(self, command, stdout=True, stderr=True, rc=True):
        output, err, return_code = self.__ssh.execute_command(
            command=command,
            return_stdout=stdout,
            return_stderr=stderr,
            return_rc=rc
        )

        return output, err, return_code

    # Execute non-blocking commands
    # Does not return anything as expected
    def execute_non_blocking(self, command):
        self.__ssh.start_command(command)

    def put_file(self, source, destination):
        self.__ssh.put_file(
            source=source,
            destination=destination,
            mode=self.mode,
            scp=self.scp,
            scp_preserve_times=self.scp_preserve_times
        )

    def put_directory(self, source, destination, recursive=True):
        self.__ssh.put_directory(
            source=source,
            destination=destination,
            mode=self.mode,
            recursive=recursive,
            scp=self.scp,
            scp_preserve_times=self.scp_preserve_times
        )

    def get_file(self, source, destination):
        self.__ssh.get_file(
            source=source,
            destination=destination,
            scp=self.scp,
            scp_preserve_times=self.scp_preserve_times
        )

    def get_directory(self, source, destination, recursive=True):
        self.__ssh.get_directory(
            source=source,
            destination=destination,
            recursive=recursive,
            scp=self.scp,
            scp_preserve_times=self.scp_preserve_times
        )

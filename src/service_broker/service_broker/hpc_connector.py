import os
import SSHLibrary

from .constants import (
    HPC_KEY_PATH,
    HPC_HOME_PATH,
)


# The Service broker uses the SSHCommunication class
# to communicate with the HPC environment
# TODO: Implement appropriate error handling
class HPCConnector:
    def __init__(self, scp="ON", scp_preserve_times=True, mode="0755"):
        # TODO: Handle the exceptions properly
        # E.g., when not connected to GOENET the SSH connection fails
        self.scp = scp
        self.scp_preserve_times = scp_preserve_times
        self.mode = mode
        self.hpc_home_path = HPC_HOME_PATH

        self.__ssh = SSHLibrary.SSHLibrary()
        self.__connection_index = None
        self.__login = None

    def connect_to_hpc(self, host, username, key_path):
        keyfile = self.__check_keyfile(key_path)
        # Provided key path not found
        if not keyfile:
            print(f"Warning: HPC key path does not exist or is not readable!")
            print(f"Checked path: \n{key_path}")
            print(f"Trying to find the default key file.")
            # Try to find keys in the default paths
            keyfile = self.__check_default_keyfile()

        self.__connection_index = self.__ssh.open_connection(host=host)
        self.__login = self.__ssh.login_with_public_key(
            username=username,
            keyfile=keyfile,
            allow_agent=True
        )

    @staticmethod
    def __check_keyfile(hpc_key_path):
        if os.path.exists(hpc_key_path) and os.path.isfile(hpc_key_path):
            return hpc_key_path
        return None

    @staticmethod
    def __check_default_keyfile():
        # TODO: Trigger an Exception instead of exiting if key not found
        if os.path.exists(HPC_KEY_PATH) and os.path.isfile(HPC_KEY_PATH):
            return HPC_KEY_PATH

        print(f"Default HPC key path do not exist or is not readable!")
        print(f"Checked paths: \n{HPC_KEY_PATH}")
        exit(1)

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

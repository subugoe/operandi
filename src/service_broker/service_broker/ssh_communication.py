import os
import SSHLibrary

from .constants import (
    HPC_HOST,
    HPC_USERNAME,
    HPC_KEY_PATH,
    HPC_KEY_VM_PATH,
    HPC_HOME_PATH,
    HPC_DEFAULT_COMMAND,
    SCP,
    SCP_PRESERVE_TIMES,
    MODE
)


# The Service broker will use the SSHCommunication class
# to communicate with the HPC environment

# This is just a dummy implementation
# TODO: Improve the code and implement appropriate error handling
class SSHCommunication:
    def __init__(self,
                 hpc_host=HPC_HOST,
                 hpc_username=HPC_USERNAME,
                 hpc_key_path=HPC_KEY_PATH,
                 scp=SCP,
                 scp_preserve_times=SCP_PRESERVE_TIMES,
                 mode=MODE):
        # TODO: Handle the exceptions properly
        # E.g., when not connected to GOENET the SSH connection fails
        self._scp = scp
        self._scp_preserve_times = scp_preserve_times
        self._mode = mode

        found_key_path = self.__check_for_hpc_keys(hpc_key_path)
        self.__ssh = SSHLibrary.SSHLibrary()
        self.__connect(host=hpc_host,
                       username=hpc_username,
                       keyfile=found_key_path)
        self.home_path = HPC_HOME_PATH

    @staticmethod
    def __check_for_hpc_keys(hpc_key_path):
        # Check the argument path
        if os.path.exists(hpc_key_path) and os.path.isfile(hpc_key_path):
            return hpc_key_path
        # Check the default VM path (in case the broker runs inside the Cloud VM
        elif os.path.exists(HPC_KEY_VM_PATH) and os.path.isfile(HPC_KEY_VM_PATH):
            return HPC_KEY_VM_PATH
        else:
            print(f"HPC key path does not exist or is not readable!")
            print(f"Checked paths: \n{hpc_key_path}\n{HPC_KEY_VM_PATH}")
            exit(1)

    def __connect(self, host, username, keyfile):
        self.__connection_index = self.__ssh.open_connection(host=host)
        self.__login = self.__ssh.login_with_public_key(username=username,
                                                        keyfile=keyfile,
                                                        allow_agent=True)

    # TODO: Handle the output and return_code instead of just returning them
    # Execute blocking commands
    # Waiting for an output and return_code
    def execute_blocking(self,
                         command=HPC_DEFAULT_COMMAND,
                         return_stdout=True,
                         return_stderr=True,
                         return_rc=True):
        output, err, return_code = self.__ssh.execute_command(command=command,
                                                              return_stdout=return_stdout,
                                                              return_stderr=return_stderr,
                                                              return_rc=return_rc)

        return output, err, return_code

    # Execute non-blocking commands
    # Does not return anything as expected
    def execute_non_blocking(self,
                             command=HPC_DEFAULT_COMMAND):
        self.__ssh.start_command(command)

    def put_file(self, source, destination):
        self.__ssh.put_file(source=source,
                            destination=destination,
                            mode=self._mode,
                            scp=self._scp,
                            scp_preserve_times=self._scp_preserve_times)

    def put_directory(self, source, destination, recursive=True):
        self.__ssh.put_directory(source=source,
                                 destination=destination,
                                 mode=self._mode,
                                 recursive=recursive,
                                 scp=self._scp,
                                 scp_preserve_times=self._scp_preserve_times)

    def get_file(self, source, destination):
        self.__ssh.get_file(source=source,
                            destination=destination,
                            scp=self._scp,
                            scp_preserve_times=self._scp_preserve_times)

    def get_directory(self, source, destination, recursive=True):
        self.__ssh.get_directory(source=source,
                                 destination=destination,
                                 recursive=recursive,
                                 scp=self._scp,
                                 scp_preserve_times=self._scp_preserve_times)

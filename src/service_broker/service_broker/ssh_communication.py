import os
import SSHLibrary

from .constants import (
    HPC_HOST,
    HPC_USERNAME,
    HPC_KEY_PATH,
    HPC_KEY_PATH2,
    HPC_HOME_PATH,
    SCP,
    SCP_PRESERVE_TIMES,
    MODE,
)


# The Service broker will use the SSHCommunication class
# to communicate with the HPC environment

# This is just a dummy implementation
# TODO: Improve the code and implement appropriate error handling
class SSHCommunication:
    def __init__(self):
        # TODO: Handle the exceptions properly
        # E.g., when not connected to GOENET the SSH connection fails
        self._SCP = SCP
        self._SCP_PRESERVE_TIMES = SCP_PRESERVE_TIMES
        self._MODE = MODE

        key_path = self.__check_hpc_key()
        self.__ssh = SSHLibrary.SSHLibrary()
        self.__connect_with_public_key(host=HPC_HOST,
                                       username=HPC_USERNAME,
                                       keyfile=key_path)
        self.home_path = HPC_HOME_PATH

    @staticmethod
    def __check_hpc_key():
        if os.path.exists(HPC_KEY_PATH) and os.path.isfile(HPC_KEY_PATH):
            return HPC_KEY_PATH
        elif os.path.exists(HPC_KEY_PATH2) and os.path.isfile(HPC_KEY_PATH2):
            return HPC_KEY_PATH2
        else:
            print(f"HPC key path does not exist or is not readable!")
            print(f"HPC_KEY_PATH: {HPC_KEY_PATH}")
            print(f"HPC_KEY_PATH2: {HPC_KEY_PATH2}")
            exit(1)

    def __connect_with_public_key(self, host, username, keyfile):
        self.__connection_index = self.__ssh.open_connection(host=host)
        self.__login = self.__ssh.login_with_public_key(username=username,
                                                        keyfile=keyfile,
                                                        allow_agent=True)

    # TODO: Handle the output and return_code instead of just returning them
    # Execute blocking commands
    # Waiting for an output and return_code
    def execute_blocking(self,
                         command="ls -la",
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
                             command="ls -la"):
        self.__ssh.start_command(command)

    def put_file(self, source, destination):
        self.__ssh.put_file(source=source,
                            destination=destination,
                            mode=self._MODE,
                            scp=self._SCP,
                            scp_preserve_times=self._SCP_PRESERVE_TIMES)

    def put_directory(self, source, destination, recursive=True):
        self.__ssh.put_directory(source=source,
                                 destination=destination,
                                 mode=self._MODE,
                                 recursive=recursive,
                                 scp=self._SCP,
                                 scp_preserve_times=self._SCP_PRESERVE_TIMES)

    def get_file(self, source, destination):
        self.__ssh.get_file(source=source,
                            destination=destination,
                            scp=self._SCP,
                            scp_preserve_times=self._SCP_PRESERVE_TIMES)

    def get_directory(self, source, destination, recursive=True):
        self.__ssh.get_directory(source=source,
                                 destination=destination,
                                 recursive=recursive,
                                 scp=self._SCP,
                                 scp_preserve_times=self._SCP_PRESERVE_TIMES)

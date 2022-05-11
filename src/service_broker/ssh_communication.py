import os
from SSHLibrary import SSHLibrary

from constants import (
    HPC_IP,
    HPC_USERNAME,
    HPC_KEY_PATH,
)


# The Service broker will use the SSHCommunication class
# to communicate with the HPC environment

# This is just a dummy implementation
# TODO: Improve the code and implement appropriate error handling
class SSHCommunication:
    def __init__(self):
        print(f"SSH Communication Constructor:")
        self.__ssh = SSHLibrary()
        if not os.path.exists(HPC_KEY_PATH) or not os.path.isfile(HPC_KEY_PATH):
            print(f"{HPC_KEY_PATH} file does not exist or is not a readable file!")
            exit(1)

        self.__connect_with_public_key(host=HPC_IP,
                                       username=HPC_USERNAME,
                                       keyfile=HPC_KEY_PATH)

    def __del__(self):
        print(f"SSHCommunication Destructor")

    # Example code to create a connection with a username and password
    def __connect_login(self, host, username, password):
        self.__connection_index = self.__ssh.open_connection(host=host)
        self.__login = self.__ssh.login(username=username,
                                        password=password)

    def __connect_with_public_key(self, host, username, keyfile):
        self.__connection_index = self.__ssh.open_connection(host=host)
        self.__login = self.__ssh.login_with_public_key(username=username,
                                                        keyfile=keyfile,
                                                        allow_agent=True)
        # print(f"Login: {self.__login}")

    # TODO: Handle the output and return_code instead of just returning them
    # Execute blocking commands
    # Waiting for an output and return_code
    def execute_blocking(self, command="ls -la", return_stdout=True, return_stderr=True, return_rc=True):
        output, err, return_code = self.__ssh.execute_command(command=command,
                                                              return_stdout=return_stdout,
                                                              return_stderr=return_stderr,
                                                              return_rc=return_rc)

        return output, err, return_code

    # Execute non-blocking commands
    # Does not return anything as expected
    def execute_non_blocking(self, command="ls -la"):
        self.__ssh.start_command(command)

    # TODO: Improve the wrappers and set the defaults appropriately
    # The next few functions are wrapper functions with simplified parameters
    # We can abstract some parameters as constants to simplify the signature

    def put_file(self, source, destination):
        mode = "0744"
        scp = "ON"
        scp_preserve_times = True
        self.__ssh.put_file(source=source,
                            destination=destination,
                            mode=mode,
                            scp=scp,
                            scp_preserve_times=scp_preserve_times)

    def put_directory(self, source, destination, recursive=True):
        mode = "0744"
        scp = "ON"
        scp_preserve_times = True
        self.__ssh.put_directory(source=source,
                                 destination=destination,
                                 mode=mode,
                                 recursive=recursive,
                                 scp=scp,
                                 scp_preserve_times=scp_preserve_times)

    def get_file(self, source, destination):
        scp = "ON"
        scp_preserve_times = True
        self.__ssh.get_file(source=source,
                            destination=destination,
                            scp=scp,
                            scp_preserve_times=scp_preserve_times)

    def get_directory(self, source, destination, recursive=True):
        scp = "ON"
        scp_preserve_times = True
        self.__ssh.get_directory(source=source,
                                 destination=destination,
                                 recursive=recursive,
                                 scp=scp,
                                 scp_preserve_times=scp_preserve_times)

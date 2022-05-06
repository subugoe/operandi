from SSHLibrary import SSHLibrary


# The Service broker will use the SSHCommunication class
# to communicate with the HPC environment

# This is just a dummy implementation
# TODO: Improve the code and implement appropriate error handling
class SSHCommunication:
    def __init__(self):
        print(f"Constructor:")
        self.__ssh = SSHLibrary()
        self.__connect(host="192.168.8.123",
                       user="example_user",
                       password="example_password")

    def __del__(self):
        print(f"Destructor")

    # Example code to create a connection
    def __connect(self, host, user, password):
        self.__connection_index = self.__ssh.open_connection("192.168.8.123")
        self.__login = self.__ssh.login("ayush_user", "password")

    # TODO: Handle the output and return_code instead of just returning them
    # Execute blocking commands
    # Waiting for an output and return_code
    def execute_blocking(self, command="ls -la", return_rc=True, return_stdout=True):
        output, return_code = self.__ssh.execute_command(command=command,
                                                         return_rc=return_rc,
                                                         return_stdout=return_stdout)

        return output, return_code

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

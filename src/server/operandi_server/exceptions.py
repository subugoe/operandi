# TODO: This needs a better organization and inheritance structure

class AuthenticationError(Exception):
    pass


class RegistrationError(Exception):
    pass


class ResponseException(Exception):
    def __init__(self, status_code: int, body: dict):
        self.status_code = status_code
        self.body = body


class WorkspaceException(Exception):
    pass


class WorkflowException(Exception):
    pass


class WorkspaceNotValidException(WorkspaceException):
    pass


class WorkspaceGoneException(WorkspaceException):
    pass


class WorkflowJobException(WorkflowException):
    pass

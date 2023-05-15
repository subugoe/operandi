class AuthenticationError(Exception):
    pass


class RegistrationError(Exception):
    pass


class ResponseException(Exception):
    def __init__(self, status_code: int, body: dict):
        self.status_code = status_code
        self.body = body

from click import ParamType
from .utils import verify_database_uri, verify_and_parse_mq_uri


class QueueServerParamType(ParamType):
    name = "RabbitMQ server string format"

    def convert(self, value, param, ctx):
        try:
            verify_and_parse_mq_uri(value)  # perform validation check only
        except Exception as error:
            self.fail(message=f"{error}", param=param, ctx=ctx)
        return value


class DatabaseParamType(ParamType):
    name = "MongoDB string format"

    def convert(self, value, param, ctx):
        try:
            verify_database_uri(value)  # perform validation check only
        except Exception as error:
            self.fail(message=f"{error}", param=param, ctx=ctx)
        return value

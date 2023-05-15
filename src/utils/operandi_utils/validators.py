from click import ParamType

from .utils import (
    verify_database_uri,
    verify_and_parse_mq_uri
)


class QueueServerParamType(ParamType):
    name = 'Message queue server string format'

    def convert(self, value, param, ctx):
        try:
            # perform validation check only
            verify_and_parse_mq_uri(value)
        except Exception as error:
            self.fail(f'{error}', param, ctx)
        return value


class DatabaseParamType(ParamType):
    name = 'Database string format'

    def convert(self, value, param, ctx):
        try:
            # perform validation check only
            verify_database_uri(value)
        except Exception as error:
            self.fail(f'{error}', param, ctx)
        return value

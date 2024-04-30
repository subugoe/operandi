from enum import Enum


class ServerApiTags(str, Enum):
    DISCOVERY = "discovery"
    USER = "user"
    WORKFLOW = "workflow"
    WORKSPACE = "workspace"

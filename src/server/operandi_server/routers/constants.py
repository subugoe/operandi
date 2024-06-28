from enum import Enum


class ServerApiTags(str, Enum):
    ADMIN = "admin"
    DISCOVERY = "discovery"
    USER = "user"
    WORKFLOW = "workflow"
    WORKSPACE = "workspace"

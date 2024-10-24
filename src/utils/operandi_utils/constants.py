from __future__ import annotations
from dotenv import load_dotenv
from enum import Enum
from typing import List

try:
    from importlib.metadata import distribution as get_distribution
except ImportError:
    from importlib_metadata import distribution as get_distribution

__all__ = [
    "AccountType",
    "LOG_FORMAT",
    "LOG_LEVEL_BROKER",
    "LOG_LEVEL_HARVESTER",
    "LOG_LEVEL_RMQ_CONSUMER",
    "LOG_LEVEL_RMQ_PUBLISHER",
    "LOG_LEVEL_SERVER",
    "LOG_LEVEL_WORKER",
    "MODULE_TYPES",
    "OLA_HD_BAG_ENDPOINT",
    "OLA_HD_USER",
    "OLA_HD_PASSWORD",
    "OPERANDI_VERSION",
    "ServerApiTag",
    "StateJob",
    "StateJobSlurm",
    "StateWorkspace",
]

load_dotenv()

LOG_FORMAT: str = "%(levelname) -7s %(asctime)s %(name) -30s %(funcName) -35s %(lineno) -5d: %(message)s"
LOG_LEVEL_SERVER: str = "INFO"
LOG_LEVEL_HARVESTER: str = "INFO"
LOG_LEVEL_BROKER: str = "INFO"
LOG_LEVEL_WORKER: str = "INFO"
LOG_LEVEL_RMQ_CONSUMER: str = "INFO"
LOG_LEVEL_RMQ_PUBLISHER: str = "INFO"

MODULE_TYPES = ["server", "harvester", "broker", "worker"]

# Notes left by @joschrew
# OLA-HD development instance, reachable only when connected to GÖNET
OLA_HD_BAG_ENDPOINT = "http://141.5.99.53/api/bag"
# The credentials are already publicly available inside the OLA-HD repo
# Ignore docker warnings about exposed credentials
OLA_HD_USER = "admin"
OLA_HD_PASSWORD = "JW24G.xR"

OPERANDI_VERSION = get_distribution("operandi_utils").version


class AccountType(str, Enum):
    ADMIN = "ADMIN"
    HARVESTER = "HARVESTER"
    MACHINE = "MACHINE"
    USER = "USER"
    UNSET = "UNSET"


class ServerApiTag(str, Enum):
    ADMIN = "admin"
    DISCOVERY = "discovery"
    USER = "user"
    WORKFLOW = "workflow"
    WORKSPACE = "workspace"


class StateJob(str, Enum):
    FAILED = "FAILED"
    QUEUED = "QUEUED"
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    TRANSFERRING_TO_HPC = "TRANSFERRING_TO_HPC"
    TRANSFERRING_FROM_HPC = "TRANSFERRING_FROM_HPC"
    UNSET = "UNSET"

    @staticmethod
    def convert_from_slurm_job(slurm_job_state: str) -> StateJob:
        if StateJobSlurm.is_state_success(slurm_job_state):
            return StateJob.SUCCESS
        if StateJobSlurm.is_state_waiting(slurm_job_state):
            return StateJob.PENDING
        if StateJobSlurm.is_state_running(slurm_job_state):
            return StateJob.RUNNING
        if StateJobSlurm.is_state_fail(slurm_job_state):
            return StateJob.FAILED
        raise ValueError(f"Invalid slurm job state: {slurm_job_state}")


class StateJobSlurm(str, Enum):
    # REFERENCE: https://slurm.schedmd.com/sacct.html#SECTION_JOB-STATE-CODES
    # Fail indicating states
    BOOT_FAIL = "BOOT_FAIL"
    CANCELLED = "CANCELLED"
    DEADLINE = "DEADLINE"
    FAILED = "FAILED"
    NODE_FAIL = "NODE_FAIL"
    OUT_OF_MEMORY = "OUT_OF_MEMORY"
    PREEMPTED = "PREEMPTED"
    REVOKED = "REVOKED"
    TIMEOUT = "TIMEOUT"
    # Success indicating states
    COMPLETED = "COMPLETED"
    # Waiting indicating states
    COMPLETING = "COMPLETING"
    PENDING = "PENDING"
    REQUEUED = "REQUEUED"
    RESIZING = "RESIZING"
    RUNNING = "RUNNING"
    SUSPENDED = "SUSPENDED"
    # Operandi defined for default value
    UNSET = "UNSET"

    @staticmethod
    def failing_states() -> List[StateJobSlurm]:
        return [StateJobSlurm.BOOT_FAIL, StateJobSlurm.CANCELLED, StateJobSlurm.DEADLINE, StateJobSlurm.FAILED,
                StateJobSlurm.NODE_FAIL, StateJobSlurm.OUT_OF_MEMORY, StateJobSlurm.PREEMPTED, StateJobSlurm.REVOKED,
                StateJobSlurm.TIMEOUT, StateJobSlurm.SUSPENDED]

    @staticmethod
    def success_states() -> List[StateJobSlurm]:
        return [StateJobSlurm.COMPLETED]

    @staticmethod
    def waiting_states() -> List[StateJobSlurm]:
        return [StateJobSlurm.PENDING, StateJobSlurm.COMPLETING, StateJobSlurm.REQUEUED, StateJobSlurm.RESIZING]

    @staticmethod
    def running_states() -> List[StateJobSlurm]:
        return [StateJobSlurm.RUNNING]

    @staticmethod
    def is_state_fail(slurm_job_state: str) -> bool:
        if slurm_job_state in StateJobSlurm.failing_states():
            return True
        return False

    @staticmethod
    def is_state_waiting(slurm_job_state: str) -> bool:
        if slurm_job_state in StateJobSlurm.waiting_states():
            return True
        return False

    @staticmethod
    def is_state_running(slurm_job_state: str) -> bool:
        if slurm_job_state in StateJobSlurm.running_states():
            return True
        return False

    @staticmethod
    def is_state_success(slurm_job_state: str) -> bool:
        if slurm_job_state in StateJobSlurm.success_states():
            return True
        return False


class StateWorkspace(str, Enum):
    RUNNING = "RUNNING"
    QUEUED = "QUEUED"
    PENDING = "PENDING"
    READY = "READY"
    TRANSFERRING_TO_HPC = "TRANSFERRING_TO_HPC"
    TRANSFERRING_FROM_HPC = "TRANSFERRING_FROM_HPC"
    UNSET = "UNSET"

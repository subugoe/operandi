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
    "LOG_LEVEL_CLIENT",
    "LOG_LEVEL_HARVESTER",
    "LOG_LEVEL_RMQ_CONSUMER",
    "LOG_LEVEL_RMQ_PUBLISHER",
    "LOG_LEVEL_SERVER",
    "LOG_LEVEL_WORKER",
    "MODULE_TYPES",
    "OCRD_PROCESSOR_EXECUTABLE_TO_IMAGE",
    "OPERANDI_VERSION",
    "ServerApiTag",
    "StateJob",
    "StateJobSlurm",
    "StateWorkspace",
]

load_dotenv()

LOG_FORMAT: str = "%(levelname) -7s %(asctime)s %(name) -30s %(funcName) -35s %(lineno) -5d: %(message)s"
LOG_LEVEL_SERVER: str = "INFO"
LOG_LEVEL_CLIENT: str = "INFO"
LOG_LEVEL_HARVESTER: str = "INFO"
LOG_LEVEL_BROKER: str = "INFO"
LOG_LEVEL_WORKER: str = "INFO"
LOG_LEVEL_RMQ_CONSUMER: str = "INFO"
LOG_LEVEL_RMQ_PUBLISHER: str = "INFO"

MODULE_TYPES = ["server", "harvester", "client", "broker", "worker"]

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
    OTON = "oton"
    OLAHD = "olahd"
    USER = "user"
    WORKFLOW = "workflow"
    WORKSPACE = "workspace"


class StateJob(str, Enum):
    FAILED = "FAILED"
    QUEUED = "QUEUED"
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    HPC_SUCCESS = "HPC_SUCCESS"
    HPC_FAILED = "HPC_FAILED"
    TRANSFERRING_TO_HPC = "TRANSFERRING_TO_HPC"
    TRANSFERRING_FROM_HPC = "TRANSFERRING_FROM_HPC"
    UNSET = "UNSET"

    @staticmethod
    def convert_from_slurm_job(slurm_job_state: str) -> StateJob:
        if StateJobSlurm.is_state_hpc_success(slurm_job_state):
            return StateJob.HPC_SUCCESS
        if StateJobSlurm.is_state_waiting(slurm_job_state):
            return StateJob.PENDING
        if StateJobSlurm.is_state_running(slurm_job_state):
            return StateJob.RUNNING
        if StateJobSlurm.is_state_hpc_fail(slurm_job_state):
            return StateJob.HPC_FAILED
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
    def is_state_hpc_fail(slurm_job_state: str) -> bool:
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
    def is_state_hpc_success(slurm_job_state: str) -> bool:
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

# TODO: Find a more optimal way of achieving this dynamically
OCRD_PROCESSOR_EXECUTABLE_TO_IMAGE = {
    "ocrd_all": "ocrd_all_maximum_image.sif",
    "ocrd": "ocrd_core.sif",
    "ocrd-tesserocr-crop": "ocrd_tesserocr.sif",
    "ocrd-tesserocr-deskew": "ocrd_tesserocr.sif",
    "ocrd-tesserocr-recognize": "ocrd_tesserocr.sif",
    "ocrd-tesserocr-segment": "ocrd_tesserocr.sif",
    "ocrd-tesserocr-segment-line": "ocrd_tesserocr.sif",
    "ocrd-tesserocr-segment-region": "ocrd_tesserocr.sif",
    "ocrd-tesserocr-segment-table": "ocrd_tesserocr.sif",
    "ocrd-tesserocr-segment-word": "ocrd_tesserocr.sif",
    "ocrd-tesserocr-fontshape": "ocrd_tesserocr.sif",
    "ocrd-tesserocr-binarize": "ocrd_tesserocr.sif",
    "ocrd-cis-ocropy-binarize": "ocrd_cis.sif",
    "ocrd-cis-ocropy-denoise": "ocrd_cis.sif",
    "ocrd-cis-ocropy-deskew": "ocrd_cis.sif",
    "ocrd-cis-ocropy-dewarp": "ocrd_cis.sif",
    "ocrd-cis-ocropy-segment": "ocrd_cis.sif",
    "ocrd-cis-ocropy-resegment": "ocrd_cis.sif",
    "ocrd-cis-ocropy-clip": "ocrd_cis.sif",
    "ocrd-cis-ocropy-recognize": "ocrd_cis.sif",
    "ocrd-cis-ocropy-train": "ocrd_cis.sif",
    "ocrd-cis-align": "ocrd_cis.sif",
    "ocrd-cis-postcorrect": "ocrd_cis.sif",
    "ocrd-kraken-recognize": "ocrd_kraken.sif",
    "ocrd-kraken-segment": "ocrd_kraken.sif",
    "ocrd-kraken-binarize": "ocrd_kraken.sif",
    "ocrd-preprocess-image": "ocrd_wrap.sif",
    "ocrd-skimage-normalize": "ocrd_wrap.sif",
    "ocrd-skimage-binarize": "ocrd_wrap.sif",
    "ocrd-skimage-denoise": "ocrd_wrap.sif",
    "ocrd-skimage-denoise-raw": "ocrd_wrap.sif",
    "ocrd-calamari-recognize": "ocrd_calamari.sif",
    "ocrd-olena-binarize": "ocrd_olena.sif",
    "ocrd-dinglehopper": "ocrd_dinglehopper.sif",
    "ocrd-eynollah-segment": "ocrd_eynollah.sif",
    "ocrd-fileformat-transform": "ocrd_fileformat.sif",
    "ocrd-nmalign-merge": "ocrd_nmalign.sif",
    "ocrd-segment-extract-glyphs": "ocrd_segment.sif",
    "ocrd-segment-extract-lines": "ocrd_segment.sif",
    "ocrd-segment-extract-pages": "ocrd_segment.sif",
    "ocrd-segment-extract-regions": "ocrd_segment.sif",
    "ocrd-segment-extract-words": "ocrd_segment.sif",
    "ocrd-segment-from-coco": "ocrd_segment.sif",
    "ocrd-segment-from-masks": "ocrd_segment.sif",
    "ocrd-segment-project": "ocrd_segment.sif",
    "ocrd-segment-repair": "ocrd_segment.sif",
    "ocrd-segment-replace-original": "ocrd_segment.sif",
    "ocrd-segment-replace-page": "ocrd_segment.sif",
    "ocrd-segment-replace-text": "ocrd_segment.sif",
    "ocrd-segment-evaluate": "ocrd_segment.sif",
    "ocrd-anybaseocr-dewarp": "ocrd_anybaseocr.sif",
    "ocrd-anybaseocr-crop": "ocrd_anybaseocr.sif",
    "ocrd-anybaseocr-binarize": "ocrd_anybaseocr.sif",
    "ocrd-anybaseocr-layout-analysis": "ocrd_anybaseocr.sif",
    "ocrd-anybaseocr-textline": "ocrd_anybaseocr.sif",
    "ocrd-anybaseocr-tiseg": "ocrd_anybaseocr.sif",
    "ocrd-anybaseocr-block-segmentation": "ocrd_anybaseocr.sif",
    "ocrd-anybaseocr-deskew": "ocrd_anybaseocr.sif",
    "ocrd-sbb-binarize": "ocrd_sbb_binarization.sif",
    "ocrd-detectron2-segment": "ocrd_detectron2.sif",
    "ocrd-froc": "ocrd_froc.sif",
    "ocrd-pagetopdf": "ocrd_pagetopdf.sif",
    "ocrd-keraslm-rate": "ocrd_keraslm.sif",
    "ocrd-docstruct": "ocrd_docstruct.sif",
    "ocrd-doxa-binarize": "ocrd_doxa.sif",
    "ocrd-im6convert": "ocrd_im6convert.sif",
    "ocrd-olahd-client": "ocrd_olahd-client.sif",
    "ocrd-cor-asv-ann-mark": "ocrd_cor-asv-ann.sif",
    "ocrd-cor-asv-ann-align": "ocrd_cor-asv-ann.sif",
    "ocrd-cor-asv-ann-evaluate": "ocrd_cor-asv-ann.sif",
    "ocrd-cor-asv-ann-join": "ocrd_cor-asv-ann.sif",
    "ocrd-cor-asv-ann-process": "ocrd_cor-asv-ann.sif"
}

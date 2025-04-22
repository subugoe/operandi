__all__ = [
    "HPC_BATCH_SUBMIT_WORKFLOW_JOB",
    "HPC_JOB_DEADLINE_TIME_REGULAR",
    "HPC_JOB_DEADLINE_TIME_TEST",
    "HPC_NHR_JOB_DEFAULT_PARTITION",
    "HPC_NHR_JOB_TEST_PARTITION",
    "HPC_JOB_QOS_DEFAULT",
    "HPC_JOB_QOS_LONG",
    "HPC_JOB_QOS_SHORT",
    "HPC_JOB_QOS_VERY_LONG",
    "HPC_SSH_CONNECTION_TRY_TIMES",
    "HPC_NHR_PROJECT",
    "HPC_NHR_CLUSTERS",
    "HPC_USE_SLIM_IMAGES",
    "HPC_WRAPPER_SUBMIT_WORKFLOW_JOB",
    "HPC_WRAPPER_CHECK_WORKFLOW_JOB_STATUS"
]

HPC_NHR_PROJECT: str = "project_pwieder_ocr_nhr"

# https://docs.hpc.gwdg.de/start_here/connecting/login_nodes_and_example_commands/index.html#the-login-nodes
# https://docs.hpc.gwdg.de/how_to_use/the_storage_systems/data_stores/scratch_work/index.html#nhr
HPC_NHR_SCRATCH_EMMY_HDD: str = f"/mnt/lustre-emmy-hdd/projects/{HPC_NHR_PROJECT}"  # Capacity - 8.4 PiB
HPC_NHR_SCRATCH_EMMY_SSD: str = f"/mnt/lustre-emmy-ssd/projects/{HPC_NHR_PROJECT}"  # Capacity - 110 TiB
HPC_NHR_SCRATCH_GRETE_SSD: str = f"/mnt/lustre-grete/projects/{HPC_NHR_PROJECT}"  # Capacity - 509 TiB

HPC_NHR_CLUSTERS = {
    "EmmyPhase1": {
        "host": "glogin-p1.hpc.gwdg.de",
        "scratch-emmy-hdd": HPC_NHR_SCRATCH_EMMY_HDD,
        "scratch-emmy-ssd": HPC_NHR_SCRATCH_EMMY_SSD,
        "scratch-grete-ssd": ""  # No Access
    },
    "EmmyPhase2": {
        "host": "glogin-p2.hpc.gwdg.de",
        "scratch-emmy-hdd": HPC_NHR_SCRATCH_EMMY_HDD,
        "scratch-emmy-ssd": HPC_NHR_SCRATCH_EMMY_SSD,
        "scratch-grete-ssd": ""  # No Access
    },
    "EmmyPhase3": {
        "host": "glogin-p3.hpc.gwdg.de",
        "scratch-emmy-hdd": HPC_NHR_SCRATCH_EMMY_HDD,
        "scratch-emmy-ssd": HPC_NHR_SCRATCH_EMMY_SSD,
        "scratch-grete-ssd": HPC_NHR_SCRATCH_GRETE_SSD
    },
    "Grete": {
        "host": "glogin-gpu.hpc.gwdg.de",
        "scratch-emmy-hdd": HPC_NHR_SCRATCH_EMMY_HDD,
        "scratch-emmy-ssd": HPC_NHR_SCRATCH_EMMY_SSD,
        "scratch-grete-ssd": HPC_NHR_SCRATCH_GRETE_SSD
    },
    "KISSKI": {
        "host": "glogin9.hpc.gwdg.de",
        "scratch-emmy-hdd": HPC_NHR_SCRATCH_EMMY_HDD,
        "scratch-emmy-ssd": HPC_NHR_SCRATCH_EMMY_SSD,
        "scratch-grete-ssd": HPC_NHR_SCRATCH_GRETE_SSD
    }
}

HPC_BATCH_SUBMIT_WORKFLOW_JOB: str = f"batch_submit_workflow_job.sh"
HPC_WRAPPER_SUBMIT_WORKFLOW_JOB: str = f"wrapper_submit_workflow_job.sh"
HPC_WRAPPER_CHECK_WORKFLOW_JOB_STATUS: str = f"wrapper_check_workflow_job_status.sh"

HPC_JOB_DEADLINE_TIME_REGULAR = "48:00:00"
HPC_JOB_DEADLINE_TIME_TEST = "00:30:00"
# TODO: Use again "standard96s:shared"
HPC_NHR_JOB_DEFAULT_PARTITION = "standard96:shared"
HPC_NHR_JOB_TEST_PARTITION = "standard96:shared"

# Check here: https://docs.hpc.gwdg.de/getting_started/transition/index.html
HPC_JOB_QOS_SHORT = "2h"
HPC_JOB_QOS_DEFAULT = "48h"  # The default deadline for non-specified QOS is 48h
HPC_JOB_QOS_LONG = "7d"
HPC_JOB_QOS_VERY_LONG = "14d"
HPC_SSH_CONNECTION_TRY_TIMES = 30

# A switch to decide whether to use the fat ocrd_all image or slim images of the processors
HPC_USE_SLIM_IMAGES: bool = False

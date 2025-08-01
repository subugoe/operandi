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
    "HPC_WRAPPER_SUBMIT_WORKFLOW_JOB",
    "HPC_WRAPPER_CHECK_WORKFLOW_JOB_STATUS"
]

HPC_NHR_PROJECT: str = "project_pwieder_ocr_nhr"
HPC_NHR_VAST = f"/mnt/vast-nhr/projects/{HPC_NHR_PROJECT}"

HPC_NHR_CLUSTERS = {
    "EmmyPhase1": {
        "host": "glogin-p1.hpc.gwdg.de",
        "vast-nhr": HPC_NHR_VAST
    },
    "EmmyPhase2": {
        "host": "glogin-p2.hpc.gwdg.de",
        "vast-nhr": HPC_NHR_VAST
    },
    "EmmyPhase3": {
        "host": "glogin-p3.hpc.gwdg.de",
        "vast-nhr": HPC_NHR_VAST
    },
    "Grete": {
        "host": "glogin-gpu.hpc.gwdg.de",
        "vast-nhr": HPC_NHR_VAST
    },
    "KISSKI": {
        "host": "glogin9.hpc.gwdg.de",
        "vast-nhr": HPC_NHR_VAST
    }
}

HPC_BATCH_SUBMIT_WORKFLOW_JOB: str = f"batch_submit_workflow_job.sh"
HPC_WRAPPER_SUBMIT_WORKFLOW_JOB: str = f"wrapper_submit_workflow_job.sh"
HPC_WRAPPER_CHECK_WORKFLOW_JOB_STATUS: str = f"wrapper_check_workflow_job_status.sh"

HPC_JOB_DEADLINE_TIME_REGULAR = "48:00:00"
HPC_JOB_DEADLINE_TIME_TEST = "00:30:00"
HPC_NHR_JOB_DEFAULT_PARTITION = "standard96:shared"
HPC_NHR_JOB_TEST_PARTITION = "standard96:shared"

# Check here: https://docs.hpc.gwdg.de/getting_started/transition/index.html
HPC_JOB_QOS_SHORT = "2h"
HPC_JOB_QOS_DEFAULT = "48h"  # The default deadline for non-specified QOS is 48h
HPC_JOB_QOS_LONG = "7d"
HPC_JOB_QOS_VERY_LONG = "14d"
HPC_SSH_CONNECTION_TRY_TIMES = 30

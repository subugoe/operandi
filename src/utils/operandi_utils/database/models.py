from beanie import Document
from typing import Optional

# NOTE: Database models must not reuse any
# response models [discovery, processor, user, workflow, workspace]
# Database models are supposed to be low level models


class DBUserAccount(Document):
    """
    Model to store a user account in the database

    Attributes:
        email:          The e-mail address of the user
        encrypted_pass: The encrypted password of the user
        salt:           Random salt value used when encrypting the password
        approved_user:  Whether the user is approved by the admin
        account_type:   The type of the account: administrator, user, or harvester

    By default, the registered user's account is not validated.
    An admin must manually validate the account by assigning True value.
    """
    email: str
    encrypted_pass: str
    salt: str
    account_type: str
    approved_user: bool = False

    class Settings:
        name = "user_accounts"


class DBWorkspace(Document):
    """
    Model to store a workspace in the mongo-database.

    Information to handle workspaces and from bag-info.txt are stored here.

    Attributes:
        ocrd_identifier             Ocrd-Identifier (mandatory)
        bagit_profile_identifier    BagIt-Profile-Identifier (mandatory)
        ocrd_base_version_checksum  Ocrd-Base-Version-Checksum (mandatory)
        mets_basename               Alternative name to the default "mets.xml"
        bag_info_adds               bag-info.txt can also (optionally) contain additional
                                    key-value-pairs which are saved here
    """
    workspace_id: str
    workspace_dir: str
    workspace_mets_path: str
    ocrd_identifier: str
    bagit_profile_identifier: str
    ocrd_base_version_checksum: Optional[str]
    mets_basename: Optional[str]
    bag_info_adds: Optional[dict]
    deleted: bool = False

    class Settings:
        name = "workspaces"


class DBWorkflow(Document):
    """
    Model to store a workflow in the mongo-database.

    Attributes:
        workflow_id             id of the workflow
        workflow_dir            dir of the workflow
        workflow_script_base    the name of the nextflow script file
        workflow_script_path    the full path of the workflow script
        deleted                 whether this record is deleted by the user
                                (still available in the DB itself)
    """
    workflow_id: str
    workflow_dir: str
    workflow_script_base: str
    workflow_script_path: str
    deleted: bool = False

    class Settings:
        name = "workflows"


class DBWorkflowJob(Document):
    """
    Model to store a Workflow-Job in the MongoDB.

    Attributes:
        job_id              the workflow job's id
        job_dir             the path of the workflow job dir
        job_state           current state of the workflow job
        workflow_id         id of the workflow the job is executing
        workspace_id        id of the workspace on which this job is running
        workflow_dir        dir of the workflow id
        workspace_dir       dir of the workspace id
        hpc_slurm_job_id    the id of the Slurm job that runs this workflow job
        deleted             whether this record is deleted by the user
                            (still available in the DB itself)
    """
    job_id: str
    job_dir: str
    job_state: str
    workflow_id: str
    workspace_id: str
    workflow_dir: str = None
    workspace_dir: str = None
    hpc_slurm_job_id: str = None
    deleted: bool = False

    class Settings:
        name = "workflow_jobs"


class DBHPCSlurmJob(Document):
    """
    Model to store an HPC slurm job in the MongoDB

    Attributes:
        workflow_job_id             the id of the workflow job
        hpc_slurm_job_id            the id of the Slurm job that runs this workflow job
        hpc_slurm_job_state         the state of the slurm job inside the HPC
        hpc_batch_script_path       path of the batch script inside the HPC
        hpc_slurm_workspace_path    path of the slurm workspace inside the HPC
        deleted                     whether this record is deleted by the user
                                    (still available in the DB itself)
    """
    workflow_job_id: str
    hpc_slurm_job_id: str
    hpc_slurm_job_state: str = None
    hpc_batch_script_path: str = None
    hpc_slurm_workspace_path: str = None
    deleted: bool = False

    class Settings:
        name = "hpc_slurm_jobs"

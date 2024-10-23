from typing import List, Optional
from beanie import Document
from datetime import datetime
from operandi_utils.constants import AccountType, StateJob, StateJobSlurm, StateWorkspace


class DBUserAccount(Document):
    """
    Model to store a user account in the database

    Attributes:
        institution_id  Unique id of the institution the user belongs to
        user_id:        Unique id of the user
        email:          The e-mail address of the user
        encrypted_pass: The encrypted password of the user
        salt:           Random salt value used when encrypting the password
        approved_user:  Whether the user is approved by the admin
        account_type:   The type of the account, any of the `AccountTypes`
        deleted:        Whether the entry has been deleted locally from the server
        datetime        Shows the created date time of the entry
        details         Extra user specified details about this entry

    By default, the registered user's account is not validated.
    An admin must manually validate the account by assigning True value.
    """
    institution_id: str
    user_id: str
    email: str
    encrypted_pass: str
    salt: str
    account_type: AccountType = AccountType.UNSET
    approved_user: bool = False
    deleted: bool = False
    datetime = datetime.now()
    details: Optional[str]

    class Settings:
        name = "user_accounts"

class DBProcessingStatistics(Document):
    """
    Model to store a user account in the database

    Attributes:
        institution_id:     Unique id of the institution the user belongs to
        user_id:            Unique id of the user to whom the statistics belong to
        pages_uploaded:     Total amount of pages uploaded as a workspace to the server
        pages_submitted:    Total amount of submitted pages in workflow jobs
        pages_succeed:      Total amount of successfully processed pages
        pages_failed:       Total amount of failed pages
        pages_downloaded:   Total amount of pages downloaded as a workspace from the server
        pages_cancel:       Total amount of cancelled pages
    """
    institution_id: str
    user_id: str
    pages_uploaded: int = 0
    pages_submitted: int = 0
    pages_succeed: int = 0
    pages_failed: int = 0
    pages_downloaded: int = 0
    pages_cancel: int = 0

    class Settings:
        name = "processing_statistics"

class DBHPCSlurmJob(Document):
    """
    Model to store an HPC slurm job in the MongoDB

    Attributes:
        user_id                     Unique id of the user who created the entry
        workflow_job_id             Unique id of the workflow job
        hpc_slurm_job_id            Unique id of the slurm job executing the current workflow job in the HPC
        hpc_slurm_job_state         The state of the slurm job inside the HPC
        hpc_batch_script_path       Full path of the batch script inside the HPC
        hpc_slurm_workspace_path    Full path of the slurm workspace inside the HPC
        deleted                     Whether the entry has been deleted locally from the server
        datetime                    Shows the created date time of the entry
        details                     Extra user specified details about this entry
    """
    user_id: str
    workflow_job_id: str
    hpc_slurm_job_id: str
    hpc_slurm_job_state: StateJobSlurm = StateJobSlurm.UNSET
    hpc_batch_script_path: Optional[str]
    hpc_slurm_workspace_path: Optional[str]
    deleted: bool = False
    datetime = datetime.now()
    details: Optional[str]

    class Settings:
        name = "hpc_slurm_jobs"

class DBWorkflow(Document):
    """
    Model to store a workflow in the mongo-database.

    Attributes:
        user_id                 Unique id of the user who created the entry
        workflow_id             Unique id of the workflow
        workflow_dir            Workflow directory full path on the server
        workflow_script_base    The name of the nextflow script file
        workflow_script_path    Nextflow workflow file full path on the server
        uses_mets_server        Whether the NF script forwards requests to a workspace mets server
        deleted                 Whether the entry has been deleted locally from the server
        datetime                Shows the created date time of the entry
        details                 Extra user specified details about this entry
    """
    user_id: str
    workflow_id: str
    workflow_dir: str
    workflow_script_base: str
    workflow_script_path: str
    uses_mets_server: bool
    deleted: bool = False
    datetime = datetime.now()
    details: Optional[str]

    class Settings:
        name = "workflows"


class DBWorkflowJob(Document):
    """
    Model to store a Workflow-Job in the MongoDB.

    Attributes:
        user_id             Unique id of the user who created the entry
        job_id              Unique id of the workflow job
        job_dir             Workflow job directory full path on the server
        job_state           The state of the workflow job inside the server
        workflow_id         Unique id of the workflow used by the workflow job
        workspace_id        Unique id of the workspace used by the workflow job
        workflow_dir        Workflow directory full path on the server used by the workflow job
        workspace_dir       Workspace directory full path on the server used by the workflow job
        hpc_slurm_job_id    Unique id of the slurm job executing the current workflow job in the HPC
        deleted             Whether the entry has been deleted locally from the server
        datetime            Shows the created date time of the entry
        details             Extra user specified details about this entry
    """
    user_id: str
    job_id: str
    job_dir: str
    workflow_id: str
    workspace_id: str
    job_state: StateJob = StateJob.UNSET
    workflow_dir: Optional[str]
    workspace_dir: Optional[str]
    hpc_slurm_job_id: Optional[str]
    deleted: bool = False
    datetime = datetime.now()
    details: Optional[str]

    class Settings:
        name = "workflow_jobs"


class DBWorkspace(Document):
    """
    Model to store a workspace in the mongo-database.

    Information to handle workspaces and from bag-info.txt are stored here.

    Attributes:
        user_id                     Unique id of the user who created the entry
        workspace_id                Unique id of the workspace
        workspace_dir               Workspace directory full path on the server
        workspace_mets_path         Workspace mets file full path on the server
        pages_amount                The amount of the physical pages, used for creating page ranges
        file_groups                 The list of available file groups
        state                       Whether the workspace is currently being processed or not
        ocrd_identifier             Ocrd-Identifier (mandatory)
        bagit_profile_identifier    BagIt-Profile-Identifier (mandatory)
        ocrd_base_version_checksum  Ocrd-Base-Version-Checksum (mandatory)
        mets_basename               Alternative name to the default "mets.xml"
        bag_info_adds               Bag-info.txt can also contain additional key-value-pairs which are saved here
        deleted                     Whether the entry has been deleted locally from the server
        datetime                    Shows the created date time of the entry
        details                     Extra user specified details about this entry
        created_by_user             Which user id has created the entry
    """
    user_id: str
    workspace_id: str
    workspace_dir: str
    workspace_mets_path: str
    pages_amount: int
    file_groups: List[str]
    state: StateWorkspace = StateWorkspace.UNSET
    ocrd_identifier: Optional[str]
    bagit_profile_identifier: Optional[str]
    ocrd_base_version_checksum: Optional[str]
    mets_basename: Optional[str]
    bag_info_adds: Optional[dict]
    deleted: bool = False
    datetime = datetime.now()
    details: Optional[str]

    class Settings:
        name = "workspaces"

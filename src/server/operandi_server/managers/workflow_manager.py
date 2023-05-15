from os import mkdir
from os.path import join
from typing import List, Union, Tuple

import operandi_utils.database.database as db
from operandi_utils.database.models import WorkflowJobDB

from ..exceptions import WorkflowJobException
from ..utils import generate_id
from .constants import WORKFLOWS_ROUTER
from .nextflow_manager import NextflowManager
from .resource_manager import ResourceManager
from .workspace_manager import WorkspaceManager


class WorkflowManager(ResourceManager):
    # Warning: Don't change these defaults
    # till everything is configured properly
    def __init__(self, log_level: str = "INFO"):
        super().__init__(logger_label=__name__, log_level=log_level, resource_router=WORKFLOWS_ROUTER)
        self.nf_version = NextflowManager.is_nf_available()
        if self.nf_version:
            self.log.info(f"Detected Nextflow version: {self.nf_version}")
        else:
            self.log.error(f"Detected Nextflow version: unable to detect")

    def get_workflows(self) -> List[Tuple[str, str]]:
        """
        Get a list of all available workflow urls.
        """
        return self.get_all_resources(local=False)

    async def create_workflow_space(self, file, uid: str = None) -> Tuple[str, str]:
        """
        Create a new workflow space. Upload a Nextflow script inside.

        Args:
            file: A Nextflow script
            uid (str): The uid is used as workflow_space-directory. If `None`, an uuid is created.
            If the corresponding dir is already existing, `None` is returned,

        """
        workflow_id, workflow_dir = self._create_resource_dir(uid)
        mkdir(workflow_dir)
        nf_script_dest = join(workflow_dir, file.filename)
        await self._receive_resource(file, nf_script_dest)
        await db.save_workflow(
            workflow_id=workflow_id,
            workflow_path=workflow_dir,
            workflow_script_path=nf_script_dest
        )

        workflow_url = self.get_resource(workflow_id, local=False)
        return workflow_id, workflow_url

    async def update_workflow_space(self, file, workflow_id: str) -> Tuple[str, str]:
        """
        Update a workflow space

        Delete the workflow space if existing and then delegate to
        :py:func:`ocrd_webapi.workflow_manager.WorkflowManager.create_workflow_space
        """
        self._delete_resource_dir(workflow_id)
        return await self.create_workflow_space(file, workflow_id)

    def create_workflow_execution_space(self, workflow_id: str) -> Tuple[str, Union[str, None]]:
        job_id = generate_id()
        job_dir = self.get_resource_job(workflow_id, job_id, local=True)
        mkdir(job_dir)
        return job_id, job_dir

    async def start_nf_workflow(self, workflow_id: str, workspace_id: str) -> Union[list, WorkflowJobException]:
        # The path to the Nextflow script inside workflow_id
        nf_script_path = self.get_resource_file(workflow_id, file_ext='.nf')
        workspace_mets_path = await db.get_workspace_mets_path(workspace_id=workspace_id)
        # workspace_dir = WorkspaceManager.static_get_resource(workspace_id, local=True)

        # TODO: These checks must happen inside the Resource Manager, not here
        if not nf_script_path:
            raise WorkflowJobException(f"Workflow script file not existing: {workflow_id}")
        if not workspace_mets_path:
            raise WorkflowJobException(f"Workspace mets file not existing: {workspace_id}")

        job_id, job_dir = self.create_workflow_execution_space(workflow_id)
        try:
            NextflowManager.execute_workflow(
                nf_script_path=nf_script_path,
                workspace_mets_path=workspace_mets_path,
                job_dir=job_dir
            )
            workflow_job_status = 'RUNNING'
            await db.save_workflow_job(job_id=job_id, workflow_id=workflow_id,
                                       workspace_id=workspace_id, job_path=job_dir, job_state=workflow_job_status)
        except Exception as error:
            # TODO: Integrate FAILED instead of STOPPED
            workflow_job_status = 'STOPPED'
            await db.save_workflow_job(job_id=job_id, workflow_id=workflow_id,
                                       workspace_id=workspace_id, job_path=job_dir, job_state=workflow_job_status)
            self.log.exception(f"Failed to execute workflow: {error}")
            raise WorkflowJobException(f"Failed to execute workflow: {workflow_id}, "f"with workspace: {workspace_id}")

        parameters = [
            # Workflow Job ID
            job_id,
            # Workflow Job URL
            self.get_resource_job(workflow_id, job_id, local=False),
            workflow_job_status,
            # Workflow URL
            self.get_resource(workflow_id, local=False),
            # Workspace URL
            WorkspaceManager.static_get_resource(workspace_id, local=False)
        ]
        return parameters

    async def get_workflow_job(self, workflow_id: str, job_id: str) -> Union[WorkflowJobDB, None]:
        wf_job_db = await db.get_workflow_job(job_id)
        job_dir = self.get_resource_job(workflow_id, job_id, local=True)
        # Check if a nextflow report is available in the job dir
        if NextflowManager.is_nf_report(job_dir):
            # If there is a report and the job state is not STOPPED/SUCCESS
            if wf_job_db.job_state != 'STOPPED' and wf_job_db.job_state != 'SUCCESS':
                # Set to STOPPED, since it probably failed.
                await db.set_workflow_job_state(job_id=job_id, job_state='STOPPED')
        return wf_job_db

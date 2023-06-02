from os import mkdir
from os.path import join
from typing import List, Union, Tuple

import operandi_utils.database.database as db
from operandi_utils.database.models import WorkflowJobDB

from .utils import generate_id
from .constants import WORKFLOWS_ROUTER
from .resource_manager import ResourceManager


class WorkflowManager(ResourceManager):
    # Warning: Don't change these defaults
    # till everything is configured properly
    def __init__(self, log_level: str = "INFO"):
        super().__init__(logger_label=__name__, log_level=log_level, resource_router=WORKFLOWS_ROUTER)

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
        nf_script_dest = join(workflow_dir, file.filename)
        await self._receive_resource(file, nf_script_dest)
        await db.save_workflow(
            workflow_id=workflow_id,
            workflow_dir=workflow_dir,
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

    def create_workflow_job_space(self, workflow_id: str) -> Tuple[str, Union[str, None]]:
        job_id = generate_id()
        job_dir = self.get_resource_job(workflow_id, job_id, local=True)
        mkdir(job_dir)
        return job_id, job_dir

    @staticmethod
    async def get_workflow_job(job_id: str) -> Union[WorkflowJobDB, None]:
        wf_job_db = await db.get_workflow_job(job_id)
        return wf_job_db

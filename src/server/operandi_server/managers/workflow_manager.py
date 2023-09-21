import logging
from os.path import join
from typing import List, Union, Tuple

from operandi_utils.database import (
    DBWorkflowJob,
    db_create_workflow,
    db_get_workflow_job,
    db_update_workflow
)

from .constants import (
    LOG_LEVEL,
    WORKFLOW_JOBS_ROUTER,
    WORKFLOWS_ROUTER
)
from .resource_manager import ResourceManager


class WorkflowManager(ResourceManager):
    def __init__(
            self,
            logger_label: str = __name__,
            log_level: str = LOG_LEVEL,
            workflow_router: str = WORKFLOWS_ROUTER,
            workflow_job_router: str = WORKFLOW_JOBS_ROUTER
    ):
        super().__init__(logger_label=logger_label, log_level=log_level)
        self.log = logging.getLogger(logger_label)
        self.log.setLevel(logging.getLevelName(log_level))
        self.workflow_router = workflow_router
        self.workflow_job_router = workflow_job_router
        self._create_resource_base_dir(self.workflow_router)
        self._create_resource_base_dir(self.workflow_job_router)

    def get_workflows(self) -> List[Tuple[str, str]]:
        """
        Get a list of all available workflow urls.
        """
        return self.get_all_resources(self.workflow_router, local=False)

    def get_workflow_jobs(self) -> List[Tuple[str, str]]:
        """
        Get a list of all available workflow job urls.
        """
        return self.get_all_resources(self.workflow_job_router, local=False)

    def get_workflow_url(self, workflow_id: str) -> str:
        return self.get_resource(
            resource_router=self.workflow_router,
            resource_id=workflow_id,
            local=False
        )

    def get_workflow_job_url(self, job_id: str, workflow_id: str = None) -> str:
        return self.get_resource(
            resource_router=self.workflow_job_router,
            resource_id=job_id,
            local=False
        )

    def get_workflow_path(self, workflow_id: str) -> str:
        return self.get_resource(
            resource_router=self.workflow_router,
            resource_id=workflow_id,
            local=True
        )

    def get_workflow_job_path(self, job_id: str, workflow_id: str = None) -> str:
        return self.get_resource(
            resource_router=self.workflow_job_router,
            resource_id=job_id,
            local=True
        )

    async def create_workflow_space(self, file, uid: str = None) -> Tuple[str, str]:
        workflow_id, workflow_dir = self._create_resource_dir(self.workflow_router, uid)
        nf_script_dest = join(workflow_dir, file.filename)
        await self._receive_resource(file, nf_script_dest)

        await db_create_workflow(
            workflow_id=workflow_id,
            workflow_dir=workflow_dir,
            workflow_script_path=nf_script_dest,
            workflow_script_base=file.filename
        )

        workflow_url = self.get_resource(self.workflow_router, workflow_id, local=False)
        return workflow_id, workflow_url

    def create_workflow_job_space(self, workflow_id: str = None) -> Tuple[str, Union[str, None]]:
        job_id, job_dir = self._create_resource_dir(self.workflow_job_router)
        return job_id, job_dir

    async def update_workflow_space(self, file, workflow_id: str) -> Tuple[str, str]:
        """
        Update a workflow space

        Delete the workflow space if existing and then delegate to
        :py:func:`ocrd_webapi.workflow_manager.WorkflowManager.create_workflow_space
        """
        self._delete_resource_dir(self.workflow_router, workflow_id)
        return await self.create_workflow_space(file, workflow_id)

    @staticmethod
    async def get_workflow_job(job_id: str) -> Union[DBWorkflowJob, None]:
        try:
            wf_job_db = await db_get_workflow_job(job_id)
        except RuntimeError as error:
            # Workflow job does not exist in the DB
            return None
        return wf_job_db

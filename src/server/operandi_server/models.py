from pydantic import BaseModel
from typing import Optional


class WorkflowArguments(BaseModel):
    workflow_id: str
    workspace_id: str
    input_file_grp: Optional[str] = "DEFAULT"
    mets_name: Optional[str] = "mets.xml"

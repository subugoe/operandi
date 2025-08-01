from beanie import Document
from datetime import datetime
from pydantic import Field


class DBProcessingStatsTotal(Document):
    """
    Stats model for summarizing the totals

    Attributes:
        institution_id:     Unique id of the institution the user belongs to
        user_id:            Unique id of the user to whom the statistics belong to
        pages_uploaded:     Total amount of pages uploaded as a workspace to the server
        pages_submitted:    Total amount of submitted pages in workflow jobs
        pages_succeeded:    Total amount of successfully processed pages
        pages_failed:       Total amount of failed pages
        pages_downloaded:   Total amount of pages downloaded as a workspace from the server
        pages_cancelled:    Total amount of cancelled pages
    """
    institution_id: str
    user_id: str
    pages_uploaded: int = Field(0, ge=0)
    pages_submitted: int = Field(0, ge=0)
    pages_succeeded: int = Field(0, ge=0)
    pages_failed: int = Field(0, ge=0)
    pages_downloaded: int = Field(0, ge=0)
    pages_cancelled: int = Field(0, ge=0)

    class Settings:
        name = "processing_stats_total"


class DBPageStat(Document):
    """
    DB model for page stat

    Attributes:
        institution_id:     Unique id of the institution the user belongs to
        user_id:            Unique id of the user to whom the statistics belong to
        datetime:           Shows the created date time of the entry
        workspace_id:       The workspace to which the pages belong to
        quantity:           The amount of the page stat
    """
    institution_id: str
    user_id: str
    datetime: datetime
    workspace_id: str
    quantity: int = Field(..., ge=0)

    class Settings:
        abstract = True

class DBPageStatUploaded(DBPageStat):
    class Settings:
        name = "page_stat_uploaded"

class DBPageStatDownloaded(DBPageStat):
    class Settings:
        name = "page_stat_downloaded"

class DBPageStatSubmitted(DBPageStat):
    workflow_job_id: str
    class Settings:
        name = "page_stat_submitted"

class DBPageStatSucceeded(DBPageStat):
    workflow_job_id: str
    class Settings:
        name = "page_stat_succeeded"

class DBPageStatFailed(DBPageStat):
    workflow_job_id: str
    class Settings:
        name = "page_stat_failed"

class DBPageStatCancelled(DBPageStat):
    workflow_job_id: str
    class Settings:
        name = "page_stat_cancelled"


PAGE_STAT_TYPE_TO_MODEL = {
    "uploaded": DBPageStatUploaded,
    "downloaded": DBPageStatDownloaded,
    "submitted": DBPageStatSubmitted,
    "succeeded": DBPageStatSucceeded,
    "failed": DBPageStatFailed,
    "cancelled": DBPageStatCancelled
}

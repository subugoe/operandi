from logging import getLogger
from os import environ
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from operandi_utils import call_sync
from .models import DBHPCSlurmJob, DBProcessingStatistics, DBUserAccount, DBWorkflow, DBWorkflowJob, DBWorkspace


async def db_initiate_database(
    db_url: str = environ.get("OPERANDI_DB_URL"), db_name: str = environ.get("OPERANDI_DB_NAME")
):
    logger = getLogger("operandi_utils.database.base")
    logger.info(f"MongoDB URL: {db_url}")
    logger.info(f"MongoDB Name: {db_name}")
    doc_models = [DBHPCSlurmJob, DBProcessingStatistics, DBUserAccount, DBWorkflow, DBWorkflowJob, DBWorkspace]
    client = AsyncIOMotorClient(db_url)
    # Documentation: https://beanie-odm.dev/
    await init_beanie(database=client.get_default_database(default=db_name), document_models=doc_models)


@call_sync
async def sync_db_initiate_database(
    db_url: str = environ.get("OPERANDI_DB_URL"), db_name: str = environ.get("OPERANDI_DB_NAME")
):
    await db_initiate_database(db_url, db_name)

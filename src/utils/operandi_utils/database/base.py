from logging import getLogger
from os import environ
from typing import List
from beanie import init_beanie, Document
from motor.motor_asyncio import AsyncIOMotorClient

from operandi_utils import call_sync
from .models import (
    DBHPCSlurmJob,
    DBUserAccount,
    DBWorkflow,
    DBWorkflowJob,
    DBWorkspace
)

OPERANDI_DB_NAME: str = environ.get("OPERANDI_DB_NAME", "operandi_db")
OPERANDI_DB_URL: str = environ.get("OPERANDI_DB_URL")


async def db_initiate_database(db_url: str, db_name: str = None, doc_models: List[Document] = None):
    logger = getLogger("operandi_utils.database.base")
    if db_name is None:
        db_name = OPERANDI_DB_NAME
    if doc_models is None:
        doc_models = [
            DBHPCSlurmJob,
            DBUserAccount,
            DBWorkflow,
            DBWorkflowJob,
            DBWorkspace
        ]

    if db_url:
        logger.info(f"MongoDB Name: {OPERANDI_DB_NAME}")
        logger.info(f"MongoDB URL: {db_url}")
    else:
        logger.error(f"MongoDB URL is invalid!")
    client = AsyncIOMotorClient(db_url)
    # Documentation: https://beanie-odm.dev/
    await init_beanie(
        database=client.get_default_database(default=db_name),
        document_models=doc_models
    )


@call_sync
async def sync_db_initiate_database(db_url: str, db_name: str = None, doc_models: List[Document] = None):
    await db_initiate_database(db_url, db_name, doc_models)

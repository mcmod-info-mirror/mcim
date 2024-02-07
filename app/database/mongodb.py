from beanie import init_beanie
from loguru import logger
from motor.core import (
    AgnosticClient,
    AgnosticCollection,
    AgnosticDatabase,
)
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import sys


from app.config import MongodbConfig
from app.models.database.curseforge import ModInfo, FileInfo, ModFilesSyncInfo, FingerprintInfo


mongodb_config = MongodbConfig.load()

dbcli: AgnosticClient = None # async motor client



def get_amcli() -> AgnosticClient:
    """
    Raw Motor client handler, use it when beanie cannot work
    :return:
    """
    global dbcli
    if dbcli is None:
        dbcli = AsyncIOMotorClient(
            f"mongodb://{mongodb_config.user}:{mongodb_config.password}@{mongodb_config.host}:{mongodb_config.port}",
        )
    return dbcli


def get_async_mongodb_database(db_name: Optional[str] = None) -> AgnosticDatabase:
    """
    Raw Motor database handler, use it when beanie cannot work
    :param db_name:
    :return:
    """
    if db_name is None:
        db_name = mongodb_config.database
    client = get_amcli()
    return client[db_name]


def get_async_mongodb_collection(col_name: str) -> AgnosticCollection:
    """
    Raw Motor collection handler, use it when beanie cannot work
    :param col_name:
    :return:
    """
    db = get_async_mongodb_database()
    return db[col_name]


async def start_async_mongodb() -> None:
    """
    Start beanie when process started.
    :return:
    """
    # try:
    async_mongodb_database = get_async_mongodb_database(mongodb_config.database)
    await init_beanie(
        database=async_mongodb_database,
        document_models=[
            ModInfo,
            FileInfo,
            ModFilesSyncInfo,
            FingerprintInfo
        ],
    )
    logger.success("started mongodb connection")
    # except Exception as e:
    #     logger.error(f"Failed to start mongodb. {e}")
    #     sys.exit(1)

async def close_async_mongodb() -> None:
    """
    Close beanie when process stopped.
    :return:
    """
    global dbcli
    if dbcli is not None:
        dbcli.close()
        logger.success("closed mongodb connection")
    else:
        logger.warning("no mongodb connection to close")
    dbcli = None

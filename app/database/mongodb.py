from beanie import init_beanie
from loguru import logger
from motor.core import (  # bad idea to use these three here,
    AgnosticClient,
    AgnosticCollection,
    AgnosticDatabase,
)
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import sys


from app.config import MongodbConfig


mongodb_config = MongodbConfig.load()

async_mongodb_client: AgnosticClient = None


def get_async_mongodb_client() -> AgnosticClient:
    """
    Raw Motor client handler, use it when beanie cannot work
    :return:
    """
    global async_mongodb_client
    if async_mongodb_client is None:
        async_mongodb_client = AsyncIOMotorClient(
            f"mongodb://{mongodb_config.user}:{mongodb_config.password}@{mongodb_config.host}:{mongodb_config.port}/{mongodb_config.database}",
        )
    return async_mongodb_client


def get_async_mongodb_database(db_name: Optional[str] = None) -> AgnosticDatabase:
    """
    Raw Motor database handler, use it when beanie cannot work
    :param db_name:
    :return:
    """
    if db_name is None:
        db_name = mongodb_config.database
    client = get_async_mongodb_client()
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
    try:
        async_mongodb_database = get_async_mongodb_database()
        await init_beanie(
            database=async_mongodb_database,
            document_models=[
                # Models
            ],
        )
        logger.success("started mongodb connection")
    except Exception as e:
        logger.error(f"Failed to start mongodb. {e}")
        sys.exit(1)

from odmantic import AIOEngine, SyncEngine
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient

from app.config import MongodbConfig
from app.models.database.curseforge import Mod, File, Fingerprint  # , ModFilesSyncInfo
from app.models.database.modrinth import Project, Version, File as ModrinthFile

_mongodb_config = MongodbConfig.load()

aio_mongo_engine: AIOEngine = None
sync_mongo_engine: SyncEngine = None


def init_mongodb_syncengine() -> SyncEngine:
    """
    Raw Motor client handler, use it when beanie cannot work
    :return:
    """
    global sync_mongo_engine
    if sync_mongo_engine is None:
        sync_mongo_engine = SyncEngine(
            client=MongoClient(
                f"mongodb://{_mongodb_config.user}:{_mongodb_config.password}@{_mongodb_config.host}:{_mongodb_config.port}"
                if _mongodb_config.auth
                else f"mongodb://{_mongodb_config.host}:{_mongodb_config.port}"
            ),
            database="mcim_backend",
        )
    return sync_mongo_engine


def init_mongodb_aioengine() -> AIOEngine:
    """
    Raw Motor client handler, use it when beanie cannot work
    :return:
    """
    global aio_mongo_engine
    if aio_mongo_engine is None:
        aio_mongo_engine = AIOEngine(
            client=AsyncIOMotorClient(
                f"mongodb://{_mongodb_config.user}:{_mongodb_config.password}@{_mongodb_config.host}:{_mongodb_config.port}"
                if _mongodb_config.auth
                else f"mongodb://{_mongodb_config.host}:{_mongodb_config.port}"
            ),
            database="mcim_backend",
        )
    return aio_mongo_engine


async def setup_async_mongodb() -> None:
    """
    Start beanie when process started.
    :return:
    """
    # try:
    await aio_mongo_engine.configure_database(
        [
            # CurseForge
            Mod,
            File,
            Fingerprint,
            # Modrinth
            Project,
            Version,
            ModrinthFile,
            # ModFilesSyncInfo,
        ]
    )
    logger.success("started mongodb connection")


aio_mongo_engine: AIOEngine = init_mongodb_aioengine()
sync_mongo_engine: SyncEngine = init_mongodb_syncengine()

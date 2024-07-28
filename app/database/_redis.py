from redis import Redis
from redis.asyncio import Redis as AioRedis
from app.utils.loger import log

from app.config import RedisdbConfig

_redis_config = RedisdbConfig.load()

aio_redis_engine: AioRedis = None
sync_redis_engine: Redis = None
file_cdn_redis_async_engine: AioRedis = None
file_cdn_redis_sync_engine: Redis = None


def init_redis_aioengine() -> AioRedis:
    global aio_redis_engine
    aio_redis_engine = AioRedis(
        host=_redis_config.host,
        port=_redis_config.port,
        password=_redis_config.password,
        db=_redis_config.database.info_cache,
    )
    return aio_redis_engine


def init_sync_redis_engine() -> Redis:
    global sync_redis_engine
    sync_redis_engine = Redis(
        host=_redis_config.host,
        port=_redis_config.port,
        password=_redis_config.password,
        db=_redis_config.database.info_cache,
    )
    return sync_redis_engine


# def init_file_cdn_redis_async_engine() -> AioRedis:
#     global file_cdn_redis_async_engine
#     file_cdn_redis_async_engine = AioRedis(
#         host=_redis_config.host,
#         port=_redis_config.port,
#         password=_redis_config.password,
#         db=_redis_config.database.file_cdn,
#     )
#     return file_cdn_redis_async_engine


# def init_file_cdn_redis_sync_engine() -> Redis:
#     global file_cdn_redis_sync_engine
#     file_cdn_redis_sync_engine = Redis(
#         host=_redis_config.host,
#         port=_redis_config.port,
#         password=_redis_config.password,
#         db=_redis_config.database.file_cdn,
#     )
#     return file_cdn_redis_sync_engine


def init_task_redis_client() -> Redis:
    global task_redis_client
    task_redis_client = Redis(
        host=_redis_config.host,
        port=_redis_config.port,
        password=_redis_config.password,
        db=_redis_config.database.tasks_queue,
    )
    return task_redis_client


async def close_aio_redis_engine():
    """
    Close aioredis when process stopped.
    """
    global aio_redis_engine
    if aio_redis_engine is not None:
        await aio_redis_engine.close()
        log.success("closed redis connection")
    else:
        log.warning("no redis connection to close")
    aio_redis_engine = None


def close_redis_engine():
    """
    Close redis when process stopped.
    """
    global sync_redis_engine
    if sync_redis_engine is not None:
        sync_redis_engine.close()
        log.success("closed redis connection")
    else:
        log.warning("no redis connection to close")
    sync_redis_engine = None


def close_file_cdn_redis_engine():
    """
    Close file cdn redis when process stopped.
    """
    global file_cdn_redis_async_engine
    if file_cdn_redis_async_engine is not None:
        file_cdn_redis_async_engine.close()
        log.success("closed file cdn redis connection")
    else:
        log.warning("no file cdn redis connection to close")
    file_cdn_redis_async_engine = None


aio_redis_engine: AioRedis = init_redis_aioengine()
sync_redis_engine: Redis = init_sync_redis_engine()
# file_cdn_redis_async_engine: AioRedis = init_file_cdn_redis_async_engine()
# file_cdn_redis_sync_engine: Redis = init_file_cdn_redis_sync_engine()

log.success("Redis connection established")  # noqa

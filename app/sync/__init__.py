import dramatiq
import os
from dramatiq.brokers.redis import RedisBroker
from dramatiq.rate_limits.backends import RedisBackend
from dramatiq.rate_limits import BucketRateLimiter, WindowRateLimiter
from redis import Redis

from app.database.mongodb import init_mongodb_syncengine, sync_mongo_engine
from app.database._redis import (
    init_sync_redis_engine,
    sync_redis_engine,
    file_cdn_redis_sync_engine,
    # init_file_cdn_redis_sync_engine,
)
from app.config import RedisdbConfig

from app.utils.loger import log

# SYNC_FILE_CDN, SYNC_INFO and SYNC_ALL
# now only support SYNC_INFO
# SYNC_MODE = os.getenv("SYNC_MODE") or "SYNC_ALL"
SYNC_MODE = "SYNC_INFO"

if __name__ == "app.sync":
    log.info(f"SYNC_MODE: {SYNC_MODE}")

_redis_config = RedisdbConfig.load()

# 现在不需要第二个 redis 了
# _sync_redis_config = SyncRedisdbConfig.load()

init_sync_redis_engine()
init_mongodb_syncengine()
# init_file_cdn_redis_sync_engine()


sync_redis_engine = sync_redis_engine
sync_mongo_engine = sync_mongo_engine
file_cdn_redis_sync_engine = file_cdn_redis_sync_engine

rate_limit_backend = RedisBackend(
    # host=_redis_config.host,
    # port=_redis_config.port,
    # password=_sync_redis_config.password,
    client=Redis(
        host=_redis_config.host,
        port=_redis_config.port,
        password=_redis_config.password,
        db=_redis_config.database.rate_limit,
    ),
)

redis_broker = RedisBroker(
    host=_redis_config.host,
    port=_redis_config.port,
    password=_redis_config.password,
    db=_redis_config.database.tasks_queue,
)


# file_cdn_redis_broker = RedisBroker(
#     host=_redis_config.host,
#     port=_redis_config.port,
#     password=_redis_config.password,
#     db=_redis_config.database.file_cdn,
# )

MODRINTH_LIMITER = WindowRateLimiter(
    rate_limit_backend, "modrinth-sync-task-distributed-mutex", limit=100, window=60
)
CURSEFORGE_LIMITER = WindowRateLimiter(
    rate_limit_backend, "curseforge-sync-task-distributed-mutex", limit=100, window=60
)

log.success("Dramatiq broker set up successfully.")

from app.sync.modrinth import *
from app.sync.curseforge import *

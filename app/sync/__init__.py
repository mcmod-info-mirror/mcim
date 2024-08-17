import dramatiq
import os
from dramatiq.brokers.redis import RedisBroker
from dramatiq.rate_limits.backends import RedisBackend
from dramatiq.rate_limits import BucketRateLimiter, WindowRateLimiter

from app.database.mongodb import init_mongodb_syncengine, sync_mongo_engine
from app.database._redis import (
    init_sync_redis_engine,
    sync_redis_engine,
    file_cdn_redis_sync_engine,
    # init_file_cdn_redis_sync_engine,
)
from app.config.redis import RedisdbConfig, SyncRedisdbConfig
from app.utils.loger import log

# SYNC_FILE_CDN, SYNC_INFO and SYNC_ALL

SYNC_MODE = os.getenv("SYNC_MODE") or "SYNC_ALL"

if __name__ == "app.sync":
    log.info(f"SYNC_MODE: {SYNC_MODE}")

_redis_config = RedisdbConfig.load()
_sync_redis_config = SyncRedisdbConfig.load()

init_sync_redis_engine()
init_mongodb_syncengine()
# init_file_cdn_redis_sync_engine()


sync_redis_engine = sync_redis_engine
sync_mongo_engine = sync_mongo_engine
file_cdn_redis_sync_engine = file_cdn_redis_sync_engine

rate_limit_backend = RedisBackend(
    host=_sync_redis_config.host,
    port=_sync_redis_config.port,
    password=_sync_redis_config.password,
)

redis_broker = RedisBroker(
    host=_redis_config.host,
    port=_redis_config.port,
    password=_redis_config.password,
    db=_redis_config.database.tasks_queue,
    namespace="file_cdn_cache" if SYNC_MODE == "SYNC_FILE_CDN" else "dramatiq",
)

file_cdn_redis_broker = RedisBroker(
    host=_redis_config.host,
    port=_redis_config.port,
    password=_redis_config.password,
    db=_redis_config.database.file_cdn,
    namespace="file_cdn_cache" if SYNC_MODE == "SYNC_FILE_CDN" else "dramatiq",
)

MODRINTH_LIMITER = WindowRateLimiter(rate_limit_backend, "modrinth-sync-task-distributed-mutex", limit=250, window=60)
CURSEFORGE_LIMITER = WindowRateLimiter(rate_limit_backend, "curseforge-sync-task-distributed-mutex", limit=250, window=60)

MODRINTH_FILE_CDN_LIMITER = WindowRateLimiter(rate_limit_backend, "modrinth-file-cdn-sync-task-distributed-mutex", limit=20, window=60)
CURSEFORGE_FILE_CDN_LIMITER = WindowRateLimiter(rate_limit_backend, "curseforge-file-cdn-sync-task-distributed-mutex", limit=20, window=60)

dramatiq.set_broker(redis_broker if SYNC_MODE in ["SYNC_INFO", "SYNC_ALL"] else file_cdn_redis_broker)

from app.sync.modrinth import *
from app.sync.curseforge import *
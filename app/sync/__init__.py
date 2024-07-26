import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.rate_limits.backends import RedisBackend
from dramatiq.rate_limits import ConcurrentRateLimiter

from app.database.mongodb import init_mongodb_syncengine, sync_mongo_engine
from app.database._redis import (
    init_sync_redis_engine,
    sync_redis_engine,
    file_cdn_redis_sync_engine,
    init_file_cdn_redis_sync_engine,
)
from app.config.redis import RedisdbConfig, SyncRedisdbConfig

_redis_config = RedisdbConfig.load()
_sync_redis_config = SyncRedisdbConfig.load()

init_sync_redis_engine()
init_mongodb_syncengine()
init_file_cdn_redis_sync_engine()


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
)

limiter = ConcurrentRateLimiter(rate_limit_backend, "sync-task-distributed-mutex", limit=8)

dramatiq.set_broker(redis_broker)

from app.sync.modrinth import *
from app.sync.curseforge import *

import dramatiq
# from dramatiq.worker import Worker
from dramatiq.brokers.redis import RedisBroker

from ..database.mongodb import init_mongodb_syncengine, sync_mongo_engine
from ..database._redis import (
    # init_task_redis_client,
    init_sync_redis_engine,
    sync_redis_engine,
    # task_redis_client,
)
from ..config.redis import RedisdbConfig

_redis_config = RedisdbConfig.load()

# init_task_redis_client()
init_sync_redis_engine()
init_mongodb_syncengine()

sync_redis_engine = sync_redis_engine
sync_mongo_engine = sync_mongo_engine

redis_broker = RedisBroker(host=_redis_config.host, port=_redis_config.port, password=_redis_config.password, db=_redis_config.database.tasks_queue)

dramatiq.set_broker(redis_broker)

from ..sync.modrinth import *
from ..sync.curseforge import *

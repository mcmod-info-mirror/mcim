from typing import Optional
from redis.asyncio import Redis
from app.utils.response_cache.key_builder import default_key_builder, KeyBuilder
from app.config.redis import RedisdbConfig

redis_config = RedisdbConfig.load()


class Cache:
    backend: Redis
    enabled: bool = False
    namespace: str = "fastapi_cache"
    key_builder: KeyBuilder = default_key_builder

    @classmethod
    def init(
        cls,
        backend: Optional[Redis] = None,
        enabled: Optional[bool] = False,
        namespace: Optional[str] = "fastapi_cache",
        key_builder: KeyBuilder = default_key_builder,
    ) -> None:
        cls.backend = (
            Redis(
                host=redis_config.host,
                port=redis_config.port,
                db=redis_config.database.info_cache,
                password=redis_config.password,
            )
            if backend is None
            else backend
        )
        cls.enabled = enabled
        cls.namespace = namespace
        cls.key_builder = key_builder
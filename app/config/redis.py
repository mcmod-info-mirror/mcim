import json
from typing import List, Union, Optional
import os
from pydantic import BaseModel, ValidationError, validator

from .constants import CONFIG_PATH

# REDIS config path
REDIS_CONFIG_PATH = os.path.join(CONFIG_PATH, "redis.json")
SYNC_REDIS_CONFIG_PATH = os.path.join(CONFIG_PATH, "sync_redis.json")


class RedisDatabaseModel(BaseModel):
    tasks_queue: int = 0  # dramatiq tasks
    info_cache: int = 1  # response_cache and static info
    file_cdn: int = 2  # file cdn
    rate_limit: int = 3  # rate limit


class RedisdbConfigModel(BaseModel):
    host: str = "redis"
    port: int = 6379
    auth: bool = True
    user: Optional[str] = None
    password: Optional[str] = None
    database: RedisDatabaseModel = RedisDatabaseModel()

class SyncRedisdbConfigModel(BaseModel):
    host: str = "sync_redis"
    port: int = 6379
    auth: bool = True
    user: Optional[str] = None
    password: Optional[str] = None

class RedisdbConfig:
    @staticmethod
    def save(
        model: RedisdbConfigModel = RedisdbConfigModel(), target=REDIS_CONFIG_PATH
    ):
        with open(target, "w") as fd:
            json.dump(model.model_dump(), fd, indent=4)

    @staticmethod
    def load(target=REDIS_CONFIG_PATH) -> RedisdbConfigModel:
        if not os.path.exists(target):
            RedisdbConfig.save(target=target)
            return RedisdbConfigModel()
        with open(target, "r") as fd:
            data = json.load(fd)
        return RedisdbConfigModel(**data)

class SyncRedisdbConfig:
    @staticmethod
    def save(
        model: SyncRedisdbConfigModel = SyncRedisdbConfigModel(), target=SYNC_REDIS_CONFIG_PATH
    ):
        with open(target, "w") as fd:
            json.dump(model.model_dump(), fd, indent=4)

    @staticmethod
    def load(target=REDIS_CONFIG_PATH) -> SyncRedisdbConfigModel:
        if not os.path.exists(target):
            SyncRedisdbConfig.save(target=target)
            return SyncRedisdbConfigModel()
        with open(target, "r") as fd:
            data = json.load(fd)
        return SyncRedisdbConfigModel(**data)

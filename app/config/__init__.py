import os
from app.config.constants import CONFIG_PATH
from app.config.mcim import MCIMConfig
from app.config.mongodb import MongodbConfig
from app.config.redis import RedisdbConfig

__all__ = [
    "MCIMConfig",
    "MongodbConfig",
    "RedisdbConfig",
]


if not os.path.exists(CONFIG_PATH):
    os.makedirs(CONFIG_PATH)

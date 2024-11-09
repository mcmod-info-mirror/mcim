import os
from app.config.constants import CONFIG_PATH
from app.config.mcim import MCIMConfig
from app.config.mongodb import MongodbConfig
from app.config.redis import RedisdbConfig
from app.config.webdav import WebDavConfig

__all__ = [
    "MCIMConfig",
    "MongodbConfig",
    "RedisdbConfig",
    "WebDavConfig",
]


if not os.path.exists(CONFIG_PATH):
    os.makedirs(CONFIG_PATH)

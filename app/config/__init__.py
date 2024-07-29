from app.config.mcim import MCIMConfig
from app.config.mongodb import MongodbConfig
from app.config.redis import RedisdbConfig
from app.config.aria2 import Aria2Config
from app.config.webdav import WebDavConfig

__all__ = [
    "MCIMConfig",
    "MongodbConfig",
    "RedisdbConfig",
    "Aria2Config",
    "WebDavConfig",
]

import os
from app.config.constants import CONFIG_PATH

if not os.path.exists(CONFIG_PATH):
    os.makedirs(CONFIG_PATH)

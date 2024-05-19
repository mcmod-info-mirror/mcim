import json
import os
from typing import Optional
from pydantic import BaseModel, ValidationError, validator

from .constants import CONFIG_PATH

# MCIM config path
MICM_CONFIG_PATH = os.path.join(CONFIG_PATH, "mcim.json")

class Curseforge:
    mod: int = 86400
    file: int = 86400

class Modrinth:
    project: int = 86400
    version: int = 86400

class ExpireSecond(BaseModel):
    curseforge: Curseforge = Curseforge()
    modrinth: Modrinth = Modrinth()

class MCIMConfigModel(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8000

    curseforge_api_key: str = "<api key>"
    curseforge_api: str = "https://api.curseforge.com/v1/"  # 不然和api的拼接对不上
    modrinth_api: str = "https://api.modrinth.com/"
    mcmod_api: str = "https://www.mcmod.cn/"
    proxies: Optional[str] = None
    sync_interval: int = 3600  # seconds
    async_timeout: int = 60  # seconds

    
    expire_second: ExpireSecond = ExpireSecond()
    expire_status_code: int = 404
    uncache_status_code: int = 404

    favicon_url: str = (
        "https://thirdqq.qlogo.cn/g?b=sdk&k=ABmaVOlfKKPceB5qfiajxqg&s=640"
    )
    
class MCIMConfig:
    @staticmethod
    def save(model: MCIMConfigModel = MCIMConfigModel(), target=MICM_CONFIG_PATH):
        with open(target, "w") as fd:
            json.dump(model.model_dump(), fd, indent=4)

    @staticmethod
    def load(target=MICM_CONFIG_PATH) -> MCIMConfigModel:
        if not os.path.exists(target):
            MCIMConfig.save(target=target)
            return MCIMConfigModel()
        with open(target, "r") as fd:
            data = json.load(fd)
        return MCIMConfigModel(**data)
import json
import os
from pydantic import BaseModel, ValidationError, validator

from .constants import CONFIG_PATH

# MYSQL config path
MYSQL_CONFIG_PATH = os.path.join(CONFIG_PATH, "mysql.json")


class MysqlConfigModel(BaseModel):
    host: str = "127.0.0.1"
    port: int = 3306
    user: str = "username"
    password: str = "password"
    database: str = "database"

class MysqlConfig:
    @staticmethod
    def save(model: MysqlConfigModel = MysqlConfigModel(), target=MYSQL_CONFIG_PATH):
        with open(target, "w") as fd:
            json.dump(model.model_dump(), fd, indent=4)

    @staticmethod
    def load(target=MYSQL_CONFIG_PATH) -> MysqlConfigModel:
        if not os.path.exists(target):
            MysqlConfig.save(target=target)
            return MysqlConfigModel()
        with open(target, "r") as fd:
            data = json.load(fd)
        return MysqlConfigModel(**data)
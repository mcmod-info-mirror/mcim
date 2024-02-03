import json
import os
from pydantic import BaseModel, ValidationError, validator

from .constants import CONFIG_PATH

# MYSQL config path
MYSQL_CONFIG_PATH = os.path.join(CONFIG_PATH, "mongodb.json")


class MongodbConfigModel(BaseModel):
    host: str = "127.0.0.1"
    port: int = 27017
    user: str = "username"
    password: str = "password"
    database: str = "database"

class MongodbConfig:
    @staticmethod
    def save(model: MongodbConfigModel = MongodbConfigModel(), target=MYSQL_CONFIG_PATH):
        with open(target, "w") as fd:
            json.dump(model.model_dump(), fd, indent=4)

    @staticmethod
    def load(target=MYSQL_CONFIG_PATH) -> MongodbConfigModel:
        if not os.path.exists(target):
            MongodbConfig.save(target=target)
            return MongodbConfigModel()
        with open(target, "r") as fd:
            data = json.load(fd)
        return MongodbConfigModel(**data)
import json
import os
from typing import Optional
from pydantic import BaseModel, ValidationError, validator

from .constants import CONFIG_PATH

RABBITMQ_CONFIG_PATH = os.path.join(CONFIG_PATH, "rabbitmq.json")


class RabbitmqConfigModel(BaseModel):
    host: str = "rabbitmq"
    port: int = 5672
    username: str = "guest"
    password: str = "guest"
    vhost: str = "/"


class RabbitmqConfig:
    @staticmethod
    def save(
        model: RabbitmqConfigModel = RabbitmqConfigModel(), target=RABBITMQ_CONFIG_PATH
    ):
        with open(target, "w") as fd:
            json.dump(model.model_dump(), fd, indent=4)

    @staticmethod
    def load(target=RABBITMQ_CONFIG_PATH) -> RabbitmqConfigModel:
        if not os.path.exists(target):
            RabbitmqConfig.save(target=target)
            return RabbitmqConfigModel()
        with open(target, "r") as fd:
            data = json.load(fd)
        return RabbitmqConfigModel(**data)

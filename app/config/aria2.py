import json
import os
from typing import Optional
from pydantic import BaseModel, ValidationError, validator

from .constants import CONFIG_PATH

# ARIA2 config path
ARIA2_CONFIG_PATH = os.path.join(CONFIG_PATH, "aria2.json")


class Aria2ConfigModel(BaseModel):
    host: str = "http://localhost"
    port: int = 6800
    secret: str = ""


class Aria2Config:
    @staticmethod
    def save(model: Aria2ConfigModel = Aria2ConfigModel(), target=ARIA2_CONFIG_PATH):
        with open(target, "w") as fd:
            json.dump(model.model_dump(), fd, indent=4)

    @staticmethod
    def load(target=ARIA2_CONFIG_PATH) -> Aria2ConfigModel:
        if not os.path.exists(target):
            Aria2Config.save(target=target)
            return Aria2ConfigModel()
        with open(target, "r") as fd:
            data = json.load(fd)
        return Aria2ConfigModel(**data)

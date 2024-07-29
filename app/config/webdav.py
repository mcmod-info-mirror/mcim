import json
import os
from typing import Optional
from pydantic import BaseModel, ValidationError, validator

from .constants import CONFIG_PATH

WEBDAV_CONFIG_PATH = os.path.join(CONFIG_PATH, "webdav.json")

class WebDavConfigModel(BaseModel):
    base_url: str = "http://alist:5244/dav"
    username: str = "admin"
    password: str = "admin"


class WebDavConfig:
    @staticmethod
    def save(
        model: WebDavConfigModel = WebDavConfigModel(), target=WEBDAV_CONFIG_PATH
    ):
        with open(target, "w") as fd:
            json.dump(model.model_dump(), fd, indent=4)

    @staticmethod
    def load(target=WEBDAV_CONFIG_PATH) -> WebDavConfigModel:
        if not os.path.exists(target):
            WebDavConfig.save(target=target)
            return WebDavConfigModel()
        with open(target, "r") as fd:
            data = json.load(fd)
        return WebDavConfigModel(**data)
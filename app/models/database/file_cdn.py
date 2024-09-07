from odmantic import Model, Field, EmbeddedModel
from pydantic import BaseModel, field_serializer, field_validator, model_validator

from typing import List, Optional, Union
from datetime import datetime

class File(Model):
    sha1: str = Field(primary_field=True, index=True)
    url: str
    path: str
    size: int
    mtime: datetime

    model_config = {
        "collection": "file_cdn_files",
    }

    @field_serializer("mtime")
    def serialize_sync_Date(self, value: datetime, _info):
        return value.timestamp()
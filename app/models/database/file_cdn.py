from odmantic import Model, Field, EmbeddedModel
from pydantic import BaseModel, field_serializer, field_validator, model_validator
import time

from typing import List, Optional, Union
from datetime import datetime

class File(Model):
    sha1: str = Field(primary_field=True, index=True)
    url: str
    path: str
    size: int
    mtime: int = Field(default_factory=lambda: int(time.time()))# , index=True) # 不可能有修改，直接强制 1725767710
    # 需要修改的时候手动改成 now
    enable: Optional[bool] = True

    model_config = {
        "collection": "file_cdn_files",
    }

    # @field_serializer("mtime")
    # def serialize_sync_date(self, value: datetime, _info):
    #     return value.strftime("%Y-%m-%dT%H:%M:%SZ")

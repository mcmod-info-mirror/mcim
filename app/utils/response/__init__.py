from fastapi.responses import ORJSONResponse, Response

from typing import Union, Optional
from pydantic import BaseModel

class TrustableResponse(ORJSONResponse):
    def __init__(self, status_code: int = 200, content: Union[dict, BaseModel] = None, trustable: bool = True):
        if isinstance(content, BaseModel):
            content = content.model_dump()
        headers = {}
        headers["Trustable"] = str(trustable)
        super().__init__(status_code=status_code, content=content, headers=headers)

# uncached response
class UncachedResponse(Response):
    def __init__(self, status_code: int = 404):
        headers = {}
        headers["Trustable"] = "False"
        super().__init__(status_code=status_code, headers=headers)
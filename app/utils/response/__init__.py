from fastapi.responses import ORJSONResponse, Response

from typing import Union, Optional
from pydantic import BaseModel


class TrustableResponse(ORJSONResponse):
    """
    A response that indicates that the content is trusted.
    """
    def __init__(
        self,
        status_code: int = 200,
        content: Union[dict, BaseModel, list] = None,
        headers: dict = {},
        trustable: bool = True,
    ):
        if isinstance(content, BaseModel):
            raw_content = content.model_dump()
        elif isinstance(content, list):
            raw_content = []
            for item in content:
                if isinstance(item, BaseModel):
                    item = item.model_dump()
                raw_content.append(item)
        headers["Trustable"] = "True" if trustable else "False"
        # TODO: default cache headers
        if "Cache-Control" not in headers:
            headers["Cache-Control"] = "public, max-age=86400"
            
        super().__init__(status_code=status_code, content=raw_content, headers=headers)


class UncachedResponse(Response):
    """
    A response that indicates that the content is not cached.
    """
    def __init__(self, status_code: int = 404, headers: dict = {}):
        headers = {}
        headers["Trustable"] = "False"
        super().__init__(status_code=status_code, headers=headers)

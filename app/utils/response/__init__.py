from fastapi.responses import ORJSONResponse, Response
from typing import Union, Optional
from pydantic import BaseModel


class BaseResponse(ORJSONResponse):
    """
    BaseResponse 类

    用于返回 JSON 响应

    默认 Cache-Control: public, max-age=86400
    """

    def __init__(
        self,
        status_code: int = 200,
        content: Union[dict, BaseModel, list] = None,
        headers: dict = {},
    ):
        # 自动序列化 BaseModel
        if isinstance(content, dict):
            raw_content = content
        elif isinstance(content, BaseModel):
            raw_content = content.model_dump()
        elif isinstance(content, list):
            raw_content = []
            for item in content:
                if isinstance(item, BaseModel):
                    item = item.model_dump()
                raw_content.append(item)
        # 默认 Cache-Control: public, max-age=86400
        if status_code == 200 and "Cache-Control" not in headers:
            headers["Cache-Control"] = "public, max-age=86400"
        super().__init__(status_code=status_code, content=content, headers=headers)


class TrustableResponse(BaseResponse):
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
        headers["Trustable"] = "True" if trustable else "False"

        super().__init__(status_code=status_code, content=content, headers=headers)


class UncachedResponse(BaseResponse):
    """
    A response that indicates that the content is not cached.
    """

    def __init__(self, status_code: int = 404, headers: dict = {}):
        headers = {}
        headers["Trustable"] = "False"
        headers["Cache-Control"] = "public, no-cache"
        super().__init__(status_code=status_code, headers=headers)

class ForceSyncResponse(BaseResponse):
    """
    A response that indicates that the content is not cached.
    """

    def __init__(self, status_code: int = 202):
        headers = {}
        headers["Trustable"] = "False"
        headers["Cache-Control"] = "public, no-cache"
        super().__init__(status_code=status_code, headers=headers)
"""
响应中间件
"""

from typing import Any, Dict, Union
from pydantic import BaseModel
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class BaseResp(BaseModel):
    code: int
    message: str
    data: Union[Dict, Any] = None


class RespMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, header_namespace: str):
        super().__init__(app)
        self.header_namespace = header_namespace

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # 先暂时就这样...我也没定义过这些东西
        if response.status_code == 200:
            data = response.body
            response.body = BaseResp(code=0, message="success", data=data).model_dump()

        return response

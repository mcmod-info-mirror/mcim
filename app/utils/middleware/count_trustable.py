"""
统计 Trustable 请求
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.metric import TRUSTABLE_RESPONSE_GAUGE


class CountTrustableMiddleware(BaseHTTPMiddleware):
    """
    统计 Trustable 请求
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if response.headers.get("Trustable") == "True":
            TRUSTABLE_RESPONSE_GAUGE.labels(route=request.url.path).inc()
        else:
            TRUSTABLE_RESPONSE_GAUGE.labels(route=request.url.path).dec()
        return response
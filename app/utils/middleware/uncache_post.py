"""
不缓存 POST 请求
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class UncachePOSTMiddleware(BaseHTTPMiddleware):
    """
    不缓存 POST 请求
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.method == "POST":
            response.headers["Cache-Control"] = "no-cache"
        return response

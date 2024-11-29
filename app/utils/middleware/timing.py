"""
DEBUG 记录请求处理时间
"""

import time
import inspect
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.loger import log

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        route = request.scope.get("route")
        if route:
            route_name = route.name
            if process_time >= 10:
                log.warning(f"{route_name} - {request.method} {request.url} {process_time:.2f}s")
            elif process_time < 0.01: # 这应该是 redis 缓存，直接忽略
                # log.debug(f"{route_name} - {request.method} {request.url} {process_time:.2f}s")
                pass
            else:
                log.debug(f"{route_name} - {request.method} {request.url} {process_time:.2f}s")
        return response

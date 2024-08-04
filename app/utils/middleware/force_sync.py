"""
force_sync.py

强制拉取中间件

检查 URL 参数 force=True 的 requests
request.state.force_sync 设置为 True
然后把 response 的 Cache-Control 设置为 no-cache
"""

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.utils.loger import log

class ForceSyncMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 检查 URL 参数 force 是否为 True
        force_sync = False
        if request.query_params.get('force') in ['true', 'True', True, 1]:
            force_sync = True
            
        if force_sync:
            # 设置 request.state.force_sync 为 True
            request.state.force_sync = True
        else:
            # 设置 request.state.force_sync 为 False
            request.state.force_sync = False
        
        # 获取响应
        response = await call_next(request)
        
        if force_sync:
            # 设置响应的 Cache-Control 头为 no-cache
            response.headers['Cache-Control'] = 'no-cache'
        
        return response
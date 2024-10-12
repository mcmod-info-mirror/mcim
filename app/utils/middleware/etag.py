"""
给 Response 添加 Etag
"""

from fastapi.responses import Response
import hashlib
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


# Etag
def generate_etag(response: Response) -> str:
    """
    Get Etag from response

    SHA1 hash of the response content and status code

    Args:
        response (Response): response

    Returns:
        str: Etag
    """
    hash_tool = hashlib.sha1()
    hash_tool.update(response.body)
    hash_tool.update(str(response.status_code).encode())
    return hash_tool.hexdigest()


class EtagMiddleware(BaseHTTPMiddleware):
    """
    给 Response 添加 Etag
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.url.path.split("/")[1] in ["modrinth", "curseforge", "file_cdn"] and response.status_code == 200:
            etag = generate_etag(response)

            # if_none_match = request.headers.get("If-None-Match")
            # if if_none_match == etag:
            #     response = Response(status_code=304)
            # else:
            #     response.headers["Etag"] = etag

            response.headers["Etag"] = f'"{etag}"'
        return response
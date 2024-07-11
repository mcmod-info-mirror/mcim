import orjson
from functools import wraps
from typing import Optional
from fastapi.responses import Response

from app.utils.response_cache.resp_builder import ResponseBuilder
from app.utils.response_cache.key_builder import default_key_builder
from app.utils.loger import log
from app.utils.response_cache import Cache


def cache(expire: Optional[int] = 60, never_expire: Optional[bool] = False):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = default_key_builder(
                func, namespace=Cache.namespace, args=args, kwargs=kwargs
            )
            value = await Cache.backend.get(key)

            if value is not None:
                value = orjson.loads(value)
                log.debug(f"Cached response: [{key}]:[{value}]")
                return ResponseBuilder.decode(value)

            result = await func(*args, **kwargs)

            if isinstance(result, Response):
                to_set = ResponseBuilder.encode(result)
            else:
                return result
            value = orjson.dumps(to_set)
            
            if never_expire:
                await Cache.backend.set(key, value)
            else:
                await Cache.backend.set(key, value, ex=expire)
            log.debug(f"Set cache: [{key}]:[{to_set}]")

            return result

        return wrapper

    return decorator

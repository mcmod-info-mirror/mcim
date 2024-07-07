import hashlib
import orjson
from functools import wraps
from typing import Optional
from app.utils.loger import log

from fastapi.responses import ORJSONResponse, RedirectResponse

from app.utils.response_cache.builder import (
    ORJsonBuilder,
    BaseRespBuilder,
    # RedirectRespBuilder,
)
from app.config import RedisdbConfig
from app.database import aio_redis_engine

def cache(expire: Optional[int] = 60, never_expire: Optional[bool] = False):
    def decorator(route):
        @wraps(route)
        async def wrapper(*args, **kwargs):
            key_material = route.__name__ + str(args) + str(kwargs)
            key = hashlib.md5(key_material.encode()).hexdigest()
            value = await aio_redis_engine.get(key)
            
            if value is not None:
                value = orjson.loads(value)
                log.debug(f"Cached response: [{key_material}]:[{key}]:[{value}]")
                if value["type"] in ["ORJSONResponse","TrustableResponse"]:
                    return ORJsonBuilder.decode(value["value"])
                elif value["type"] == "Response":
                    return BaseRespBuilder.decode(value["value"])
                # elif value["type"] == "RedirectResponse":
                #     return RedirectRespBuilder.decode(value["value"])

            result = await route(*args, **kwargs)
            if isinstance(result, ORJSONResponse):
                value = ORJsonBuilder.encode(result)
            # elif isinstance(result, RedirectResponse):
            #     value = RedirectRespBuilder.encode(result)
            else:
                value = BaseRespBuilder.encode(result)

            value = orjson.dumps({"type": result.__class__.__name__, "value": value})
            log.debug(f"Set cache: [{key_material}]:[{key}]:[{value}]")
            if never_expire:
                await aio_redis_engine.set(key, value)
            else:
                await aio_redis_engine.set(key, value, ex=expire)
            return result

        return wrapper

    return decorator

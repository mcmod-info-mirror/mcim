
import hashlib
import orjson
from redis.asyncio import Redis
from functools import wraps
from typing import Optional

from fastapi.responses import ORJSONResponse

from app.utils.response_cache.builder import ORJsonBuilder, BaseRespBuilder

redis = Redis(db=3, port=25565, host="localhost")

def cache(expire: Optional[int] = 60, never_expire: Optional[bool] = False):
    def decorator(route):
        @wraps(route)
        async def wrapper(*args, **kwargs):
            key_material = route.__name__ + str(args) + str(kwargs)
            key = hashlib.md5(key_material.encode()).hexdigest()
            value = await redis.get(key)

            if value is not None:
                value = orjson.loads(value)
                if value["type"] == "ORJSONResponse":
                    return ORJsonBuilder.decode(value["value"])
                elif value["type"] == "Response":
                    return BaseRespBuilder.decode(value["value"])
            
            result = await route(*args, **kwargs)
            value = {
                "type": result.__class__.__name__,
                "value": ORJsonBuilder.encode(result)
            }
            if never_expire:
                await redis.set(key, value)
            else:
                await redis.set(key, value, ex=expire)
            return result
        return wrapper
    return decorator
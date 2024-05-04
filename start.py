import uvicorn


from app.config import MCIMConfig
from app.config import MCIMConfig
from app.database.mongodb import init_mongodb_aioengine
from app.database._redis import init_redis_aioengine

from app import APP


mcim_config = MCIMConfig.load()

if __name__ == "__main__":
    init_mongodb_aioengine()
    init_redis_aioengine()
    uvicorn.run(APP, host=mcim_config.host, port=mcim_config.port)

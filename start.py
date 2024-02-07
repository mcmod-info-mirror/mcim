import uvicorn


from app.config.mcim import MCIMConfig
from app.config import MCIMConfig

from app import APP


mcim_config = MCIMConfig.load()

if __name__ == "__main__":
    uvicorn.run(APP, host=mcim_config.host, port=mcim_config.port)

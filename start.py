import uvicorn

from app.config import MCIMConfig
from app import APP

mcim_config = MCIMConfig.load()

if __name__ == "__main__":
    config = uvicorn.Config(APP, host=mcim_config.host, port=mcim_config.port, log_config=None)
    server = uvicorn.Server(config)
    server.run()

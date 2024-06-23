import aria2p
from typing import List


from app.config import Aria2Config

aria2_config = Aria2Config.load()

# Aria2 client

ARIA2_API = aria2p.API(
        aria2p.Client(
            host=aria2_config.host, port=aria2_config.port, secret=aria2_config.secret
        )
    )


def add_http_task(url: str, dir: str, name: str, **kwargs) -> aria2p.Download:
    # add HTTP task
    return ARIA2_API.add(url, options={"out": name, "dir": dir}, **kwargs)[0]
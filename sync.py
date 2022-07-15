#!/usr/bin/python3

import datetime
import time
import os
import logging
import requests
from .api_config import Config
from .apis import *
from .async_httpclient import *
# import yarl 暂时不需要...你想整的话，去改curseforgeapi那些

if not os.path.exists("logs"):
    os.makedirs("logs")

logging.basicConfig(level=logging.INFO,
    filename="logs/log-{datetime}.txt".format(datetime=datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")),
    format = "[" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+'] [%(levelname)s]: %(message)s')

logging.debug("Logging started")

# a_req = async_request.Async_request()
# for url in a_req.request(["https://qq.com", "https://baidu.com"]):
#     print(url.status)

class Cache:
    def __init__(self):
        logging.info("Cache init")
    
    class CurseforgeCache:
        def __init__(self) -> None:
            self.key = Config.api_key
            self.base_api_url = Config.base_api_url
            self.proxies = Config.proxies

if __name__ == "__main__":
    cache = Cache()
    while True:
        # sync
        cache
        # time.sleep(Config.sync_interval * 60)
        break

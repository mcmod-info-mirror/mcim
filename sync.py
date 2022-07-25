#!/usr/bin/python3

import datetime
import json
import os
import logging
import asyncio
import aiohttp
from config import *
from async_httpclient import *
from apis import *
from mysql import *

class CurseforgeCache:
    '''
    缓存 curseforge 的信息
    '''
    def __init__(self, database: DataBase, *, limit: int = 64) -> None:
        self.key = MCIMConfig.curseforge_api_key
        self.api_url = MCIMConfig.curseforge_api
        self.proxies = MCIMConfig.proxies
        self.timeout = MCIMConfig.async_timeout
        self.headers = {
            'Accept': 'application/json',
            'x-api-key': "$2a$10$2DOXBr1x82Acn1A6GGw5b.psdLVOo29u5gEahTQSiGYmDOp2QXFSu"
        }
        self.cli = AsyncHTTPClient(headers=self.headers, timeout=aiohttp.ClientTimeout(total=self.timeout))
        self.api = CurseForgeApi(self.api_url, self.key, self.proxies, acli=self.cli)
        self.database = database
        self.sem = asyncio.Semaphore(limit)

    async def try_mod(self, modid):
        async with self.sem:
            try:
                data = await self.api.get_mod(modid)
                self.database.exe(insert("mod_status", dict(modid=modid, status=200), replace=True))
                self.database.exe(insert("mod_info", dict(modid=modid, data=json.dumps(data), replace=True)))
                logging.info(f"Get mod: {modid}")
            except StatusCodeException as e:
                self.database.exe(insert("mod_status", dict(modid=modid, status=e.status_code), replace=True))
                logging.info(f"Get mod: {modid} Error: {e.status_code}")
            await asyncio.sleep(1)

    async def sync(self):
        tasks = []
        for modid in range(10000, 100000):
            task = self.try_mod(modid)
            tasks.append(task)
        logging.info("get urls")
        await asyncio.gather(*tasks)
        logging.info("Finish")

async def main():
    MCIMConfig.load()
    MysqlConfig.load()
    database = DataBase(**MysqlConfig.to_dict())

    if not os.path.exists("logs"):
        os.makedirs("logs")

    logging.basicConfig(level=logging.INFO,
        filename="logs/log-{datetime}.txt".format(datetime=datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")),
        format='[' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + '] [%(levelname)s]: %(message)s')

    logging.debug("Logging started")

    cache = CurseforgeCache(database)
    await cache.sync()


if __name__ == "__main__":
    asyncio.run(main())

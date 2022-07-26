#!/usr/bin/python3

import datetime
import time
import json
import os
import logging
import asyncio
import aiohttp
from config import *
from async_httpclient import *
from apis import *
from mysql import *

def log(text,logging=logging.info):
    print(text)
    logging(text)

class CurseforgeCache:
    '''
    缓存 curseforge 的信息
    '''
    def __init__(self, database: DataBase, *, limit: int = 2) -> None:
        self.key = MCIMConfig.curseforge_api_key
        self.api_url = MCIMConfig.curseforge_api
        self.proxies = MCIMConfig.proxies
        self.timeout = MCIMConfig.async_timeout
        self.headers = {
            'Accept': 'application/json',
            'x-api-key': self.key
        }
        self.cli = AsyncHTTPClient(headers=self.headers, timeout=aiohttp.ClientTimeout(total=self.timeout))
        self.database = database
        self.sem = asyncio.Semaphore(limit)
        self.api = CurseForgeApi(self.api_url, self.key, self.proxies, acli=self.cli)

    async def try_mod(self, modid):
        async with self.sem:
            with self.database:
                try:
                    data = await self.api.get_mod(modid)
                    self.database.exe(insert("mod_info", dict(modid=modid, status=200, data=data, time=int(time.time())), replace=True)) # TODO time=time.time()
                    log(f"Get mod: {modid}")
                except StatusCodeException as e:
                    self.database.exe(insert("mod_info", dict(modid=modid, status=e.status, time=int(time.time())), replace=True))
                    log(f"Get mod: {modid} Error: {e.status}", logging=logging.error)
                except asyncio.TimeoutError:
                    log(f"Get mod: {modid} Timeout", logging=logging.error)
                    self.database.exe(insert("mod_info", dict(modid=modid, status=000, time=int(time.time())), replace=True))
                except TypeError:
                    log(f"Get mod: {modid} {data} JSON Error", logging=logging.error)
                    self.database.exe(insert("mod_info", dict(modid=modid, status=000, time=int(time.time())), replace=True))
                except KeyboardInterrupt:
                    log("BYE")
                except Exception as e:
                    log(f"Get mod: {modid} {e}", logging=logging.error)
                await asyncio.sleep(1)

    async def sync(self):
        tasks = []
        for modid in range(14000, 100000):
            task = self.try_mod(modid)
            tasks.append(task)
        log("Get curseforge mods")
        await asyncio.gather(*tasks)
        log("Finish curseforge mods")

def getLogFile(basedir='logs'):
    if not os.path.exists(basedir):
        os.makedirs(basedir)
    date = datetime.datetime.now().strftime('%Y-%m-%d')
    path = os.path.join(basedir, f'{date}.log')
    if os.path.exists(path):
        i = 1
        while os.path.exists(path):
            path = os.path.join(basedir, f'{date}-{i}.log')
            i += 1
    return path

async def main():
    MCIMConfig.load()
    MysqlConfig.load()
    database = DataBase(**MysqlConfig.to_dict())

    logging.basicConfig(level=logging.INFO,
        filename=getLogFile(), filemode='w',
        format='[%(asctime)s] [%(levelname)s]: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')

    logging.debug("Logging started")

    cache = CurseforgeCache(database,limit=16)
    await cache.sync()


if __name__ == "__main__":
    asyncio.run(main())

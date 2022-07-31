#!/usr/bin/python3

import datetime
import time
import json
import os
import logging
import asyncio
import aiohttp
import requests
from config import *
from async_httpclient import *
from apis import *
from mysql import *


def log(text, logging=logging.info, to_qq=False, to_file=True):
    print("[" + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()) + "] " + text)
    if to_file == True:
        logging(text)
    
    # 把必要 log 转发到我 QQ
    if to_qq == True: 
        if MCIMConfig.cqhttp_type == "user":
            url = f"{MCIMConfig.cqhttp_baseurl}send_private_msg"
            res = requests.get(url=url, params={"user_id": MCIMConfig.cqhttp_userid, "message": text})
        elif MCIMConfig.cqhttp_type == "group":
            url = f"{MCIMConfig.cqhttp_baseurl}send_group_msg"
            res = requests.get(url=url, params={"group_id": MCIMConfig.cqhttp_groupid, "message": text})
        elif MCIMConfig.cqhttp_type == "guild":
            url = f"{MCIMConfig.cqhttp_baseurl}send_guild_channel_msg"
            res = requests.get(url=url, params={"guild_id": MCIMConfig.cqhttp_guild_id, "channel_id": MCIMConfig.cqhttp_channel_id, "message": text})
        if res.status_code == 200:
            if res.json()["status"] in ["ok","async"]:
                pass
            else:
                print(f"Failed Request CqHttp",res.json())
        else:
            print(f"Request CqHttp Bad, Status Code: {res.status_code}")


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
        self.cli = AsyncHTTPClient(
            headers=self.headers, timeout=aiohttp.ClientTimeout(total=self.timeout))
        self.database = database
        self.sem = asyncio.Semaphore(limit)
        self.api = CurseForgeApi(self.api_url, self.key, self.proxies, acli=self.cli)
        # self.clash = clash.Clash(api_url=ClashConfig.api_url, port=ClashConfig.api_port, secret=ClashConfig.api_secret)

    async def try_mod(self, modid):
        async with self.sem:
            with self.database:
                try:
                    res, data = await self.api.get_mod(modid)
                    self.database.exe(insert("mod_info", dict(modid=modid, status=200, data=json.dumps(data), time=int(
                        time.time())), replace=True))  # TODO time=time.time()
                    log(f"Get mod: {modid}")
                except StatusCodeException as e:
                    self.database.exe(insert("mod_info", dict(
                        modid=modid, status=e.status, time=int(time.time())), replace=True))
                    log(f"Get mod: {modid} Status: {e.status}",
                        logging=logging.error)
                    if e.status == 403:
                        time.sleep(60*20)
                        log("=================OQS limit====================",
                            logging=logging.warning, to_qq=True)
                except asyncio.TimeoutError:
                    log(f"Get mod: {modid} Timeout", logging=logging.error)
                    self.database.exe(insert("mod_info", dict(
                        modid=modid, status=0, time=int(time.time())), replace=True))
                except TypeError:
                    log(f"Get mod: {modid} Type Error", logging=logging.error)
                    self.database.exe(insert("mod_info", dict(
                        modid=modid, status=0, time=int(time.time())), replace=True))
                except KeyboardInterrupt:
                    log("~~ BYE ~~", to_qq=True)
                except Exception as e:
                    log("Error: " + str(e), logging=logging.error, to_qq=True)

            await asyncio.sleep(1)



    async def sync(self):
        # MOD
        log("Start ALL MODS", to_qq=True)
        modid = 10000
        part = 0
        while True:
            if modid >= 105000:
                log("Finish ALL MODS", to_qq=True)
                break
            else:
                part += 1
                tasks = []
                for a in range(0, 950):
                    task = self.try_mod(modid)
                    tasks.append(task)
                    modid += 1
                log(f"Start {part}/100 curseforge mods", to_qq=True)
                await asyncio.gather(*tasks)
                log(f"Finish {part}/100 curseforge mods", to_qq=True)
                time.sleep(60*10)


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
    ClashConfig.load()
    database = DataBase(**MysqlConfig.to_dict())

    logging.basicConfig(level=logging.INFO,
                        filename=getLogFile(), filemode='w',
                        format='[%(asctime)s] [%(levelname)s]: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    log("Logging started", logging=logging.debug, to_qq=True)

    while True:
        log("Start sync", to_qq=True)
        cache = CurseforgeCache(database, limit=16)
        await cache.sync()
        log("Finish sync", to_qq=True)
        time.sleep(60*60)


if __name__ == "__main__":
    asyncio.run(main())

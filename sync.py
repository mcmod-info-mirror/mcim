#!/usr/bin/python3

import datetime
import json
import os
import time
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
    def __init__(self, database: DataBase) -> None:
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

        if not os.path.exists("cache/cursefroge"):
            os.makedirs("cache/cursefroge", exist_ok=True)

        with open(os.path.join("cache/cursefroge", "error_mod.json"), "w") as f:
            json.dump({"error_mod":{}}, f)

    def save_json_to_file(self, filename, data):
        with open(filename, "w") as f:
            json.dump(data, f)
    
    # def save_json_to_mysql(self, table, **kwargs):
    #     self.database.insert(table=table, **kwargs)

    async def callback(self, res):
        modid = res.url.path.split("/")[-1]
        status = res.status
        logging.info(res.url)
        if status == 200:
            # self.save_json_to_file(os.path.join("cache/cursefroge", "mod" + modid + ".json"),await res.json())
            self.database.exe(insert("mod_status", dict(modid=modid, status=status)))
            self.database.exe(insert("mod_info", dict(modid=modid, data=json.dumps(await res.json()))))
            logging.info(f"=========get modid {modid}==========")
        # if res.status == 403:
        #     print("QOS limit")
        #     time.sleep(60)
        else:
            self.database.exe(insert("mod_status", dict(modid=modid, status=status)))
            logging.info(f"--------get modid {modid} Error: {status}--------")
        # time.sleep(0.1) # 避免 QOS 限制
        await asyncio.sleep(0.1)

    async def sync(self):
        # categories = self.api.get_categories(gameid=432,classid=6)["data"]
        # total = 0
        # for category in categories:

        #     if category["parentCategoryId"] != 6 and category["url"] != "https://www.curseforge.com":
        #         search = self.api.search(gameid=432,classid=6,categoryid=category["id"])
        #         total = total + search["pagination"]["totalCount"]
        #         self.save_json_to_file("category"+str(category["id"])+".json",search)
        # print(total) #21211 mod不全 未知原因

        # search = self.api.search(gameid=432,classid=6,categoryid=6)


        # null_modids = {}
        # for modid in range(10000,100000):
        #     try:
        #         mod = self.api.get_mod(modid)
        #         if type(mod) == dict:
        #             self.save_json_to_file("mod"+str(modid)+".json",mod)
        #             print("get modid "+str(modid))
        #         else:
        #             null_modids[str(modid)] = mod
        #             print("get modid "+str(modid)+" error: "+str(mod))
        #     except Exception as e:
        #         print(e)
        # with open("error_modid.json","w") as f:
        #     json.dump(null_modids,f)

        # async
        limit = 50
        tasks = []
        headers = {
            'Accept': 'application/json',
            'x-api-key': self.key
        }
        for modid in range(10000, 100000):
            task = self.api.get_mod(modid)
        logging.info("get urls")
        await asyncio.gather(tasks)
        logging.info("Finish")

async def main():
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

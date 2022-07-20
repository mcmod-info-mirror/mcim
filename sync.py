#!/usr/bin/python3

import datetime
import json
import os
import time
import logging
import asyncio
import aiohttp
from wsproto import Headers
from api_config import Config
from async_httpclient import *
from apis import *


if not os.path.exists("logs"):
    os.makedirs("logs")

logging.basicConfig(level=logging.INFO,
    filename="logs/log-{datetime}.txt".format(datetime=datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")),
    format = "[" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+'] [%(levelname)s]: %(message)s')

logging.debug("Logging started")

# a_req = async_request.Async_request()
# for url in a_req.request(["https://qq.com", "https://baidu.com"]):
#     print(url.status)

def log(text,level="info"):
    if level == "info":
        logging.info(text)
    elif level == "debug":
        logging.debug(text)
    elif level == "error":
        logging.error(text)
    elif level == "warning":
        logging.warning(text)
    else:
        logging.info(text)
    print(text)

class CurseforgeCache:
    '''
    缓存 curseforge 的信息
    '''
    def __init__(self) -> None:
        self.key = Config.api_key
        self.base_api_url = Config.curseforge_base_api_url
        self.proxies = Config.proxies
        self.timeout = Config.async_timeout
        self.api = CurseForgeApi(self.base_api_url,self.key, self.proxies)
        self.headers = {
            'Accept': 'application/json',
            'x-api-key': "$2a$10$2DOXBr1x82Acn1A6GGw5b.psdLVOo29u5gEahTQSiGYmDOp2QXFSu"
        }
        self.cli = AsyncHTTPClient(headers=self.headers, timeout=aiohttp.ClientTimeout(total=self.timeout))

        if not os.path.exists("cache/cursefroge"):
            os.makedirs("cache/cursefroge", exist_ok=True)

        with open(os.path.join("cache/cursefroge","error_mod.json"), "w") as f:
            json.dump({"error_mod":{}}, f)

    def save_json_to_file(self, filename, data):
        with open(filename, "w") as f:
            json.dump(data, f)
    
    async def callback(self, res):
        modid = res.url.path.split("/")[-1]
        log(res.url,type(res.status))
        if res.status == 200:
            self.save_json_to_file(os.path.join("cache/cursefroge", "mod" + modid + ".json"),await res.json())
            log("=========get modid "+str(modid)+"==========")
        # if res.status == 403:
        #     print("QOS limit")
        #     time.sleep(60)
        else:
            with open(os.path.join("cache/cursefroge","error_mod.json"),"r") as f:
                data = json.load(f)
                data["error_mod"][modid] = res.status
            with open(os.path.join("cache/cursefroge","error_mod.json"),"w") as wf:
                json.dump(data,wf)
            log("--------get modid "+str(modid)+" error: "+str(res.status)+"--------")
        # time.sleep(0.1) # 避免 QOS 限制
        time.sleep(0.1)

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
        urls = []
        headers={
            'Accept': 'application/json',
            'x-api-key': self.api
        }
        for modid in range(10000, 100000):
            url = self.base_api_url + "/mods/{modid}".format(modid=modid)
            urls.append(url)
        log("get urls")
        aiohttp.ClientSession()
        async with self.cli:
            await self.cli.get_all(urls=urls, limit=limit, callback=self.callback)
            # await cli.get_all(urls=urls,headers=self.headers,timeout=self.timeout,sem=sem,callback=self.callback)
            log("Finish")
        pass

if __name__ == "__main__":
    cache = CurseforgeCache()
    asyncio.run(cache.sync())
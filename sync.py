#!/usr/bin/python3

import datetime
import json
import os
import logging
import asyncio
import aiohttp
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

cli = AsyncHTTPClient()
    
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
            'x-api-key': self.key
        }

        if not os.path.exists("cache/cursefroge"):
            os.makedirs("cache/cursefroge",exist_ok=True)

        with open(os.path.join("cache/cursefroge","error_mod.json"),"w") as f:
            json.dump({"error_mod":{}},f)

    def save_json_to_file(self,filename,data):
        with open(filename,"w") as f:
            json.dump(data,f)
    
    async def callback(self,res):
        modid = res.url.path.split("/")[-1]
        if res.status == 200:
            self.save_json_to_file(os.path.join("cache/cursefroge","mod" + modid + ".json"),await res.json())
            print("=========get modid "+str(modid)+"==========")
        else:
            with open(os.path.join("cache/cursefroge","error_mod.json"),"r") as f:
                data = json.load(f)
                data["error_mod"][modid] = res.status
            with open(os.path.join("cache/cursefroge","error_mod.json"),"w") as wf:
                json.dump(data,wf)
            print("--------get modid "+str(modid)+" error: "+str(res.status)+"--------")
    
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
        sem = 100
        urls = []

        for modid in range(10000,100000):
            url = self.base_api_url + "v1/mods/{modid}".format(modid=modid)
            urls.append(url)
        print("get urls")
        async with aiohttp.ClientSession(headers=self.headers, timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
            await cli.get_all(urls=urls, session=session,sem=sem,callback=self.callback) #试图只用一个session
            # await cli.get_all(urls=urls,headers=self.headers,timeout=self.timeout,sem=sem,callback=self.callback)
            print("Finish")
        pass

if __name__ == "__main__":
    try:
        cache = CurseforgeCache()
        asyncio.run(cache.sync())
    except RuntimeError:
        pass
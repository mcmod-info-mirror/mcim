#!/usr/bin/python3

import base64
import threading
import datetime
import re
import time
import json
import os
import logging
import asyncio
from typing import List
import aiohttp
import requests
from config import *
from async_httpclient import *
from apis import *
from mysql import *

import warnings 
warnings.filterwarnings("ignore")

def log(text, logging=logging.info, to_qq=False, to_file=True):
    print("[" + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()) + "] " + text)
    if to_file:
        logging(text)

    # 把必要 log 转发到我 QQ
    if to_qq:
        if MCIMConfig.cqhttp_type == "user":
            url = f"{MCIMConfig.cqhttp_baseurl}send_private_msg"
            res = requests.get(url=url, params={"user_id": MCIMConfig.cqhttp_userid, "message": text})
        elif MCIMConfig.cqhttp_type == "group":
            url = f"{MCIMConfig.cqhttp_baseurl}send_group_msg"
            res = requests.get(url=url, params={"group_id": MCIMConfig.cqhttp_groupid, "message": text})
        elif MCIMConfig.cqhttp_type == "guild":
            url = f"{MCIMConfig.cqhttp_baseurl}send_guild_channel_msg"
            res = requests.get(url=url, params={
                "guild_id": MCIMConfig.cqhttp_guild_id,
                "channel_id": MCIMConfig.cqhttp_channel_id,
                "message": text
            })
        if res.status_code == 200:
            if res.json()["status"] not in ["ok", "async"]:
                print(f"Failed Request CqHttp", res.json())
        else:
            print(f"Request CqHttp Bad, Status Code: {res.status_code}")


def getLogFile(basedir='logs'):
    if not os.path.exists(basedir):
        os.makedirs(basedir)
    date = datetime.datetime.now().strftime('%Y-%m-%d')
    path = os.path.join(basedir, f'{date}.log')
    if os.path.exists(path):
        i = 0
        while os.path.exists(path):
            i += 1
            path = os.path.join(basedir, f'{date}-{i}.log')
    return path


class CurseforgeCache:
    '''
    缓存 curseforge 的信息
    '''

    def __init__(self, database: DataBase = None, *, limit: int = 16) -> None:
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
        if database is None:
            self.database: DataBase = DataBase(**MysqlConfig.to_dict())
        else:
            self.database = database
        self.sem = asyncio.Semaphore(limit)
        self.api = CurseForgeApi(self.api_url, self.key, self.proxies, acli=self.cli)
        # self.clash = clash.Clash(api_url=ClashConfig.api_url, port=ClashConfig.api_port, secret=ClashConfig.api_secret)

    async def try_mod(self, modid):
        async with self.sem:
            with self.database:
                try:
                    data = (await self.api.get_mod(modid))["data"]
                    data["cachetime"] = int(time.time())
                    self.database.exe(
                        insert("curseforge_mod_info", dict(modid=modid, status=200, data=json.dumps(data), time=int(
                            time.time())), replace=True))
                    log(f"Get mod: {modid}")
                except StatusCodeException as e:
                    self.database.exe(insert("curseforge_mod_info", dict(
                        modid=modid, status=e.status, time=int(time.time())), replace=True))
                    log(f"Get mod: {modid} Status: {e.status}",
                        logging=logging.error)
                    if e.status == 403:
                        time.sleep(60 * 20)
                        log("=================OQS limit====================", logging=logging.warning, to_qq=True)
                except asyncio.TimeoutError:
                    log(f"Get mod: {modid} Timeout", logging=logging.error)
                    self.database.exe(insert("curseforge_mod_info", dict(
                        modid=modid, status=0, time=int(time.time())), replace=True))
                # except TypeError:
                #     log(f"Get mod: {modid} Type Error", logging=logging.error)
                #     self.database.exe(insert("curseforge_mod_info", dict(
                #         modid=modid, status=0, time=int(time.time())), replace=True))
            await asyncio.sleep(1)

    async def try_games(self, gameid):
        async with self.sem:
            with self.database:
                try:
                    data = (await self.api.get_game(gameid))["data"]
                    self.database.exe(
                        insert("curseforge_game_info", dict(gameid=gameid, status=200, data=json.dumps(data), time=int(
                            time.time())), replace=True))
                    log(f"Get game: {gameid}")
                except StatusCodeException as e:
                    self.database.exe(insert("curseforge_game_info", dict(
                        gameid=gameid, status=e.status, time=int(time.time())), replace=True))
                    log(f"Get game: {gameid} Status: {e.status}",
                        logging=logging.error)
                    if e.status == 403:
                        time.sleep(60 * 20)
                        log("=================OQS limit====================", logging=logging.warning, to_qq=True)
                except asyncio.TimeoutError:
                    log(f"Get game: {gameid} Timeout", logging=logging.error)
                    self.database.exe(insert("curseforge_game_info", dict(
                        gameid=gameid, status=0, time=int(time.time())), replace=True))
                # except TypeError:
                #     log(f"Get game: {gameid} Type Error", logging=logging.error)
                #     self.database.exe(insert("curseforge_game_info", dict(
                #         gameid=gameid, status=0, time=int(time.time())), replace=True))
            await asyncio.sleep(1)

    async def sync(self):
        log("Start sync Curseforge", to_qq=True)
        # Games
        log("Start ALL GAMES", to_qq=True)
        all_games = await self.api.get_all_games()
        for game in all_games["data"]:
            gameid = game["id"]
            game["cachetime"] = int(time.time())
            self.database.exe(insert(
                "curseforge_game_info",
                dict(gameid=gameid, status=200, time=int(time.time()), data=json.dumps(game)),
                replace=True))
        log("Finish ALL GAMES", to_qq=True)

        # MOD
        log("Start ALL MODS", to_qq=True)
        start_modid = 10000
        end_modid = 105000
        modid = start_modid
        tasks = []
        for modid in range(start_modid, end_modid):
            task = self.try_mod(modid)
            tasks.append(task)
            modid += 1
            if len(tasks) >= 950:
                log(f"Start {modid}/{end_modid} curseforge mods", to_qq=True)
                await asyncio.gather(*tasks)
                log(f"Finish {modid}/{end_modid} curseforge mods", to_qq=True)
                tasks.clear()
                time.sleep(60 * 10)
        log("Finish ALL MODS", to_qq=True)
        log("Finish sync Curseforge", to_qq=True)


class ModrinthCache:
    def __init__(self, database: DataBase = None, *, limit: int = 16):
        self.api_url = MCIMConfig.modrinth_api
        self.proxies = MCIMConfig.proxies
        self.timeout = MCIMConfig.async_timeout
        self.headers = {
            "User-Agent": "github_org/mcim/1.0.0 (mcim.z0z0r4.top)",
            'Accept': 'application/json'
        }
        self.cli = AsyncHTTPClient(
            headers=self.headers, timeout=aiohttp.ClientTimeout(total=self.timeout))
        if database is None:
            self.database: DataBase = DataBase(**MysqlConfig.to_dict())
        else:
            self.database = database
        self.sem = asyncio.Semaphore(limit)
        self.api = ModrinthApi(self.api_url, proxies=self.proxies, acli=self.cli)

    async def _sync_one(self, limit: int, offset: int):
        res = await self.api.search(limit=limit, offset=offset)
        for proj in res["hits"]:
            pid = proj["project_id"]
            proj = await self.api.get_project(pid)
            proj["cachetime"] = int(time.time())
            with self.database:
                self.database.exe(cmd := insert("modrinth_project_info", dict(
                    project_id=pid, slug=proj["slug"], status=200, time=int(time.time()),
                    data=json.dumps(proj)), replace=True))
                for vid in proj["versions"]:
                    ver = await self.api.get_project_version(vid)
                    ver["cachetime"] = int(time.time())
                    self.database.exe(cmd := insert("modrinth_version_info", dict(
                        project_id=pid, version_id=vid,
                        status=200, time=int(time.time()), data=json.dumps(ver)), replace=True))
                    log(f'Get version: {vid}')
                log(f"Get mod: {pid}")

    async def sync(self):
        log("Start sync Modrinth", to_qq=True)
        async with self.sem:
            # tag
            log("Start ALL TAGS", to_qq=True)
            async def _modrinth_sync_tag_category():
                data = await self.api.get_categories()
                self.database.exe(insert("modrinth_tag_info",
                                    dict(slug="category", status=200,
                                        time=int(time.time()),
                                        data=json.dumps(data)), replace=True))

            async def _modrinth_sync_tag_loader():
                data = await self.api.get_loaders()
                self.database.exe(insert("modrinth_tag_info",
                                    dict(slug="loader", status=200,
                                        time=int(time.time()),
                                        data=json.dumps(data)), replace=True))

            async def _modrinth_sync_tag_game_version():
                data = await self.api.get_game_versions()
                self.database.exe(insert("modrinth_tag_info",
                                    dict(slug="game_version", status=200,
                                        time=int(time.time()),
                                        data=json.dumps(data)), replace=True))

            async def _modrinth_sync_tag_license():
                data = await self.api.get_licenses()
                self.database.exe(insert("modrinth_tag_info",
                                    dict(slug="license", status=200,
                                        time=int(time.time()),
                                        data=json.dumps(data)), replace=True))
            await asyncio.gather(_modrinth_sync_tag_category(),_modrinth_sync_tag_game_version(),_modrinth_sync_tag_loader(),_modrinth_sync_tag_license())
            log("Finish ALL TAGS", to_qq=True)

            # project
            log("Start ALL PROJECTS", to_qq=True)
            limit = 100
            offset = 0
            res = await self.api.search(limit=limit, offset=offset)
            total = res["total_hits"]
            for offset in range(0, total, limit):
                try:
                    await self._sync_one(limit, offset)
                except Exception as e:
                    log("Error: " + str(e), logging=logging.error, to_qq=True)
            log("Finish ALL PROJECTS", to_qq=True)
        log("Start sync Modrinth", to_qq=True)
        

class McModCache:
    def __init__(self, database: DataBase = None, limit: int = 4) -> None:
        self.api_url = MCIMConfig.mcmod_api
        self.req_proxies = {"http": "http://127.0.0.1:7890/","https": "http://127.0.0.1:7890/"}
        self.proxies = "http://127.0.0.1:7890/"
        self.timeout = MCIMConfig.async_timeout
        self.headers = {
            "User-Agent": "github_org/mcim/1.0.0 (mcim.z0z0r4.top)"
        }
        self.cf_headers = {
            'Accept': 'application/json',
            'x-api-key': MCIMConfig.curseforge_api_key
        }
        self.cli = AsyncHTTPClient(
            headers=self.headers, timeout=aiohttp.ClientTimeout(total=self.timeout))
        if database is None:
            self.database: DataBase = DataBase(**MysqlConfig.to_dict())
        else:
            self.database = database
        self.sem = asyncio.Semaphore(limit)
        self.cf_api = CurseForgeApi(baseurl=MCIMConfig.curseforge_api, api_key=MCIMConfig.curseforge_api_key, proxies=MCIMConfig.proxies, acli=AsyncHTTPClient(headers=self.cf_headers, timeout=aiohttp.ClientTimeout(total=self.timeout)))
        self.mr_api = ModrinthApi(self.api_url, proxies=self.proxies, acli=self.cli)
    
    async def get_class_html(self, classid: int):
        async with self.cli:
            async with self.sem:
                # res, content = await self.cli.get(f'{self.api_url}class/{classid}.html', proxy=self.proxies, verify_ssl=False)
                try:
                    res = requests.get(f'{self.api_url}class/{classid}.html', proxies=self.req_proxies, verify=False)
                    if res.status_code == 200:
                        content = res.text
                        # content = str(content, "UTF-8")
                        # get chinese name
                        insert_dict = {}
                        insert_dict["classid"] = classid
                        zh_name_match_result = re.findall("<h3>(.+?)</h3>", content)
                        en_name_match_result = re.findall("<h4>(.+?)</h4>", content)
                        if len(zh_name_match_result) != 0:
                            if (zh_name_match_result[0].encode( 'UTF-8' ).isalpha() or "'" in zh_name_match_result[0]) and en_name_match_result == []:
                                insert_dict["en_name"] = zh_name_match_result[0] # 只有英文名
                            else:
                                insert_dict["en_name"] = en_name_match_result[0]
                                insert_dict["zh_name"] = zh_name_match_result[0]
                            if "zh_name" and "en_name" in locals()["insert_dict"]:
                                log(f'{classid} found {insert_dict["en_name"]} to {insert_dict["zh_name"]}')
                            else:
                                log(f'{classid} found {insert_dict} to None')
                            insert_dict = await self.get_info(insert_dict, content, classid)
                            return self.database.exe(insert("mcmod_info", obj=insert_dict, replace=True))
                        else:
                            log(f"{classid} not found any name")
                except Exception as e:
                    log(f'GET {self.api_url}class/{classid}.html error {e}')
                    return None                
    async def get_info(self, insert_dict: dict, content: str, classid: int):
        insert_dict["status"] = 200
        insert_dict["time"] = int(time.time())
        for herf in re.findall('"//link.mcmod.cn/target/(.+?)"', content):
            herf = herf.replace("@","/").replace("\\","").replace("-","+")
            if "aHR0cHM6" in herf:
                # try:
                url = base64.b64decode(herf).decode(encoding="UTF-8")
                if "https://www.curseforge.com/" in url:
                    slug = url.split("/")[-1]
                    cmd = select("curseforge_mod_info", ["modid"]).where("slug", slug).done()
                    query = self.database.queryone(cmd)
                    if query is not None:
                        insert_dict["modid"] = query[0]
                    else:
                        insert_dict["modid"] = (await self.cf_api.search(slug=slug))["data"][0]["id"]
                if "https://modrinth.com/" in url:
                    slug = url.split("/")[-1]
                    cmd = select("modrinth_project_info", ["project_id"]).where("slug", slug).done()
                    query = self.database.queryone(cmd)
                    if query is not None:
                        insert_dict["project_id"] = query[0]
                    else:
                        insert_dict["project_id"] = (await self.mr_api.get_project(slug=slug))["id"]
                # except:
                #     log(f"{classid} decode {herf} error")
                #     return None
        return insert_dict

    async def sync(self):
        log("Start sync MCMod", to_qq=True)
        with self.database:
            tasks = []
            for classid in range(1, 1000):
                tasks.append(self.get_class_html(classid=classid))
            await asyncio.gather(*tasks)
        log("Finish sync MCMod", to_qq=True)

async def main():
    MCIMConfig.load()
    MysqlConfig.load()
    ClashConfig.load()
    database = DataBase(**MysqlConfig.to_dict())

    logging.basicConfig(level=logging.INFO,
                        filename=getLogFile(), filemode='w',
                        format='[%(asctime)s] [%(threadName)s] [%(levelname)s]: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S', encoding="UTF-8")
    
    log("Logging started", logging=logging.debug, to_qq=True)
    threads = []
    try:
        while True:
            threads = [
            # log("Start sync Modrinth", to_qq=True)
            # Modrinth_sync_thread = threading.Thread(target=asyncio.run, args=(ModrinthCache(database=database).sync(),), daemon=True)
            threading.Thread(name="Modrinthsync", target=asyncio.run, args=(ModrinthCache().sync(),), daemon=True),
            # await ModrinthCache(database=database).sync()
            # log("Finish sync Modrinth", to_qq=True)

            # log("Start sync Curseforge", to_qq=True)
            # Curseforge_sync_thread = threading.Thread(target=asyncio.run, args=(CurseforgeCache(database=database).sync(),), daemon=True)
            threading.Thread(name="Curseforgesync", target=asyncio.run, args=(CurseforgeCache().sync(),), daemon=True),
            # await CurseforgeCache(database=database, limit=16).sync()
            # log("Finish sync Curseforge", to_qq=True)
            # McMod_sync_thread = threading.Thread(target=asyncio.run, args=(McModCache(database=database).sync(),), daemon=True)
            threading.Thread(name="McModsync", target=asyncio.run, args=(McModCache().sync(),), daemon=True)
            # await McModCache(database=database).sync()
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

    except KeyboardInterrupt:
        pass
    # except Exception as e:
    #     log("Error: " + str(e), logging=logging.error, to_qq=True)
    # log("~~ BYE ~~", to_qq=True)


if __name__ == "__main__":
    # opts, agrs = getopt.getopt(sys.argv[1:], '-s:', ['start_modid='])
    # for opt_name, opt_value in opts:
    #     if opt_name in ("-s", "--start_modid"):
    #         start_modid = int(opt_value)
    #     else:
    #         start_modid = 10000
    asyncio.run(main())

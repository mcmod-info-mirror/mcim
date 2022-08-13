#!/usr/bin/python3

import datetime
import time
import json
import os
import sys
import getopt
import logging
import asyncio
from typing import List
import aiohttp
import requests
from config import *
from async_httpclient import *
from apis import *
from mysql import *


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
        global start_modid
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


class ModrinthCache:
    def __init__(self, database: DataBase, *, limit: int = 2):
        self.api_url = MCIMConfig.modrinth_api
        self.proxies = MCIMConfig.proxies
        self.timeout = MCIMConfig.async_timeout
        self.headers = {
            "User-Agent": "github_org/mcim/1.0.0 (mcim.z0z0r4.top)",
            'Accept': 'application/json'
        }
        self.cli = AsyncHTTPClient(
            headers=self.headers, timeout=aiohttp.ClientTimeout(total=self.timeout))
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
        limit = 100
        offset = 0
        res = await self.api.search(limit=limit, offset=offset)
        total = res["total_hits"]
        for offset in range(0, total, limit):
            try:
                self._sync_one(limit, offset)
            except Exception as e:
                log("Error: " + str(e), logging=logging.error, to_qq=True)
        
        # tag
        async def _modrinth_sync_tag_category():
            data = await self.api.get_categories()
            data["cachetime"] = int(time.time())
            self.database.exe(insert("modrinth_tag_info",
                                dict(slug="category", status=200,
                                    time=data["cachetime"],
                                    data=json.dumps(data)), replace=True))

        async def _modrinth_sync_tag_loader():
            data = await self.api.get_loaders()
            data["cachetime"] = int(time.time())
            self.database.exe(insert("modrinth_tag_info",
                                dict(slug="loader", status=200,
                                    time=data["cachetime"],
                                    data=json.dumps(data)), replace=True))

        async def _modrinth_sync_tag_game_version():
            data = await self.api.get_game_versions()
            data["cachetime"] = int(time.time())
            self.database.exe(insert("modrinth_tag_info",
                                dict(slug="game_version", status=200,
                                    time=data["cachetime"],
                                    data=json.dumps(data)), replace=True))

        async def _modrinth_sync_tag_license():
            data = await self.api.get_licenses()
            data["cachetime"] = int(time.time())
            self.database.exe(insert("modrinth_tag_info",
                                dict(slug="license", status=200,
                                    time=data["cachetime"],
                                    data=json.dumps(data)), replace=True))
        await asyncio.gather(_modrinth_sync_tag_category(),_modrinth_sync_tag_game_version(),_modrinth_sync_tag_loader(),_modrinth_sync_tag_license())

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

    try:
        while True:
            log("Start sync Modrinth", to_qq=True)
            await ModrinthCache(database=database).sync()
            log("Finish sync Modrinth", to_qq=True)

            log("Start sync Curseforge", to_qq=True)
            cache = CurseforgeCache(database=database, limit=16)
            await cache.sync()
            log("Finish sync Curseforge", to_qq=True)
            time.sleep(60 * 60)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        log("Error: " + str(e), logging=logging.error, to_qq=True)
    log("~~ BYE ~~", to_qq=True)


if __name__ == "__main__":
    opts, agrs = getopt.getopt(sys.argv[1:], '-s:', ['start_modid='])
    for opt_name, opt_value in opts:
        if opt_name in ("-s", "--start_modid"):
            start_modid = int(opt_value)
        else:
            start_modid = 10000
    asyncio.run(main())

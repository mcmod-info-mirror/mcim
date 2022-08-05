
import time
import json
import functools
import asyncio
import aiohttp
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from apis import *
from config import *
from async_httpclient import *
from mysql import *

MCIMConfig.load()
MysqlConfig.load()

api = FastAPI()
proxies = MCIMConfig.proxies
timeout = MCIMConfig.async_timeout
database = DataBase(**MysqlConfig.to_dict())

# for cf
cf_key = MCIMConfig.curseforge_api_key
cf_api_url = MCIMConfig.curseforge_api
cf_headers = {
    'Accept': 'application/json',
    'x-api-key': cf_key
}
cf_cli = AsyncHTTPClient(
    headers=cf_headers, timeout=aiohttp.ClientTimeout(total=timeout))
database = database
cf_api = CurseForgeApi(cf_api_url, cf_key, proxies=proxies, acli=cf_cli)


def api_json_middleware(callback):
    @functools.wraps(callback)
    async def w(*args, **kwargs):
        try:
            res = await callback(*args, **kwargs)
            return res
        except StatusCodeException as e:
            if e.status == 404:
                return {"status": "failed", "error": "DataNotExists", "errorMessage": "Data Not exists"}
            return {"status": "failed", "error": "StatusCodeException", "errorMessage": str(e)}
        except Exception as e:
            return {"status": "failed", "error": "InternalError", "errorMessage": str(e)}
    return w


@api.get("/")
@api_json_middleware
async def root():
    return {"status": "success", "message": "z0z0r4 Mod Info"}


@api.get("/curseforge")
@api_json_middleware
async def curseforge():
    return await cf_api.end_point()


async def _sync_game(gameid: int):
    data = await cf_api.get_game(gameid=gameid)
    # add cachetime
    cache_data = data["data"]
    cache_data["cachetime"] = int(time.time())
    database.exe(insert("game_info", dict(gameid=gameid, status=200, time=int(
        time.time()), data=json.dumps(cache_data)), replace=True))
    return cache_data


async def _get_game(gameid: int):
    with database:
        result = database.query(
            select("game_info", ["time", "status", "data"]).where("gameid", gameid).done())
        if result is None or len(result) == 0 or result[1] != 200:
            data = await _sync_game(gameid)
        else:
            data = json.loads(result[2])
            if int(time.time()) - int(data["cachetime"]) > 60 * 60 * 4:
                data = await _sync_game(gameid)
    return {"status": "success", "data": data}


@api.get("/curseforge/game/{gameid}")
@api_json_middleware
async def curseforge_game(gameid: int):
    return await _get_game(gameid=gameid)


@api.get("/curseforge/games")
@api_json_middleware
async def curseforge_games():
    all_data = []
    with database:
        sql_games_result = database.query(
            select("game_info", ["gameid", "time", "status", "data"]), all=True)
        for result in sql_games_result:
            if result is None or result == () or result[2] != 200:
                break
            else:
                gameid, time_tag, status, data = result
                data = json.loads(data)
                if int(time.time()) - int(data["cachetime"]) > 60 * 60 * 4:
                    break
                else:
                    all_data.append(data)
        else:
            return {"status": "success", "data": all_data}
        all_data = []
        sync_games_result = await cf_api.get_all_games()
        for result in sync_games_result["data"]:
            gameid = result["id"]
            result["cachetime"] = int(time.time())
            a = database.exe(insert("game_info", dict(gameid=gameid, status=200, time=int(
                time.time()), data=json.dumps(result)), replace=True))
            all_data.append(result)
    return {"status": "success", "data": all_data}


@api.get("/curseforge/categories")
@api_json_middleware
# 无法缓存...
async def curseforge_categories(gameid: int = 432, classid: int = None):
    with database:
        data = await cf_api.get_categories(gameid=gameid, classid=classid)
        return {"status": "success", "data": data}


async def _sync_mod(modid: int):
    data = await cf_api.get_mod(modid=modid)
    # add cachetime
    cache_data = data["data"]
    cache_data["cachetime"] = int(time.time())
    database.exe(insert("mod_info", dict(modid=modid, status=200, time=int(
        time.time()), data=json.dumps(cache_data)), replace=True))
    return cache_data


async def _get_mod(modid: int):
    with database:
        result = database.query(
            select("mod_info", ["time", "status", "data"]).where("modid", modid).done())
        if result is None or len(result) == 0 or result[1] != 200:
            data = await _sync_mod(modid)
        else:
            data = json.loads(result[2])
            if int(time.time()) - int(data["cachetime"]) > 60 * 60 * 4:
                data = await _sync_mod(modid)
    return {"status": "success", "data": data}


@api.get("/curseforge/mod/{modid}")
@api_json_middleware
async def get_mod(modid: int):
    return await _get_mod(modid)


class ModItemModel(BaseModel):
    modid: list[int]


@api.post('/curseforge/mods')
@api_json_middleware
async def get_mods(item: ModItemModel):
    modids_data = []
    for modid in set(item.modid):
        data = await _get_mod(modid)
        modids_data.append(data)

    return {"status": "success", "data": modids_data}


@api.get("/curseforge/mod/{modid}/description")
@api_json_middleware
async def get_mod_description(modid: int):
    result = database.query(select("mod_description", ["modid", "time", "status", "description"]).where("modid", modid).done(), all=True)
    if result is None or len(result) == 0 or result[2] != 200 or int(time.time()) - result[2] > 60 * 60 * 4:
        time = int(time.time())
        data = (await cf_api.get_mod_description(modid=modid))["data"]
        database.exe(insert("mod_description", dict(modid=modid, status=200, time=time, description=data["description"]), replace=True))
    else:
        description = result[3]
        time = result[2]
    data = {"status": "success", "data": {"description": description}, "cachetime": time}



@api.get("/curseforge/search")
@api_json_middleware
async def curseforge_search(gameId: int, classId: int = None, categoryId: int = None, gameVersion: str = None, searchFilter: str = None, sortField: int | str = None, sortOrder: str = None, modLoaderType: int = None, gameVersionTypeId: int = None, slug: str = None, index: int = None, pageSize: int = 50):
    return {"status": "success", "data":
            (await cf_api.search(gameid=gameId, classid=classId, categoryid=categoryId, gameversion=gameVersion, searchfilter=searchFilter, sortfield=sortField, sortorder=sortOrder, modloadertype=modLoaderType, gameversiontypeid=gameVersionTypeId, slug=slug, index=index, pagesize=pageSize))["data"]
            }


async def _sync_file_info(modid: int, fileid: int, isinsert: bool = False):
    cache_data = (await cf_api.get_file(modid=modid, fileid=fileid))["data"]
    cache_data["cachetime"] = int(time.time())
    if isinsert:
        cmd = insert("file_info", dict(modid=modid, fileid=fileid, status=200, time=int(time.time()), data=json.dumps(cache_data)))
    else:
        cmd = update("file_info", dict(status=200, time=int(time.time(
        )), data=json.dumps(cache_data))).where("modid", modid).AND("fileid", fileid).done()
    database.exe(cmd)
    return cache_data


async def _get_file_info(modid: int, fileid: int):
    with database:
        cmd = select("file_info", ["time", "status", "data"]).where(
            "modid", modid).AND("fileid", fileid).done()
        query = database.query(cmd)
        if query is None:
            data = await _sync_file_info(modid=modid, fileid=fileid, isinsert=True)
            return {"status": "success", "data": data}
        elif len(query) <= 0 or query[1] != 200:
            data = await _sync_file_info(modid=modid, fileid=fileid)
            return {"status": "success", "data": data}
        else:
            data = json.loads(query[2])
            if int(time.time()) - int(data["cachetime"]) > 60 * 60 * 4:
                data = await _sync_file_info(modid=modid, fileid=fileid)
        return {"status": "success", "data": data}


@api.get("/curseforge/mod/{modId}/file/{fileId}")
@api_json_middleware
async def curseforge_mod_file(modId: int, fileId: int):
    return await _get_file_info(modid=modId, fileid=fileId)

@api.get("/curseforge/mod/{modId}/files")
@api_json_middleware
async def curseforge_mod_files(modId: int):
    return {"status": "success", "data": await cf_api.get_files(modid=modId)}


async def _sync_mod_file_changelog(modid: int, fileid: int, isinsert: bool = False):
    changelog = (await cf_api.get_mod_file_changelog(modid=modid, fileid=fileid))["data"]
    if isinsert:
        cmd = insert("file_info", dict(modid=modid, fileid=fileid, status=200, time=int(time.time()), changelog=changelog))
    else:
        cmd = update("file_info", dict(status=200, time=int(time.time()), changelog=changelog)).where("modid", modid).AND("fileid", fileid).done()
    database.exe(cmd)
    return changelog


async def _get_mod_file_changelog(modid: int, fileid: int):
    with database:
        cmd = select("file_info", ["time", "status", "changelog"]).where(
            "modid", modid).AND("fileid", fileid).done()
        query = database.query(cmd)
        if query is None:
            data = await _sync_mod_file_changelog(modid=modid, fileid=fileid, isinsert=True)
            time = int(time.time())
            return {"status": "success", "data": data, "cachetime": time}
        elif len(query) <= 0 or query[1] != 200:
            data = await _sync_file_info(modid=modid, fileid=fileid)
            time = int(time.time())
            return {"status": "success", "data": data, "cachetime": time}
        else:
            data = str(query[2])
            time = int(query[0])
            if int(time.time()) - time > 60 * 60 * 4:
                data = await _sync_file_info(modid=modid, fileid=fileid)
                time = int(time.time())
        return {"status": "success", "data": data, "cachetime": time}


@api.get("/curseforge/mod/{modId}/file/{fileId}/changelog")
@api_json_middleware
async def curseforge_mod_file_changelog(modId: int, fileId: int):
    return await _get_mod_file_changelog(modid=modId, fileid=fileId)


if __name__ == "__main__":
    host, port = "127.0.0.1", 8000
    try:
        uvicorn.run(api, host=host, port=port)
    except KeyboardInterrupt:
        print("~~ BYE ~~")


import time
import json
import functools
import asyncio
import aiohttp
import uvicorn
from fastapi import Body, FastAPI
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
cf_cli = AsyncHTTPClient(headers=cf_headers, timeout=aiohttp.ClientTimeout(total=timeout))
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

@api.get("/curseforge/games")
@api_json_middleware
async def curseforge_games(cache: bool = True):
    with database:
        if cache == True:
            data = []
            result = database.query(select("game_info", ["data"]), all=True)
            for res in result:
                data.append(json.loads(res[0]))

        else:
            notimedata = await cf_api.get_all_games()
            data = []
            for game_data in notimedata["data"]:
                gameid = game_data["id"]

                # add cachetime
                game_data["cachetime"] = int(time.time())
                data.append(game_data)

                database.exe(insert("game_info", dict(gameid=gameid, status=200, time=int(time.time()), data=json.dumps(game_data)), replace=True))
    
    return {"status": "success", "data": data}

async def _get_game(gameid: int):
    data = await cf_api.get_game(gameid=gameid)

    # add cachetime
    cache_data = data["data"]
    cache_data["cachetime"] = int(time.time())

    database.exe(insert("game_info", dict(gameid=gameid, status=200, time=int(time.time()), data=json.dumps(cache_data)), replace=True))
    return cache_data

@api.get("/curseforge/game/{gameid}")
@api_json_middleware
async def curseforge_game(gameid: int, cache: bool = True):
    with database:
        if cache:
            result = database.query(select("game_info", ["time", "status", "data"]).where("gameid", gameid).done())
            if result == None:
                await _get_game(gameid)
                return {"status": "failed", "error": "DataNotExists", "errorMessage": "Data Not exists"}

            if result != ():
                time_tag, status, data = result
                data = json.loads(data)
                if not status == 200:
                    await _get_game(gameid)
                else:
                    result_data = data
            else:
                await _get_game(gameid)
        else:
            await _get_game(gameid)

    return {"status": "success", "data": result_data}

@api.get("/curseforge/categories")
@api_json_middleware
async def curseforge_categories(gameid: int = 432, classid: int = None): # 无法缓存...
    with database:
        data = await cf_api.get_categories(gameid=gameid, classid=classid)
        return {"status": "success", "data": data}

async def _get_mod(modid: int, cache: bool = True):
    with database:
        if not cache:
            data = await cf_api.get_mod(modid=modid)

            # add cachetime
            cache_data = data["data"]
            cache_data["cachetime"] = int(time.time())

            database.exe(insert("mod_info", dict(modid=modid, status=200, data=json.dumps(cache_data), time=int(time.time())), replace=True))
        
        result = database.query(select("mod_info", ["time", "status", "data"]).where("modid", modid).done())
        
        if not result is None:
            time_tag, status, data = result

            if status == 403:
                data = await cf_api.get_mod(modid=modid)
                return {"status": "success", "data": data}
            elif status == 404:
                return {"status": "failed", "error": "ModNotExists", "errorMessage": "Mod not exists"}
            data = json.loads(data)["data"]
        else: # cache not exists
            data = await cf_api.get_mod(modid=modid)
            # add cachetime
            cache_data = data["data"]
            cache_data["cachetime"] = int(time.time())
            database.exe(insert("mod_info", dict(modid=modid, status=200, data=json.dumps(cache_data), time=int(time.time())), replace=True))
    
    return {"status": "success", "data": data}

@api.get("/curseforge/mod/{modid}")
@api_json_middleware
async def get_mod(modid: int, cache: bool = True):
    return await _get_mod(modid, cache=cache)

class ModItemModel(BaseModel):
    modid: list[int]

@api.post('/curseforge/mods')
@api_json_middleware
async def test_post(item: ModItemModel, cache: bool = True):
    modids_data = []
    for modid in set(item.modid):
        data = await _get_mod(modid, cache=cache)
        modids_data.append(data)

    return {"status": "success", "data": modids_data}



if __name__ == "__main__":
    host, port = "127.0.0.1", 8000
    try:
        uvicorn.run(api, host=host, port=port)
    except KeyboardInterrupt:
        print("~~ BYE ~~")

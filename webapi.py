from fastapi import FastAPI
import time
import json
import uvicorn
import aiohttp
import asyncio
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


@api.get("/")
async def root():
    return {"message": "z0z0r4 Mod Info"}

@api.get("/curseforge")
async def curseforge():
    try:
        await cf_api.end_point()
    except (asyncio.TimeoutError, TypeError, StatusCodeException, Exception) as e:
        return {"time": int(time.time()), "status": "Failed", "error": "MCIM Connect to CurseForge API Error"}

@api.get("/curseforge/games")
async def curseforge_games():
    try:
        return {"time": int(time.time()), "status":"Succeed", "cached": False, "data": await cf_api.get_all_games()}
    except (asyncio.TimeoutError, TypeError, StatusCodeException, Exception) as e:
        return {"time": int(time.time()), "status":"Failed", "cached": False}

@api.get("/curseforge/game/{gameid}")
async def curseforge_game(gameid):
    try:
        return {"time": int(time.time()), "status":"Succeed", "cached": False, "data": await cf_api.get_game(gameid=gameid)}
    except (asyncio.TimeoutError, TypeError, StatusCodeException, Exception) as e:
        return {"time": int(time.time()), "status":"Failed", "cached": False}

@api.get("/curseforge/categories")
async def curseforge_categories(gameid: int = 432, classid: int = None):
    try:
        return {"time": int(time.time()), "status":"Succeed", "cached": False, "data": await cf_api.get_categories(gameid=gameid, classid=classid)}
    except (asyncio.TimeoutError, TypeError, StatusCodeException, Exception) as e:
        return {"time": int(time.time()), "status":"Failed", "cached": False}

@api.get("/curseforge/mods/{modid}")
async def get_mod(modid: int, cache: bool = True):
    try:
        if cache == True:
            result = database.exe(select("mod_info",["time","status","data"]).where("modid",modid).done(), cursor=database.cursor())[0]
            time_tag, status, data = result
            if status == 404:
                return {"time": int(time.time()), "status":"Failed", "cached": False}
            else:
                return {"time": time_tag, "status":"Succeed", "cached": True, "data": json.loads(data)["data"]}
        else:
            return {"time": int(time.time()), "status":"Succeed", "cached": False, "data": await cf_api.get_mod(modid=modid)}
    except (asyncio.TimeoutError, TypeError, StatusCodeException, Exception) as e:
        return {"time": int(time.time()), "status":"Failed", "cached": False}

if __name__ == "__main__":
    try:
        uvicorn.run(api, host="127.0.0.1", port=8000)
    except KeyboardInterrupt:
        print("~~ BYE ~~")
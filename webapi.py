
import time
import json
import functools
import asyncio
import aiohttp
import uvicorn
from fastapi import FastAPI, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from pydantic import BaseModel

from apis import *
from config import *
from async_httpclient import *
from mysql import *

MCIMConfig.load()
MysqlConfig.load()

api = FastAPI(docs_url=None, redoc_url=None, title="MCIM")
api.mount("/static", StaticFiles(directory="static"), name="static")

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

# docs
@api.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=api.openapi_url,
        title=api.title + " - Swagger UI",
        oauth2_redirect_url=api.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )


@api.get(api.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


@api.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=api.openapi_url,
        title=api.title + " - ReDoc",
        redoc_js_url="/static/redoc.standalone.js",
    )


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
async def curseforge_categories(gameid: int = 432, classid: int = None):
    with database:
        data = await cf_api.get_categories(gameid=gameid, classid=classid)
        return {"status": "success", "data": data["data"]}


async def _sync_mod(modid: int):
    data = await cf_api.get_mod(modid=modid)
    # add cachetime
    cache_data = data["data"]
    cache_data["cachetime"] = int(time.time())
    database.exe(insert("mod_info", dict(modid=modid, status=200, time=int(
        time.time()), data=json.dumps(cache_data)), replace=True))
    return cache_data


async def _get_mod(modid: int, background_tasks=None):
    with database:
        result = database.query(
            select("mod_info", ["time", "status", "data"]).where("modid", modid).done())
        if result is None or len(result) == 0 or result[1] != 200:
            data = await _sync_mod(modid)
        else:
            data = json.loads(result[2])
            if int(time.time()) - int(data["cachetime"]) > 60 * 60 * 4:
                data = await _sync_mod(modid)
    # to mod_notification
    if not background_tasks is None:
        background_tasks.add_task(mod_notification, modid)
    return {"status": "success", "data": data}

# 在有 mod 请求来后拉取 file_info 和 description，以及对应 file 的 changelog
async def mod_notification(modid: int):
    with database:
        # files
        files_info = await _get_files_info(modid=modid)
        for file_info in files_info:
            fileid = file_info["id"]

            # file_info
            cmd = select("file_info", ["time", "status", "data"]).where(
                "modid", modid).AND("fileid", fileid).done()
            query = database.query(cmd)
            if query is None:
                await _sync_file_info(modid=modid, fileid=fileid, isinsert=True)
            else:
                await _sync_file_info(modid=modid, fileid=fileid)
            database.exe(cmd)

            # changelog
            cmd = select("file_changelog", ["time", "status", "changelog"]).where(
                "modid", modid).AND("fileid", fileid).done()
            query = database.query(cmd)
            if query is None:
                await _sync_mod_file_changelog(modid=modid, fileid=fileid, isinsert=True)
            else:
                await _sync_mod_file_changelog(modid=modid, fileid=fileid)
        pass
        # description
        cmd = select("mod_description", ["time", "status", "description"]).where(
            "modid", modid).done()
        query = database.query(cmd)
        if query is None:
            cachetime = int(time.time())
            description = (await cf_api.get_mod_description(modid=modid))["data"]
            database.exe(insert("mod_description", dict(modid=modid, status=200, time=cachetime, description=description), replace=True))
        else:
            cachetime = int(time.time())
            description = (await cf_api.get_mod_description(modid=modid))["data"]
            database.exe(update("mod_description", dict(status=200, time=cachetime, description=description)).where("modid", modid).done())



@api.get("/curseforge/mod/{modid}")
@api_json_middleware
async def get_mod(modid: int, background_tasks: BackgroundTasks):
    # background_tasks.add_task(mod_notification, modid)
    return await _get_mod(modid, background_tasks=background_tasks)


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
    with database:
        result = database.query(select("mod_description", ["modid", "time", "status"]).where("modid", modid).done())
        if result is None or len(result) == 0:
            cachetime = int(time.time())
            description = (await cf_api.get_mod_description(modid=modid))["data"]
            database.exe(insert("mod_description", dict(modid=modid, status=200, time=cachetime, description=description), replace=True))
        elif result[2] != 200:
            cachetime = int(time.time())
            description = (await cf_api.get_mod_description(modid=modid))["data"]
            database.exe(insert("mod_description", dict(modid=modid, status=200, time=cachetime, description=description), replace=True))
        else:
            description = result[3]
            cachetime = result[1]
    return {"status": "success", "data": description, "cachetime": cachetime}



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
            cachetime = data["cachetime"]
        elif len(query) <= 0 or query[1] != 200:
            data = await _sync_file_info(modid=modid, fileid=fileid)
            cachetime = data["cachetime"]
        else:
            data = json.loads(query[2])
            if int(time.time()) - int(data["cachetime"]) > 60 * 60 * 4:
                data = await _sync_file_info(modid=modid, fileid=fileid)
                cachetime = data["cachetime"]
            else:
                cachetime = query[0]
        return {"status": "success", "data": data, "cachetime": cachetime}

async def _get_files_info(modid: int):
    return (await cf_api.get_files(modid=modid))["data"]

@api.get("/curseforge/mod/{modId}/file/{fileId}")
@api_json_middleware
async def curseforge_mod_file(modId: int, fileId: int):
    return await _get_file_info(modid=modId, fileid=fileId)

@api.get("/curseforge/mod/{modId}/files")
@api_json_middleware
async def curseforge_mod_files(modId: int):
    return {"status": "success", "data": await _get_files_info(modid=modId)}


async def _sync_mod_file_changelog(modid: int, fileid: int, isinsert: bool = False):
    changelog = (await cf_api.get_mod_file_changelog(modid=modid, fileid=fileid))["data"]
    if isinsert:
        cmd = insert("file_changelog", dict(modid=modid, fileid=fileid, status=200, time=int(time.time()), changelog=changelog))
    else:
        cmd = update("file_changelog", dict(status=200, time=int(time.time()), changelog=changelog)).where("modid", modid).AND("fileid", fileid).done()
    database.exe(cmd)
    return changelog


async def _get_mod_file_changelog(modid: int, fileid: int):
    with database:
        cmd = select("file_changelog", ["time", "status", "changelog"]).where(
            "modid", modid).AND("fileid", fileid).done()
        query = database.query(cmd)
        if query is None:
            data = await _sync_mod_file_changelog(modid=modid, fileid=fileid, isinsert=True)
            cachetime = int(time.time())
        elif len(query) <= 0 or query[1] != 200:
            data = await _sync_file_info(modid=modid, fileid=fileid)
            cachetime = int(time.time())
        else:
            data = str(query[2])
            cachetime = int(query[0])
            if int(time.time()) - cachetime > 60 * 60 * 4:
                data = await _sync_file_info(modid=modid, fileid=fileid)
                cachetime = int(time.time())
            else:
                cachetime = query[0]
        return {"status": "success", "data": data, "cachetime": cachetime}


@api.get("/curseforge/mod/{modId}/file/{fileId}/changelog")
@api_json_middleware
async def curseforge_mod_file_changelog(modId: int, fileId: int):
    return await _get_mod_file_changelog(modid=modId, fileid=fileId)

@api.get("/curseforge/mod/{modid}/file/{fileid}/download-url")
@api_json_middleware
async def get_mod_file_download_url(modid: int, fileid: int):
    with database:
        cmd = select("file_info", ["time", "status", "data"]).where(
            "modid", modid).AND("fileid", fileid).done()
        query = database.query(cmd)
        if query is None:
            data = await _sync_file_info(modid=modid, fileid=fileid, isinsert=True)
            cachetime = int(time.time())
        elif len(query) <= 0 or query[1] != 200:
            data = await _sync_file_info(modid=modid, fileid=fileid)
            cachetime = int(time.time())
        else:
            data = json.loads(query[2])
            if int(time.time()) - int(data["cachetime"]) > 60 * 60 * 4:
                data = await _sync_file_info(modid=modid, fileid=fileid)
                cachetime = int(time.time())
            else:
                cachetime = query[0]
        return {"status": "success", "data": data["downloadUrl"], "cachetime": cachetime}

if __name__ == "__main__":
    host, port = "127.0.0.1", 8000
    try:
        uvicorn.run(api, host=host, port=port)
    except KeyboardInterrupt:
        print("~~ BYE ~~")

import functools
import json
import time
from typing import List

import aiohttp
import uvicorn
from fastapi import FastAPI, BackgroundTasks
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from apis import *
from async_httpclient import *
from config import *
from mysql import *

MCIMConfig.load()
MysqlConfig.load()

api = FastAPI(docs_url=None, redoc_url=None, title="MCIM",
              description="这是一个为 Curseforge Mod 信息加速的 API")
api.mount("/static", StaticFiles(directory="static"), name="static")

proxies = MCIMConfig.proxies
timeout = MCIMConfig.async_timeout
database = DataBase(**MysqlConfig.to_dict())

# for cf
cf_key = MCIMConfig.curseforge_api_key
cf_api_url = MCIMConfig.curseforge_api
cf_headers = {
    "User-Agent": "github_org/mcim/1.0.0 (mcim.z0z0r4.top)",
    'Accept': 'application/json',
    'x-api-key': cf_key
}
cf_cli = AsyncHTTPClient(
    headers=cf_headers, timeout=aiohttp.ClientTimeout(total=timeout))
cf_api = CurseForgeApi(cf_api_url, cf_key, proxies=proxies, acli=cf_cli)

# for mr
mr_api_url = MCIMConfig.modrinth_api
mr_headers = {
    "User-Agent": "github_org/mcim/1.0.0 (mcim.z0z0r4.top)",
    'Accept': 'application/json'
}
mr_cli = AsyncHTTPClient(headers=mr_headers, timeout=aiohttp.ClientTimeout(total=timeout))
mr_api = ModrinthApi(baseurl=mr_api_url, proxies=proxies, acli=mr_cli, ua="github_org/mcim/1.0.0 (mcim.z0z0r4.top)")


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


def str_to_list(text: str):
    # Why not `json.loads(text)` ?
    li = []
    for t in text[1:-1].split(","):
        li.append(t[1:-1])
    return li


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


@api.get(
    "/",
    responses={200: {"description": "MCIM API status", "content": {
        "application/json": {"example":
                                 {"status": "success", "message": "z0z0r4 Mod Info"}
                             }}}
               },
    description="MCIM API")
@api_json_middleware
async def root():
    return {"status": "success", "message": "z0z0r4 Mod Info"}


@api.get("/curseforge",
         responses={200: {"description": "CFCore", "content": {
             "text/plain": {"example": "CurseForge Core (397e291)"}}}
                    },
         description="Curseforge API", tags=["Curseforge"])
@api_json_middleware
async def curseforge():
    return await cf_api.end_point()

async def _curseforge_sync_game(gameid: int):
    data = await cf_api.get_game(gameid=gameid)
    cache_data = data["data"]
    cache_data["cachetime"] = int(time.time())
    database.exe(insert("curseforge_game_info",
        dict(gameid=gameid, status=200, time=int(time.time()), data=json.dumps(cache_data)), replace=True))
    return cache_data


async def _curseforge_get_game(gameid: int):
    with database:
        result = database.queryone(
            select("curseforge_game_info", ["time", "status", "data"]).where("gameid", gameid).done())
        if result is None or len(result) == 0 or result[1] != 200:
            data = await _curseforge_sync_game(gameid)
        else:
            data = json.loads(result[2])
            if int(time.time()) - int(data["cachetime"]) > 60 * 60 * 4:
                data = await _curseforge_sync_game(gameid)
    return {"status": "success", "data": data}


curseforge_game_example = {"id": 0, "name": "string", "slug": "string", "dateModified": "2019-08-24T14:15:22Z",
                           "assets": {"iconUrl": "string", "tileUrl": "string", "coverUrl": "string"}, "status": 1,
                           "apiStatus": 1}


@api.get("/curseforge/game/{gameid}",
         responses={200: {"description": "Curseforge Game info", "content": {
             "application/json": {"example":
                                      {"status": "success", "data": curseforge_game_example}
                                  }}}
                    }, description="Curseforge Game 信息", tags=["Curseforge"])
@api_json_middleware
async def curseforge_game(gameid: int):
    return await _curseforge_get_game(gameid=gameid)


@api.get("/curseforge/games",
         responses={200: {"description": "Curseforge Games info", "content": {
             "application/json": {"example":
                                      {"status": "success", "data": [curseforge_game_example]}
                                  }}}
                    }, description="Curseforge 的全部 Game 信息", tags=["Curseforge"])
@api_json_middleware
async def curseforge_games():
    all_data = []
    sql_games_result = database.query(
        select("curseforge_game_info", ["gameid", "time", "status", "data"]))
    for result in sql_games_result:
        if result is None or result == () or result[2] != 200:
            break
        gameid, time_tag, status, data = result
        data = json.loads(data)
        if int(time.time()) - int(data["cachetime"]) > 60 * 60 * 4:
            break
        all_data.append(data)
    else:
        return {"status": "success", "data": all_data}
    all_data = []
    sync_games_result = await cf_api.get_all_games()
    with database:
        for result in sync_games_result["data"]:
            gameid = result["id"]
            tmnow = int(time.time())
            result["cachetime"] = tmnow
            database.exe(insert("curseforge_game_info",
                dict(gameid=gameid, status=200, time=tmnow, data=json.dumps(result)), replace=True))
            all_data.append(result)
    return {"status": "success", "data": all_data}


curseforge_category_example = {"id": 0, "gameId": 0, "name": "string", "slug": "string", "url": "string",
                               "iconUrl": "string", "dateModified": "2019-08-24T14:15:22Z", "isClass": True,
                               "classId": 0, "parentCategoryId": 0, "displayIndex": 0}


@api.get("/curseforge/categories",
    responses={
        200: {
            "description": "Curseforge category info",
            "content": {
                "application/json": {
                    "example": {"status": "success", "data": [curseforge_category_example]}
                }
            }
        }
    }, description="Curseforge 的 Category 信息", tags=["Curseforge"])
@api_json_middleware
async def curseforge_categories(gameid: int = 432, classid: int = None):
    with database:
        data = await cf_api.get_categories(gameid=gameid, classid=classid)
        return {"status": "success", "data": data["data"]}


async def _curseforge_sync_mod(modid: int):
    data = await cf_api.get_mod(modid=modid)
    # add cachetime
    tmnow = int(time.time())
    cache_data = data["data"]
    cache_data["cachetime"] = tmnow
    database.exe(insert("curseforge_mod_info",
        dict(modid=modid, status=200, time=tmnow, data=json.dumps(cache_data)), replace=True))
    return cache_data


async def _curseforge_get_mod(modid: int, background_tasks=None):
    with database:
        result = database.queryone(
            select("curseforge_mod_info", ["time", "status", "data"]).where("modid", modid).done())
        if result is None or len(result) == 0 or result[1] != 200:
            data = await _curseforge_sync_mod(modid)
        else:
            data = json.loads(result[2])
            if int(time.time()) - int(data["cachetime"]) > 60 * 60 * 4:
                data = await _curseforge_sync_mod(modid)
    # to mod_notification
    if not background_tasks is None:
        background_tasks.add_task(mod_notification, modid)
    return {"status": "success", "data": data}


# 在有 mod 请求来后拉取 file_info 和 description，以及对应 file 的 changelog


async def mod_notification(modid: int):
    with database:
        # files
        files_info = await _curseforge_get_files_info(modid=modid)
        for file_info in files_info:
            fileid = file_info["id"]
            # file_info
            await _curseforge_sync_file_info(modid=modid, fileid=fileid)
            # changelog
            await _curseforge_sync_mod_file_changelog(modid=modid, fileid=fileid)
        # description
        cmd = select("curseforge_mod_description", ["time", "status", "description"]).where(
            "modid", modid).done()
        cachetime = int(time.time())
        description = (await cf_api.get_mod_description(modid=modid))["data"]
        database.exe(insert("mod_description",
            dict(modid=modid, status=200, time=cachetime, description=description), replace=True))


curseforge_mod_example = {"id": 0, "gameId": 0, "name": "string", "slug": "string",
                          "links": {"websiteUrl": "string", "wikiUrl": "string", "issuesUrl": "string",
                                    "sourceUrl": "string"}, "summary": "string", "status": 1, "downloadCount": 0,
                          "isFeatured": True, "primaryCategoryId": 0, "categories": [
        {"id": 0, "gameId": 0, "name": "string", "slug": "string", "url": "string", "iconUrl": "string",
         "dateModified": "2019-08-24T14:15:22Z", "isClass": True, "classId": 0, "parentCategoryId": 0,
         "displayIndex": 0}], "classId": 0, "authors": [{"id": 0, "name": "string", "url": "string"}],
                          "logo": {"id": 0, "modId": 0, "title": "string", "description": "string",
                                   "thumbnailUrl": "string", "url": "string"}, "screenshots": [
        {"id": 0, "modId": 0, "title": "string", "description": "string", "thumbnailUrl": "string", "url": "string"}],
                          "mainFileId": 0, "latestFiles": [
        {"id": 0, "gameId": 0, "modId": 0, "isAvailable": True, "displayName": "string", "fileName": "string",
         "releaseType": 1, "fileStatus": 1, "hashes": [{"value": "string", "algo": 1}],
         "fileDate": "2019-08-24T14:15:22Z", "fileLength": 0, "downloadCount": 0, "downloadUrl": "string",
         "gameVersions": ["string"], "sortableGameVersions": [
            {"gameVersionName": "string", "gameVersionPadded": "string", "gameVersion": "string",
             "gameVersionReleaseDate": "2019-08-24T14:15:22Z", "gameVersionTypeId": 0}],
         "dependencies": [{"modId": 0, "relationType": 1}], "exposeAsAlternative": True, "parentProjectFileId": 0,
         "alternateFileId": 0, "isServerPack": True, "serverPackFileId": 0, "fileFingerprint": 0,
         "modules": [{"name": "string", "fingerprint": 0}]}], "latestFilesIndexes": [
        {"gameVersion": "string", "fileId": 0, "filename": "string", "releaseType": 1, "gameVersionTypeId": 0,
         "modLoader": 0}], "dateCreated": "2019-08-24T14:15:22Z", "dateModified": "2019-08-24T14:15:22Z",
                          "dateReleased": "2019-08-24T14:15:22Z", "allowModDistribution": True, "gamePopularityRank": 0,
                          "isAvailable": True, "thumbsUpCount": 0}


@api.get("/curseforge/mod/{modid}",
    responses={
        200: {
            "description": "Curseforge mod info",
            "content": {
                "application/json": {
                    "example": {"status": "success", "data": curseforge_mod_example}
                }
            }
        }
    }, description="Curseforge Mod 信息", tags=["Curseforge"])
@api_json_middleware
async def get_mod(modid: int, background_tasks: BackgroundTasks):
    return await _curseforge_get_mod(modid, background_tasks=background_tasks)


class ModItemModel(BaseModel):
    modid: list[int]


@api.post('/curseforge/mods',
    responses={
        200: {
            "description": "Curseforge mods info",
            "content": {
                "application/json": {
                    "example": {"status": "success", "data": [curseforge_mod_example]}
                }
            }
        }
    }, description="批量获取 Curseforge Mods 信息", tags=["Curseforge"])
@api_json_middleware
async def get_mods(item: ModItemModel):
    modids_data = []
    for modid in set(item.modid):
        data = await _curseforge_get_mod(modid)
        modids_data.append(data)

    return {"status": "success", "data": modids_data}


@api.get("/curseforge/mod/{modid}/description",
        responses={
            200: {
                "description": "Curseforge mod description",
                "content": {
                    "application/json": {
                        "example": {"status": "success", "description": "string", "cachetime": "integer"}
                    }
                }
            }
        }, description="Curseforge Mod 的描述信息", tags=["Curseforge"])
@api_json_middleware
async def get_mod_description(modid: int):
    with database:
        result = database.queryone(select(
            "mod_description", ["modid", "time", "status"]).where("modid", modid).done())
        if result is None or len(result) == 0:
            cachetime = int(time.time())
            description = (await cf_api.get_mod_description(modid=modid))["data"]
            database.exe(insert("mod_description", dict(
                modid=modid, status=200, time=cachetime, description=description), replace=True))
        elif result[2] != 200:
            cachetime = int(time.time())
            description = (await cf_api.get_mod_description(modid=modid))["data"]
            database.exe(insert("mod_description", dict(
                modid=modid, status=200, time=cachetime, description=description), replace=True))
        else:
            description = result[3]
            cachetime = result[1]
    return {"status": "success", "data": description, "cachetime": cachetime}


curseforge_search_example = {
    'data': [
        {'id': 0, 'gameId': 0, 'name': 'string', 'slug': 'string', 'links': {'websiteUrl': 'string', 'wikiUrl': 'string', 'issuesUrl': 'string', 'sourceUrl': 'string'}, 'summary': 'string', 'status': 1, 'downloadCount': 0, 'isFeatured': True, 'primaryCategoryId': 0, 'categories': [{'id': 0, 'gameId': 0, 'name': 'string', 'slug': 'string', 'url': 'string', 'iconUrl': 'string', 'dateModified': '2019-08-24T14:15:22Z', 'isClass': True, 'classId': 0, 'parentCategoryId': 0, 'displayIndex': 0}], 'classId': 0, 'authors': [{'id': 0, 'name': 'string', 'url': 'string'}], 'logo': {'id': 0, 'modId': 0, 'title': 'string', 'description': 'string', 'thumbnailUrl': 'string', 'url': 'string'}, 'screenshots': [{'id': 0, 'modId': 0, 'title': 'string', 'description': 'string', 'thumbnailUrl': 'string', 'url': 'string'}], 'mainFileId': 0, 'latestFiles': [{'id': 0, 'gameId': 0, 'modId': 0, 'isAvailable': True, 'displayName': 'string', 'fileName': 'string', 'releaseType': 1, 'fileStatus': 1, 'hashes': [{'value': 'string', 'algo': 1}], 'fileDate': '2019-08-24T14:15:22Z', 'fileLength': 0, 'downloadCount': 0, 'downloadUrl': 'string', 'gameVersions': ['string'], 'sortableGameVersions': [{'gameVersionName': 'string', 'gameVersionPadded': 'string', 'gameVersion': 'string', 'gameVersionReleaseDate': '2019-08-24T14:15:22Z', 'gameVersionTypeId': 0}], 'dependencies': [{'modId': 0, 'relationType': 1}], 'exposeAsAlternative': True, 'parentProjectFileId': 0, 'alternateFileId': 0, 'isServerPack': True, 'serverPackFileId': 0, 'fileFingerprint': 0, 'modules': [{'name': 'string', 'fingerprint': 0}]}], 'latestFilesIndexes': [{'gameVersion': 'string', 'fileId': 0, 'filename': 'string', 'releaseType': 1, 'gameVersionTypeId': 0, 'modLoader': 0}], 'dateCreated': '2019-08-24T14:15:22Z', 'dateModified': '2019-08-24T14:15:22Z', 'dateReleased': '2019-08-24T14:15:22Z', 'allowModDistribution': True, 'gamePopularityRank': 0, 'isAvailable': True, 'thumbsUpCount': 0}
    ],
    'pagination': {'index': 0, 'pageSize': 0, 'resultCount': 0, 'totalCount': 0}
}


@api.get("/curseforge/search",
    responses={
        200: {
            "description": "Curseforge search",
            "content": {
                "application/json": {
                    "example": {"status": "success", "data": curseforge_search_example}
                }
            }
        }
    }, description="Curseforge 搜索", tags=["Curseforge"])
@api_json_middleware
async def curseforge_search(gameId: int, classId: int = None, categoryId: int = None, gameVersion: str = None,
                            searchFilter: str = None, sortField=None, sortOrder: str = None, modLoaderType: int = None,
                            gameVersionTypeId: int = None, slug: str = None, index: int = None, pageSize: int = 50):
    # TODO 在数据库中搜索
    data = await cf_api.search(
        gameid=gameId, classid=classId, categoryid=categoryId, gameversion=gameVersion,
        searchfilter=searchFilter, sortfield=sortField, sortorder=sortOrder,
        modloadertype=modLoaderType, gameversiontypeid=gameVersionTypeId, slug=slug, index=index,
        pagesize=pageSize)
    return {"status": "success", "data": data["data"]}

async def _curseforge_sync_file_info(modid: int, fileid: int):
    cache_data = (await cf_api.get_file(modid=modid, fileid=fileid))["data"]
    cache_data["cachetime"] = int(time.time())
    database.exe(cmd := insert("curseforge_file_info",
        dict(modid=modid, fileid=fileid, status=200, time=int(time.time()), data=json.dumps(cache_data)),
        replace=True))
    return cache_data

async def _curseforge_get_file_info(modid: int, fileid: int):
    with database:
        query = database.queryone(cmd := select("curseforge_file_info", ["time", "status", "data"]).
            where("modid", modid).AND("fileid", fileid).done())
        if query is None or query[1] != 200:
            data = await _curseforge_sync_file_info(modid=modid, fileid=fileid)
            cachetime = data["cachetime"]
        else:
            data = json.loads(query[2])
            if int(time.time()) - int(data["cachetime"]) > 60 * 60 * 4:
                data = await _curseforge_sync_file_info(modid=modid, fileid=fileid)
                cachetime = data["cachetime"]
            else:
                cachetime = query[0]
        return {"status": "success", "data": data, "cachetime": cachetime}


async def _curseforge_get_files_info(modid: int):
    return (await cf_api.get_files(modid=modid))["data"]


curseforge_file_info_example = {
    "id": 0, "gameId": 0, "modId": 0, "isAvailable": True, "displayName": "string",
    "fileName": "string", "releaseType": 1, "fileStatus": 1,
    "hashes": [{"value": "string", "algo": 1}], "fileDate": "2019-08-24T14:15:22Z",
    "fileLength": 0, "downloadCount": 0, "downloadUrl": "string",
    "gameVersions": ["string"], "sortableGameVersions": [{
        "gameVersionName": "string", "gameVersionPadded": "string", "gameVersion": "string",
        "gameVersionReleaseDate": "2019-08-24T14:15:22Z", "gameVersionTypeId": 0
    }],
    "dependencies": [{"modId": 0, "relationType": 1}], "exposeAsAlternative": True,
    "parentProjectFileId": 0, "alternateFileId": 0, "isServerPack": True,
    "serverPackFileId": 0, "fileFingerprint": 0,
    "modules": [{"name": "string", "fingerprint": 0}]
}


@api.get("/curseforge/mod/{modId}/file/{fileId}",
    responses={
        200: {
            "description": "Curseforge mod file info", "content": {
                "application/json": {
                    "example": {"status": "success", "data": curseforge_file_info_example}
                }
            }
        }
    }, description="Curseforge Mod 的文件信息", tags=["Curseforge"])
@api_json_middleware
async def curseforge_mod_file(modId: int, fileId: int):
    return await _curseforge_get_file_info(modid=modId, fileid=fileId)


@api.get("/curseforge/mod/{modId}/files",
    responses={
        200: {
            "description": "Curseforge mod files info", "content": {
                "application/json": {
                    "example": {"status": "success", "data": [curseforge_file_info_example]}
                }
            }
        }
    }, description="Curseforge Mod 的全部文件信息", tags=["Curseforge"])
@api_json_middleware
async def curseforge_mod_files(modId: int):
    return {"status": "success", "data": await _curseforge_get_files_info(modid=modId)}  # TODO 在数据库中搜索


async def _curseforge_sync_mod_file_changelog(modid: int, fileid: int):
    changelog = (await cf_api.get_mod_file_changelog(modid=modid, fileid=fileid))["data"]
    database.exe(cmd := insert("curseforge_file_changelog",
        dict(modid=modid, fileid=fileid, status=200, time=int(time.time()), changelog=changelog), replace=True))
    return changelog


async def _curseforge_get_mod_file_changelog(modid: int, fileid: int):
    with database:
        cmd = select("curseforge_file_changelog", ["time", "status", "changelog"]).where(
            "modid", modid).AND("fileid", fileid).done()
        query = database.queryone(cmd)
        if query is None or query[1] != 200:
            data = await _curseforge_sync_mod_file_changelog(modid=modid, fileid=fileid)
            cachetime = int(time.time())
        else:
            data = str(query[2])
            cachetime = int(query[0])
            if int(time.time()) - cachetime > 60 * 60 * 4:
                data = await _curseforge_sync_file_info(modid=modid, fileid=fileid)
                cachetime = int(time.time())
            else:
                cachetime = query[0]
        return {"status": "success", "changelog": data, "cachetime": cachetime}


@api.get("/curseforge/mod/{modId}/file/{fileId}/changelog",
         responses={200: {"description": "Curseforge mod file changelog", "content": {
             "application/json": {"example":
                                      {"status": "success", "changelog": "string",
                                       "cachetime": "integer"}
                                  }}}
                    }, description="Curseforge Mod 的文件 Changelog", tags=["Curseforge"])
@api_json_middleware
async def curseforge_mod_file_changelog(modId: int, fileId: int):
    return await _curseforge_get_mod_file_changelog(modid=modId, fileid=fileId)


@api.get("/curseforge/mod/{modid}/file/{fileid}/download-url",
         responses={200: {"description": "Curseforge mod file download url", "content": {
             "application/json": {"example":
                                      {"status": "success", "url": "string",
                                       "cachetime": "integer"}
                                  }}}
                    }, description="Curseforge Mod 的文件下载地址", tags=["Curseforge"])
@api_json_middleware
async def curseforge_get_mod_file_download_url(modid: int, fileid: int):
    with database:
        cmd = select("curseforge_file_info", ["time", "status", "data"]).where(
            "modid", modid).AND("fileid", fileid).done()
        query = database.queryone(cmd)
        if query is None:
            data = await _curseforge_sync_file_info(modid=modid, fileid=fileid)
            cachetime = int(time.time())
        elif len(query) <= 0 or query[1] != 200:
            data = await _curseforge_sync_file_info(modid=modid, fileid=fileid)
            cachetime = int(time.time())
        else:
            data = json.loads(query[2])
            if int(time.time()) - int(data["cachetime"]) > 60 * 60 * 4:
                data = await _curseforge_sync_file_info(modid=modid, fileid=fileid)
                cachetime = int(time.time())
            else:
                cachetime = query[0]
        return {"status": "success", "url": data["downloadUrl"], "cachetime": cachetime}


@api.get("/modrinth",
         responses={200: {"description": "Modrinth API", "content": {
             "application/json": {"example":
                 {
                     "about": "Welcome traveler!",
                     "documentation": "https://docs.modrinth.com",
                     "name": "modrinth-labrinth",
                     "version": "2.5.0"
                 }
             }}}
                    }, description="Modrinth API", tags=["Modrinth"])
@api_json_middleware
async def modrinth():
    return await mr_api.end_point()

modrinth_mod_example = {"slug": "my_project", "title": "My Project", "description": "A short description",
                        "categories": ["technology", "adventure", "fabric"], "client_side": "required",
                        "server_side": "optional", "body": "A long body describing my project in detail",
                        "issues_url": "https://github.com/my_user/my_project/issues",
                        "source_url": "https://github.com/my_user/my_project",
                        "wiki_url": "https://github.com/my_user/my_project/wiki",
                        "discord_url": "https://discord.gg/AaBbCcDd", "donation_urls": [
        {"id": "patreon", "platform": "Patreon", "url": "https://www.patreon.com/my_user"}], "project_type": "mod",
                        "downloads": 0,
                        "icon_url": "https://cdn.modrinth.com/data/AABBCCDD/b46513nd83hb4792a9a0e1fn28fgi6090c1842639.png",
                        "id": "AABBCCDD", "team": "MMNNOOPP", "body_url": None, "moderator_message": None,
                        "published": "2019-08-24T14:15:22Z", "updated": "2019-08-24T14:15:22Z", "followers": 0,
                        "status": "approved",
                        "license": {"id": "lgpl-3", "name": "GNU Lesser General Public License v3",
                                    "url": "https://cdn.modrinth.com/licenses/lgpl-3.txt"},
                        "versions": ["IIJJKKLL", "QQRRSSTT"], "gallery": [
        {"url": "https://cdn.modrinth.com/data/AABBCCDD/images/009b7d8d6e8bf04968a29421117c59b3efe2351a.png",
         "featured": True, "title": "My awesome screenshot!",
         "description": "This awesome screenshot shows all of the blocks in my mod!",
         "created": "2019-08-24T14:15:22Z"}]}


async def _modrinth_background_task_sync_version(data: dict):
    with database:
        for version_id in data["versions"]:
            await _modrinth_sync_version(version_id=version_id)
        print(f'{data["id"]} sync version done')


async def _modrinth_sync_project(idslug: str):  # 优先采用 slug
    cache_data = await mr_api.get_project(slug=idslug)
    slug = cache_data["slug"]
    project_id = cache_data["id"]
    cache_data["cachetime"] = int(time.time())
    database.exe(
        insert("modrinth_project_info", dict(project_id=project_id, slug=slug, status=200, time=int(time.time()),
                                             data=json.dumps(cache_data)), replace=True))
    return cache_data


async def _modrinth_get_project(idslug: str, background_tasks=None):
    with database:
        id_cmd = select("modrinth_project_info", ["time", "status", "data"]).where("project_id", idslug).done()
        id_query = database.queryone(id_cmd)
        if id_query is None:
            slug_cmd = select("modrinth_project_info", ["time", "status", "data"]).where("slug", idslug).done()
            slug_query = database.queryone(slug_cmd)
            if slug_query is None:
                data = await _modrinth_sync_project(idslug=idslug)
            else:
                cachetime, status, data = slug_query
                data = json.loads(data)
                if int(time.time()) - data["cachetime"] > 60 * 60 * 4:
                    data = await _modrinth_sync_project(idslug=idslug)
        else:
            cachetime, status, data = id_query
            data = json.loads(data)
            if int(time.time()) - data["cachetime"] > 60 * 60 * 4:
                data = await _modrinth_sync_project(idslug=idslug)
        # TODO 添加后台任务：version_info
        if background_tasks is not None:
            background_tasks.add_task(
                _modrinth_background_task_sync_version, data)
        return {"status": "success", "data": data}


@api.get("/modrinth/project/{idslug}",
    responses={
        200: {
            "description": "Modrinth project info",
            "content": {
                "application/json": {
                    "example": modrinth_mod_example
                }
            }
        }
    }, description="Modrinth project info", tags=["Modrinth"])
@api_json_middleware
async def get_modrinth_project(idslug: str, background_tasks: BackgroundTasks):
    return await _modrinth_get_project(idslug, background_tasks=background_tasks)


@api.get("/modrinth/projects",
    responses={
        200: {
            "description": "Modrinth projects info",
            "content": {
                "application/json": {
                    "example": [modrinth_mod_example]
                }
            }
        }
    }, description="Modrinth project list", tags=["Modrinth"])
@api_json_middleware
async def get_modrinth_projects(ids: str, background_tasks: BackgroundTasks):
    ids = str_to_list(ids)
    projects_data = []
    for project_id in ids:
        project_data = (await _modrinth_get_project(idslug=project_id, background_tasks=background_tasks))["data"]
        projects_data.append(project_data)
    return {"status": "success", "data": projects_data}


modrinth_search_example = {
    "name": "Version 1.0.0",
    "version_number": "1.0.0",
    "changelog": "List of changes in this version: ...",
    "dependencies": [
        {
            "version_id": "IIJJKKLL",
            "project_id": "QQRRSSTT",
            "dependency_type": "required"
        }
    ],
    "game_versions": [
        "1.16.5",
        "1.17.1"
    ],
    "version_type": "release",
    "loaders": [
        "fabric",
        "forge"
    ],
    "featured": True,
    "id": "IIJJKKLL",
    "project_id": "AABBCCDD",
    "author_id": "EEFFGGHH",
    "date_published": "2019-08-24T14:15:22Z",
    "downloads": 0,
    "changelog_url": None,
    "files": [
        {
            "hashes": {
                "sha512": "93ecf5fe02914fb53d94aa3d28c1fb562e23985f8e4d48b9038422798618761fe208a31ca9b723667a4e05de0d91a3f86bcd8d018f6a686c39550e21b198d96f",
                "sha1": "c84dd4b3580c02b79958a0590afd5783d80ef504"
            },
            "url": "https://cdn.modrinth.com/data/AABBCCDD/versions/1.0.0/my_file.jar",
            "filename": "my_file.jar",
            "primary": False,
            "size": 1097270
        }
    ]
}


@api.get("/modrinth/search",
         responses={200: {"description": "Modrinth search", "content": {
             "application/json": {"example":
                                      [modrinth_search_example]
                                  }}}
                    }, description="Modrinth search", tags=["Modrinth"])
@api_json_middleware
async def modrinth_search(query: str = None, facets: str = None, limit: int = 20, offset: int = 0,
                          index: str = "relevance"):
    search_result = await mr_api.search(query=query, facets=facets, limit=limit, offset=offset, index=index)
    return {"status": "success", "data": search_result}  # TODO 在数据库中搜索


modrinth_version_example = {
    "name": "Version 1.0.0",
    "version_number": "1.0.0",
    "changelog": "List of changes in this version: ...",
    "dependencies": [
        {
            "version_id": "IIJJKKLL",
            "project_id": "QQRRSSTT",
            "dependency_type": "required"
        }
    ],
    "game_versions": [
        "1.16.5",
        "1.17.1"
    ],
    "version_type": "release",
    "loaders": [
        "fabric",
        "forge"
    ],
    "featured": True,
    "id": "IIJJKKLL",
    "project_id": "AABBCCDD",
    "author_id": "EEFFGGHH",
    "date_published": "2019-08-24T14:15:22Z",
    "downloads": 0,
    "changelog_url": None,
    "files": [
        {
            "hashes": {
                "sha512": "93ecf5fe02914fb53d94aa3d28c1fb562e23985f8e4d48b9038422798618761fe208a31ca9b723667a4e05de0d91a3f86bcd8d018f6a686c39550e21b198d96f",
                "sha1": "c84dd4b3580c02b79958a0590afd5783d80ef504"
            },
            "url": "https://cdn.modrinth.com/data/AABBCCDD/versions/1.0.0/my_file.jar",
            "filename": "my_file.jar",
            "primary": False,
            "size": 1097270
        }
    ]
}


async def _modrinth_sync_version(version_id: str):
    cache_data = await mr_api.get_project_version(version_id=version_id)
    project_id = cache_data["project_id"]
    cache_data["cachetime"] = int(time.time())
    database.exe(insert("modrinth_version_info",
                        dict(project_id=project_id, version_id=version_id, status=200, time=cache_data["cachetime"],
                             data=json.dumps(cache_data)), replace=True))
    return cache_data


async def _modrinth_get_version(version_id: str):
    with database:
        cmd = select("modrinth_version_info", ["time", "status", "data"]).where("version_id", version_id).done()
        query = database.queryone(cmd)
        if query is None:
            data = await _modrinth_sync_version(version_id=version_id)
            pass
        else:
            cachetime, status, data = query
            if status == 200:
                data = json.loads(data)
                if int(time.time()) - data["cachetime"] > 60 * 60 * 4:
                    data = await _modrinth_sync_version(version_id=version_id)
            else:
                data = await _modrinth_sync_version(version_id=version_id)
        return {"status": "success", "data": data}


@api.get("/modrinth/version/{version_id}",
         responses={200: {"description": "Modrinth version info", "content": {
             "application/json": {"example":
                                      modrinth_version_example
                                  }}}
                    }, description="Modrinth version info", tags=["Modrinth"])
@api_json_middleware
async def get_modrinth_version(version_id: str):
    return await _modrinth_get_version(version_id)


async def _modrinth_get_project_versions(project_id: str, game_versions: list = None, loaders: list = None, featured: bool = None):
    version_info_lsit = await mr_api.get_project_versions(project_id=project_id, game_versions=game_versions, loaders=loaders, featured=featured)
    for version_info in version_info_lsit:
        version_info["cachetime"] = int(time.time())
        database.exe(insert("modrinth_version_info",
                            dict(project_id=project_id, version_id=version_info["id"], status=200,
                                 time=version_info["cachetime"],
                                 data=json.dumps(version_info)), replace=True))
    # TODO Background_task
    return {"status": "success", "data": version_info_lsit}


@api.get("/modrinth/project/{idslug}/versions",
         responses={200: {"description": "Modrinth project versions info", "content": {
             "application/json": {"example":
                                      [modrinth_version_example]
                                  }}}
                    }, description="Modrint project versions info", tags=["Modrinth"])
@api_json_middleware
async def get_modrinth_project_versions(idslug: str, loaders: str = None, game_versions: str = None, featured: bool = None):
    with database:
        if loaders:
            loaders = str_to_list(loaders)
        if game_versions:
            game_versions = str_to_list(game_versions)
        project_data = (await _modrinth_get_project(idslug))["data"]
        project_id = project_data["id"]
        query = database.query(
            select("modrinth_version_info", ["time", "status", "data"]).where("project_id", project_id).done())
        if query is None:
            version_info_list = await _modrinth_get_project_versions(project_id=project_id, loaders=loaders, game_versions=game_versions, featured=featured)
        else:
            version_info_list = []
            for version_info in query:
                cachetime, status, data = version_info
                if status == 200:
                    data = json.loads(data)
                    if data["cachetime"] - int(time.time()) < 60 * 60 * 4:
                        if featured:
                            if data["featured"] != featured:
                                continue
                        if loaders:
                            if len(list(set(loaders) & set(data["loaders"]))) == 0:
                                continue
                        if game_versions:
                            if len(list(set(game_versions) & set(data["game_versions"]))) == 0:
                                continue
                    else:
                        data = await _modrinth_sync_version(version_id=data["id"])
                else:
                    data = await _modrinth_sync_version(version_id=data["id"])
                version_info_list.append(data)
    return {"status": "success", "data": version_info_list}

async def _modrinth_sync_tag_category():
    data = await mr_api.get_categories()
    
    database.exe(insert("modrinth_tag_info",
                        dict(slug="category", status=200,
                             time=int(time.time()),
                             data=json.dumps(data)), replace=True))
    return data

async def _modrinth_sync_tag_loader():
    data = await mr_api.get_loaders()
    
    database.exe(insert("modrinth_tag_info",
                        dict(slug="loader", status=200,
                             time=int(time.time()),
                             data=json.dumps(data)), replace=True))
    return data

async def _modrinth_sync_tag_game_version():
    data = await mr_api.get_game_versions()
    
    database.exe(insert("modrinth_tag_info",
                        dict(slug="game_version", status=200,
                             time=int(time.time()),
                             data=json.dumps(data)), replace=True))
    return data

async def _modrinth_sync_tag_license():
    data = await mr_api.get_licenses()
    
    database.exe(insert("modrinth_tag_info",
                        dict(slug="license", status=200,
                             time=int(time.time()),
                             data=json.dumps(data)), replace=True))
    return data

@api.get("/modrinth/tag/category")
async def get_modrinth_tag_category():
    with database:
        cmd = select("modrinth_tag_info", ["time", "status", "data"]).where(
            "slug", "category").done()
        query = database.queryone(cmd)
        if query is None:
            data = await _modrinth_sync_tag_category()
            cachetime = int(time.time())
        else:
            cachetime, status, data = query
            if cachetime - int(time.time()) < 60 * 60 * 4 and status == 200:
                data = json.loads(data)
            else:
                data = await _modrinth_sync_tag_category()
    return {"status": "success", "cachetime": cachetime, "data": data}


@api.get("/modrinth/tag/loader")
async def get_modrinth_tag_loader():
    with database:
        cmd = select("modrinth_tag_info", ["time", "status", "data"]).where(
            "slug", "loader").done()
        query = database.queryone(cmd)
        if query is None:
            data = await _modrinth_sync_tag_loader()
            cachetime = int(time.time())
        else:
            cachetime, status, data = query
            if cachetime - int(time.time()) < 60 * 60 * 4 and status == 200:
                data = json.loads(data)
            else:
                data = await _modrinth_sync_tag_loader()
    return {"status": "success", "cachetime": cachetime, "data": data}


@api.get("/modrinth/tag/game_version")
async def get_modrinth_tag_game_version():
    with database:
        cmd = select("modrinth_tag_info", ["time", "status", "data"]).where(
            "slug", "game_version").done()
        query = database.queryone(cmd)
        if query is None:
            data = await _modrinth_sync_tag_game_version()
            cachetime = int(time.time())
        else:
            cachetime, status, data = query
            if cachetime - int(time.time()) < 60 * 60 * 4 and status == 200:
                data = json.loads(data)
            else:
                data = await _modrinth_sync_tag_game_version()
    return {"status": "success", "cachetime": cachetime, "data": data}


@api.get("/modrinth/tag/license")
async def get_modrinth_tag_license():
    with database:
        cmd = select("modrinth_tag_info", ["time", "status", "data"]).where(
            "slug", "license").done()
        query = database.queryone(cmd)
        if query is None:
            data = await _modrinth_sync_tag_license()
            cachetime = int(time.time())
        else:
            cachetime, status, data = query
            if cachetime - int(time.time()) < 60 * 60 * 4 and status == 200:
                data = json.loads(data)
            else:
                data = await _modrinth_sync_tag_license()
    return {"status": "success", "cachetime": cachetime, "data": data}

if __name__ == "__main__":
    host, port = "0.0.0.0", 8000
    try:
        uvicorn.run(api, host=host, port=port)
    except KeyboardInterrupt:
        print("~~ BYE ~~")

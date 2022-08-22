from typing import List
from sqlalchemy import *
from sqlalchemy.orm import Session
from sqlalchemy.dialects.mysql import insert
import functools
import json
import os
import time
import logging
import datetime
import traceback
import aiohttp
import uvicorn
from fastapi import FastAPI, BackgroundTasks, Body, status
from fastapi.responses import JSONResponse, Response
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# local package
from apis import *
from async_httpclient import *
from config import *
# inti config
MCIMConfig.load()
MysqlConfig.load()
proxies = MCIMConfig.proxies
timeout = MCIMConfig.async_timeout
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
mr_cli = AsyncHTTPClient(
    headers=mr_headers, timeout=aiohttp.ClientTimeout(total=timeout))
mr_api = ModrinthApi(baseurl=mr_api_url, proxies=proxies,
                     acli=mr_cli, ua="github_org/mcim/1.0.0 (mcim.z0z0r4.top)")

# DB 我不要造轮子
# from mysql import *
# dbpool = AsyncDBPool(MysqlConfig.to_dict(), size=8)
# from databases import Database
engine = create_engine(
    f'mysql+pymysql://{MysqlConfig.user}:{MysqlConfig.password}@{MysqlConfig.host}:{MysqlConfig.port}/{MysqlConfig.database}?autocommit=1', pool_size=128, max_overflow=32)
metadata = MetaData(bind=engine)
# init table
Table = TableConfig(metadata=metadata)
metadata.create_all()

api = FastAPI(docs_url=None, redoc_url=None, title="MCIM",
              description="这是一个为 Curseforge Mod 信息加速的 API")


def getLogFile(basedir='logs'):
    if not os.path.exists(basedir):
        os.makedirs(basedir)
    else:
        if os.path.exists(os.path.join(basedir, "latest.log")):
            date = datetime.datetime.now().strftime('%Y-%m-%d')
            path = os.path.join(basedir, f'{date}.log')
            if os.path.exists(path):
                i = 0
                while os.path.exists(path):
                    i += 1
                    path = os.path.join(basedir, f'{date}-{i}.log')
                os.rename(os.path.join(basedir, "latest.log"), path)
            else:
                os.rename(os.path.join(basedir, "latest.log"), path)
    return os.path.join(basedir, "latest.log")


def log(text, logger=logging.info):
    logger(text)
    print(f'[{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}] {text}')


logging.basicConfig(level=logging.INFO,
                    filename=getLogFile(basedir="logs/sync"), filemode='w',
                    format='[%(asctime)s] [%(threadName)s] [%(levelname)s]: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', encoding="UTF-8")
api.mount("/log", StaticFiles(directory="logs"), name="logs")

# docs
api.mount("/static", StaticFiles(directory="static"), name="static")


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


def sql_replace(sess: Session, table, **kwargs):
    insert_stmt = insert(table).values(kwargs)
    on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(**kwargs)
    sess.execute(on_duplicate_key_stmt)


def api_json_middleware(callback):
    @functools.wraps(callback)
    async def w(*args, **kwargs):
        try:
            res = await callback(*args, **kwargs)
            return res
        except StatusCodeException as e:
            if e.status == 404:
                return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"status": "failed", "error": "DataNotExists", "errorMessage": "Data Not exists"})
            return JSONResponse(status_code=e.status, content={"status": "failed", "error": "StatusCodeException", "errorMessage": str(e)})
        except Exception as e:
            traceback.print_exc()
            return JSONResponse(status_code=500, content={"status": "failed", "error": "Exception", "errorMessage": str(e)})
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
    return JSONResponse(content={"status": "success", "message": "z0z0r4 Mod Info", "information": {"Status": "https://status.mcim.z0z0r4.top/status/mcim", "Docs": ["https://mcim.z0z0r4.top/docs", "https://mcim.z0z0r4.top/redoc"], "Github": "https://github.com/z0z0r4/mcim", "contact": {"Eamil": "z0z0r4@outlook.com", "QQ": "3531890582"}}}, headers={"Cache-Control": "max-age=300, public"})


@api.get("/logs")
@api_json_middleware
async def get_log():
    def walk(path):
        info = {}
        for root, dirs, files in os.walk(path):
            info["files"] = files
            for dir in dirs:
                info[dir] = walk(os.path.join(root, dir))
        return info
    return JSONResponse({"logs": walk("logs")}, headers={"Cache-Control": "max-age=300, public"})


@api.get("/curseforge",
         responses={200: {"description": "CFCore", "content": {
             "text/plain": {"example": "CurseForge Core (397e291)"}}}
         },
         description="Curseforge API", tags=["Curseforge"])
@api_json_middleware
async def curseforge():
    return Response(content=await cf_api.end_point(), headers={"Cache-Control": "max-age=300, public"})


async def _curseforge_sync_game(sess: Session, gameid: int):
    data = await cf_api.get_game(gameid=gameid)
    cache_data = data["data"]
    cache_data["cachetime"] = int(time.time())
    insert_stmt = insert(Table.curseforge_game_info).values(
        gameid=gameid, status=200, time=int(time.time()), data=cache_data)
    on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
        data=insert_stmt.inserted.data)
    sess.execute(on_duplicate_key_stmt)
    sess.commit()
    log(f'Sync curseforge game {gameid}')
    return cache_data


async def _curseforge_get_game(gameid: int):
    with Session(bind=engine) as sess:
        # result = sess.query(
        #     select("curseforge_game_info", ["time", "status", "data"]).where("gameid", gameid).done())
        t = Table.curseforge_game_info
        result = sess.query(t.c.time, t.c.status, t.c.data).where(
            t.c.gameid == gameid).first()
        if result is None or len(result) == 0 or result[1] != 200:
            data = await _curseforge_sync_game(sess, gameid)
        else:
            data = result[2]
            if int(time.time()) - int(data["cachetime"]) > 60 * 60 * 4:
                data = await _curseforge_sync_game(sess, gameid)
        return JSONResponse(content={"status": "success", "data": data}, headers={"Cache-Control": "max-age=300, public"})


curseforge_game_example = {"id": 0, "name": "string", "slug": "string", "dateModified": "2019-08-24T14:15:22Z",
                           "assets": {"iconUrl": "string", "tileUrl": "string", "coverUrl": "string"}, "status": 1,
                           "apiStatus": 1}


@api.get("/curseforge/game/{gameid}",
         responses={200: {"description": "Curseforge Game info", "content": {
             "application/json": {"example":
                                  {"status": "success",
                                      "data": curseforge_game_example}
                                  }}}
                    }, description="Curseforge Game 信息", tags=["Curseforge"])
# @api_json_middleware
async def curseforge_game(gameid: int):
    return await _curseforge_get_game(gameid=gameid)


@api.get("/curseforge/games",
         responses={200: {"description": "Curseforge Games info", "content": {
             "application/json": {"example":
                                  {"status": "success", "data": [
                                      curseforge_game_example]}
                                  }}}
                    }, description="Curseforge 的全部 Game 信息", tags=["Curseforge"])
@api_json_middleware
async def curseforge_games():
    with Session(engine) as sess:
        all_data = []
        # sql_games_result = db.query(
        #     select("curseforge_game_info", ["gameid", "time", "status", "data"]))
        t = Table.curseforge_game_info
        sql_games_result = sess.query(t, t.c.time, t.c.status, t.c.data).all()
        for result in sql_games_result:
            if result is None or result == () or result[2] != 200:
                break
            gameid, time_tag, status, data = result
            if status == 200:
                if int(time.time()) - int(data["cachetime"]) > 60 * 60 * 4:
                    break
            all_data.append(data)
        else:
            return JSONResponse(content={"status": "success", "data": all_data}, headers={"Cache-Control": "max-age=300, public"})
        all_data = []
        sync_games_result = await cf_api.get_all_games()
        for result in sync_games_result["data"]:
            gameid = result["id"]
            tmnow = int(time.time())
            result["cachetime"] = tmnow
            # db.exe(insert("curseforge_game_info",
            #             dict(gameid=gameid, status=200, time=tmnow, data=json.dumps(result)), replace=True))
            sql_replace(sess, t, gameid=gameid, status=200,
                        time=tmnow, data=result)
            all_data.append(result)
        sess.commit()
    return JSONResponse(content={"status": "success", "data": all_data}, headers={"Cache-Control": "max-age=300, public"})


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
    data = await cf_api.get_categories(gameid=gameid, classid=classid)
    return JSONResponse({"status": "success", "data": data["data"]}, headers={"Cache-Control": "max-age=300, public"})

# mod 请求后台拉取 file_info 和 description，以及对应 file 的 changelog


async def curseforge_mod_background_task(sess: Session, modid: int):
    # files
    files_info = await _curseforge_get_files_info(modid=modid)
    for file_info in files_info:
        fileid = file_info["id"]
        # file_info
        await _curseforge_sync_file_info(sess, modid=modid, fileid=fileid)
        # changelog
        await _curseforge_sync_mod_file_changelog(sess, modid=modid, fileid=fileid)
    # description
    cachetime = int(time.time())
    description = (await cf_api.get_mod_description(modid=modid))["data"]
    # db.exe(insert("curseforge_mod_description",
    #                 dict(modid=modid, status=200, time=cachetime, description=description), replace=True))
    t = Table.curseforge_mod_description
    sql_replace(sess, t, modid=modid, status=200,
                time=cachetime, description=description)
    sess.commit()


async def _curseforge_sync_mod(sess: Session, modid: int):
    t = Table.curseforge_mod_info
    data = await cf_api.get_mod(modid=modid)
    # add cachetime
    tmnow = int(time.time())
    cache_data = data["data"]
    cache_data["cachetime"] = tmnow
    sql_replace(sess, t, modid=modid, status=200, time=tmnow, data=cache_data)
    sess.commit()
    log(f'Sync curseforge mod {modid}')
    return cache_data


async def _curseforge_get_mod(modid: int = None, slug: str = None, background_tasks=None):
    with Session(engine) as sess:
        t = Table.curseforge_mod_info
        if slug is not None:
            query = "slug"
            result = sess.query(t.c.time, t.c.status, t.c.data).where(
                t.c.slug == slug).first()
        elif modid is not None:
            query = "modid"
            result = sess.query(t.c.time, t.c.status, t.c.data).where(
                t.c.modid == modid).first()
        else:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"status": "failed", "error": "Neither slug and modid is not None"})
        if result is None or len(result) == 0 or result[1] != 200:
            if query == "slug":
                return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"status": "failed", "error": f"Can't found {slug} in cache database, please request by modid it first"})
            data = await _curseforge_sync_mod(sess, modid)
            background_tasks.add_task(
                curseforge_mod_background_task, sess, modid)
        else:
            data = result[2]
            # data = result[2]
            if int(time.time()) - int(data["cachetime"]) > 60 * 60 * 4:
                if query == "slug":
                    modid = data["id"]
                    data = await _curseforge_sync_mod(sess, modid)
                    # return {"status": "warning", "data": data, "error": "Data out of cachetime"}
                data = await _curseforge_sync_mod(sess, modid)
        # to mod_notification
        # if not background_tasks is None and query == "modid":
        #     background_tasks.add_task(curseforge_mod_background_task, sess, modid)
    return data


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


@api.get("/curseforge/mod/{modid_slug}",
         responses={
             200: {
                 "description": "Curseforge mod info",
                 "content": {
                     "application/json": {
                         "example": {"status": "success", "data": curseforge_mod_example}
                     }
                 }
             }
         }, description="Curseforge Mod 信息；可以传入modid，不建议使用此处的 slug 参数，因为将从缓存数据库查询", tags=["Curseforge"])
# @api_json_middleware
async def get_mod(modid_slug: int | str, background_tasks: BackgroundTasks):
    if type(modid_slug) is str:
        return JSONResponse({"status": "success", "data": await _curseforge_get_mod(slug=modid_slug, background_tasks=background_tasks)}, headers={"Cache-Control": "max-age=300, public"})
    else:
        return JSONResponse({"status": "success", "data": await _curseforge_get_mod(modid=modid_slug, background_tasks=background_tasks)}, headers={"Cache-Control": "max-age=300, public"})
    # slug 查询为 https://www.cfwidget.com/ 的启发


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

    return JSONResponse({"status": "success", "data": modids_data}, headers={"Cache-Control": "max-age=300, public"})


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
    with Session(engine) as sess:
        t = Table.curseforge_mod_description
        result = sess.query(t.c.time, t.c.status, t.c.description).where(
            t.c.modid == modid).first()
        # result = db.queryone(select(
        #     "curseforge_mod_description", ["modid", "time", "status", "description"]).where("modid", modid).done())
        if result is None or len(result) == 0:
            cachetime = int(time.time())
            description = (await cf_api.get_mod_description(modid=modid))["data"]
            # db.exe(insert("curseforge_mod_description", dict(
            #     modid=modid, status=200, time=cachetime, description=description), replace=True))
            sql_replace(sess, t, modid=modid, time=int(
                time.time()), status=200, description=description)
            sess.commit()
        elif result[2] != 200:
            cachetime = int(time.time())
            description = (await cf_api.get_mod_description(modid=modid))["data"]
            sql_replace(sess, t, modid=modid, time=int(
                time.time()), status=200, description=description)
            sess.commit()
        else:
            description = result[3]
            cachetime = result[1]
    return JSONResponse({"status": "success", "data": description, "cachetime": cachetime}, headers={"Cache-Control": "max-age=300, public"})


curseforge_search_example = {
    'data': [
        {'id': 0, 'gameId': 0, 'name': 'string', 'slug': 'string', 'links': {'websiteUrl': 'string', 'wikiUrl': 'string', 'issuesUrl': 'string', 'sourceUrl': 'string'}, 'summary': 'string', 'status': 1, 'downloadCount': 0, 'isFeatured': True, 'primaryCategoryId': 0, 'categories': [{'id': 0, 'gameId': 0, 'name': 'string', 'slug': 'string', 'url': 'string', 'iconUrl': 'string', 'dateModified': '2019-08-24T14:15:22Z', 'isClass': True, 'classId': 0, 'parentCategoryId': 0, 'displayIndex': 0}], 'classId': 0, 'authors': [{'id': 0, 'name': 'string', 'url': 'string'}], 'logo': {'id': 0, 'modId': 0, 'title': 'string', 'description': 'string', 'thumbnailUrl': 'string', 'url': 'string'}, 'screenshots': [{'id': 0, 'modId': 0, 'title': 'string', 'description': 'string', 'thumbnailUrl': 'string', 'url': 'string'}], 'mainFileId': 0, 'latestFiles': [{'id': 0, 'gameId': 0, 'modId': 0, 'isAvailable': True, 'displayName': 'string', 'fileName': 'string', 'releaseType': 1, 'fileStatus': 1, 'hashes': [
            {'value': 'string', 'algo': 1}], 'fileDate': '2019-08-24T14:15:22Z', 'fileLength': 0, 'downloadCount': 0, 'downloadUrl': 'string', 'gameVersions': ['string'], 'sortableGameVersions': [{'gameVersionName': 'string', 'gameVersionPadded': 'string', 'gameVersion': 'string', 'gameVersionReleaseDate': '2019-08-24T14:15:22Z', 'gameVersionTypeId': 0}], 'dependencies': [{'modId': 0, 'relationType': 1}], 'exposeAsAlternative': True, 'parentProjectFileId': 0, 'alternateFileId': 0, 'isServerPack': True, 'serverPackFileId': 0, 'fileFingerprint': 0, 'modules': [{'name': 'string', 'fingerprint': 0}]}], 'latestFilesIndexes': [{'gameVersion': 'string', 'fileId': 0, 'filename': 'string', 'releaseType': 1, 'gameVersionTypeId': 0, 'modLoader': 0}], 'dateCreated': '2019-08-24T14:15:22Z', 'dateModified': '2019-08-24T14:15:22Z', 'dateReleased': '2019-08-24T14:15:22Z', 'allowModDistribution': True, 'gamePopularityRank': 0, 'isAvailable': True, 'thumbsUpCount': 0}
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
                            gameVersionTypeId: int = None, slug: str = None, index: int = None, pageSize: int = 50, background_tasks: BackgroundTasks = None):
    # TODO 在数据库中搜索
    data = await cf_api.search(
        gameid=gameId, classid=classId, categoryid=categoryId, gameversion=gameVersion,
        searchfilter=searchFilter, sortfield=sortField, sortorder=sortOrder,
        modloadertype=modLoaderType, gameversiontypeid=gameVersionTypeId, slug=slug, index=index,
        pagesize=pageSize)
    background_tasks.add_task(curseforge_search_background_task, data["data"])
    return JSONResponse({"status": "success", "data": data["data"]}, headers={"Cache-Control": "max-age=300, public"})


async def curseforge_search_background_task(data: List):
    with Session(engine) as sess:
        t = Table.curseforge_mod_info
        for mod in data:
            modid = mod["id"]
            # add cachetime
            tmnow = int(time.time())
            mod["cachetime"] = tmnow
            sql_replace(sess, t, modid=modid, status=200, time=tmnow, data=mod)
        sess.commit()


async def _curseforge_sync_file_info(sess: Session, modid: int, fileid: int):
    t = Table.curseforge_file_info
    cache_data = (await cf_api.get_file(modid=modid, fileid=fileid))["data"]
    cache_data["cachetime"] = int(time.time())
    sql_replace(sess, t, modid=modid, fileid=fileid, status=200,
                time=int(time.time()), data=cache_data)
    sess.commit()
    log(f'Sync curseforge file {fileid}')
    return cache_data


async def _curseforge_get_file_info(modid: int, fileid: int):
    with Session(engine) as sess:
        t = Table.curseforge_file_info
        query = sess.query(t.c.time, t.c.status, t.c.data).where(
            t.c.modid == modid, t.c.fileid == fileid).first()
        if query is None or query[1] != 200:
            data = await _curseforge_sync_file_info(sess, modid=modid, fileid=fileid)
            cachetime = data["cachetime"]
        else:
            data = query[2]
            if int(time.time()) - int(data["cachetime"]) > 60 * 60 * 4:
                data = await _curseforge_sync_file_info(sess, modid=modid, fileid=fileid)
                cachetime = data["cachetime"]
            else:
                cachetime = query[0]
    return JSONResponse({"status": "success", "data": data, "cachetime": cachetime})


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
    return JSONResponse({"status": "success", "data": await _curseforge_get_files_info(modid=modId)}, headers={"Cache-Control": "max-age=300, public"})


async def _curseforge_sync_mod_file_changelog(sess: Session, modid: int, fileid: int):
    t = Table.curseforge_file_changelog
    changelog = (await cf_api.get_mod_file_changelog(modid=modid, fileid=fileid))["data"]
    sql_replace(sess, t, modid=modid, fileid=fileid, status=200,
                time=int(time.time()), changelog=changelog)
    sess.commit()
    log(f'Sync curseforge file changelog {fileid}')
    return changelog


async def _curseforge_get_mod_file_changelog(modid: int, fileid: int):
    with Session(engine) as sess:
        t = Table.curseforge_file_changelog
        # query = db.queryone(cmd := select("curseforge_file_changelog", ["time", "status", "changelog"]).where(
        #     "modid", modid).AND("fileid", fileid).done())
        query = sess.query(t.c.time, t.c.status, t.c.changelog).where(
            t.c.modid == modid, t.c.fileid == fileid).first()
        if query is None or query[1] != 200:
            data = await _curseforge_sync_mod_file_changelog(sess, modid=modid, fileid=fileid)
            cachetime = int(time.time())
        else:
            data = str(query[2])
            cachetime = int(query[0])
            if int(time.time()) - cachetime > 60 * 60 * 4:
                data = await _curseforge_sync_file_info(sess, modid=modid, fileid=fileid)
                cachetime = int(time.time())
            else:
                cachetime = query[0]
    return JSONResponse({"status": "success", "changelog": data, "cachetime": cachetime}, headers={"Cache-Control": "max-age=300, public"})


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
    with Session(engine) as sess:
        t = Table.curseforge_file_info
        # query = db.queryone(cmd := select("curseforge_file_info", ["time", "status", "data"]).where(
        #     "modid", modid).AND("fileid", fileid).done())
    query = sess.query(t.c.time, t.c.status, t.c.data).where(
        t.c.modid == modid, t.c.fileid == fileid).first()
    if query is None:
        data = await _curseforge_sync_file_info(sess, modid=modid, fileid=fileid)
        cachetime = int(time.time())
    elif len(query) <= 0 or query[1] != 200:
        data = await _curseforge_sync_file_info(sess, modid=modid, fileid=fileid)
        cachetime = int(time.time())
    else:
        data = json.loads(query[2])
        if int(time.time()) - int(data["cachetime"]) > 60 * 60 * 4:
            data = await _curseforge_sync_file_info(sess, modid=modid, fileid=fileid)
            cachetime = int(time.time())
        else:
            cachetime = query[0]
    return JSONResponse({"status": "success", "url": data["downloadUrl"], "cachetime": cachetime}, headers={"Cache-Control": "max-age=300, public"})

# 仍未能够了解 fingerprint 到底是如何工作的...尤其是fuzzy fingerprint
# 暂时不缓存fingerprint信息
# 为啥不像 modrinth 一样简单明了
class FingerprintsItemModel(BaseModel):
    fingerprints: List[int]

class Fuzzy_Fingerprint(BaseModel):
    foldername = str
    fingerprints: List[int]

class Fuzzy_FingerprintModel(BaseModel):
    gameId = int
    fingerprints: List[Fuzzy_Fingerprint]

curseforge_fingerprint_example = {"data":{"isCacheBuilt":true,"exactMatches":[{"id":0,"file":{"id":0,"gameId":0,"modId":0,"isAvailable":true,"displayName":"string","fileName":"string","releaseType":1,"fileStatus":1,"hashes":[{"value":"string","algo":1}],"fileDate":"2019-08-24T14:15:22Z","fileLength":0,"downloadCount":0,"downloadUrl":"string","gameVersions":["string"],"sortableGameVersions":[{"gameVersionName":"string","gameVersionPadded":"string","gameVersion":"string","gameVersionReleaseDate":"2019-08-24T14:15:22Z","gameVersionTypeId":0}],"dependencies":[{"modId":0,"relationType":1}],"exposeAsAlternative":true,"parentProjectFileId":0,"alternateFileId":0,"isServerPack":true,"serverPackFileId":0,"fileFingerprint":0,"modules":[{"name":"string","fingerprint":0}]},"latestFiles":[{"id":0,"gameId":0,"modId":0,"isAvailable":true,"displayName":"string","fileName":"string","releaseType":1,"fileStatus":1,"hashes":[{"value":"string","algo":1}],"fileDate":"2019-08-24T14:15:22Z","fileLength":0,"downloadCount":0,"downloadUrl":"string","gameVersions":["string"],"sortableGameVersions":[{"gameVersionName":"string","gameVersionPadded":"string","gameVersion":"string","gameVersionReleaseDate":"2019-08-24T14:15:22Z","gameVersionTypeId":0}],"dependencies":[{"modId":0,"relationType":1}],"exposeAsAlternative":true,"parentProjectFileId":0,"alternateFileId":0,"isServerPack":true,"serverPackFileId":0,"fileFingerprint":0,"modules":[{"name":"string","fingerprint":0}]}]}],"exactFingerprints":[0],"partialMatches":[{"id":0,"file":{"id":0,"gameId":0,"modId":0,"isAvailable":true,"displayName":"string","fileName":"string","releaseType":1,"fileStatus":1,"hashes":[{"value":"string","algo":1}],"fileDate":"2019-08-24T14:15:22Z","fileLength":0,"downloadCount":0,"downloadUrl":"string","gameVersions":["string"],"sortableGameVersions":[{"gameVersionName":"string","gameVersionPadded":"string","gameVersion":"string","gameVersionReleaseDate":"2019-08-24T14:15:22Z","gameVersionTypeId":0}],"dependencies":[{"modId":0,"relationType":1}],"exposeAsAlternative":true,"parentProjectFileId":0,"alternateFileId":0,"isServerPack":true,"serverPackFileId":0,"fileFingerprint":0,"modules":[{"name":"string","fingerprint":0}]},"latestFiles":[{"id":0,"gameId":0,"modId":0,"isAvailable":true,"displayName":"string","fileName":"string","releaseType":1,"fileStatus":1,"hashes":[{"value":"string","algo":1}],"fileDate":"2019-08-24T14:15:22Z","fileLength":0,"downloadCount":0,"downloadUrl":"string","gameVersions":["string"],"sortableGameVersions":[{"gameVersionName":"string","gameVersionPadded":"string","gameVersion":"string","gameVersionReleaseDate":"2019-08-24T14:15:22Z","gameVersionTypeId":0}],"dependencies":[{"modId":0,"relationType":1}],"exposeAsAlternative":true,"parentProjectFileId":0,"alternateFileId":0,"isServerPack":true,"serverPackFileId":0,"fileFingerprint":0,"modules":[{"name":"string","fingerprint":0}]}]}],"partialMatchFingerprints":{"property1":[0],"property2":[0]},"installedFingerprints":[0],"unmatchedFingerprints":[0]}}
curseforge_fuzzy_fingerprint_example = {"data":{"fuzzyMatches":[{"id":0,"file":{"id":0,"gameId":0,"modId":0,"isAvailable":true,"displayName":"string","fileName":"string","releaseType":1,"fileStatus":1,"hashes":[{"value":"string","algo":1}],"fileDate":"2019-08-24T14:15:22Z","fileLength":0,"downloadCount":0,"downloadUrl":"string","gameVersions":["string"],"sortableGameVersions":[{"gameVersionName":"string","gameVersionPadded":"string","gameVersion":"string","gameVersionReleaseDate":"2019-08-24T14:15:22Z","gameVersionTypeId":0}],"dependencies":[{"modId":0,"relationType":1}],"exposeAsAlternative":true,"parentProjectFileId":0,"alternateFileId":0,"isServerPack":true,"serverPackFileId":0,"fileFingerprint":0,"modules":[{"name":"string","fingerprint":0}]},"latestFiles":[{"id":0,"gameId":0,"modId":0,"isAvailable":true,"displayName":"string","fileName":"string","releaseType":1,"fileStatus":1,"hashes":[{"value":"string","algo":1}],"fileDate":"2019-08-24T14:15:22Z","fileLength":0,"downloadCount":0,"downloadUrl":"string","gameVersions":["string"],"sortableGameVersions":[{"gameVersionName":"string","gameVersionPadded":"string","gameVersion":"string","gameVersionReleaseDate":"2019-08-24T14:15:22Z","gameVersionTypeId":0}],"dependencies":[{"modId":0,"relationType":1}],"exposeAsAlternative":true,"parentProjectFileId":0,"alternateFileId":0,"isServerPack":true,"serverPackFileId":0,"fileFingerprint":0,"modules":[{"name":"string","fingerprint":0}]}],"fingerprints":[0]}]}}


@api.post("/curseforge/fingerprints",
          responses={200: {"description": "Curseforge fingerprint", "content": {
              "application/json": {"example": curseforge_fingerprint_example}}}
          }, description="Curseforge Fingerprints", tags=["Curseforge"])
@api_json_middleware
async def get_curseforge_fingerprints(item: FingerprintsItemModel):
    result = (await cf_api.get_fingerprint(item.fingerprints))["data"]
    return JSONResponse({"status": "success", "data": result}, headers={"Cache-Control": "max-age=300, public"})

@api.post("/curseforge/fingerprints/fuzzy",
          responses={200: {"description": "Curseforge fuzzy fingerprint", "content": {
              "application/json": {"example": curseforge_fuzzy_fingerprint_example}}}
          }, description="Curseforge Fuzzy Fingerprints", tags=["Curseforge"])
@api_json_middleware
async def get_curseforge_fuzzy_fingerprints(item: Fuzzy_FingerprintModel):
    result = (await cf_api.get_fuzzy_fingerprnt(gameid=item.gameId, fingerprints=item.fingerprints))["data"]
    return JSONResponse({"status": "success", "data": result}, headers={"Cache-Control": "max-age=300, public"})


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


# async def _modrinth_background_task_sync_version(sess: Session, data: dict):
#     # for version_id in data["versions"]:
#     #     await _modrinth_sync_version(sess, version_id=version_id)
#     project_id = data["id"]
#     await mr_api.get_project_versions(project_id=project_id)
#     for version_id in data["versions"]:
#         pass


async def _modrinth_sync_project(sess: Session, idslug: str, background_tasks: BackgroundTasks = None):  # 优先采用 slug
    t = Table.modrinth_project_info
    cache_data = await mr_api.get_project(slug=idslug)
    slug = cache_data["slug"]
    project_id = cache_data["id"]
    cache_data["cachetime"] = int(time.time())
    # db.exe(insert("modrinth_project_info",
    #               dict(project_id=project_id, slug=slug, status=200,
    #                    time=int(time.time()), data=json.dumps(cache_data)),
    #               replace=True))
    sql_replace(sess, t, project_id=project_id, slug=slug,
                status=200, time=int(time.time()), data=cache_data)
    log(f'Sync modrinth project {project_id}')
    sess.commit()
    if background_tasks is not None:
        background_tasks.add_task(
            _modrinth_sync_project_versions, sess, idslug)
    return cache_data


async def _modrinth_get_project(idslug: str, background_tasks=None):
    with Session(engine) as sess:
        # id_cmd = select("modrinth_project_info", ["time", "status", "data"]).where(
        #     "project_id", idslug).done()
        # id_query = db.queryone(id_cmd)
        t = Table.modrinth_project_info
        query = sess.query(t.c.time, t.c.status, t.c.data).where(
            t.c.project_id == idslug).first()
        if query is None:
            # slug_cmd = select("modrinth_project_info", [
            #                   "time", "status", "data"]).where("slug", idslug).done()
            # slug_query = db.queryone(slug_cmd)
            query = sess.query(t.c.time, t.c.status, t.c.data).where(
                t.c.slug == idslug).first()
            if query is None:
                data = await _modrinth_sync_project(sess, idslug=idslug, background_tasks=background_tasks)
            else:
                cachetime, status, data = query
                if status == 200:
                    # data = json.loads(data)
                    if int(time.time()) - data["cachetime"] > 60 * 60 * 4:
                        data = await _modrinth_sync_project(sess, idslug=idslug, background_tasks=background_tasks)
                else:
                    data = await _modrinth_sync_project(sess, idslug=idslug, background_tasks=background_tasks)
        else:
            print(query)
            cachetime, status, data = query
            if status == 200:
                if int(time.time()) - data["cachetime"] > 60 * 60 * 4:
                    data = await _modrinth_sync_project(sess, idslug=idslug, background_tasks=background_tasks)
            else:
                data = await _modrinth_sync_project(sess, idslug=idslug, background_tasks=background_tasks)
        # 添加后台任务：version_info
        # if background_tasks is not None:
        #     background_tasks.add_task(
        #         _modrinth_background_task_sync_version, sess, data)
        return data


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
    # return await _modrinth_get_project(idslug, background_tasks=background_tasks)
    return JSONResponse({"status": "success", "data": await _modrinth_get_project(idslug, background_tasks=background_tasks)}, headers={"Cache-Control": "max-age=300, public"})


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
    return JSONResponse({"status": "success", "data": projects_data},  headers={"Cache-Control": "max-age=300, public"})


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
    # TODO 在数据库中搜索
    return JSONResponse({"status": "success", "data": search_result}, headers={"Cache-Control": "max-age=300, public"})


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


async def _modrinth_sync_version(sess: Session, version_id: str):
    t = Table.modrinth_version_info
    cache_data = await mr_api.get_project_version(version_id=version_id)
    project_id = cache_data["project_id"]
    cache_data["cachetime"] = int(time.time())
    # db.exe(insert("modrinth_version_info", dict(project_id=project_id, version_id=version_id,
    #        status=200, time=cache_data["cachetime"], data=json.dumps(cache_data)), replace=True))
    sql_replace(sess, t, project_id=project_id, version_id=version_id,
                status=200, time=cache_data["cachetime"], data=cache_data)
    sess.commit()
    log(f'Sync modrinth version {version_id}')
    return cache_data


async def _modrinth_sync_project_versions(sess: Session, project_id: str):
    t = Table.modrinth_version_info
    versions = await mr_api.get_project_versions(project_id=project_id)
    for version in versions:
        version["cachetime"] = int(time.time())
        # db.exe(insert("modrinth_version_info",
        #               dict(project_id=project_id, version_id=version_info["id"], status=200,
        #                    time=version_info["cachetime"],
        #                    data=json.dumps(version_info)), replace=True))
        sql_replace(sess, t, project_id=project_id,
                    version_id=version["id"], status=200, time=version["cachetime"], data=version)
        sess.commit()
    log(f'Sync modrinth project {project_id} versions')
    return versions


async def _modrinth_get_version(version_id: str):
    with Session(engine) as sess:
        t = Table.modrinth_version_info
        # cmd = select("modrinth_version_info", ["time", "status", "data"]).where(
        #     "version_id", version_id).done()
        # query = db.queryone(cmd)
        query = sess.query(t.c.time, t.c.status, t.c.data).filter(
            t.c.version_id == version_id).first()
        if query is None:
            data = await _modrinth_sync_version(sess, version_id=version_id)
        else:
            cachetime, status, data = query
            if status == 200:
                if int(time.time()) - data["cachetime"] > 60 * 60 * 4:
                    data = await _modrinth_sync_version(sess, version_id=version_id)
            else:
                data = await _modrinth_sync_version(sess, version_id=version_id)
        return JSONResponse({"status": "success", "data": data},  headers={"Cache-Control": "max-age=300, public"})


@api.get("/modrinth/version/{version_id}",
         responses={200: {"description": "Modrinth version info", "content": {
             "application/json": {"example":
                                  modrinth_version_example
                                  }}}
                    }, description="Modrinth version info", tags=["Modrinth"])
@api_json_middleware
async def get_modrinth_version(version_id: str):
    return await _modrinth_get_version(version_id)


async def _modrinth_get_project_versions(idslug: str, game_versions: list = None, loaders: list = None, featured: bool = None):
    async def sync_version_info_list(project_id: str, game_versions: list = None, loaders: list = None, featured: bool = None):
        version_info_list = await _modrinth_sync_project_versions(sess, project_id=project_id)
        versions = []
        for version_info in version_info_list:
            if featured:
                if version_info["featured"] != featured:
                    continue
            if loaders:
                if len(list(set(loaders) & set(version_info["loaders"]))) == 0:
                    continue
            if game_versions:
                if len(list(set(game_versions) & set(version_info["game_versions"]))) == 0:
                    continue
            versions.append(version_info)
        return versions

    with Session(engine) as sess:
        t = Table.modrinth_version_info
        if loaders:
            loaders = str_to_list(loaders)
        if game_versions:
            game_versions = str_to_list(game_versions)
        project_data = await _modrinth_get_project(idslug)  # 获取 project_id
        project_id = project_data["id"]
        # query = db.query(
        #     select("modrinth_version_info", ["time", "status", "data"]).where("project_id", project_id).done())
        query = sess.query(t.c.time, t.c.status, t.c.data).filter(
            t.c.project_id == project_id).all()
        if len(query) == 0:  # all() return List
            version_info_list = await sync_version_info_list(project_id)
        else:
            version_info_list = []
            for version_info in query:
                cachetime, status, data = version_info
                if status == 200:
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
                        version_info_list = await sync_version_info_list(project_id)
                        break
                else:
                    version_info_list = await sync_version_info_list(project_id)
                    break
                version_info_list.append(data)
    # return {"status": "success", "data": version_info_list}
    return JSONResponse({"status": "success", "data": version_info_list}, headers={"Cache-Control": "max-age=300, public"})
    # version_info_list = await sync_version_info_list(project_id)
    # t = Table.modrinth_version_info
    # version_info_lsit = await mr_api.get_project_versions(project_id=project_id, game_versions=game_versions, loaders=loaders, featured=featured)
    # for version_info in version_info_lsit:
    #     version_info["cachetime"] = int(time.time())
    #     # db.exe(insert("modrinth_version_info",
    #     #               dict(project_id=project_id, version_id=version_info["id"], status=200,
    #     #                    time=version_info["cachetime"],
    #     #                    data=json.dumps(version_info)), replace=True))
    #     sql_replace(sess, t, project_id=project_id, version_id=version_info["id"], status=200, time=version_info["cachetime"], data=version_info)
    #     sess.commit()
    # # TODO Background_task


@api.get("/modrinth/project/{idslug}/versions",
         responses={200: {"description": "Modrinth project versions info", "content": {
             "application/json": {"example":
                                  [modrinth_version_example]
                                  }}}
                    }, description="Modrint project versions info", tags=["Modrinth"])
@api_json_middleware
async def get_modrinth_project_versions(idslug: str, loaders: str = None, game_versions: str = None, featured: bool = None):
    return await _modrinth_get_project_versions(idslug, loaders=loaders, game_versions=game_versions, featured=featured)
    # return JSONResponse({"status": "success", "data": version_info_list}, headers={"Cache-Control": "max-age=300, public"})

example_modrinth_category = [
    {
        "icon": "<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><circle cx=\"12\" cy=\"12\" r=\"10\"/><polygon points=\"16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76\"/></svg>",
        "name": "adventure",
        "project_type": "mod"
    }
]


async def _modrinth_sync_tag_category(sess: Session):
    t = Table.modrinth_tag_info
    data = await mr_api.get_categories()
    # db.exe(insert("modrinth_tag_info",
    #               dict(slug="category", status=200,
    #                    time=int(time.time()),
    #                    data=json.dumps(data)), replace=True))
    sql_replace(sess, t, slug="category", status=200,
                time=int(time.time()), data=data)
    sess.commit()
    log(f'Sync modrinth tag category')
    return data

example_modrinth_loader = [
    {
        "icon": "<svg viewBox=\"0 0 276 288\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"23\" stroke-linecap=\"round\" stroke-linejoin=\"round\"><g transform=\"matrix(1,0,0,1,-3302.43,-67.3276)\"><g transform=\"matrix(0.564163,0,0,1.70346,1629.87,0)\"><g transform=\"matrix(1.97801,-0.0501803,0.151517,0.655089,1678.7,-354.14)\"><g><path d=\"M820.011,761.092C798.277,738.875 754.809,694.442 734.36,673.389C729.774,668.668 723.992,663.75 708.535,674.369C688.629,688.043 700.073,696.251 703.288,699.785C711.508,708.824 787.411,788.803 800.523,803.818C802.95,806.597 780.243,781.318 793.957,764.065C799.444,757.163 811.985,752.043 820.011,761.092C826.534,768.447 830.658,779.178 816.559,790.826C791.91,811.191 714.618,873.211 689.659,893.792C677.105,904.144 661.053,896.143 653.827,887.719C646.269,878.908 623.211,853.212 602.539,829.646C596.999,823.332 598.393,810.031 604.753,804.545C639.873,774.253 696.704,730.787 716.673,713.831\"/></g></g></g></g></svg>",
        "name": "fabric",
        "supported_project_types": [
            "mod",
            "modpack"
        ]
    }
]


async def _modrinth_sync_tag_loader(sess: Session):
    t = Table.modrinth_tag_info
    data = await mr_api.get_loaders()
    # db.exe(insert("modrinth_tag_info",
    #               dict(slug="loader", status=200,
    #                    time=int(time.time()),
    #                    data=json.dumps(data)), replace=True))
    sql_replace(sess, t, slug="loader", status=200,
                time=int(time.time()), data=data)
    sess.commit()
    log(f'Sync modrinth tag loader')
    return data

example_modrinth_game_version = [
    {
        "version": "1.18.1",
        "version_type": "release",
        "date": "2019-08-24T14:15:22Z",
        "major": True
    }
]


async def _modrinth_sync_tag_game_version(sess: Session):
    t = Table.modrinth_tag_info
    data = await mr_api.get_game_versions()
    # db.exe(insert("modrinth_tag_info",
    #               dict(slug="game_version", status=200,
    #                    time=int(time.time()),
    #                    data=json.dumps(data)), replace=True))
    sql_replace(sess, t, slug="game_version", status=200,
                time=int(time.time()), data=data)
    sess.commit()
    log(f'Sync modrinth tag game_version')
    return data

example_modrinth_license = [
    {
        "short": "lgpl-3",
        "name": "GNU Lesser General Public License v3"
    }
]


async def _modrinth_sync_tag_license(sess: Session):
    t = Table.modrinth_tag_info
    data = await mr_api.get_licenses()
    # db.exe(insert("modrinth_tag_info",
    #               dict(slug="license", status=200,
    #                    time=int(time.time()),
    #                    data=json.dumps(data)), replace=True))
    sql_replace(sess, t, slug="license", status=200,
                time=int(time.time()), data=data)
    sess.commit()
    log(f'Sync modrinth tag license')
    return data


@api.get("/modrinth/tag/category", responses={200: {"description": "Modrinth tag catrgory", "content": {
    "application/json": {"example":
                         example_modrinth_category
                         }}}
}, description="Modrinth tag category", tags=["Modrinth"])
async def get_modrinth_tag_category():
    with Session(engine) as sess:
        t = Table.modrinth_tag_info
        # cmd = select("modrinth_tag_info", ["time", "status", "data"]).where(
        #     "slug", "category").done()
        # query = db.queryone(cmd)
        query = sess.query(t.c.time, t.c.status, t.c.data).filter(
            t.c.slug == "category").first()
        if query is None:
            data = await _modrinth_sync_tag_category(sess)
            cachetime = int(time.time())
        else:
            cachetime, status, data = query
            if cachetime - int(time.time()) > 60 * 60 * 4 or status == 200:
                data = await _modrinth_sync_tag_category(sess)
    return JSONResponse({"status": "success", "cachetime": cachetime, "data": data}, headers={"Cache-Control": "max-age=300, public"})


@api.get("/modrinth/tag/loader", responses={200: {"description": "Modrinth tag loader", "content": {
    "application/json": {"example":
                         example_modrinth_loader
                         }}}
}, description="Modrinth tag loader", tags=["Modrinth"])
async def get_modrinth_tag_loader():
    t = Table.modrinth_tag_info
    with Session(engine) as sess:
        # cmd = select("modrinth_tag_info", ["time", "status", "data"]).where(
        #     "slug", "loader").done()
        # query = db.queryone(cmd)
        query = sess.query(t.c.time, t.c.status, t.c.data).filter(
            t.c.slug == "loader").first()
        if query is None:
            data = await _modrinth_sync_tag_loader(sess)
            cachetime = int(time.time())
        else:
            cachetime, status, data = query
            if cachetime - int(time.time()) > 60 * 60 * 4 or status == 200:
                data = await _modrinth_sync_tag_loader(sess)
    return JSONResponse({"status": "success", "cachetime": cachetime, "data": data}, headers={"Cache-Control": "max-age=300, public"})


@api.get("/modrinth/tag/game_version", responses={200: {"description": "Modrinth tag game version", "content": {
    "application/json": {"example":
                         example_modrinth_game_version
                         }}}
}, description="Modrinth tag game version", tags=["Modrinth"])
async def get_modrinth_tag_game_version():
    t = Table.modrinth_tag_info
    with Session(engine) as sess:
        # cmd = select("modrinth_tag_info", ["time", "status", "data"]).where(
        #     "slug", "game_version").done()
        # query = db.queryone(cmd)
        query = sess.query(t.c.time, t.c.status, t.c.data).filter(
            t.c.slug == "game_version").first()
        if query is None:
            data = await _modrinth_sync_tag_game_version(sess)
            cachetime = int(time.time())
        else:
            cachetime, status, data = query
            if cachetime - int(time.time()) > 60 * 60 * 4 or status == 200:
                data = await _modrinth_sync_tag_game_version(sess)
    return JSONResponse({"status": "success", "cachetime": cachetime, "data": data}, headers={"Cache-Control": "max-age=300, public"})


@api.get("/modrinth/tag/license", responses={200: {"description": "Modrinth tag license", "content": {
    "application/json": {"example":
                         example_modrinth_license
                         }}}
}, description="Modrinth tag license", tags=["Modrinth"])
async def get_modrinth_tag_license():
    t = Table.modrinth_tag_info
    with Session(engine) as sess:
        # cmd = select("modrinth_tag_info", ["time", "status", "data"]).where(
        #     "slug", "license").done()
        # query = db.queryone(cmd)
        query = sess.query(t.c.time, t.c.status, t.c.data).filter(
            t.c.slug == "license").first()
        if query is None:
            data = await _modrinth_sync_tag_license(sess)
            cachetime = int(time.time())
        else:
            cachetime, status, data = query
            if cachetime - int(time.time()) > 60 * 60 * 4 or status == 200:
                data = await _modrinth_sync_tag_license(sess)
    return JSONResponse({"status": "success", "cachetime": cachetime, "data": data}, headers={"Cache-Control": "max-age=300, public"})


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(message)s",
            "use_colors": False,
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '%(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s',
            "use_colors": False
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": "logs/web/latest.log"
        },
        "access": {
            "formatter": "access",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": "logs/web/latest.log"
        },
    },
    "loggers": {
        "": {"handlers": ["default"], "level": "INFO"},
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
    },
}

if __name__ == "__main__":
    host, port = "0.0.0.0", 8000
    try:
        getLogFile(basedir="logs/web")
        uvicorn.run(api, host=host, port=port)
    except KeyboardInterrupt:
        print("~~ BYE ~~")

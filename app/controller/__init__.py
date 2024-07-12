from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from odmantic import query
from typing import Optional
from app.controller.v1 import v1_router
from app.models.database.curseforge import File as cfFile
from app.models.database.modrinth import File as mrFile
from app.config import MCIMConfig
from app.sync.curseforge import file_cdn_url_cache as cf_file_cdn_url_cache
from app.sync.modrinth import file_cdn_url_cache as mr_file_cdn_url_cache
from app.sync.modrinth import file_cdn_cache_add_task as mr_file_cdn_cache_add_task
from app.sync.curseforge import file_cdn_cache_add_task as cf_file_cdn_cache_add_task
from app.sync.curseforge import file_cdn_cache as cf_file_cdn_cache
from app.sync.modrinth import file_cdn_cache as mr_file_cdn_cache
from app.sync.modrinth import sync_project
from app.sync.curseforge import sync_mutil_files
from app.utils.loger import log
from app.utils.response_cache import cache

mcim_config = MCIMConfig.load()

controller_router = APIRouter()

controller_router.include_router(v1_router, prefix="/v1")


# expire 3h

ARIA2_ENABLED: bool = mcim_config.aria2

if mcim_config.file_cdn:
    # modrinth | example: https://cdn.modrinth.com/data/AANobbMI/versions/IZskON6d/sodium-fabric-0.5.8%2Bmc1.20.6.jar
    # WARNING: 直接查 version_id 忽略 project_id
    # WARNING: 必须文件名一致
    @controller_router.get("/data/{project_id}/versions/{version_id}/{file_name}")
    @cache(expire=int(60 * 60 * 2.8))
    async def get_modrinth_file(project_id: str, version_id: str, file_name: str, request: Request):
        key = f'file_cdn_modrinth:{project_id}:{version_id}:{file_name}'
        cache = await request.app.state.file_cdn_redis_async_engine.get(key)
        if cache:
            cache = cache.decode("UTF-8")
            log.debug(f"URL cache found, return {cache}")
            return RedirectResponse(url=cache)
        else:
            file: Optional[mrFile] = await request.app.state.aio_mongo_engine.find_one(mrFile, query.and_(mrFile.version_id == version_id, mrFile.filename == file_name))
            if file:
                sha1 = file.hashes.sha1
                alist_url = f'{mcim_config.alist_endpoint}/modrinth/{sha1[:2]}/{sha1}'
                if file.file_cdn_cached:
                    mr_file_cdn_url_cache.send(url=alist_url, key=key)
                    log.debug(f"URL cache not found, return {alist_url} directly.")
                    return RedirectResponse(url=alist_url) # TODO: cache headers
                else:
                    if ARIA2_ENABLED:
                        mr_file_cdn_cache_add_task.send(file.model_dump())
                        log.debug(f"file cache not found, {alist_url} send with aria2 mode.")
                    else:
                        mr_file_cdn_cache.send(file.model_dump())
                        log.debug(f"file cache not found, {alist_url} send with normal mode.")
            else:
                sync_project.send(project_id)
                log.debug(f"sync project {project_id} task send.")
        
        return RedirectResponse(url=f"https://cdn.modrinth.com/data/{project_id}/versions/{version_id}/{file_name}")

    # curseforge | example: https://edge.forgecdn.net/files/3040/523/jei_1.12.2-4.16.1.301.jar
    @controller_router.get("/files/{fileid1}/{fileid2}/{file_name}")
    @cache(expire=int(60 * 60 * 2.8))
    async def get_curseforge_file(fileid1: str, fileid2: str, file_name: str, request: Request):
        fileid = int(f"{fileid1}{fileid2}")
        key = f'file_cdn_curseforge:{fileid}:{file_name}'
        cache = await request.app.state.file_cdn_redis_async_engine.get(key)
        if cache:
            cache = cache.decode("UTF-8")
            log.debug(f"URL cache found, return {cache}")
            return RedirectResponse(url=cache)
        else: # redis 中没有缓存网盘链接
            file: Optional[cfFile] = await request.app.state.aio_mongo_engine.find_one(cfFile, query.and_(cfFile.id == fileid, cfFile.fileName == file_name))
            if file: # 数据库中有文件
                sha1 = file.hashes[0].value if file.hashes[0].algo == 1 else file.hashes[1].value
                alist_url = f'{mcim_config.alist_endpoint}/curseforge/{sha1[:2]}/{sha1}'
                if file.file_cdn_cached:
                    cf_file_cdn_url_cache.send(url=alist_url, key=key)
                    log.debug(f"URL cache not found, return {alist_url} directly.")
                    return RedirectResponse(url=alist_url)
                else:
                    if ARIA2_ENABLED:
                        cf_file_cdn_cache_add_task.send(file.model_dump())
                        log.debug(f"file cache not found, {alist_url} send with aria2 mode.")
                    else:
                        cf_file_cdn_cache.send(file.model_dump())
                        log.debug(f"file cache not found, {alist_url} send with normal mode.")
            else:
                sync_mutil_files.send([fileid])
                log.debug(f"sync fileId {fileid} task send.")
        RedirectResponse(url=f"https://mediafilez.curseforge.com/files{fileid1}/{fileid2}/{file_name}")
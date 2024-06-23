from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from odmantic import query

from app.controller.v1 import v1_router
from app.database import aio_mongo_engine, file_cdn_redis_async_engine
from app.models.database.curseforge import File as cfFile
from app.models.database.modrinth import File as mrFile
from app.config import MCIMConfig
from app.sync.curseforge import file_cdn_url_cache as cf_file_cdn_url_cache
from app.sync.modrinth import file_cdn_url_cache as mr_file_cdn_url_cache
from app.sync.modrinth import file_cdn_cache_add_task as mr_file_cdn_cache_add_task
from app.sync.curseforge import file_cdn_cache_add_task as cf_file_cdn_cache_add_task

mcim_config = MCIMConfig.load()

controller_router = APIRouter()

controller_router.include_router(v1_router, prefix="/v1")

# file cdn
# redis db 4 | expire 3h

if mcim_config.file_cdn:
    # modrinth | example: https://cdn.modrinth.com/data/AANobbMI/versions/IZskON6d/sodium-fabric-0.5.8%2Bmc1.20.6.jar
    # WARNING: 直接查 version_id 忽略 project_id
    # WARNING: 必须文件名一致
    @controller_router.get("/data/{project_id}/versions/{version_id}/{file_name}")
    async def get_modrinth_file(project_id: str, version_id: str, file_name: str):
        cache = await file_cdn_redis_async_engine.hget("file_cdn_modrinth", f'{project_id}/{version_id}/{file_name}')
        if cache:
            return RedirectResponse(url=cache)
        else:
            file: mrFile = await aio_mongo_engine.find_one(mrFile, query.and_(mrFile.version_id == version_id, mrFile.filename == file_name))
            sha1 = file.hashes.sha1
            if file:
                if file.file_cdn_cached:
                    url = f'{mcim_config.alist_endpoint}/modrinth/{sha1[:2]}/{sha1}'
                    mr_file_cdn_url_cache.send(url=url, key=f'{project_id}/{version_id}/{file_name}')
                    return RedirectResponse(url=url)
                else:
                    mr_file_cdn_cache_add_task.send(file)
            return RedirectResponse(url=f"https://cdn.modrinth.com/data/{project_id}/versions/{version_id}/{file_name}")

    # curseforge | example: https://edge.forgecdn.net/files/3040/523/jei_1.12.2-4.16.1.301.jar
    @controller_router.get("/files/{fileid1}/{fileid2}/{file_name}")
    async def get_curseforge_file(fileid1: str, fileid2: str, file_name: str):
        fileid = int(f"{fileid1}{fileid2}")
        cache = await file_cdn_redis_async_engine.hget("file_cdn_curseforge", f'{fileid}/{file_name}')
        if cache:
            return RedirectResponse(url=cache)
        else:
            file: cfFile = await aio_mongo_engine.find_one(cfFile, query.and_(cfFile.id == fileid, cfFile.fileName == file_name))
            sha1 = file.hashes[0].value if file.hashes[0].algo == 1 else file.hashes[1].value
            if file:
                if file.file_cdn_cached:
                    url = f'{mcim_config.alist_endpoint}/curseforge/{sha1[:2]}/{sha1}'
                    cf_file_cdn_url_cache.send(url=url, key=f'{fileid}/{file_name}')
                    return RedirectResponse(url=url)
                else:
                    cf_file_cdn_cache_add_task.send(file)
            RedirectResponse(url=f"https://mediafilez.curseforge.com/files{fileid1}/{fileid2}/{file_name}")
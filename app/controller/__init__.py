from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from odmantic import query

from app.controller.v1 import v1_router
from app.database.mongodb import aio_mongo_engine
from app.models.database.curseforge import File as cfFile
from app.models.database.modrinth import File as mrFile
from app.config import MCIMConfig

mcim_config = MCIMConfig.load()

controller_router = APIRouter()

controller_router.include_router(v1_router, prefix="/v1")

# file cdn

if mcim_config.file_cdn:
    # modrinth | example: https://cdn.modrinth.com/data/AANobbMI/versions/IZskON6d/sodium-fabric-0.5.8%2Bmc1.20.6.jar
    # WARNING: 直接查 version_id 忽略 project_id
    # WARNING: 必须文件名一致
    @controller_router.get("/data/{project_id}/versions/{version_id}/{file_name}")
    async def get_modrinth_file(project_id: str, version_id: str, file_name: str):
        file: mrFile = await aio_mongo_engine.find_one(mrFile, query.and_(mrFile.version_id == version_id, mrFile.filename == file_name))
        if file:
            if file.file_cdn_cached:
                return RedirectResponse(url=f'{mcim_config.alist_endpoint}/modrinth/{file.hashes.sha1}')
        return RedirectResponse(url=f"https://cdn.modrinth.com/data/{project_id}/versions/{version_id}/{file_name}")

    # curseforge | example: https://edge.forgecdn.net/files/3040/523/jei_1.12.2-4.16.1.301.jar
    @controller_router.get("/files/{fileid1}/{fileid2}/{file_name}")
    async def get_curseforge_file(fileid1: str, fileid2: str, file_name: str):
        fileid = int(f"{fileid1}{fileid2}")
        file: cfFile = await aio_mongo_engine.find_one(cfFile, query.and_(cfFile.id == fileid, cfFile.fileName == file_name))
        if file:
            if file.file_cdn_cached:
                return RedirectResponse(url=f'{mcim_config.alist_endpoint}/curseforge/{file_name}')
        RedirectResponse(url=f"https://edge.curseforge.com/files{fileid1}/{fileid2}/{file_name}")
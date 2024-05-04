from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response
from typing import List, Optional, Union
from odmantic import query
import time

from app.sync.curseforge import sync_mod, sync_mutil_mods, sync_mutil_files, sync_file
from app.models.database.curseforge import Mod, File
from app.database.mongodb import aio_mongo_engine
from app.config.mcim import MCIMConfig


mcim_config = MCIMConfig.load()

API = mcim_config.curseforge_api
EXPIRE_STATUS_CODE = mcim_config.expire_status_code

mod_router = APIRouter(prefix="/mod", tags=["curseforge"])


@mod_router.get(
    "/{modId}",
    description="Curseforge Mod 信息",
    response_model=Mod,
)
async def curseforge_mod(modId: int):
    mod_model = await aio_mongo_engine.find_one(Mod, Mod.id == modId)
    if mod_model is None:
        # return RedirectResponse(url=f"{API}/v1/mods/{modId}")
        return Response(status_code=EXPIRE_STATUS_CODE)
    elif mod_model.sync_at.timestamp() + mcim_config.expire_second.Curseforge.mod < time.time():
        sync_mod.send(modId=modId)
    return JSONResponse(content=mod_model.model_dump())


# get mods
@mod_router.post(
    "/",
    description="Curseforge Mods 信息",
    response_model=List[Mod],
)
async def curseforge_mods(modIds: List[int], filterPcOnly: Optional[bool] = True):
    mod_models = await aio_mongo_engine.find(Mod, query.in_(Mod.id, modIds))
    if mod_models is None:
        return Response(status_code=EXPIRE_STATUS_CODE)
    elif len(mod_models) != len(modIds):
        sync_mutil_mods.send(modIds=modIds)
        return Response(status_code=EXPIRE_STATUS_CODE)
    content = []
    for model in mod_models:
        # expire
        if model.sync_at.timestamp() + mcim_config.expire_second.Curseforge.mod < time.time():
            sync_mod.send(modId=model.id)
        content.append(model.model_dump())
    return JSONResponse(content=content)


@mod_router.get(
    "/{modId}/files",
    description="Curseforge Mod 文件信息",
    response_model=List[File],
)
async def curseforge_mod_files(modId: int):
    mod_models = await aio_mongo_engine.find(File, File.modId == modId)
    if mod_models is None:
        sync_mod.send(modId=modId)
        return Response(status_code=EXPIRE_STATUS_CODE)
    return JSONResponse(content=[model.model_dump() for model in mod_models])


# get files
@mod_router.get(
    "/files",
    description="Curseforge Mod 文件信息",
    response_model=List[File],
)
async def curseforge_mod_files(fileids: List[int]):
    file_models = await aio_mongo_engine.find(File, query.in_(File.id, fileids))
    if not file_models:
        sync_mutil_files.send(fileIds=fileids)
        return Response(status_code=EXPIRE_STATUS_CODE)
    elif len(file_models) != len(fileids):
        sync_mutil_files.send(fileIds=fileids)
        return Response(status_code=EXPIRE_STATUS_CODE)
    content = []
    for model in file_models:
        # expire
        if model.sync_at.timestamp() + mcim_config.expire_second.Curseforge.file < time.time():
            sync_file.send(modId=model.modId, fileId=model.id)
        content.append(model.model_dump())
    return JSONResponse(content=content)


# get file
@mod_router.get(
    "/{modId}/files/{fileId}",
    description="Curseforge Mod 文件信息",
)
async def curseforge_mod_file(modid: int, fileid: int):
    model = await aio_mongo_engine.find_one(
        File, File.modId == modid, File.id == fileid
    )
    if model is None:
        sync_file.send(modId=modid, fileId=fileid)
        return Response(status_code=EXPIRE_STATUS_CODE)
    elif model.sync_at.timestamp() + mcim_config.expire_second.Curseforge.file < time.time():
        sync_file.send(modId=modid, fileId=fileid)
    return JSONResponse(content=model.model_dump())
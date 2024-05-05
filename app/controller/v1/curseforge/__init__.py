from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response
from typing import List, Optional, Union
from odmantic import query
import time
import json

from app.sync.curseforge import sync_mod, sync_mutil_mods, sync_mutil_files, sync_file, sync_fingerprints, sync_categories
from app.models.database.curseforge import Mod, File, Fingerprint
from app.models.response.curseforge import FingerprintResponse, Category
from app.database.mongodb import aio_mongo_engine
from app.database._redis import aio_redis_engine
from app.config.mcim import MCIMConfig

mcim_config = MCIMConfig.load()

curseforge_router = APIRouter(prefix="/curseforge", tags=["curseforge"])

EXPIRE_STATUS_CODE = mcim_config.expire_status_code
UNCACHE_STATUS_CODE = mcim_config.uncache_status_code

@curseforge_router.get("/")
async def get_curseforge():
    return {"message": "CurseForge"}


@curseforge_router.get(
    "/mods/{modId}",
    description="Curseforge Mod 信息",
    response_model=Mod,
)
async def curseforge_mod(modId: int):
    mod_model = await aio_mongo_engine.find_one(Mod, Mod.id == modId)
    if mod_model is None:
        return Response(status_code=UNCACHE_STATUS_CODE)
    elif mod_model.sync_at.timestamp() + mcim_config.expire_second.Curseforge.mod < time.time():
        sync_mod.send(modId=modId)
    return JSONResponse(content=mod_model.model_dump())


# get mods
@curseforge_router.post(
    "/mods",
    description="Curseforge Mods 信息",
    response_model=List[Mod],
)
async def curseforge_mods(modIds: List[int], filterPcOnly: Optional[bool] = True):
    mod_models = await aio_mongo_engine.find(Mod, query.in_(Mod.id, modIds))
    if mod_models is None:
        return Response(status_code=UNCACHE_STATUS_CODE)
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


@curseforge_router.get(
    "/mods/{modId}/files",
    description="Curseforge Mod 文件信息",
    response_model=List[File],
)
async def curseforge_mod_files(modId: int):
    mod_models = await aio_mongo_engine.find(File, File.modId == modId)
    if mod_models is None:
        sync_mod.send(modId=modId)
        return Response(status_code=UNCACHE_STATUS_CODE)
    return JSONResponse(content=[model.model_dump() for model in mod_models])


# get files
@curseforge_router.get(
    "/mods/files",
    description="Curseforge Mod 文件信息",
    response_model=List[File],
)
async def curseforge_mod_files(fileids: List[int]):
    file_models = await aio_mongo_engine.find(File, query.in_(File.id, fileids))
    if not file_models:
        sync_mutil_files.send(fileIds=fileids)
        return Response(status_code=UNCACHE_STATUS_CODE)
    elif len(file_models) != len(fileids):
        sync_mutil_files.send(fileIds=fileids)
        return Response(status_code=UNCACHE_STATUS_CODE)
    content = []
    for model in file_models:
        # expire
        if model.sync_at.timestamp() + mcim_config.expire_second.Curseforge.file < time.time():
            sync_file.send(modId=model.modId, fileId=model.id)
        content.append(model.model_dump())
    return JSONResponse(content=content)


# get file
@curseforge_router.get(
    "/mods/{modId}/files/{fileId}",
    description="Curseforge Mod 文件信息",
)
async def curseforge_mod_file(modid: int, fileid: int):
    model = await aio_mongo_engine.find_one(
        File, File.modId == modid, File.id == fileid
    )
    if model is None:
        sync_file.send(modId=modid, fileId=fileid)
        return Response(status_code=UNCACHE_STATUS_CODE)
    elif model.sync_at.timestamp() + mcim_config.expire_second.Curseforge.file < time.time():
        sync_file.send(modId=modid, fileId=fileid)
    return JSONResponse(content=model.model_dump())

@curseforge_router.post(
    "/fingerprints/",
    description="Curseforge Fingerprint 文件信息",
    response_model=FingerprintResponse,
)
async def curseforge_fingerprints(fingerprints: List[int]):
    fingerprints_models = await aio_mongo_engine.find(
        Fingerprint, query.in_(Fingerprint.id, fingerprints)
    )
    if fingerprints_models is None:
        sync_fingerprints.send(fingerprints=fingerprints)
        return Response(status_code=EXPIRE_STATUS_CODE)
    elif len(fingerprints_models) != len(fingerprints):
        sync_fingerprints.send(fingerprints=fingerprints)
        return Response(status_code=EXPIRE_STATUS_CODE)
    exactFingerprints = [fingerprint.id for fingerprint in fingerprints_models]
    unmatchedFingerprints = [
        fingerprint
        for fingerprint in fingerprints
        if fingerprint not in exactFingerprints
    ]
    return JSONResponse(
        content=FingerprintResponse(
            isCacheBuilt=True,
            exactFingerprints=exactFingerprints,
            exactMatches=fingerprints_models,
            unmatchedFingerprints=unmatchedFingerprints,
            installedFingerprints=[],
        ).model_dump()
    )

@curseforge_router.get(
    "/categories/",
    description="Curseforge Categories 信息",
    response_model=List[Category],
)
async def curseforge_categories():
    categories = await aio_redis_engine.hget("curseforge","categories")
    if categories is None:
        sync_categories.send()
        return Response(status_code=404)
    return JSONResponse(content=json.loads(categories))
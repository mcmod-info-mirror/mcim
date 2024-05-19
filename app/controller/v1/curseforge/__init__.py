from fastapi import APIRouter
from fastapi.responses import Response
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
from app.utils.response import TrustableResponse, UncachedResponse

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
    trustable: bool = True
    mod_model = await aio_mongo_engine.find_one(Mod, Mod.id == modId)
    if mod_model is None:
        return UncachedResponse()
    elif mod_model.sync_at.timestamp() + mcim_config.expire_second.curseforge.mod < time.time():
        sync_mod.send(modId=modId)
        trustable = False
    return TrustableResponse(content=mod_model.model_dump(), trustable=trustable)


# get mods
@curseforge_router.post(
    "/mods",
    description="Curseforge Mods 信息",
    response_model=List[Mod],
)
async def curseforge_mods(modIds: List[int], filterPcOnly: Optional[bool] = True):
    trustable: bool = True
    mod_models = await aio_mongo_engine.find(Mod, query.in_(Mod.id, modIds))
    if not mod_models:
        return UncachedResponse()
    elif len(mod_models) != len(modIds):
        sync_mutil_mods.send(modIds=modIds)
        trustable = False
    content = []
    expire_modid: List[int] = []
    for model in mod_models:
        # expire
        if model.sync_at.timestamp() + mcim_config.expire_second.curseforge.mod < time.time():
            expire_modid.append(model.id)
        content.append(model.model_dump())
    if expire_modid:
        trustable = False
        sync_mutil_mods.send(modIds=expire_modid)
    return TrustableResponse(content=content, trustable=trustable)


@curseforge_router.get(
    "/mods/{modId}/files",
    description="Curseforge Mod 文件信息",
    response_model=List[File],
)
async def curseforge_mod_files(modId: int):
    mod_models = await aio_mongo_engine.find(File, File.modId == modId)
    if not mod_models:
        sync_mod.send(modId=modId)
        return UncachedResponse()
    return TrustableResponse(content=[model.model_dump() for model in mod_models])


# get files
@curseforge_router.get(
    "/mods/files",
    description="Curseforge Mod 文件信息",
    response_model=List[File],
)
async def curseforge_mod_files(fileids: List[int]):
    trustable = True
    file_models = await aio_mongo_engine.find(File, query.in_(File.id, fileids))
    if not file_models:
        sync_mutil_files.send(fileIds=fileids)
        return UncachedResponse()
    elif len(file_models) != len(fileids):
        sync_mutil_files.send(fileIds=fileids)
        trustable = False
    content = []
    expire_fileid: List[int] = []
    for model in file_models:
        # expire
        if model.sync_at.timestamp() + mcim_config.expire_second.curseforge.file < time.time():
            expire_fileid.append(model.id)
        content.append(model.model_dump())
    if expire_fileid:
        sync_mutil_files.send(fileIds=expire_fileid)
        trustable = False
    return TrustableResponse(content=content, trustable=trustable)


# get file
@curseforge_router.get(
    "/mods/{modId}/files/{fileId}",
    description="Curseforge Mod 文件信息",
)
async def curseforge_mod_file(modid: int, fileid: int):
    trustable = True
    model = await aio_mongo_engine.find_one(
        File, File.modId == modid, File.id == fileid
    )
    if model is None:
        sync_file.send(modId=modid, fileId=fileid)
        return UncachedResponse()
    elif model.sync_at.timestamp() + mcim_config.expire_second.curseforge.file < time.time():
        sync_file.send(modId=modid, fileId=fileid)
        trustable = False
    return TrustableResponse(content=model.model_dump(), trustable=trustable)

@curseforge_router.post(
    "/fingerprints/",
    description="Curseforge Fingerprint 文件信息",
    response_model=FingerprintResponse,
)
async def curseforge_fingerprints(fingerprints: List[int]):
    """
    未找到所有 fingerprint 会视为不可信，因为不存在的 fingerprint 会被记录
    """
    trustable = True
    fingerprints_models = await aio_mongo_engine.find(
        Fingerprint, query.in_(Fingerprint.id, fingerprints)
    )
    if not fingerprints_models:
        sync_fingerprints.send(fingerprints=fingerprints)
        trustable = False
        return TrustableResponse(
            content=FingerprintResponse(unmatchedFingerprints=fingerprints).model_dump(),
            trustable=trustable
            )
    elif len(fingerprints_models) != len(fingerprints):
        sync_fingerprints.send(fingerprints=fingerprints)
        trustable = False
    exactFingerprints = [fingerprint.id for fingerprint in fingerprints_models]
    unmatchedFingerprints = [
        fingerprint
        for fingerprint in fingerprints
        if fingerprint not in exactFingerprints
    ]
    return TrustableResponse(
        content=FingerprintResponse(
            isCacheBuilt=True,
            exactFingerprints=exactFingerprints,
            exactMatches=fingerprints_models,
            unmatchedFingerprints=unmatchedFingerprints,
            installedFingerprints=[],
        ).model_dump(),
        trustable=trustable,
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
        return UncachedResponse()
    return TrustableResponse(content=json.loads(categories))
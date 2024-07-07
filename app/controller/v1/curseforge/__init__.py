from fastapi import APIRouter
from fastapi.responses import Response
from typing import List, Optional, Union
from pydantic import BaseModel
from odmantic import query
from enum import Enum
import time
import json

from app.sync.curseforge import (
    sync_mod,
    sync_mutil_mods,
    sync_mutil_files,
    sync_file,
    sync_fingerprints,
    sync_categories,
)
from app.models.database.curseforge import Mod, File, Fingerprint
from app.models.response.curseforge import (
    FingerprintResponse,
    Category,
    CurseforgeBaseResponse,
)
from app.database.mongodb import aio_mongo_engine
from app.database._redis import aio_redis_engine
from app.config.mcim import MCIMConfig
from app.utils.response import TrustableResponse, UncachedResponse
from app.utils.network import request_sync
from app.utils.loger import log
from app.utils.response_cache import cache

mcim_config = MCIMConfig.load()

API = mcim_config.curseforge_api

x_api_key = mcim_config.curseforge_api_key

curseforge_router = APIRouter(prefix="/curseforge", tags=["curseforge"])

EXPIRE_STATUS_CODE = mcim_config.expire_status_code
UNCACHE_STATUS_CODE = mcim_config.uncache_status_code


@curseforge_router.get("/")
@cache(never_expire=True)
async def get_curseforge():
    return {"message": "CurseForge"}


"""
ModsSearchSortField
1=Featured
2=Popularity
3=LastUpdated
4=Name
5=Author
6=TotalDownloads
7=Category
8=GameVersion
9=EarlyAccess
10=FeaturedReleased
11=ReleasedDate
12=Rating
"""


class ModsSearchSortField(int, Enum):
    Featured = 1
    Popularity = 2
    LastUpdated = 3
    Name = 4
    Author = 5
    TotalDownloads = 6
    Category = 7
    GameVersion = 8
    EarlyAccess = 9
    FeaturedReleased = 10
    ReleasedDate = 11
    Rating = 12


"""
ModLoaderType
0=Any
1=Forge
2=Cauldron
3=LiteLoader
4=Fabric
5=Quilt
6=NeoForge
"""


class ModLoaderType(int, Enum):
    Any = 0
    Forge = 1
    Cauldron = 2
    LiteLoader = 3
    Fabric = 4
    Quilt = 5
    NeoForge = 6


@curseforge_router.get(
    "/mods/search",
    description="Curseforge Category 信息",
    # response_model TODO
)
@cache(expire=mcim_config.expire_second.curseforge.search)
async def curseforge_search(
    gameId: int = 432,
    classId: Optional[int] = None,
    categoryId: Optional[int] = None,
    categoryIds: Optional[str] = None,
    gameVersion: Optional[str] = None,
    gameVersions: Optional[str] = None,
    searchFilter: Optional[str] = None,
    sortField: Optional[ModsSearchSortField] = None,
    sortOrder: Optional[str] = None,
    modLoaderType: Optional[ModLoaderType] = None,
    modLoaderTypes: Optional[str] = None,
    gameVersionTypeId: Optional[int] = None,
    authorId: Optional[int] = None,
    primaryAuthorId: Optional[int] = None,
    slug: Optional[str] = None,
    index: Optional[int] = None,
    pageSize: Optional[int] = 50,
):
    params = {
        "gameId": gameId,
        "classId": classId,
        "categoryId": categoryId,
        "categoryIds": categoryIds,
        "gameVersion": gameVersion,
        "gameVersions": gameVersions,
        "searchFilter": searchFilter,
        "sortField": sortField.value if not sortField is None else None,
        "sortOrder": sortOrder,
        "modLoaderType": modLoaderType.value if not modLoaderType is None else None,
        "modLoaderTypes": modLoaderTypes,
        "gameVersionTypeId": gameVersionTypeId,
        "authorId": authorId,
        "primaryAuthorId": primaryAuthorId,
        "slug": slug,
        "index": index,
        "pageSize": pageSize,
    }
    res = request_sync(
        f"{API}/v1/mods/search", params=params, headers={"x-api-key": x_api_key}
    ).json()
    return TrustableResponse(content=res)


@curseforge_router.get(
    "/mods/{modId}",
    description="Curseforge Mod 信息",
    response_model=Mod,
)
@cache(expire=mcim_config.expire_second.curseforge.mod)
async def curseforge_mod(modId: int):
    trustable: bool = True
    mod_model = await aio_mongo_engine.find_one(Mod, Mod.id == modId)
    if mod_model is None:
        sync_mod.send(modId=modId)
        log.debug(f"modId: {modId} not found, send sync task.")
        return UncachedResponse()
    elif (
        mod_model.sync_at.timestamp() + mcim_config.expire_second.curseforge.mod
        < time.time()
    ):
        sync_mod.send(modId=modId)
        log.debug(f"modId: {modId} expired, send sync task.")
        trustable = False
    return TrustableResponse(
        content=CurseforgeBaseResponse(data=mod_model).model_dump(), trustable=trustable
    )


class modIds_item(BaseModel):
    modIds: List[int]
    filterPcOnly: Optional[bool] = True


# get mods
@curseforge_router.post(
    "/mods",
    description="Curseforge Mods 信息",
    response_model=List[Mod],
)
@cache(expire=mcim_config.expire_second.curseforge.mod)
async def curseforge_mods(item: modIds_item):
    trustable: bool = True
    mod_models = await aio_mongo_engine.find(Mod, query.in_(Mod.id, item.modIds))
    mod_model_count = len(mod_models)
    item_count = len(item.modIds)
    if not mod_models:
        sync_mutil_mods.send(modIds=item.modIds)
        log.debug(f"modIds: {item.modIds} not found, send sync task.")
        return UncachedResponse()
    elif mod_model_count != item_count:
        sync_mutil_mods.send(modIds=item.modIds)
        log.debug(f"modIds: {item.modIds} {mod_model_count}/{item_count} not found, send sync task.")
        trustable = False
    content = []
    expire_modid: List[int] = []
    for model in mod_models:
        # expire
        if (
            model.sync_at.timestamp() + mcim_config.expire_second.curseforge.mod
            < time.time()
        ):
            expire_modid.append(model.id)
        content.append(model.model_dump())
    if expire_modid:
        trustable = False
        sync_mutil_mods.send(modIds=expire_modid)
        log.debug(f"modIds: {expire_modid} expired, send sync task.")
    return TrustableResponse(
        content=CurseforgeBaseResponse(data=content).model_dump(), trustable=trustable
    )


@curseforge_router.get(
    "/mods/{modId}/files",
    description="Curseforge Mod 文件信息",
    response_model=List[File],
)
@cache(expire=mcim_config.expire_second.curseforge.file)
async def curseforge_mod_files(modId: int):
    mod_models = await aio_mongo_engine.find(File, File.modId == modId)
    if not mod_models:
        sync_mod.send(modId=modId)
        log.debug(f"modId: {modId} not found, send sync task.")
        return UncachedResponse()
    return TrustableResponse(
        content=CurseforgeBaseResponse(
            data=[model for model in mod_models]
        ).model_dump()
    )


class fileIds_item(BaseModel):
    fileIds: List[int]


# get files
@curseforge_router.post(
    "/mods/files",
    description="Curseforge Mod 文件信息",
    response_model=List[File],
)
@cache(expire=mcim_config.expire_second.curseforge.file)
async def curseforge_mod_files(item: fileIds_item):
    trustable = True
    file_models = await aio_mongo_engine.find(File, query.in_(File.id, item.fileIds))
    if not file_models:
        sync_mutil_files.send(fileIds=item.fileIds)
        return UncachedResponse()
    elif len(file_models) != len(item.fileIds):
        sync_mutil_files.send(fileIds=item.fileIds)
        trustable = False
    content = []
    expire_fileid: List[int] = []
    for model in file_models:
        # expire
        if (
            model.sync_at.timestamp() + mcim_config.expire_second.curseforge.file
            < time.time()
        ):
            expire_fileid.append(model.id)
        content.append(model.model_dump())
    if expire_fileid:
        sync_mutil_files.send(fileIds=expire_fileid)
        
        trustable = False
    return TrustableResponse(
        content=CurseforgeBaseResponse(data=content).model_dump(), trustable=trustable
    )


# get file
@curseforge_router.get(
    "/mods/{modId}/files/{fileId}",
    description="Curseforge Mod 文件信息",
)
@cache(expire=mcim_config.expire_second.curseforge.file)
async def curseforge_mod_file(modId: int, fileId: int):
    trustable = True
    model = await aio_mongo_engine.find_one(
        File, File.modId == modId, File.id == fileId
    )
    if model is None:
        sync_file.send(modId=modId, fileId=fileId)
        return UncachedResponse()
    elif (
        model.sync_at.timestamp() + mcim_config.expire_second.curseforge.file
        < time.time()
    ):
        sync_file.send(modId=modId, fileId=fileId)
        trustable = False
    return TrustableResponse(
        content=CurseforgeBaseResponse(data=model).model_dump(), trustable=trustable
    )


class fingerprints_item(BaseModel):
    fingerprints: List[int]


@curseforge_router.post(
    "/fingerprints",
    description="Curseforge Fingerprint 文件信息",
    response_model=FingerprintResponse,
)
@cache(expire=mcim_config.expire_second.curseforge.fingerprint)
async def curseforge_fingerprints(item: fingerprints_item):
    """
    未找到所有 fingerprint 会视为不可信，因为不存在的 fingerprint 会被记录
    """
    trustable = True
    fingerprints_models = await aio_mongo_engine.find(
        Fingerprint, query.in_(Fingerprint.id, item.fingerprints)
    )
    if not fingerprints_models:
        sync_fingerprints.send(fingerprints=item.fingerprints)
        trustable = False
        return TrustableResponse(
            content=CurseforgeBaseResponse(
                data=FingerprintResponse(unmatchedFingerprints=item.fingerprints)
            ).model_dump(),
            trustable=trustable,
        )
    elif len(fingerprints_models) != len(item.fingerprints):
        sync_fingerprints.send(fingerprints=item.fingerprints)
        trustable = False
    exactFingerprints = [fingerprint.id for fingerprint in fingerprints_models]
    unmatchedFingerprints = [
        fingerprint
        for fingerprint in item.fingerprints
        if fingerprint not in exactFingerprints
    ]
    return TrustableResponse(
        content=CurseforgeBaseResponse(data=
            FingerprintResponse(
                isCacheBuilt=True,
                exactFingerprints=exactFingerprints,
                exactMatches=fingerprints_models,
                unmatchedFingerprints=unmatchedFingerprints,
                installedFingerprints=[],
            )
        ).model_dump(),
        trustable=trustable,
    )


@curseforge_router.get(
    "/categories",
    description="Curseforge Categories 信息",
    response_model=List[Category],
)
@cache(expire=mcim_config.expire_second.curseforge.categories)
async def curseforge_categories():
    categories = await aio_redis_engine.hget("curseforge", "categories")
    if categories is None:
        sync_categories.send()
        return UncachedResponse()
    return TrustableResponse(content=CurseforgeBaseResponse(data=json.loads(categories)).model_dump())

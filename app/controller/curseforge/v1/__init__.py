from fastapi import APIRouter, Request, BackgroundTasks
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
    CurseforgePageBaseResponse,
    Pagination,
)
from app.config.mcim import MCIMConfig
from app.utils.response import TrustableResponse, UncachedResponse, BaseResponse
from app.utils.network import request_sync, request
from app.utils.loger import log
from app.utils.response_cache import cache

from app.database.mongodb import aio_mongo_engine

mcim_config = MCIMConfig.load()

API = mcim_config.curseforge_api

x_api_key = mcim_config.curseforge_api_key

v1_router = APIRouter(prefix="/v1", tags=["curseforge"])

EXPIRE_STATUS_CODE = mcim_config.expire_status_code
UNCACHE_STATUS_CODE = mcim_config.uncache_status_code
SEARCH_TIMEOUT = 3

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


# background task
async def check_search_result(res: dict):
    modids = set()
    for mod in res["data"]:
        modids.add(mod["id"])

    # check if modids in db
    if modids:
        mod_models: List[Mod] = await aio_mongo_engine.find(
            Mod, query.in_(Mod.id, list(modids))
        )

        not_found_modids = modids - set([mod.id for mod in mod_models])

        if not_found_modids:
            sync_mutil_mods.send(modIds=list(not_found_modids))
            log.debug(f"modIds: {not_found_modids} not found, send sync task.")


@v1_router.get(
    "/mods/search",
    description="Curseforge Category 信息",
    # response_model TODO
)
@cache(expire=mcim_config.expire_second.curseforge.search)
async def curseforge_search(
    background_tasks: BackgroundTasks,
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
    res = (
        await request(
            f"{API}/v1/mods/search",
            params=params,
            headers={"x-api-key": x_api_key},
            timeout=SEARCH_TIMEOUT,
        )
    ).json()
    background_tasks.add_task(check_search_result, res)
    return TrustableResponse(content=res)


@v1_router.get(
    "/mods/{modId}",
    description="Curseforge Mod 信息",
    response_model=Mod,
)
@cache(expire=mcim_config.expire_second.curseforge.mod)
async def curseforge_mod(modId: int, request: Request):
    if request.state.force_sync:
        sync_mod.send(modId=modId)
        log.debug(f"modId: {modId} force sync.")
        return UncachedResponse()
    trustable: bool = True
    mod_model: Optional[Mod] = await request.app.state.aio_mongo_engine.find_one(
        Mod, Mod.id == modId
    )
    if mod_model is None:
        sync_mod.send(modId=modId)
        log.debug(f"modId: {modId} not found, send sync task.")
        return UncachedResponse()
    elif (
        mod_model.sync_at.timestamp() + mcim_config.expire_second.curseforge.mod
        < time.time()
    ):
        sync_mod.send(modId=modId)
        log.debug(
            f'modId: {modId} expired, send sync task, sync_at {mod_model.sync_at.strftime("%Y-%m-%dT%H:%M:%SZ")}.'
        )
        trustable = False
    return TrustableResponse(
        content=CurseforgeBaseResponse(data=mod_model).model_dump(), trustable=trustable
    )


class modIds_item(BaseModel):
    modIds: List[int]
    filterPcOnly: Optional[bool] = True


# get mods
@v1_router.post(
    "/mods",
    description="Curseforge Mods 信息",
    response_model=List[Mod],
)
# @cache(expire=mcim_config.expire_second.curseforge.mod)
async def curseforge_mods(item: modIds_item, request: Request):
    if request.state.force_sync:
        sync_mutil_mods.send(modIds=item.modIds)
        log.debug(f"modIds: {item.modIds} force sync.")
        # return UncachedResponse()
        return TrustableResponse(
            content=CurseforgeBaseResponse(data=[]).model_dump(),
            trustable=False,
        )
    trustable: bool = True
    mod_models: Optional[List[Mod]] = await request.app.state.aio_mongo_engine.find(
        Mod, query.in_(Mod.id, item.modIds)
    )
    mod_model_count = len(mod_models)
    item_count = len(item.modIds)
    if not mod_models:
        sync_mutil_mods.send(modIds=item.modIds)
        log.debug(f"modIds: {item.modIds} not found, send sync task.")
        # return UncachedResponse()
        return TrustableResponse(
            content=CurseforgeBaseResponse(data=[]).model_dump(),
            trustable=False,
        )
    elif mod_model_count != item_count:
        sync_mutil_mods.send(modIds=item.modIds)
        log.debug(
            f"modIds: {item.modIds} {mod_model_count}/{item_count} not found, send sync task."
        )
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
            log.debug(
                f'modId: {model.id} expired, send sync task, sync_at {model.sync_at.strftime("%Y-%m-%dT%H:%M:%SZ")}.'
            )
        content.append(model.model_dump())
    if expire_modid:
        trustable = False
        sync_mutil_mods.send(modIds=expire_modid)
        log.debug(f"modIds: {expire_modid} expired, send sync task.")
    return TrustableResponse(
        content=CurseforgeBaseResponse(data=content).model_dump(),
        trustable=trustable,
    )


"""
Parameters
Name	In	Type	Required	Description
modId	path	integer(int32)	true	The mod id the files belong to
gameVersion	query	string	false	Filter by game version string
modLoaderType	query	ModLoaderType	false	ModLoaderType enumeration
gameVersionTypeId	query	integer(int32)	false	Filter only files that are tagged with versions of the given gameVersionTypeId
index	query	integer(int32)	false	A zero based index of the first item to include in the response, the limit is: (index + pageSize <= 10,000).
pageSize	query	integer(int32)	false	The number of items to include in the response, the default/maximum value is 50.
"""

"""
Possible enum values:
0=Any
1=Forge
2=Cauldron
3=LiteLoader
4=Fabric
5=Quilt
6=NeoForge
"""


def convert_modloadertype(type_id: int) -> Optional[str]:
    match type_id:
        case 1:
            return "Forge"
        case 2:
            return "Cauldron"
        case 3:
            return "LiteLoader"
        case 4:
            return "Fabric"
        case 5:
            return "Quilt"
        case 6:
            return "NeoForge"
        case _:
            return None


@v1_router.get(
    "/mods/{modId}/files",
    description="Curseforge Mod 文件信息",
    response_model=List[File],
)
@cache(expire=mcim_config.expire_second.curseforge.file)
# async def curseforge_mod_files(
#     request: Request,
#     modId: int,
#     gameVersion: Optional[str] = None,
#     modLoaderType: Optional[ModLoaderType] = None,
#     gameVersionTypeId: Optional[int] = None,
#     index: Optional[int] = None,
#     pageSize: Optional[int] = 50,
# ):
#     if request.state.force_sync:
#         sync_mod.send(modId=modId)
#         log.debug(f"modId: {modId} force sync.")
#         return UncachedResponse()
#     mod_models: Optional[List[File]] = await request.app.state.aio_mongo_engine.find(
#         File, File.modId == modId, limit=pageSize, skip=index
#     )
#     if not mod_models:
#         sync_mod.send(modId=modId)
#         log.debug(f"modId: {modId} not found, send sync task.")
#         return UncachedResponse()
#     return TrustableResponse(
#         content=CurseforgePageBaseResponse(
#             data=[model for model in mod_models],
#             pagination=Pagination(index=index, pageSize=pageSize, resultCount=len(mod_models)),
#         ).model_dump()
#     )
async def curseforge_mod_files(
    request: Request,
    modId: int,
    gameVersion: Optional[str] = None,
    modLoaderType: Optional[int] = None,
    # gameVersionTypeId: Optional[int] = None,
    index: Optional[int] = 0,
    pageSize: Optional[int] = 50,
):
    if request.state.force_sync:
        sync_mod.send(modId=modId)
        log.debug(f"modId: {modId} force sync.")
        return UncachedResponse()

    # 定义聚合管道
    match_conditions = {"modId": modId}
    gameVersionFilter = []
    if gameVersion:
        gameVersionFilter.append(gameVersion)
    if modLoaderType:
        modLoaderType = convert_modloadertype(modLoaderType)
        if modLoaderType:
            gameVersionFilter.append(modLoaderType)
    if len(gameVersionFilter) != 0:
        match_conditions["gameVersions"] = {"$all": gameVersionFilter}

    pipeline = [
        {"$match": match_conditions},
        {
            "$facet": {
                "resultCount": [
                    {"$count": "count"},
                ],
                "totalCount": [
                    {"$match": {"modId": modId}},
                    {"$count": "count"},
                ],
                "documents": [
                    {"$skip": index if index else 0},
                    {"$limit": pageSize},
                ],
            }
        },
    ]

    # 执行聚合查询
    files_collection = request.app.state.aio_mongo_engine.get_collection(File)
    result = await files_collection.aggregate(pipeline).to_list(length=None)

    if not result or not result[0]["documents"]:
        sync_mod.send(modId=modId)
        log.debug(f"modId: {modId} not found, send sync task.")
        return UncachedResponse()

    total_count = result[0]["totalCount"][0]["count"]
    result_count = result[0]["resultCount"][0]["count"]
    documents = result[0]["documents"]

    doc_results = []
    for doc in documents:
        _id = doc.pop("_id")
        doc["id"] = _id
        doc_results.append(doc)

    return TrustableResponse(
        content=CurseforgePageBaseResponse(
            data=doc_results,
            pagination=Pagination(
                index=index,
                pageSize=pageSize,
                resultCount=result_count,
                totalCount=total_count,
            ),
        )
    )


class fileIds_item(BaseModel):
    fileIds: List[int]


# get files
@v1_router.post(
    "/mods/files",
    description="Curseforge Mod 文件信息",
    response_model=CurseforgeBaseResponse,
)
# @cache(expire=mcim_config.expire_second.curseforge.file)
async def curseforge_files(item: fileIds_item, request: Request):
    if request.state.force_sync:
        sync_mutil_files.send(fileIds=item.fileIds)
        log.debug(f"fileIds: {item.fileIds} force sync.")
        return UncachedResponse()
    trustable = True
    file_models: Optional[List[File]] = await request.app.state.aio_mongo_engine.find(
        File, query.in_(File.id, item.fileIds)
    )
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
            log.debug(
                f'fileId: {model.id} expired, send sync task, sync_at {model.sync_at.strftime("%Y-%m-%dT%H:%M:%SZ")}.'
            )
        content.append(model.model_dump())
    if expire_fileid:
        sync_mutil_files.send(fileIds=expire_fileid)
        trustable = False
    return TrustableResponse(
        content=CurseforgeBaseResponse(data=content).model_dump(),
        trustable=trustable,
    )


# get file
@v1_router.get(
    "/mods/{modId}/files/{fileId}",
    description="Curseforge Mod 文件信息",
)
@cache(expire=mcim_config.expire_second.curseforge.file)
async def curseforge_mod_file(modId: int, fileId: int, request: Request):
    if request.state.force_sync:
        sync_file.send(modId=modId, fileId=fileId)
        log.debug(f"modId: {modId} fileId: {fileId} force sync.")
        return UncachedResponse()
    trustable = True
    model: Optional[File] = await request.app.state.aio_mongo_engine.find_one(
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
        log.debug(
            f'modId: {modId} fileId: {fileId} expired, send sync task, sync_at {model.sync_at.strftime("%Y-%m-%dT%H:%M:%SZ")}.'
        )
        trustable = False
    return TrustableResponse(
        content=CurseforgeBaseResponse(data=model).model_dump(),
        trustable=trustable,
    )


@v1_router.get(
    "/mods/{modId}/files/{fileId}/download-url",
    description="Curseforge Mod 文件下载地址",
)
# @cache(expire=mcim_config.expire_second.curseforge.file)
async def curseforge_mod_file_download_url(modId: int, fileId: int, request: Request):
    model: Optional[File] = await request.app.state.aio_mongo_engine.find_one(
        File, File.modId == modId, File.id == fileId
    )
    if model is None:
        sync_file.send(modId=modId, fileId=fileId)
        return UncachedResponse()
    return TrustableResponse(
        content=CurseforgeBaseResponse(data=model.downloadUrl).model_dump(),
        trustable=True,
    )


class fingerprints_item(BaseModel):
    fingerprints: List[int]


@v1_router.post(
    "/fingerprints",
    description="Curseforge Fingerprint 文件信息",
    response_model=FingerprintResponse,
)
# @cache(expire=mcim_config.expire_second.curseforge.fingerprint)
async def curseforge_fingerprints(item: fingerprints_item, request: Request):
    """
    未找到所有 fingerprint 会视为不可信，因为不存在的 fingerprint 会被记录
    """
    if request.state.force_sync:
        sync_fingerprints.send(fingerprints=item.fingerprints)
        log.debug(f"fingerprints: {item.fingerprints} force sync.")
        return UncachedResponse()
    trustable = True
    fingerprints_models: List[Fingerprint] = (
        await request.app.state.aio_mongo_engine.find(
            Fingerprint, query.in_(Fingerprint.id, item.fingerprints)
        )
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
    exactFingerprints = []
    result_fingerprints_models = []
    for fingerprint_model in fingerprints_models:
        # fingerprint_model.id = fingerprint_model.file.id
        # 神奇 primary_key 不能修改，没辙只能这样了
        fingerprint = fingerprint_model.model_dump()
        fingerprint["id"] = fingerprint_model.file.id
        result_fingerprints_models.append(fingerprint)
        exactFingerprints.append(fingerprint_model.id)
    # exactFingerprints = [fingerprint.id for fingerprint in fingerprints_models]
    unmatchedFingerprints = [
        fingerprint
        for fingerprint in item.fingerprints
        if fingerprint not in exactFingerprints
    ]
    return TrustableResponse(
        content=CurseforgeBaseResponse(
            data=FingerprintResponse(
                isCacheBuilt=True,
                exactFingerprints=exactFingerprints,
                exactMatches=result_fingerprints_models,
                unmatchedFingerprints=unmatchedFingerprints,
                installedFingerprints=[],
            ).model_dump()
        ),
        trustable=trustable,
    )


@v1_router.post(
    "/fingerprints/432",
    description="Curseforge Fingerprint 文件信息",
    response_model=FingerprintResponse,
)
# @cache(expire=mcim_config.expire_second.curseforge.fingerprint)
async def curseforge_fingerprints_432(item: fingerprints_item, request: Request):
    """
    未找到所有 fingerprint 会视为不可信，因为不存在的 fingerprint 会被记录
    """
    if request.state.force_sync:
        sync_fingerprints.send(fingerprints=item.fingerprints)
        log.debug(f"fingerprints: {item.fingerprints} force sync.")
        return UncachedResponse()
    trustable = True
    fingerprints_models: List[Fingerprint] = (
        await request.app.state.aio_mongo_engine.find(
            Fingerprint, query.in_(Fingerprint.id, item.fingerprints)
        )
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
    exactFingerprints = []
    result_fingerprints_models = []
    for fingerprint_model in fingerprints_models:
        # fingerprint_model.id = fingerprint_model.file.id
        # 神奇 primary_key 不能修改，没辙只能这样了
        fingerprint = fingerprint_model.model_dump()
        fingerprint["id"] = fingerprint_model.file.id
        result_fingerprints_models.append(fingerprint)
        exactFingerprints.append(fingerprint_model.id)
    unmatchedFingerprints = [
        fingerprint
        for fingerprint in item.fingerprints
        if fingerprint not in exactFingerprints
    ]
    return TrustableResponse(
        content=CurseforgeBaseResponse(
            data=FingerprintResponse(
                isCacheBuilt=True,
                exactFingerprints=exactFingerprints,
                exactMatches=result_fingerprints_models,
                unmatchedFingerprints=unmatchedFingerprints,
                installedFingerprints=[],
            ).model_dump()
        ),
        trustable=trustable,
    )


@v1_router.get(
    "/categories",
    description="Curseforge Categories 信息",
    response_model=List[Category],
)
@cache(expire=mcim_config.expire_second.curseforge.categories)
async def curseforge_categories(request: Request):
    if request.state.force_sync:
        sync_categories.send()
        log.debug("categories force sync.")
        return UncachedResponse()
    categories = await request.app.state.aio_redis_engine.hget(
        "curseforge", "categories"
    )
    if categories is None:
        sync_categories.send()
        return UncachedResponse()
    return TrustableResponse(
        content=CurseforgeBaseResponse(data=json.loads(categories)).model_dump()
    )

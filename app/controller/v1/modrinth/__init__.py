from fastapi import APIRouter, Query, Path, Request
from fastapi.responses import Response
from typing_extensions import Annotated
from typing import List, Optional, Union
from enum import Enum
from pydantic import BaseModel
from odmantic import query
import json
import time
from datetime import datetime

from app.sync import *
from app.models.database.modrinth import Project, Version, File
from app.sync.modrinth import (
    sync_project,
    sync_version,
    sync_multi_projects,
    sync_multi_projects,
    sync_multi_versions,
    sync_hash,
    sync_multi_hashes,
    sync_tags,
)
from app.config.mcim import MCIMConfig
from app.utils.response import TrustableResponse, UncachedResponse
from app.utils.network import request_sync
from app.utils.loger import log
from app.utils.response_cache import cache

mcim_config = MCIMConfig.load()

API = mcim_config.modrinth_api

EXPIRE_STATUS_CODE = mcim_config.expire_status_code
UNCACHE_STATUS_CODE = mcim_config.uncache_status_code

modrinth_router = APIRouter(prefix="/modrinth", tags=["modrinth"])


@modrinth_router.get("/")
@cache(never_expire=True)
async def get_curseforge():
    return {"message": "Modrinth"}


@modrinth_router.get(
    "/project/{idslug}",
    description="Modrinth Project 信息",
    response_model=Project,
)
@cache(expire=mcim_config.expire_second.modrinth.project)
async def modrinth_project(idslug: str, request: Request):
    trustable = True
    model = await request.app.state.aio_mongo_engine.find_one(
        Project, query.or_(Project.id == idslug, Project.slug == idslug)
    )
    if model is None:
        sync_project.send(idslug)
        log.debug(f"Project {idslug} not found, send sync task.")
        return UncachedResponse()
    elif (
        model.sync_at.timestamp() + mcim_config.expire_second.modrinth.project
        < time.time()
    ):
        sync_project.send(idslug)
        log.debug(f"Project {idslug} expire, send sync task.")
        trustable = False
    return TrustableResponse(content=model.model_dump(), trustable=trustable)


@modrinth_router.get(
    "/projects",
    description="Modrinth Projects 信息",
    response_model=List[Project],
)
@cache(expire=mcim_config.expire_second.modrinth.project)
async def modrinth_projects(ids: str, request: Request):
    ids_list = json.loads(ids)
    trustable = True
    # id or slug
    models = await request.app.state.aio_mongo_engine.find(
        Project,
        query.or_(query.in_(Project.id, ids_list), query.in_(Project.slug, ids_list)),
    )
    models_count = len(models)
    ids_count = len(ids_list)
    if not models:
        sync_multi_projects.send(project_ids=ids_list)
        log.debug(f"Projects {ids_list} not found, send sync task.")
        return UncachedResponse()
    elif models_count != ids_count:
        sync_multi_projects.send(project_ids=ids_list)
        log.debug(
            f"Projects {ids_list} {models_count}/{ids_count} not completely found, send sync task."
        )
        trustable = False
    # check expire
    # TODO: 直接根据日期查询，不在后端对比
    expire_project_ids = []
    for model in models:
        if (
            model.sync_at.timestamp() + mcim_config.expire_second.modrinth.project
            < time.time()
        ):
            expire_project_ids.append(model.id)
    if expire_project_ids:
        sync_multi_projects.send(project_ids=expire_project_ids)
        log.debug(f"Projects {expire_project_ids} expire, send sync task.")
        trustable = False
    return TrustableResponse(
        content=[model.model_dump() for model in models], trustable=trustable
    )


@modrinth_router.get(
    "/project/{idslug}/version",
    description="Modrinth Projects 全部版本信息",
    response_model=List[Project],
)
@cache(expire=mcim_config.expire_second.modrinth.version)
async def modrinth_project_versions(idslug: str, request: Request):
    trustable = True
    model = await request.app.state.aio_mongo_engine.find(
        Version, query.or_(Version.project_id == idslug, Version.slug == idslug)
    )
    if not model:
        sync_project.send(idslug)
        log.debug(f"Project {idslug} not found, send sync task.")
        return UncachedResponse()
    for version in model:
        if (
            version.sync_at.timestamp() + mcim_config.expire_second.modrinth.version
            < time.time()
        ):
            sync_project.send(idslug)
            log.debug(f"Project {idslug} expire, send sync task.")
            trustable = False
            break
    return TrustableResponse(
        content=[version.model_dump() for version in model], trustable=trustable
    )


class SearchIndex(str, Enum):
    relevance = "relevance"
    downloads = "downloads"
    follows = "follows"
    newest = "newest"
    updated = "updated"


@modrinth_router.get(
    "/search",
    description="Modrinth Projects 搜索",
    # response_model=List[Project],
)
@cache(expire=mcim_config.expire_second.modrinth.search)
async def modrinth_search_projects(
    query: Optional[str] = None,
    facets: Optional[str] = None,
    offset: Optional[int] = 0,
    limit: Optional[int] = 10,
    index: Optional[SearchIndex] = SearchIndex.relevance,
):
    # TODO: Search
    res = request_sync(
        f"{API}/search",
        params={
            "query": query,
            "facets": facets,
            "offset": offset,
            "limit": limit,
            "index": index.value,
        },
    ).json()
    return TrustableResponse(content=res)


@modrinth_router.get(
    "/version/{id}",
    description="Modrinth Version 信息",
    response_model=Version,
)
@cache(expire=mcim_config.expire_second.modrinth.version)
async def modrinth_version(
    version_id: Annotated[str, Path(alias="id")], request: Request
):
    trustable = True
    model = await request.app.state.aio_mongo_engine.find_one(
        # Version, query.or_(Version.id == version_id, Version.slug == version_id)
        Version,
        Version.id == version_id,
    )
    if model is None:
        sync_version.send(version_id=version_id)
        log.debug(f"Version {version_id} not found, send sync task.")
        return UncachedResponse()
    elif (
        model.sync_at.timestamp() + mcim_config.expire_second.modrinth.version
        < time.time()
    ):
        sync_version.send(version_id=version_id)
        log.debug(f"Version {version_id} expire, send sync task.")
        # return Response(status_code=EXPIRE_STATUS_CODE)
        trustable = False
    return TrustableResponse(content=model.model_dump(), trustable=trustable)


@modrinth_router.get(
    "/versions",
    description="Modrinth Versions 信息",
    response_model=List[Version],
)
@cache(expire=mcim_config.expire_second.modrinth.version)
async def modrinth_versions(ids: str, request: Request):
    trustable = True
    ids_list = json.loads(ids)
    models = await request.app.state.aio_mongo_engine.find(
        Version, query.in_(Version.id, ids_list)
    )
    models_count = len(models)
    ids_count = len(ids_list)
    if not models:
        sync_multi_versions.send(ids_list=ids_list)
        log.debug(f"Versions {ids_list} not found, send sync task.")
        return UncachedResponse()
    elif models_count != ids_count:
        sync_multi_versions.send(ids_list=ids_list)
        log.debug(
            f"Versions {ids_list} {models_count}/{ids_count} not completely found, send sync task."
        )
        trustable = False
    expire_version_ids = []
    for model in models:
        if (
            model.sync_at.timestamp() + mcim_config.expire_second.modrinth.version
            < time.time()
        ):
            expire_version_ids.append(model.id)
    if expire_version_ids:
        sync_multi_versions.send(ids_list=expire_version_ids)
        log.debug(f"Versions {expire_version_ids} expire, send sync task.")
        trustable = False
    return TrustableResponse(
        content=[model.model_dump() for model in models], trustable=trustable
    )


class Algorithm(str, Enum):
    sha1 = "sha1"
    sha512 = "sha512"


@modrinth_router.get(
    "/version_file/{hash}",
    description="Modrinth File 信息",
    response_model=File,
)
@cache(expire=mcim_config.expire_second.modrinth.file)
async def modrinth_file(
    request: Request,
    hash_: Annotated[str, Path(alias="hash")],
    algorithm: Optional[Algorithm] = Algorithm.sha1,
):
    trustable = True
    # ignore algo
    file: Optional[File] = await request.app.state.aio_mongo_engine.find_one(
        File, query.or_(File.hashes.sha512 == hash_, File.hashes.sha1 == hash_)
    )
    if file is None:
        sync_hash.send(hash=hash_, algorithm=algorithm)
        log.debug(f"File {hash_} not found, send sync task.")
        return UncachedResponse()
    # Don't need to check file expire
    # elif file.sync_at.timestamp() + mcim_config.expire_second.modrinth.file < time.time():
    #     sync_hash.send(hash=hash_, algorithm=algorithm)
    #     log.debug(f"File {hash_} expire, send sync task.")
    #     trustable = False

    # TODO: Add Version reference directly but not query File again
    # get version object
    version: Optional[Version] = await request.app.state.aio_mongo_engine.find_one(
        Version, Version.id == file.version_id
    )
    if version is None:
        sync_version.send(version_id=file.version_id)
        log.debug(f"Version {file.version_id} not found, send sync task.")
        return UncachedResponse()
    elif (
        version.sync_at.timestamp() + mcim_config.expire_second.modrinth.version
        < time.time()
    ):
        sync_version.send(version_id=file.version_id)
        log.debug(f"Version {file.version_id} expire, send sync task.")
        trustable = False

    return TrustableResponse(content=version, trustable=trustable)


class HashesQuery(BaseModel):
    hashes: List[str]
    algorithm: Algorithm


@modrinth_router.post(
    "/version_files",
    description="Modrinth Files 信息",
    response_model=List[File],
)
@cache(expire=mcim_config.expire_second.modrinth.file)
async def modrinth_files(items: HashesQuery, request: Request):
    trustable = True
    # ignore algo
    files_models: List[File] = await request.app.state.aio_mongo_engine.find(
        File,
        query.or_(
            query.in_(File.hashes.sha1, items.hashes),
            query.in_(File.hashes.sha512, items.hashes),
        ),
    )
    model_count = len(files_models)
    hashes_count = len(items.hashes)
    if not files_models:
        sync_multi_hashes.send(hashes=items.hashes, algorithm=items.algorithm)
        log.debug("Files not found, send sync task.")
        return UncachedResponse()
    elif model_count != hashes_count:
        sync_multi_hashes.send(hashes=items.hashes, algorithm=items.algorithm)
        log.debug(
            f"Files {items.hashes} {model_count}/{hashes_count} not completely found, send sync task."
        )
        trustable = False
    # Don't need to check version expire

    version_ids = [file.version_id for file in files_models]
    version_models: List[Version] = await request.app.state.aio_mongo_engine.find(
        Version, query.in_(Version.id, version_ids)
    )
    # len(version_models) != len(files_models)
    version_model_count = len(version_models)
    file_model_count = len(files_models)
    if not version_models:
        sync_multi_versions.send(ids_list=version_ids)
        log.debug("Versions not found, send sync task.")
        return UncachedResponse()
    elif version_model_count != file_model_count:
        sync_multi_versions.send(ids_list=version_ids)
        log.debug(
            f"Versions {version_ids} {version_model_count}/{file_model_count} not completely found, send sync task."
        )
        trustable = False
    return TrustableResponse(
        content=[model.model_dump() for model in version_models], trustable=trustable
    )


class UpdateItems(BaseModel):
    loaders: List[str]
    game_versions: List[str]


@modrinth_router.post("/version_file/{hash}/update")
@cache(expire=mcim_config.expire_second.modrinth.file)
async def modrinth_file_update(
    request: Request,
    items: UpdateItems,
    hash_: Annotated[str, Path(alias="hash")],
    algorithm: Optional[Algorithm] = Algorithm.sha1,
):
    trustable = True
    files_collection = request.app.state.aio_mongo_engine.get_collection(File)
    pipeline = [
        (
            {"$match": {"_id.sha1": hash_}}
            if algorithm is Algorithm.sha1
            else {"$match": {"_id.sha512": hash_}}
        ),
        {
            "$lookup": {
                "from": "modrinth_versions",
                "localField": "project_id",
                "foreignField": "project_id",
                "as": "versions_fields",
            }
        },
        {"$unwind": "$versions_fields"},
        {
            "$match": {
                "versions_fields.game_versions": {"$in": items.game_versions},
                "versions_fields.loaders": {"$in": items.loaders},
            }
        },
        {"$sort": {"versions_fields.date_published": -1}},
        # {
        #     "$group": {
        #         "_id": "$_id.sha1" if items.algorithm is Algorithm.sha1 else "$_id.sha512",
        #         "latest_date": {"$first": "$versions_fields.date_published"},
        #         "detail": ,  # 只保留第一个匹配版本
        #     }
        # },
        {"$replaceRoot": {"newRoot": "$versions_fields"}},
    ]
    version_result = await files_collection.aggregate(pipeline).to_list(length=None)
    if len(version_result) != 0:
        version_result = version_result[0]
        if not (
                datetime.strptime(
                    version_result["sync_at"], "%Y-%m-%dT%H:%M:%SZ"
                ).timestamp()
                + mcim_config.expire_second.modrinth.file
                > time.time()
            ):
            sync_project.send(project_id=version_result["project_id"])
            log.debug(f"Project {version_result["project_id"]} expired, send sync task.")
            trustable = False
    else:
        sync_hash.send(hash=hash_, algorithm=algorithm.value)
        log.debug(f"Hash {hash_} not found, send sync task")
        return UncachedResponse()
    return TrustableResponse(content=version_result, trustable=trustable)



class MultiUpdateItems(BaseModel):
    hashes: List[str]
    algorithm: Algorithm
    loaders: Optional[List[str]]
    game_versions: Optional[List[str]]


@modrinth_router.post("/version_files/update")
@cache(expire=mcim_config.expire_second.modrinth.file)
async def modrinth_mutil_file_update(request: Request, items: MultiUpdateItems):
    trustable = True
    files_collection = request.app.state.aio_mongo_engine.get_collection(File)
    pipeline = [
        (
            {"$match": {"_id.sha1": {"$in": items.hashes}}}
            if items.algorithm is Algorithm.sha1
            else {"$match": {"_id.sha512": {"$in": items.hashes}}}
        ),
        {
            "$lookup": {
                "from": "modrinth_versions",
                "localField": "project_id",
                "foreignField": "project_id",
                "as": "versions_fields",
            }
        },
        {"$unwind": "$versions_fields"},
        {
            "$match": {
                "versions_fields.game_versions": {"$in": items.game_versions},
                "versions_fields.loaders": {"$in": items.loaders},
            }
        },
        {"$sort": {"versions_fields.date_published": -1}},
        {
            "$group": {
                "_id": (
                    "$_id.sha1" if items.algorithm is Algorithm.sha1 else "$_id.sha512"
                ),
                "latest_date": {"$first": "$versions_fields.date_published"},
                "detail": {"$first": "$versions_fields"},  # 只保留第一个匹配版本
                # "original_hash": { "$first": "$_id.sha1" if items.algorithm is Algorithm.sha1 else "$_id.sha512" }
            }
        },
    ]
    versions_result = await files_collection.aggregate(pipeline).to_list(length=None)
    if len(versions_result) == 0:
        sync_multi_hashes.send(hashes=items.hashes, algorithm=items.algorithm.value)
        log.debug(f"Hashes {items.hashes} not found, send sync task")
        return UncachedResponse()
    else:
        # check expire
        resp = {}
        project_ids_to_sync = set()
        for version_result in versions_result:
            original_hash = version_result["_id"]
            version_detail= version_result["detail"]
            resp[original_hash] = version_detail
            if not (
                datetime.strptime(
                    version_detail["sync_at"], "%Y-%m-%dT%H:%M:%SZ"
                ).timestamp()
                + mcim_config.expire_second.modrinth.file
                > time.time()
            ):
                project_ids_to_sync.add(version_detail["project_id"])
                trustable = False
        if len(project_ids_to_sync) != 0:
            sync_multi_projects.send(project_ids=list(project_ids_to_sync))
            log.debug(f"Project {project_ids_to_sync} expired, send sync task.")
        return TrustableResponse(content=resp, trustable=trustable)


@modrinth_router.get(
    "/tag/category",
    description="Modrinth Category 信息",
    response_model=List,
)
@cache(expire=mcim_config.expire_second.modrinth.category)
async def modrinth_tag_categories(request: Request):
    category = await request.app.state.aio_redis_engine.hget("modrinth", "categories")
    if category is None:
        sync_tags.send()
        log.debug("Category not found, send sync task.")
        return UncachedResponse()
    return TrustableResponse(content=json.loads(category))


@modrinth_router.get(
    "/tag/loader",
    description="Modrinth Loader 信息",
    response_model=List,
)
@cache(expire=mcim_config.expire_second.modrinth.category)
async def modrinth_tag_loaders(request: Request):
    loader = await request.app.state.aio_redis_engine.hget("modrinth", "loaders")
    if loader is None:
        sync_tags.send()
        log.debug("Loader not found, send sync task.")
        return UncachedResponse()
    return TrustableResponse(content=json.loads(loader))


@modrinth_router.get(
    "/tag/game_version",
    description="Modrinth Game Version 信息",
    response_model=List,
)
@cache(expire=mcim_config.expire_second.modrinth.category)
async def modrinth_tag_game_versions(request: Request):
    game_version = await request.app.state.aio_redis_engine.hget(
        "modrinth", "game_versions"
    )
    if game_version is None:
        sync_tags.send()
        log.debug("Game Version not found, send sync task.")
        return UncachedResponse()
    return TrustableResponse(content=json.loads(game_version))


@modrinth_router.get(
    "/tag/donation_platform",
    description="Modrinth Donation Platform 信息",
    response_model=List,
)
@cache(expire=mcim_config.expire_second.modrinth.category)
async def modrinth_tag_donation_platforms(request: Request):
    donation_platform = await request.app.state.aio_redis_engine.hget(
        "modrinth", "donation_platform"
    )
    if donation_platform is None:
        sync_tags.send()
        log.debug("Donation Platform not found, send sync task.")
        return UncachedResponse()
    return TrustableResponse(content=json.loads(donation_platform))


@modrinth_router.get(
    "/tag/project_type",
    description="Modrinth Project Type 信息",
    response_model=List,
)
@cache(expire=mcim_config.expire_second.modrinth.category)
async def modrinth_tag_project_types(request: Request):
    project_type = await request.app.state.aio_redis_engine.hget(
        "modrinth", "project_type"
    )
    if project_type is None:
        sync_tags.send()
        log.debug("Project Type not found, send sync task.")
        return UncachedResponse()
    return TrustableResponse(content=json.loads(project_type))


@modrinth_router.get(
    "/tag/side_type",
    description="Modrinth Side Type 信息",
    response_model=List,
)
@cache(expire=mcim_config.expire_second.modrinth.category)
async def modrinth_tag_side_types(request: Request):
    side_type = await request.app.state.aio_redis_engine.hget("modrinth", "side_type")
    if side_type is None:
        sync_tags.send()
        log.debug("Side Type not found, send sync task.")
        return UncachedResponse()
    return TrustableResponse(content=json.loads(side_type))

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse, Response
from typing_extensions import Annotated
from typing import List, Optional, Union
from enum import Enum
from pydantic import BaseModel
from odmantic import query
import json

from app.sync import *
from app.models.database.modrinth import Project, Version, File
from app.sync.modrinth import sync_project, sync_version, sync_multi_projects, sync_multi_projects
from app.database.mongodb import aio_mongo_engine
from app.database._redis import aio_redis_engine
from app.config.mcim import MCIMConfig

mcim_config = MCIMConfig.load()

API = mcim_config.modrinth_api

EXPIRE_STATUS_CODE = mcim_config.expire_status_code
UNCACHE_STATUS_CODE = mcim_config.uncache_status_code

modrinth_router = APIRouter(prefix="/modrinth", tags=["modrinth"])

@modrinth_router.get("/")
async def get_curseforge():
    return {"message": "Modrinth"}

@modrinth_router.get(
    "/project/{idslug}",
    description="Modrinth Project 信息",
    response_model=Project,
)
async def modrinth_project(idslug: str):
    model = await aio_mongo_engine.find_one(Project, query.or_(Project.id == idslug, Project.slug == idslug))
    if model is None:
        sync_project.send(idslug)
        return Response(status_code=EXPIRE_STATUS_CODE)
    return JSONResponse(content=model.model_dump())

@modrinth_router.get(
    "/projects",
    description="Modrinth Projects 信息",
    response_model=List[Project],
)
async def modrinth_projects(Ids: List[int]):
    models = await aio_mongo_engine.find(Project, query.in_(Project.id, Ids))
    if models is None:
        pass
    elif len(models) != len(Ids):
        pass
    return JSONResponse(content=[model.model_dump() for model in models])

@modrinth_router.get(
    "/project/{idslug}/version",
    description="Modrinth Projects 全部版本信息",
    response_model=List[Project],
)
async def modrinth_project_versions(idslug: str):
    model = await aio_mongo_engine.find(Version, query.or_(Version.project_id == idslug, Version.slug == idslug))
    if model is None:
        pass
    return JSONResponse(content=[version.model_dump() for version in model])

@modrinth_router.get(
    "/search",
    description="Modrinth Projects 搜索",
    response_model=List[Project],
)
async def modrinth_search_projects(query: str):
    # models = await aio_mongo_engine.find(Project, Project.title.contains(query))
    # if models is None:
    #     pass
    # return JSONResponse(content=[model.model_dump() for model in models])
    pass

@modrinth_router.get(
    "/version/{id}",
    description="Modrinth Version 信息",
    response_model=Version,
)
async def modrinth_version(version_id: Annotated[str, Query(alias="id")]):
    model = await aio_mongo_engine.find_one(Version, query.or_(Version.id == version_id, Version.slug == version_id))
    if model is None:
        pass
    return JSONResponse(content=model.model_dump())

@modrinth_router.get(
    "/versions",
    description="Modrinth Versions 信息",
    response_model=List[Version],
)
async def modrinth_versions(ids: str):
    ids_list = json.loads(ids)
    models = await aio_mongo_engine.find(Version, query.in_(Version.id, ids_list))
    if models is None:
        pass
    elif len(models) != len(ids_list):
        pass
    return JSONResponse(content=[model.model_dump() for model in models])


class Algorithm(str, Enum):
    sha1 = "sha1"
    sha512 = "sha512"

@modrinth_router.get(
    "/version_file/{hash}",
    description="Modrinth File 信息",
    response_model=File,
)
async def modrinth_file(hash: str, algorithm: Optional[Algorithm] = Algorithm.sha1):
    if algorithm == Algorithm.sha1:
        file_model = await aio_mongo_engine.find_one(File, File.hashes.sha1 == hash)
    elif algorithm == Algorithm.sha512:
        file_model = await aio_mongo_engine.find_one(File, File.hashes.sha512 == hash)
    version_model = await aio_mongo_engine.find_one(Version, Version.id == file_model.version_id)
    return JSONResponse(content=version_model.model_dump())

class HashesQuery(BaseModel):
    hashes: List[str]
    algorithm: Algorithm

@modrinth_router.post(
    "/version_files",
    description="Modrinth Files 信息",
    response_model=List[File],
)
async def modrinth_files(items: HashesQuery):
    if items.algorithm == Algorithm.sha1:
        files_models = await aio_mongo_engine.find(File, query.in_(File.hashes.sha1, items.hashes))
    elif items.algorithm == Algorithm.sha512:
        files_models = await aio_mongo_engine.find(File, query.in_(File.hashes.sha512, items.hashes))
    if files_models is None:
        pass
    elif len(files_models) != len(items.hashes):
        pass
    version_models = await aio_mongo_engine.find(Version, query.in_(Version.id, [file.version_id for file in files_models]))
    
    if files_models is None:
        pass
    elif len(version_models) != len(files_models):
        pass
    
    return JSONResponse(content=[model.model_dump() for model in version_models])

@modrinth_router.get(
    "/tag/category",
    description="Modrinth Category 信息",
    response_model=List,
)
async def modrinth_tag_categories():
    category = await aio_redis_engine.hget("modrinth", "categories")
    return JSONResponse(content=json.loads(category))

@modrinth_router.get(
    "/tag/loader",
    description="Modrinth Loader 信息",
    response_model=List,
)
async def modrinth_tag_loaders():
    loader = await aio_redis_engine.hget("modrinth", "loaders")
    return JSONResponse(content=json.loads(loader))

@modrinth_router.get(
    "/tag/game_version",
    description="Modrinth Game Version 信息",
    response_model=List,
)
async def modrinth_tag_game_versions():
    game_version = await aio_redis_engine.hget("modrinth", "game_versions")
    return JSONResponse(content=json.loads(game_version))

@modrinth_router.get(
    "/tag/donation_platform",
    description="Modrinth Donation Platform 信息",
    response_model=List,
)
async def modrinth_tag_donation_platforms():
    donation_platform = await aio_redis_engine.hget("modrinth", "donation_platform")
    return JSONResponse(content=json.loads(donation_platform))

@modrinth_router.get(
    "/tag/project_type",
    description="Modrinth Project Type 信息",
    response_model=List,
)
async def modrinth_tag_project_types():
    project_type = await aio_redis_engine.hget("modrinth", "project_type")
    return JSONResponse(content=json.loads(project_type))

@modrinth_router.get(
    "/tag/side_type",
    description="Modrinth Side Type 信息",
    response_model=List,
)
async def modrinth_tag_side_types():
    side_type = await aio_redis_engine.hget("modrinth", "side_type")
    return JSONResponse(content=json.loads(side_type))
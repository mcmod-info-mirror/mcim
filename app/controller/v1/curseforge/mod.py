from fastapi import APIRouter
from fastapi.responses import JSONResponse
from typing import List, Optional, Union
from odmantic import query

from app.sync import *
from app.models.database.curseforge import Mod, File
from app.database.mongodb import aio_mongo_engine
from app.config.mcim import MCIMConfig


mcim_config = MCIMConfig.load()

API = mcim_config.curseforge_api

mod_router = APIRouter(prefix="/mod", tags=["curseforge"])


@mod_router.get(
    "/{modId}",
    responses={
        200: {
            "description": "Curseforge Mod info",
            "content": {
                "application/json": {
                    # "example": {"status": "success", "data": curseforge_mod_example}
                }
            },
        }
    },
    description="Curseforge Mod 信息",
    response_model=Mod,
)
async def curseforge_mod(modId: int):
    mod_model = await aio_mongo_engine.find_one(Mod, Mod.id == modId)
    if mod_model is None:
        # return RedirectResponse(url=f"{API}/v1/mods/{modId}")
        pass
    return JSONResponse(content=mod_model.model_dump())


# get mods
@mod_router.post(
    "/",
    responses={
        200: {
            "description": "Curseforge Mods info",
            "content": {
                "application/json": {
                    # "example": {"status": "success", "data": curseforge_mods_example}
                }
            },
        }
    },
    description="Curseforge Mods 信息",
    response_model=List[Mod],
)
async def curseforge_mods(modIds: List[int], filterPcOnly: Optional[bool] = True):
    mod_models = await aio_mongo_engine.find(Mod, query.in_(Mod.id, modIds))
    if mod_models is None:
        # return RedirectResponse(url=f"{API}/v1/mods/{modId}")
        pass
    elif len(mod_models) != len(modIds):
        pass
    return JSONResponse(content=[mod.model_dump() for mod in mod_models])


@mod_router.get(
    "/{modId}/files",
    responses={
        200: {
            "description": "Curseforge Mod files info",
            "content": {
                "application/json": {
                    # "example": {"status": "success", "data": curseforge_mod_files_example}
                }
            },
        }
    },
    description="Curseforge Mod 文件信息",
    response_model=List[File],
)
async def curseforge_mod_files(modId: int):
    mod_models = await aio_mongo_engine.find(File, File.modId == modId)
    if mod_models is None:
        # return RedirectResponse(url=f"{API}/v1/mods/{modId}")
        pass
    return JSONResponse(content=[model.model_dump() for model in mod_models])


# get files
@mod_router.get(
    "/files",
    responses={
        200: {
            "description": "Curseforge Mod files info",
            "content": {
                "application/json": {
                    # "example": {"status": "success", "data": curseforge_mod_files_example}
                }
            },
        }
    },
    description="Curseforge Mod 文件信息",
)
async def curseforge_mod_files(fileids: List[int]):
    file_models = await aio_mongo_engine.find(File, query.in_(File.id, fileids))
    if not file_models:
        pass
    elif len(file_models) != len(fileids):
        pass
    return JSONResponse(content=[model.model_dump() for model in file_models])


# get file
@mod_router.get(
    "/{modId}/files/{fileId}",
    responses={
        200: {
            "description": "Curseforge Mod file info",
            "content": {
                "application/json": {
                    # "example": {"status": "success", "data": curseforge_mod_file_example}
                }
            },
        }
    },
    description="Curseforge Mod 文件信息",
)
async def curseforge_mod_file(modid: int, fileid: int):
    model = await aio_mongo_engine.find_one(
        File, File.modId == modid, File.id == fileid
    )
    return JSONResponse(content=model.model_dump())

from app.service.curseforge import *

from fastapi import APIRouter
from fastapi.responses import JSONResponse

mod_router = APIRouter(prefix="/mod", tags=["curseforge"])


@mod_router.get(
    "/{modid}",
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
)
async def curseforge_mod(modid: int):
    info = await get_mod_info(modid)
    return JSONResponse(content=info)


# get mods
@mod_router.get(
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
)
async def curseforge_mods(modids: list):
    info = await get_mods_info(modids)
    return JSONResponse(content=info)


@mod_router.get(
    "/{modid}/files",
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
async def curseforge_mod_files(modid: int):
    info = await get_mod_files_info(modid)
    return JSONResponse(content=info)


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
async def curseforge_mod_files(fileids: list):
    info = await get_files_info(fileids)
    return JSONResponse(content=info)


# get file
@mod_router.get(
    "/{modid}/files/{fileid}",
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
    info = await get_file_info(modid, fileid)
    return JSONResponse(content=info)


import os
from fastapi import FastAPI, APIRouter
from fastapi.responses import JSONResponse, Response, RedirectResponse, ORJSONResponse
from starlette.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from .controller import controller_router

# from .middleware.resp import RespMiddleware
from .config.mcim import MCIMConfig
from .database.mongodb import setup_async_mongodb, init_mongodb_aioengine
from .database._redis import init_redis_aioengine, close_aio_redis_engine

from app.utils.response_cache import cache
from app.utils.response import TrustableResponse

mcim_config = MCIMConfig.load()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await setup_async_mongodb()
    yield
    # await close_async_mongodb()
    await close_aio_redis_engine()


APP = FastAPI(
    title="MCIM", description="这是一个为 Mod 信息加速的 API", lifespan=lifespan
)

APP.include_router(controller_router)

if mcim_config.file_cdn:
    # modrinth cdn
    os.makedirs("./data/modrinth", exist_ok=True)
    APP.mount("/data", StaticFiles(directory="./data/modrinth"), name="modrinth")

    # curseforge cdn
    os.makedirs("./data/curseforge", exist_ok=True)
    APP.mount("/curseforge", StaticFiles(directory="./data/curseforge"), name="curseforge")

APP.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@APP.get("favicon.ico")
async def favicon():
    return RedirectResponse(status_code=301, url=mcim_config.favicon_url)


@APP.get(
    "/",
    responses={
        200: {
            "description": "MCIM API status",
            "content": {
                "APPlication/json": {
                    "example": {"status": "success", "message": "z0z0r4 Mod Info"}
                }
            },
        }
    },
    description="MCIM API",
)
@cache()
async def root():
    return ORJSONResponse(content={
        "status": "success",
        "message": "z0z0r4 Mod Info",
        "information": {
            "Status": "https://status.mcim.z0z0r4.top/status/mcim",
            "Docs": [
                "https://mcim.z0z0r4.top/docs",
            ],
            "Github": "https://github.com/z0z0r4/mcim",
            "contact": {"Eamil": "z0z0r4@outlook.com", "QQ": "3531890582"},
        },
    })
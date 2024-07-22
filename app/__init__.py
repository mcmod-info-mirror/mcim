import os
import shutil
from fastapi import FastAPI
from fastapi.responses import RedirectResponse, ORJSONResponse, Response
from starlette.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
from prometheus_fastapi_instrumentator import Instrumentator, metrics

from app.controller import controller_router
from app.utils.loger import log
from app.config import MCIMConfig
from app.database.mongodb import setup_async_mongodb, init_mongodb_aioengine
from app.database._redis import (
    init_redis_aioengine,
    close_aio_redis_engine,
    init_file_cdn_redis_async_engine,
)
from app.utils.response_cache import Cache
from app.utils.response_cache import cache
from app.utils.response_cache.key_builder import xxhash_key_builder
from app.utils.response import BaseResponse
from app.utils.middleware import ForceSyncMiddleware, TimingMiddleware

mcim_config = MCIMConfig.load()


def init_file_cdn():
    os.makedirs(mcim_config.modrinth_download_path, exist_ok=True)
    os.makedirs(mcim_config.curseforge_download_path, exist_ok=True)
    for i in range(256):
        os.makedirs(
            os.path.join(mcim_config.modrinth_download_path, format(i, "02x")),
            exist_ok=True,
        )
        os.makedirs(
            os.path.join(mcim_config.curseforge_download_path, format(i, "02x")),
            exist_ok=True,
        )
    log.success("File CDN enabled, cache folder ready.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.aio_redis_engine = init_redis_aioengine()
    await app.state.aio_redis_engine.flushall()
    app.state.aio_mongo_engine = init_mongodb_aioengine()
    await setup_async_mongodb(app.state.aio_mongo_engine)

    if mcim_config.redis_cache:
        app.state.fastapi_cache = Cache.init(enabled=True)

    if mcim_config.file_cdn:
        app.state.file_cdn_redis_async_engine = init_file_cdn_redis_async_engine()
        init_file_cdn()

    yield

    await close_aio_redis_engine()


APP = FastAPI(
    title="MCIM", description="这是一个为 Mod 信息加速的 API", lifespan=lifespan
)

if mcim_config.prometheus:
    instrumentator: Instrumentator = Instrumentator(
        should_round_latency_decimals=True,
        excluded_handlers=["/metrics", "/docs", "/favicon.ico", "/openapi.json"],
        inprogress_name="inprogress",
        inprogress_labels=True,
    )
    instrumentator.add(metrics.default())
    instrumentator.instrument(APP).expose(
        APP, include_in_schema=False, should_gzip=True
    )


APP.include_router(controller_router)

APP.add_middleware(GZipMiddleware, minimum_size=1000)

APP.add_middleware(TimingMiddleware)

# 强制同步中间件 force=True
APP.add_middleware(ForceSyncMiddleware)

APP.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@APP.get("/favicon.ico")
@cache(never_expire=True)
async def favicon():
    return RedirectResponse(url=mcim_config.favicon_url, status_code=301)


WELCOME_MESSAGE = {
    "status": "success",
    "message": "mcimirror",
    "information": {
        "Status": "https://status.mcimirror.top",
        "Docs": [
            "https://mod.mcimirror.top/docs",
        ],
        "Github": "https://github.com/mcmod-info-mirror/mcim",
        "contact": {"Eamil": "z0z0r4@outlook.com", "QQ": "3531890582"},
    },
}


@APP.get(
    "/",
    responses={
        200: {
            "description": "MCIM API status",
            "content": {
                "APPlication/json": {
                    "example": WELCOME_MESSAGE,
                }
            },
        }
    },
    description="MCIM API",
)
@cache(never_expire=True)
async def root():
    return BaseResponse(content=WELCOME_MESSAGE)

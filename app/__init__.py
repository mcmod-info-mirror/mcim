from fastapi import FastAPI, APIRouter
from fastapi.responses import JSONResponse, Response, RedirectResponse, ORJSONResponse
from starlette.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.controller import controller_router

# from app.middleware.resp import RespMiddleware
from app.config.mcim import MCIMConfig
from app.database.mongodb import setup_async_mongodb, init_mongodb_aioengine
from app.database._redis import init_redis_aioengine, close_aio_redis_engine
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

APP.add_middleware(GZipMiddleware, minimum_size=1000)

APP.add_middleware(RawContextMiddleware, plugins=(plugins.RequestIdPlugin(),))

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
                    "example": {"status": "success", "message": "mcimirror"}
                }
            },
        }
    },
    description="MCIM API",
)
@cache()
async def root():
    return ORJSONResponse(
        content={
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
    )

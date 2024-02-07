from fastapi import FastAPI, BackgroundTasks, Body, status, APIRouter
from fastapi.responses import JSONResponse, Response, RedirectResponse
from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from .controller.v1 import v1_router
from .middleware.resp import RespMiddleware
from .config.mcim import MCIMConfig
from .database.mongodb import start_async_mongodb, close_async_mongodb

mcim_config = MCIMConfig.load()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await start_async_mongodb()
    yield
    await close_async_mongodb()


APP = FastAPI(
    title="MCIM", description="这是一个为 Mod 信息加速的 API", lifespan=lifespan
)

APP.include_router(v1_router, prefix="/v1")

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
async def root():
    return JSONResponse(
        content={
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
        },
        headers={"Cache-Control": "max-age=300, public"},
    )

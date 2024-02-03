from fastapi import FastAPI, BackgroundTasks, Body, status, APIRouter
from fastapi.responses import JSONResponse, Response, RedirectResponse
from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .controller.v1 import v1_router
from .docs import docs_router
from .config.mcim import MCIMConfig

mcim_config = MCIMConfig.load()

APP = FastAPI(
    docs_url=None,
    redoc_url=None,
    title="MCIM",
    description="这是一个为 Mod 信息加速的 API",
)

APP.include_router(docs_router)
APP.include_router(v1_router, prefix="/v1")
APP.mount("/static", StaticFiles(directory="app/static"), name="static")

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

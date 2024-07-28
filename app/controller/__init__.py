from fastapi import APIRouter, Request
from typing import Optional
from app.controller.modrinth import modrinth_router
from app.controller.curseforge import curseforge_router
from app.controller.file_cdn import file_cdn_router
from app.config import MCIMConfig
from app.utils.loger import log


mcim_config = MCIMConfig.load()

controller_router = APIRouter()
controller_router.include_router(curseforge_router)
controller_router.include_router(modrinth_router)
controller_router.include_router(file_cdn_router)
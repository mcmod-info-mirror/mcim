from fastapi import APIRouter, Request
from app.controller.curseforge.v1 import v1_router
from app.utils.response_cache import cache

curseforge_router= APIRouter(prefix="/curseforge", tags=["curseforge"])

curseforge_router.include_router(v1_router)

@curseforge_router.get("/")
@cache(never_expire=True)
async def get_curseforge():
    return {"message": "CurseForge"}
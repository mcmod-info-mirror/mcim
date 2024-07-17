from fastapi import APIRouter, Request
from app.controller.modrinth.v2 import v2_router
from app.utils.response_cache import cache

modrinth_router = APIRouter(prefix="/modrinth", tags=["modrinth"])
modrinth_router.include_router(v2_router)

@modrinth_router.get("/")
@cache(never_expire=True)
async def get_curseforge():
    return {"message": "Modrinth"}
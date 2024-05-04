from fastapi import APIRouter

# from .games import games_router
from .mod import mod_router
from .fingerprint import fingerprint_router

curseforge_router = APIRouter(prefix="/curseforge", tags=["curseforge"])

curseforge_router.include_router(mod_router)
curseforge_router.include_router(fingerprint_router)


@curseforge_router.get("/")
async def get_curseforge():
    return {"message": "CurseForge"}
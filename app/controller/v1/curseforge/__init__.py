from fastapi import APIRouter
# from .games import games_router
curseforge_router = APIRouter(prefix="/curseforge", tags=["curseforge"])

@curseforge_router.get("/")
async def get_curseforge():
    return {"message": "CurseForge"}

# curseforge_router.include_router(games_router)
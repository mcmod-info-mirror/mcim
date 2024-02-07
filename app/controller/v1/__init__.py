from fastapi import APIRouter

from .curseforge import curseforge_router as curseforge_router

v1_router = APIRouter()

v1_router.include_router(curseforge_router)


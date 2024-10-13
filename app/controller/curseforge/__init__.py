from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.controller.curseforge.v1 import v1_router
from app.utils.response_cache import cache
from app.utils.response import BaseResponse
from app.models.database.curseforge import Mod, File, Fingerprint

curseforge_router = APIRouter(prefix="/curseforge", tags=["curseforge"])

curseforge_router.include_router(v1_router)


@curseforge_router.get("/")
@cache(never_expire=True)
async def get_curseforge():
    return BaseResponse(content={"message": "CurseForge"})


class CurseforgeStatistics(BaseModel):
    mods: int
    files: int
    fingerprints: int


# statistics
@curseforge_router.get(
    "/statistics",
    description="Curseforge 缓存统计信息",
    response_model=CurseforgeStatistics,
    include_in_schema=False,
)
# @cache(expire=3600)
async def curseforge_statistics(request: Request):
    mod_collection = request.app.state.aio_mongo_engine.get_collection(Mod)
    file_collection = request.app.state.aio_mongo_engine.get_collection(File)
    fingerprint_collection = request.app.state.aio_mongo_engine.get_collection(
        Fingerprint
    )

    mod_count = await mod_collection.aggregate([{"$collStats": {"count": {}}}])
    file_count = await file_collection.aggregate([{"$collStats": {"count": {}}}])
    fingerprint_count = await fingerprint_collection.aggregate(
        [{"$collStats": {"count": {}}}]
    )

    return BaseResponse(
        content=CurseforgeStatistics(
            mods=mod_count["count"],
            files=file_count["count"],
            fingerprints=fingerprint_count["count"],
        )
    )
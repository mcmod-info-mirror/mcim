from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.controller.modrinth.v2 import v2_router
from app.utils.response_cache import cache
from app.utils.response import BaseResponse
from app.models.database.modrinth import Project, Version, File

modrinth_router = APIRouter(prefix="/modrinth", tags=["modrinth"])
modrinth_router.include_router(v2_router)


@modrinth_router.get("/")
@cache(never_expire=True)
async def get_curseforge():
    return BaseResponse(content={"message": "Modrinth"})


class ModrinthStatistics(BaseModel):
    projects: int
    versions: int
    files: int


@modrinth_router.get(
    "/statistics",
    description="Modrinth 缓存统计信息",
    response_model=ModrinthStatistics,
    include_in_schema=False,
)
# @cache(expire=3600)
async def modrinth_statistics(request: Request):
    """
    没有统计 author
    """
    # count
    project_count = await request.app.state.aio_mongo_engine.count(Project)
    version_count = await request.app.state.aio_mongo_engine.count(Version)
    file_count = await request.app.state.aio_mongo_engine.count(File)
    return BaseResponse(
        content=ModrinthStatistics(
            projects=project_count, versions=version_count, files=file_count
        )
    )

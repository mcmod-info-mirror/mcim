"""
v1 router

逻辑：

如果不存在/过期，则返回 origin 链接，然后将任务加入任务队列

TODO: 优化任务队列，聚合多个任务，在积累一定值/定时批量拉取
"""
from fastapi import APIRouter

from app.controller.v1.curseforge import curseforge_router as curseforge_router
from app.controller.v1.modrinth import modrinth_router as modrinth_router

v1_router = APIRouter()

v1_router.include_router(curseforge_router)
v1_router.include_router(modrinth_router)
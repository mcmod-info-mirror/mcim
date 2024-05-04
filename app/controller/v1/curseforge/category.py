from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response
from typing import List, Optional, Union
from odmantic import query
import json

from app.database._redis import aio_redis_engine
from app.sync.curseforge import sync_categories
from app.models.response.curseforge import Category
from app.config.mcim import MCIMConfig

mcim_config = MCIMConfig.load()

category_router = APIRouter(prefix="/categories", tags=["curseforge"])

# 强制返回所有分类信息，不筛选
@category_router.get(
    "/",
    description="Curseforge Categories 信息",
    response_model=List[Category],
)
async def curseforge_categories():
    categories = await aio_redis_engine.hget("curseforge","categories")
    if categories is None:
        sync_categories.send()
        return Response(status_code=404)
    return JSONResponse(content=json.loads(categories))
from app.service.curseforge import *
from app.models.request.curseforge import Fingerprints

from fastapi import APIRouter
from fastapi.responses import JSONResponse

fingerprint_router = APIRouter(prefix="/fingerprints", tags=["curseforge"])


@fingerprint_router.post(
    "/",
    responses={
        200: {
            "description": "Curseforge Mod files info",
            "content": {
                "application/json": {
                    # "example": {"status": "success", "data": curseforge_mod_files_example}
                }
            },
        }
    },
    description="Curseforge Fingerprint 文件信息",
)
async def curseforge_fingerprints(items: Fingerprints):
    info = await get_fingerprints(items.fingerprints)
    return JSONResponse(content=info)

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from typing import List, Optional, Union
from odmantic import query

from app.sync import *
from app.models.database.curseforge import Fingerprint
from app.models.response.curseforge import FingerprintResponse
from app.database.mongodb import aio_mongo_engine

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
    response_model=FingerprintResponse,
)
async def curseforge_fingerprints(fingerprints: List[int]):
    fingerprints_models = await aio_mongo_engine.find(
        Fingerprint, query.in_(Fingerprint.id, fingerprints)
    )
    if fingerprints_models is None:
        pass
    exactFingerprints = [fingerprint.id for fingerprint in fingerprints_models]
    unmatchedFingerprints = [
        fingerprint
        for fingerprint in fingerprints
        if fingerprint not in exactFingerprints
    ]
    return JSONResponse(
        content=FingerprintResponse(
            isCacheBuilt=True,
            exactFingerprints=exactFingerprints,
            exactMatches=fingerprints_models,
            unmatchedFingerprints=unmatchedFingerprints,
            installedFingerprints=[],
        ).model_dump()
    )
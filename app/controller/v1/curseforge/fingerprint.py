from fastapi import APIRouter
from fastapi.responses import JSONResponse, Response
from typing import List, Optional, Union
from odmantic import query

from app.sync.curseforge import sync_fingerprints
from app.models.database.curseforge import Fingerprint
from app.models.response.curseforge import FingerprintResponse
from app.database.mongodb import aio_mongo_engine
from app.config.mcim import MCIMConfig

mcim_config = MCIMConfig.load()

EXPIRE_STATUS_CODE = mcim_config.expire_status_code

fingerprint_router = APIRouter(prefix="/fingerprints", tags=["curseforge"])

# PCL2 和 HCML 都没使用里面的 latestFiles
# 将不会提供过期时间，过期不会主动刷新 Fingerprint，只跟随拉取版本刷新
@fingerprint_router.post(
    "/",
    description="Curseforge Fingerprint 文件信息",
    response_model=FingerprintResponse,
)
async def curseforge_fingerprints(fingerprints: List[int]):
    fingerprints_models = await aio_mongo_engine.find(
        Fingerprint, query.in_(Fingerprint.id, fingerprints)
    )
    if fingerprints_models is None:
        sync_fingerprints.send(fingerprints=fingerprints)
        return Response(status_code=EXPIRE_STATUS_CODE)
    elif len(fingerprints_models) != len(fingerprints):
        sync_fingerprints.send(fingerprints=fingerprints)
        return Response(status_code=EXPIRE_STATUS_CODE)
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
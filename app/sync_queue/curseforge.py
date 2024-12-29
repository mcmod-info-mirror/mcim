from typing import List, Union, Optional

from app.database._redis import (
    sync_queuq_redis_engine,
)

# curseforge
async def add_curseforge_modIds_to_queue(modIds: List[int]):
    if len(modIds) != 0:
        await sync_queuq_redis_engine.sadd("curseforge_modids", *modIds)


async def add_curseforge_fileIds_to_queue(fileIds: List[int]):
    if len(fileIds) != 0:
        await sync_queuq_redis_engine.sadd("curseforge_fileids", *fileIds)


async def add_curseforge_fingerprints_to_queue(fingerprints: List[int]):
    if len(fingerprints) != 0:
        await sync_queuq_redis_engine.sadd("curseforge_fingerprints", *fingerprints)

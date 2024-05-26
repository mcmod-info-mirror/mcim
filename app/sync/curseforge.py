from typing import List, Optional, Union
from dramatiq import actor
import json

from app.sync.worker import sync_mongo_engine as mongodb_engine
from app.sync.worker import sync_redis_engine as redis_engine
from app.models.database.curseforge import File, Mod, Pagination, Fingerprint, FileInfo
from app.exceptions import ResponseCodeException
from app.utils.network.network import request
from app.config.mcim import MCIMConfig


mcim_config = MCIMConfig.load()

API = mcim_config.curseforge_api

headers = {"x-api-key": mcim_config.curseforge_api_key}


def submit_models(models: List[Union[File, Mod, Fingerprint]]):
    mongodb_engine.save_all(models)


@actor
def check_alive():
    return request(API, headers=headers).text


@actor
def sync_mod_all_files(
    modId: int, models: List[Union[File, Mod]] = [], submit: bool = True, latestFiles: List[dict] = None
):
    if not latestFiles:
        latestFiles = request(f"{API}/v1/mods/{modId}", headers=headers).json()["data"]["latestFiles"]

    res = request(
        f"{API}/v1/mods/{modId}/files",
        headers=headers,
        params={"index": 0, "pageSize": 50},
    ).json()
    page = Pagination(**res["pagination"])
    # index A zero based index of the first item to include in the response, the limit is: (index + pageSize <= 10,000).
    while page.index < page.totalCount - 1:
        params = {"index": page.index + page.pageSize, "pageSize": page.pageSize}
        res = request(
            f"{API}/v1/mods/{modId}/files", headers=headers, params=params
        ).json()
        for file in res["data"]:
            models.append(File(found=True, **file))
            models.append(Fingerprint(id=file["fileFingerprint"], file=file, latestFiles=latestFiles, found=True))
        page = Pagination(**res["pagination"])
    
    if not submit:
        return models
    submit_models(models)


@actor
def sync_multi_projects_all_files(
    modIds: List[int], models: List[Union[File, Mod]] = [], submit: bool = True
):
    # 去重
    modIds = list(set(modIds))
    for modId in modIds:
        models.extend(sync_mod_all_files(modId, submit=False))
    if not submit:
        return models
    submit_models(models)


@actor
def sync_mod(modId: int):
    models: List[Union[File, Mod]] = []
    res = request(f"{API}/v1/mods/{modId}", headers=headers).json()["data"]
    models.append(Mod(found=True, **res))
    sync_mod_all_files(modId, models, submit=True)


@actor
def sync_mutil_mods(modIds: List[int]):
    modIds = list(set(modIds))
    data = {"modIds": modIds}
    res = request(
        method="POST", url=f"{API}/v1/mods", json=data, headers=headers
    ).json()["data"]
    models: List[Union[File, Mod]] = []
    for mod in res:
        models.append(Mod(found=True, **mod))
    sync_multi_projects_all_files([model.id for model in models], models)


@actor
def sync_file(modId: int, fileId: int, expire: bool = False):
    res = request(f"{API}/v1/mods/{modId}/files/{fileId}", headers=headers).json()[
        "data"
    ]
    latestFiles = request(f"{API}/v1/mods/{modId}", headers=headers).json()["data"]["latestFiles"]
    models = [File(found=True, **res), Fingerprint(found=True, id=res["fileFingerprint"], file=res, latestFiles=latestFiles)]
    if not expire:
        sync_mod_all_files(modId, models, submit=False, latestFiles=latestFiles)
    submit_models(models)


@actor
def sync_mutil_files(fileIds: List[int]):
    models: List[Union[File, Mod]] = []
    res = request(
        method="POST",
        url=f"{API}/v1/mods/files",
        headers=headers,
        json={"fileIds": fileIds},
    ).json()["data"]
    for file in res:
        models.append(File(found=True, **file))
    sync_multi_projects_all_files([model.modId for model in models], models)


@actor
def sync_fingerprints(fingerprints: List[int]):
    res = request(
        method="POST",
        url=f"{API}/v1/fingerprints/432",
        headers=headers,
        json={"fingerprints": fingerprints},
    ).json()
    models = []
    for file in res["data"]["exactMatches"]:
        models.append(
            Fingerprint(
                id=file["file"]["fileFingerprint"],
                file=file["file"],
                latestFiles=file["latestFiles"],
                found=True,
            )
        )
    sync_multi_projects_all_files([model.file.modId for model in models], models)

@actor
def sync_categories():
    res = request(f"{API}/v1/categories", headers=headers).json()["data"]
    redis_engine.hset("curseforge", "categories", json.dumps(res))
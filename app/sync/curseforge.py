from typing import List, Optional, Union
from dramatiq import actor
import json
import os
import time


from app.sync import sync_mongo_engine as mongodb_engine
from app.sync import sync_redis_engine as redis_engine
from app.sync import file_cdn_redis_sync_engine
from app.models.database.curseforge import File, Mod, Pagination, Fingerprint
from app.utils.network import request_sync, download_file_sync
from app.config import MCIMConfig, Aria2Config
from app.utils.aria2 import add_http_task, ARIA2_API
from app.utils.loger import log


mcim_config = MCIMConfig.load()
aria2_config = Aria2Config.load()

API = mcim_config.curseforge_api
MAX_LENGTH = 1024 * 10024 * 20
MIN_DOWNLOAD_COUNT = 500
HEADERS = {"x-api-key": mcim_config.curseforge_api_key}


def submit_models(models: List[Union[File, Mod, Fingerprint]]):
    if mcim_config.file_cdn:
        for model in models:
            if isinstance(model, File):
                if (
                    not model.file_cdn_cached
                    and model.gameId == 432
                    and model.fileLength <= MAX_LENGTH
                    and model.downloadCount >= MIN_DOWNLOAD_COUNT
                ):
                    if len(model.hashes) != 0:
                        if not os.path.exists(
                            os.path.join(
                                mcim_config.curseforge_download_path,
                                model.hashes[0].value,
                            )
                        ):
                            if mcim_config.aria2:
                                file_cdn_cache_add_task.send(model.model_dump())
                            else:
                                file_cdn_cache.send(model.model_dump())
                        else:
                            model.file_cdn_cached = True
                    else:
                        file_cdn_cache.send(model.model_dump())
                        log.debug(f"File {model.id} has no hash")

    mongodb_engine.save_all(models)


@actor
def check_alive():
    return request_sync(API, headers=HEADERS).text


def append_model_from_files_res(
    res, latestFiles: dict, need_to_cache: bool = True
) -> List[Union[File, Fingerprint]]:
    models = []
    for file in res["data"]:
        models.append(File(found=True, need_to_cache=need_to_cache, **file))
        models.append(
            Fingerprint(
                id=file["fileFingerprint"],
                file=file,
                latestFiles=latestFiles,
                found=True,
            )
        )
    return models


@actor
def sync_mod_all_files(
    modId: int, latestFiles: List[dict] = None, need_to_cache: bool = True
) -> List[Union[File, Mod]]:
    models = []
    if not latestFiles:
        data = request_sync(f"{API}/v1/mods/{modId}", headers=HEADERS).json()["data"]
        latestFiles = data["latestFiles"]
        need_to_cache = True if data["classId"] == 6 else False

    res = request_sync(
        f"{API}/v1/mods/{modId}/files",
        headers=HEADERS,
        params={"index": 0, "pageSize": 50},
    ).json()
    models.extend(
        append_model_from_files_res(res, latestFiles, need_to_cache=need_to_cache)
    )
    page = Pagination(**res["pagination"])
    # index A zero based index of the first item to include in the response, the limit is: (index + pageSize <= 10,000).
    while page.index < page.totalCount - 1:
        params = {"index": page.index + page.pageSize, "pageSize": page.pageSize}
        res = request_sync(
            f"{API}/v1/mods/{modId}/files", headers=HEADERS, params=params
        ).json()
        models.extend(
            append_model_from_files_res(res, latestFiles, need_to_cache=need_to_cache)
        )
        page = Pagination(**res["pagination"])

    return models


@actor
def sync_multi_mods_all_files(modIds: List[int]) -> List[Union[File, Mod]]:
    models = []
    # 去重
    modIds = list(set(modIds))
    for modId in modIds:
        models.extend(sync_mod_all_files(modId))
    return models


@actor
def sync_mod(modId: int):
    models: List[Union[File, Mod]] = []
    res = request_sync(f"{API}/v1/mods/{modId}", headers=HEADERS).json()["data"]
    models.append(Mod(found=True, **res))
    models.extend(
        sync_mod_all_files(
            modId,
            latestFiles=res["latestFiles"],
            need_to_cache=True if res["classId"] == 6 else False,
        )
    )
    submit_models(models)


@actor
def sync_mutil_mods(modIds: List[int]):
    modIds = list(set(modIds))
    data = {"modIds": modIds}
    res = request_sync(
        method="POST", url=f"{API}/v1/mods", json=data, headers=HEADERS
    ).json()["data"]
    models: List[Union[File, Mod]] = []
    for mod in res:
        models.append(Mod(found=True, **mod))
    models.extend(sync_multi_mods_all_files([model.modId for model in models]))
    submit_models(models)


@actor
def sync_file(modId: int, fileId: int, expire: bool = False):
    # res = request_sync(f"{API}/v1/mods/{modId}/files/{fileId}", headers=headers).json()[
    #     "data"
    # ]
    # latestFiles = request_sync(f"{API}/v1/mods/{modId}", headers=HEADERS).json()[
    #     "data"
    # ]["latestFiles"]
    # models = [
    #     File(found=True, **res),
    #     Fingerprint(
    #         found=True, id=res["fileFingerprint"], file=res, latestFiles=latestFiles
    #     ),
    # ]
    # 下面会拉取所有文件，不重复添加
    models = []
    # if not expire:
    # models.extend(sync_mod_all_files(modId, latestFiles=latestFiles))
    models.extend(sync_mod_all_files(modId))
    submit_models(models)


@actor
def sync_mutil_files(fileIds: List[int]):
    models: List[Union[File, Mod]] = []
    res = request_sync(
        method="POST",
        url=f"{API}/v1/mods/files",
        headers=HEADERS,
        json={"fileIds": fileIds},
    ).json()["data"]
    for file in res:
        models.append(File(found=True, **file))
    models = sync_multi_mods_all_files([model.modId for model in models])
    submit_models(models)


@actor
def sync_fingerprints(fingerprints: List[int]):
    res = request_sync(
        method="POST",
        url=f"{API}/v1/fingerprints/432",
        headers=HEADERS,
        json={"fingerprints": fingerprints},
    ).json()
    models: List[Fingerprint] = []
    for file in res["data"]["exactMatches"]:
        models.append(
            Fingerprint(
                id=file["file"]["fileFingerprint"],
                file=file["file"],
                latestFiles=file["latestFiles"],
                found=True,
            )
        )
    models = sync_multi_mods_all_files([model.file.modId for model in models])
    submit_models(models)


@actor
def sync_categories():
    res = request_sync(
        f"{API}/v1/categories", headers=HEADERS, params={"gameId": "432"}
    ).json()["data"]
    redis_engine.hset("curseforge", "categories", json.dumps(res))


@actor(actor_name="cf_file_cdn_url_cache")
def file_cdn_url_cache(url: str, key: str):
    res = request_sync(method="HEAD", url=url, ignore_status_code=True)
    file_cdn_redis_sync_engine.set(key, res.headers["Location"], ex=int(3600 * 2.8))
    log.debug(f"URL cache {key} set {res.headers['Location']}")


@actor
def file_cdn_cache_add_task(file: dict):
    file = File(**file)
    for hash_info in file.hashes:
        if hash_info.algo == 1:
            hash = hash_info.value
            break
    url = file.downloadUrl.replace("edge", "mediafilez")
    download = add_http_task(
        url=url,
        name=hash,
        dir=os.path.join(mcim_config.curseforge_download_path, hash[:2]),
    )
    gid = download.gid
    while True:
        download = ARIA2_API.get_download(gid)
        if download.is_waiting or download.is_active:
            time.sleep(0.5)
        elif download.is_complete:
            file.file_cdn_cached = True
            mongodb_engine.save(file)
            break
        elif download.has_failed:
            return download.error_message


@actor(actor_name="cf_file_cdn_cache")
def file_cdn_cache(file: dict):
    file: File = File(**file)
    hash_ = {}
    for hash_info in file.hashes:
        if hash_info.algo == 1:
            hash_["sha1"] = hash_info.value
        if hash_info.algo == 2:
            hash_["md5"] = hash_info.value
    url = file.downloadUrl
    # url = file.downloadUrl.replace("edge", "mediafilez")
    if url is not None:
        try:
            if hash_:
                hashes_dict = download_file_sync(
                    url=url,
                    path=mcim_config.curseforge_download_path,
                    hash_=hash_,
                    size=file.fileLength,
                    ignore_exist=False,
                )
            else:
                hashes_dict = download_file_sync(
                    url=url,
                    path=mcim_config.curseforge_download_path,
                    ignore_exist=False,
                )
            if len(file.hashes) == 0:
                file.hashes = [
                    {"algo": 1, "value": hashes_dict["sha1"]},
                    {"algo": 2, "value": hashes_dict["md5"]},
                ]
            file.file_cdn_cached = True
            mongodb_engine.save(file)
            log.debug(f"Cached file {file.hashes}")
        except Exception as e:
            log.debug(f"Failed to cache file {file.hashes} {e}")

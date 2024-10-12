from typing import List, Optional, Union
from dramatiq import actor
import dramatiq
import httpx
import json
import os
import time
from datetime import datetime
from odmantic import query

from app.sync import sync_mongo_engine as mongodb_engine
from app.sync import sync_redis_engine as redis_engine
from app.sync import rabbitmq_broker
from app.sync import (
    CURSEFORGE_LIMITER,
    # CURSEFORGE_FILE_CDN_LIMITER,
    # file_cdn_redis_broker,
)  # file_cdn_redis_sync_engine,
from app.sync import SYNC_MODE
from app.models.database.curseforge import File, Mod, Pagination, Fingerprint
from app.models.database.file_cdn import File as FileCDN
from app.utils.network import request_sync, download_file_sync
from app.config import MCIMConfig #, Aria2Config
# from app.utils.aria2 import add_http_task, ARIA2_API
from app.utils.loger import log
from app.utils.webdav import client as webdav_client
from app.exceptions import ResponseCodeException


mcim_config = MCIMConfig.load()
# aria2_config = Aria2Config.load()

API = mcim_config.curseforge_api
MAX_LENGTH = mcim_config.max_file_size
MIN_DOWNLOAD_COUNT = 0
HEADERS = {
    "x-api-key": mcim_config.curseforge_api_key,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.54",
}


def submit_models(models: List[Union[File, Mod, Fingerprint]]):
    mongodb_engine.save_all(models)
    log.debug(f"Submited: {len(models)}")


def should_retry(retries_so_far, exception):
    return retries_so_far < 3 and (
        isinstance(exception, httpx.TransportError)
        or isinstance(exception, dramatiq.RateLimitExceeded)
        or isinstance(exception, dramatiq.middleware.time_limit.TimeLimitExceeded)
    )


# limit decorator
def limit(func):
    def wrapper(*args, **kwargs):
        # if func.__name__ == "file_cdn_cache":
        #     with CURSEFORGE_FILE_CDN_LIMITER.acquire():
        #         return func(*args, **kwargs)
        # else:
        #     with CURSEFORGE_LIMITER.acquire():
        #         return func(*args, **kwargs)
        with CURSEFORGE_LIMITER.acquire():
            return func(*args, **kwargs)

    return wrapper


@actor(
    max_retries=3,
    retry_when=should_retry,
    throws=(ResponseCodeException,),
    min_backoff=1000 * 60,
    actor_name="cf_check_alive",

)
@limit
def check_alive():
    return request_sync(API, headers=HEADERS).text


# def add_file_cdn_tasks(models: List[Union[File, Mod, Fingerprint]]):
#     added_count = 0
#     if mcim_config.file_cdn:
#         for model in models:
#             if isinstance(model, File):
#                 if (
#                     not model.file_cdn_cached
#                     and model.gameId == 432
#                     and model.fileLength <= MAX_LENGTH
#                     and model.downloadCount >= MIN_DOWNLOAD_COUNT
#                 ):
#                     if len(model.hashes) != 0:
#                         if mcim_config.aria2:
#                             file_cdn_cache_add_task.send(model.model_dump())
#                         else:
#                             file_cdn_cache.send_with_options(
#                                 kwargs={"file": model.model_dump(), "checked": False},
#                                 queue_name="file_cdn_cache",
#                             )
#                         added_count += 1
#                         # log.debug(f"File {model.id} cache task added")
#                     else:
#                         file_cdn_cache.send(model.model_dump())
#                         log.debug(f"File {model.id} has no hash")
#     log.debug(f"Added {added_count} file cache tasks") if added_count != 0 else None


def append_model_from_files_res(
    res, latestFiles: dict, need_to_cache: bool = True
) -> List[Union[File, Fingerprint]]:
    models = []
    for file in res["data"]:
        for _hash in file["hashes"]:
            if _hash["algo"] == 1:
                file["sha1"] = _hash["value"]
            elif _hash["algo"] == 2:
                file["md5"] = _hash["value"]
        file_model = File(found=True, need_to_cache=need_to_cache, **file)
        models.append(file_model)
        models.append(
            Fingerprint(
                id=file["fileFingerprint"],
                file=file,
                latestFiles=latestFiles,
                found=True,
            )
        )
        # for file_cdn
        if mcim_config.file_cdn:
            if (
                file_model.sha1 is not None
                and file_model.gameId == 432
                and file_model.fileLength <= MAX_LENGTH
                and file_model.downloadCount >= MIN_DOWNLOAD_COUNT
                and file_model.downloadUrl is not None
            ):
                models.append(
                    FileCDN(
                        sha1=file_model.sha1,
                        url=file_model.downloadUrl,
                        path=file_model.sha1,
                        size=file_model.fileLength,
                        # mtime=(
                        #     file_model.fileDate
                        #     if file_model.fileDate
                        #     else datetime.now()
                        # ),
                        mtime=int(time.time()),
                    )
                )
    return models


# verify_expire: False 为待验证，True 为已验证过期
def sync_mod_all_files(
    modId: int,
    latestFiles: List[dict] = None,
    need_to_cache: bool = True,
    verify_expire: Optional[bool] = False,
) -> List[Union[File, Mod]]:
    if not verify_expire:  # 未确认
        # 再次检查是否已经过期，以免反复 update
        mod_model: Optional[Mod] = mongodb_engine.find_one(Mod, Mod.id == modId)
        if mod_model is not None:
            if (
                time.time()
                <= mod_model.sync_at.timestamp()
                + mcim_config.expire_second.curseforge.mod
            ):
                log.info(f"Mod {modId} is not expired, pass!")
                return None
    models = []
    if not latestFiles:
        data = request_sync(f"{API}/v1/mods/{modId}", headers=HEADERS).json()["data"]
        latestFiles = data["latestFiles"]
        need_to_cache = True if data["classId"] == 6 else False

    params = {"index": 0, "pageSize": 50}
    res = request_sync(
        f"{API}/v1/mods/{modId}/files",
        headers=HEADERS,
        params=params,
    ).json()

    # models.extend(
    #     append_model_from_files_res(res, latestFiles, need_to_cache=need_to_cache)
    # )
    models = append_model_from_files_res(res, latestFiles, need_to_cache=need_to_cache)
    submit_models(models=models)
    log.info(
        f'Finished modid:{modId} i:ps:t {params["index"]}:{params["pageSize"]}:{res["pagination"]["totalCount"]}'
    )
    # add_file_cdn_tasks(models=models)

    page = Pagination(**res["pagination"])
    # index A zero based index of the first item to include in the response, the limit is: (index + pageSize <= 10,000).
    while page.index < page.totalCount - 1:
        params = {"index": page.index + page.pageSize, "pageSize": page.pageSize}
        res = request_sync(
            f"{API}/v1/mods/{modId}/files", headers=HEADERS, params=params
        ).json()
        page = Pagination(**res["pagination"])
        models = append_model_from_files_res(
            res, latestFiles, need_to_cache=need_to_cache
        )
        submit_models(models=models)
        log.info(
            f'Finished modid:{modId} i:ps:t {params["index"]}:{params["pageSize"]}:{page.totalCount}'
        )

def sync_multi_mods_all_files(modIds: List[int]):
    # 去重
    modIds = list(set(modIds))
    mod_models: Optional[List[Mod]] = mongodb_engine.find(
        Mod, query.in_(Mod.id, modIds)
    )
    for mod_model in mod_models:
        if (
            time.time()
            <= mod_model.sync_at.timestamp() + mcim_config.expire_second.curseforge.mod
        ):
            log.info(f"Mod {mod_model.id} is not expired, pass!")
            modIds.remove(mod_model.id)
    for modId in modIds:
        sync_mod_all_files(modId, verify_expire=True)


@actor(
    max_retries=3,
    retry_when=should_retry,
    throws=(ResponseCodeException,),
    min_backoff=1000 * 60,
    actor_name="sync_mod",

)
@limit
def sync_mod(modId: int):
    models: List[Union[File, Mod]] = []
    res = request_sync(f"{API}/v1/mods/{modId}", headers=HEADERS).json()["data"]
    models.append(Mod(found=True, **res))
    mod = mongodb_engine.find_one(Mod, Mod.id == modId)
    if mod is not None:
        if mod.dateReleased == models[0].dateReleased:
            log.info(f"Mod {modId} is not updated, pass!")
            return
    sync_mod_all_files(
        modId,
        latestFiles=res["latestFiles"],
        need_to_cache=True if res["classId"] == 6 else False,
    )
    submit_models(models)


@actor(
    max_retries=3,
    retry_when=should_retry,
    throws=(ResponseCodeException,),
    min_backoff=1000 * 60,
    actor_name="sync_mutil_mods",

)
@limit
def sync_mutil_mods(modIds: List[int]):
    modIds = list(set(modIds))
    data = {"modIds": modIds}
    res = request_sync(
        method="POST", url=f"{API}/v1/mods", json=data, headers=HEADERS
    ).json()["data"]
    models: List[Union[File, Mod]] = []
    mods = mongodb_engine.find(Mod, query.in_(Mod.id, modIds))
    mods_index = {mod.id: mod for mod in mods}
    for mod in res:
        models.append(Mod(found=True, **mod))
        if mods_index.get(mod["id"]) is not None:
            if mods_index[mod["id"]].dateReleased == mod["dateReleased"]:
                log.info(f"Mod {mod['id']} is not updated, pass!")
                modIds.remove(mod["id"])
            
    sync_multi_mods_all_files([model.id for model in models])
    submit_models(models)

@actor(
    max_retries=3,
    retry_when=should_retry,
    throws=(ResponseCodeException,),
    min_backoff=1000 * 60,
    actor_name="sync_file",

)
@limit
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
    # models = []
    # if not expire:
    # models.extend(sync_mod_all_files(modId, latestFiles=latestFiles))
    # models.extend()
    # submit_models(models)
    sync_mod_all_files(modId)


@actor(
    max_retries=3,
    retry_when=should_retry,
    throws=(ResponseCodeException,),
    min_backoff=1000 * 60,
    actor_name="sync_mutil_files",

)
@limit
def sync_mutil_files(fileIds: List[int]):
    # models: List[Union[File, Mod]] = []
    res = request_sync(
        method="POST",
        url=f"{API}/v1/mods/files",
        headers=HEADERS,
        json={"fileIds": fileIds},
    ).json()["data"]
    # for file in res:
    # models.append(File(found=True, **file))
    modids = [file["modId"] for file in res]
    sync_multi_mods_all_files(modids)
    # submit_models(models)


@actor(
    max_retries=3,
    retry_when=should_retry,
    throws=(ResponseCodeException,),
    min_backoff=1000 * 60,
    actor_name="sync_fingerprints",

)
@limit
def sync_fingerprints(fingerprints: List[int]):
    res = request_sync(
        method="POST",
        url=f"{API}/v1/fingerprints/432",
        headers=HEADERS,
        json={"fingerprints": fingerprints},
    ).json()
    # models: List[Fingerprint] = []
    # for file in res["data"]["exactMatches"]:
    # models.append(
    #     Fingerprint(
    #         id=file["file"]["fileFingerprint"],
    #         file=file["file"],
    #         latestFiles=file["latestFiles"],
    #         found=True,
    #     )
    # )
    modids = [file["file"]["modId"] for file in res["data"]["exactMatches"]]
    sync_multi_mods_all_files(modids)
    # submit_models(models)


@actor(
    max_retries=3,
    retry_when=should_retry,
    throws=(ResponseCodeException,),
    min_backoff=1000 * 60,
    actor_name="sync_categories",

)
@limit
def sync_categories():
    res = request_sync(
        f"{API}/v1/categories", headers=HEADERS, params={"gameId": "432"}
    ).json()["data"]
    redis_engine.hset("curseforge", "categories", json.dumps(res))


# @actor(max_retries=3, retry_when=should_retry, throws=(ResponseCodeException,), min_backoff=1000*6, actor_name="cf_file_cdn_url_cache")
# @limit
# def file_cdn_url_cache(url: str, key: str):
#     res = request_sync(method="HEAD", url=url, ignore_status_code=True)
#     file_cdn_redis_sync_engine.set(key, res.headers["Location"], ex=int(3600 * 2.8))
#     log.debug(f"URL cache {key} set {res.headers['Location']}")


# @actor(
#     max_retries=3,
#     retry_when=should_retry,
#     throws=(ResponseCodeException,),
#     min_backoff=1000 * 60,
#     actor_name="cf_file_cdn_cache_add_task",
# )
# @limit
# def file_cdn_cache_add_task(file: dict):
#     file_model = File(**file)
#     for hash_info in file_model.hashes:
#         if hash_info.algo == 1:
#             hash = hash_info.value
#             break
#     url = file_model.downloadUrl.replace("edge", "mediafilez")
#     download = add_http_task(
#         url=url,
#         name=hash,
#         dir=os.path.join(mcim_config.curseforge_download_path, hash[:2]),
#     )
#     gid = download.gid
#     while True:
#         download = ARIA2_API.get_download(gid)
#         if download.is_waiting or download.is_active:
#             time.sleep(0.5)
#         elif download.is_complete:
#             file_model.file_cdn_cached = True
#             mongodb_engine.save(file_model)
#             break
#         elif download.has_failed:
#             return download.error_message


# @actor(
#     max_retries=3,
#     retry_when=should_retry,
#     throws=(ResponseCodeException,),
#     min_backoff=1000 * 60,
#     actor_name="cf_file_cdn_cache",
#     queue_name="file_cdn_cache",
#     broker=file_cdn_redis_broker,
# )
# @limit
# def file_cdn_cache(file: dict, checked: bool = False):
#     file: File = File(**file)
#     hash_ = {}
#     for hash_info in file.hashes:
#         if hash_info.algo == 1:
#             hash_["sha1"] = hash_info.value
#         if hash_info.algo == 2:
#             hash_["md5"] = hash_info.value
#     url = file.downloadUrl
#     # url = file.downloadUrl.replace("edge", "mediafilez")
#     if url is not None:
#         try:
#             if len(hash_.values()) == 2:
#                 hashes_dict = download_file_sync(
#                     url=url,
#                     path=mcim_config.curseforge_download_path,
#                     hash_=hash_,
#                     size=file.fileLength,
#                     ignore_exist=False if not checked else True,
#                 )
#             else:
#                 hashes_dict = download_file_sync(
#                     url=url,
#                     path=mcim_config.curseforge_download_path,
#                     ignore_exist=False if not checked else True,
#                 )
#             if file.hashes is not None:
#                 if len(file.hashes) == 0:
#                     file.hashes = [
#                         {"algo": 1, "value": hashes_dict["sha1"]},
#                         {"algo": 2, "value": hashes_dict["md5"]},
#                     ]
#             file.file_cdn_cached = True
#             mongodb_engine.save(file)
#             log.debug(f"Saved {file.id}")
#         except Exception as e:
#             log.exception(e)
#             log.error(f"Failed to cache file {file.hashes}")
#     else:
#         log.debug(f"File {file.id} has no download url")

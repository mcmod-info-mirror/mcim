"""
拉取 Modrinth 信息

version 信息包含了 file 信息，所以拉取 version 信息时，会拉取 version 下的所有 file 信息

sync_project 只刷新 project 信息，不刷新 project 下的 version 信息

刷新 project 信息后，会刷新 project 下的所有 version 信息，以及 version 下的所有 file 信息，不刷新 project 自身信息

同步逻辑：
1. 刷新 project | 触发条件: project 不存在或已经过期 -> sync_project -> 刷新 project 下的所有 version -> 刷新 project 下的所有 File

2. 刷新 version | 触发条件: version 不存在或已经过期 -> sync_version -> 刷新 version 下的 File -> 刷新 project 下的所有 version

3. 刷新 hash | 触发条件: hash 不存在 -> sync_hash -> 刷新 hash 下的 File -> 刷新 project 下的所有 version
"""

from typing import List, Optional, Union
from dramatiq import actor
import dramatiq
import json
import os
import time
import httpx
from datetime import datetime
from odmantic import query

from app.sync import sync_mongo_engine as mongodb_engine
from app.sync import sync_redis_engine as redis_engine
from app.sync import rabbitmq_broker
from app.sync import (
    MODRINTH_LIMITER,
    # MODRINTH_FILE_CDN_LIMITER,
    # file_cdn_redis_broker,
)  # file_cdn_redis_sync_engine,
from app.models.database.modrinth import Project, File, Version
from app.models.database.file_cdn import File as FileCDN
from app.utils.network import request_sync, download_file_sync
from app.exceptions import ResponseCodeException
from app.config import MCIMConfig  # , Aria2Config

# from app.utils.aria2 import add_http_task, ARIA2_API
from app.utils.loger import log

mcim_config = MCIMConfig.load()
# aria2_config = Aria2Config.load()

API = mcim_config.modrinth_api
MAX_LENGTH = mcim_config.max_file_size


def submit_models(models: List[Union[Project, File, Version]]):
    # 弃用 alist 同步任务
    # if mcim_config.file_cdn:
    #     for model in models:
    #         if isinstance(model, File):
    #             if (
    #                 model.size <= MAX_LENGTH
    #                 and model.filename
    #                 and model.url
    #                 and model.hashes.sha1
    #             ):
    #                 models.append(
    #                     FileCDN(
    #                         url=model.url,
    #                         sha1=model.hashes.sha1,
    #                         size=model.size,
    #                         mtime=int(time.time()),
    #                         path=model.hashes.sha1,
    #                     )
    #                 )
    #             if not model.file_cdn_cached and model.size <= MAX_LENGTH:
    #                 # if not fs.exists(
    #                 #     os.path.join(
    #                 #         mcim_config.modrinth_download_path,
    #                 #         model.hashes.sha1[:2],
    #                 #         model.hashes.sha1,
    #                 #     )
    #                 # ):
    #                 if mcim_config.aria2:
    #                     file_cdn_cache_add_task.send(model.model_dump())
    #                 else:
    #                     file_cdn_cache.send_with_options(
    #                         kwargs={"file": model.model_dump(), "checked": False},
    #                         queue_name="file_cdn_cache",
    #                     )
    log.debug(f"Submited: {len(models)}")
    mongodb_engine.save_all(models)


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
        #     with MODRINTH_FILE_CDN_LIMITER.acquire():
        #         return func(*args, **kwargs)
        # else:
        #     with MODRINTH_LIMITER.acquire():
        #         return func(*args, **kwargs)
        with MODRINTH_LIMITER.acquire():
            return func(*args, **kwargs)

    return wrapper


@actor(
    max_retries=3,
    retry_when=should_retry,
    throws=(ResponseCodeException,),
    min_backoff=1000 * 60,
    actor_name="check_alive",
)
@limit
def check_alive():
    res = request_sync("https://api.modrinth.com")
    return res.json()


@actor(
    max_retries=3,
    retry_when=should_retry,
    throws=(ResponseCodeException,),
    min_backoff=1000 * 60,
    actor_name="sync_project_all_version",
)
@limit
def sync_project_all_version(
    project_id: str,
    slug: Optional[str] = None,
    verify_expire: bool = False,
) -> List[Union[Project, File, Version]]:
    if not verify_expire:
        project: Optional[Project] = mongodb_engine.find_one(
            Project, Project.id == project_id
        )
        if project:
            if (
                time.time()
                <= project.sync_at.timestamp()
                + mcim_config.expire_second.modrinth.project
            ):
                log.info(f"Project {project_id} is not expired, pass!")
                return
            elif not slug:
                slug = project.slug

    models = []
    if not slug:
        project = mongodb_engine.find_one(Project, Project.id == project_id)
        if project:
            slug = project.slug
        else:
            try:
                res = request_sync(f"{API}/project/{project_id}").json()
            except ResponseCodeException as e:
                if e.status_code == 404:
                    models.append(Project(found=False, id=project_id, slug=project_id))
                    return
            slug = res["slug"]
    try:
        res = request_sync(f"{API}/project/{project_id}/version").json()
    except ResponseCodeException as e:
        if e.status_code == 404:
            models.append(Project(found=False, id=project_id, slug=project_id))
            return
    for version in res:
        for file in version["files"]:
            file["version_id"] = version["id"]
            file["project_id"] = version["project_id"]
            file_model = File(found=True, slug=slug, **file)
            if (
                file_model.size <= MAX_LENGTH
                and file_model.filename
                and file_model.url
                and file_model.hashes.sha1
            ):
                models.append(
                    FileCDN(
                        url=file_model.url,
                        sha1=file_model.hashes.sha1,
                        size=file_model.size,
                        mtime=int(time.time()),
                        path=file_model.hashes.sha1,
                    )
                )
            models.append(file_model)
            if len(models) >= 100:
                submit_models(models)
                models = []
        models.append(Version(found=True, slug=slug, **version))
    submit_models(models)


def sync_multi_projects_all_version(
    project_ids: List[str],
    slugs: Optional[dict] = None,
    # ) -> List[Union[Project, File, Version]]:
) -> None:
    mod_models: Optional[List[Project]] = mongodb_engine.find(
        Project, query.in_(Project.id, project_ids)
    )
    if mod_models:
        for model in mod_models:
            if (
                time.time()
                <= model.sync_at.timestamp()
                + mcim_config.expire_second.modrinth.project
            ):
                project_ids.remove(model.id)
                log.info(f"Project {model.id} is not expired, pass!")

    for project_id in project_ids:
        sync_project_all_version(
            project_id, slug=slugs[project_id] if slugs else None, verify_expire=True
        )


@actor(
    max_retries=3,
    retry_when=should_retry,
    throws=(ResponseCodeException,),
    min_backoff=1000 * 60,
    actor_name="sync_project",
)
@limit
def sync_project(project_id: str):
    models = []
    try:
        res = request_sync(f"{API}/project/{project_id}").json()
        models.append(Project(found=True, **res))
        db_project = mongodb_engine.find_one(Project, Project.id == project_id)
        if db_project is not None:
            # check updated
            if db_project.updated != res["updated"]:
                models.append(Project(found=True, **res))
                sync_project_all_version(project_id, slug=res["slug"])
            else:
                return
    except ResponseCodeException as e:
        if e.status_code == 404:
            models = [Project(found=False, id=project_id, slug=project_id)]
    submit_models(models)


@actor(
    max_retries=3,
    retry_when=should_retry,
    throws=(ResponseCodeException,),
    min_backoff=1000 * 60,
    actor_name="sync_multi_projects",
)
@limit
def sync_multi_projects(project_ids: List[str]):
    try:
        res = request_sync(
            f"{API}/projects", params={"ids": json.dumps(project_ids)}
        ).json()
    except ResponseCodeException as e:
        if e.status_code == 404:
            models = []
            for project_id in project_ids:
                models.append(Project(found=False, id=project_id, slug=project_id))
            submit_models(models)
            return
    db_projects = mongodb_engine.find(Project, query.in_(Project.id, project_ids))
    temp_db_projects_updated = {}
    for db_project in db_projects:
        temp_db_projects_updated[db_project.id] = db_project.updated
    for project_res in res:
        if project_res["id"] in temp_db_projects_updated:
            if temp_db_projects_updated[project_res["id"]] == project_res["updated"]:
                project_ids.remove(project_res["id"])
                log.info(f"Project {project_res['id']} is not out-of-date, pass!")

    models = []
    slugs = {}
    for project_res in res:
        slugs[project_res["id"]] = project_res["slug"]
        models.append(Project(found=True, **project_res))
    sync_multi_projects_all_version(project_ids, slugs=slugs)
    submit_models(models)


def process_version_resp(res: dict) -> List[Union[Project, File, Version]]:
    models = []
    for file in res["files"]:
        file["version_id"] = res["id"]
        file["project_id"] = res["project_id"]
        models.append(File(found=True, **file))
    models.append(Version(found=True, **res))
    return models


@actor(
    max_retries=3,
    retry_when=should_retry,
    throws=(ResponseCodeException,),
    min_backoff=1000 * 60,
    actor_name="sync_version",
)
@limit
def sync_version(version_id: str):
    try:
        res = request_sync(f"{API}/version/{version_id}").json()
    except ResponseCodeException as e:
        if e.status_code == 404:
            models = [Version(found=False, id=version_id)]
            # submit_models(models)
            return
    sync_project_all_version(res["project_id"])


def process_multi_versions(res: List[dict]):
    models = []
    for version in res:
        for file in version["files"]:
            file["version_id"] = version["id"]
            file["project_id"] = res["project_id"]
            models.append(File(found=True, **file))
        models.append(Version(found=True, **version))
    return models


@actor(
    max_retries=3,
    retry_when=should_retry,
    throws=(ResponseCodeException,),
    min_backoff=1000 * 60,
    actor_name="sync_multi_versions",
)
@limit
def sync_multi_versions(version_ids: List[str]):
    try:
        res = request_sync(
            f"{API}/versions", params={"ids": json.dumps(version_ids)}
        ).json()
    except ResponseCodeException as e:
        if e.status_code == 404:
            models = []
            for version_id in version_ids:
                models.append(Version(found=False, id=version_id))
            submit_models(models)
            return
    project_ids = list(set([version["project_id"] for version in res]))  # 去重
    sync_multi_projects_all_version(project_ids)


@actor(
    max_retries=3,
    retry_when=should_retry,
    throws=(ResponseCodeException,),
    min_backoff=1000 * 60,
    actor_name="sync_hash",
)
@limit
def sync_hash(hash: str, algorithm: str):
    try:
        res = request_sync(
            f"{API}/version_file/{hash}", params={"algorithm": algorithm}
        ).json()
    except ResponseCodeException as e:
        # if e.status_code == 404:
        #     models = [File(found=False, hash=hash)]
        #     submit_models(models)
        #     return
        return
    sync_project_all_version(res["project_id"])


def process_multi_hashes(res: dict):
    models = []
    for version in res.values():
        for file in version["files"]:
            file["version_id"] = version["id"]
            file["project_id"] = version["project_id"]
            models.append(File(found=True, **file))
        models.append(Version(found=True, **version))
    return models


@actor(
    max_retries=3,
    retry_when=should_retry,
    throws=(ResponseCodeException,),
    min_backoff=1000 * 60,
    actor_name="sync_multi_hashes",
)
@limit
def sync_multi_hashes(hashes: List[str], algorithm: str):
    try:
        res = request_sync(
            method="POST",
            url=f"{API}/version_files",
            json={"hashes": hashes, "algorithm": algorithm},
        ).json()
    except ResponseCodeException as e:
        # if e.status_code == 404:
        #     models = []
        #     for hash in hashes:
        #         models.append(File(found=False, hash=hash))
        #     submit_models(models)
        return
    # models = []
    # models.extend(process_multi_hashes(res))
    sync_multi_projects_all_version([version["project_id"] for version in res.values()])
    # submit_models(models)


@actor(
    max_retries=3,
    retry_when=should_retry,
    throws=(ResponseCodeException,),
    min_backoff=1000 * 60,
    actor_name="sync_tags",
)
@limit
def sync_tags():
    # db 1
    categories = request_sync(f"{API}/tag/category").json()
    loaders = request_sync(f"{API}/tag/loader").json()
    game_versions = request_sync(f"{API}/tag/game_version").json()
    donation_platform = request_sync(f"{API}/tag/donation_platform").json()
    project_type = request_sync(f"{API}/tag/project_type").json()
    side_type = request_sync(f"{API}/tag/side_type").json()

    redis_engine.hset("modrinth", "categories", json.dumps(categories))
    redis_engine.hset("modrinth", "loaders", json.dumps(loaders))
    redis_engine.hset("modrinth", "game_versions", json.dumps(game_versions))
    redis_engine.hset("modrinth", "donation_platform", json.dumps(donation_platform))
    redis_engine.hset("modrinth", "project_type", json.dumps(project_type))
    redis_engine.hset("modrinth", "side_type", json.dumps(side_type))


# # file cdn url cache
# @actor(max_retries=3, retry_when=should_retry, throws=(ResponseCodeException,), min_backoff=1000*60, actor_name="mr_file_cdn_url_cache")
# @limit
# def file_cdn_url_cache(url: str, key: str):
#     res = request_sync(method="HEAD", url=url, ignore_status_code=True)
#     file_cdn_redis_sync_engine.set(key, res.headers["Location"], ex=int(3600 * 2.8))
#     log.debug(f"URL cache set [{key}]:[{res.headers['Location']}]")


# @actor(
#     max_retries=3,
#     retry_when=should_retry,
#     throws=(ResponseCodeException,),
#     min_backoff=1000 * 60,
#     actor_name="mr_file_cdn_cache_add_task",
# )
# @limit
# def file_cdn_cache_add_task(file: dict):
#     file = File(**file)
#     sha1 = file.hashes.sha1
#     download = add_http_task(
#         url=file.url,
#         name=sha1,
#         dir=os.path.join(mcim_config.modrinth_download_path, sha1[:2]),
#     )
#     gid = download.gid
#     while True:
#         download = ARIA2_API.get_download(gid)
#         if download.is_waiting or download.is_active:
#             time.sleep(0.5)
#         elif download.is_complete:
#             file.file_cdn_cached = True
#             mongodb_engine.save(file)
#             break
#         elif download.has_failed:
#             return download.error_message


# # 默认 modrinth 提供 hashes 我累了
# @actor(
#     max_retries=3,
#     retry_when=should_retry,
#     throws=(ResponseCodeException,),
#     min_backoff=1000 * 60,
#     actor_name="mr_file_cdn_cache",
#     queue_name="file_cdn_cache",
#     broker=file_cdn_redis_broker,
# )
# @limit
# def file_cdn_cache(file: dict, checked: bool = False):
#     file: File = File(**file)
#     if file.hashes:
#         hash_ = {"sha1": file.hashes.sha1}
#     try:
#         download_file_sync(
#             url=file.url,
#             path=mcim_config.modrinth_download_path,
#             hash_=hash_,
#             size=file.size,
#             ignore_exist=False if not checked else True,
#         )
#         file.file_cdn_cached = True
#         mongodb_engine.save(file)
#         log.debug(f"Cached file {file.hashes}")
#     except Exception as e:
#         log.debug(f"Failed to cache file {file.hashes} {e}")

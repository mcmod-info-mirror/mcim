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
import json
import os
import time

from app.sync import sync_mongo_engine as mongodb_engine
from app.sync import sync_redis_engine as redis_engine
from app.sync import file_cdn_redis_sync_engine
from app.models.database.modrinth import Project, File, Version
from app.utils.network import request_sync
from app.exceptions import ResponseCodeException
from app.config import MCIMConfig, Aria2Config
from app.utils.aria2 import add_http_task, ARIA2_API

mcim_config = MCIMConfig.load()
aria2_config = Aria2Config.load()

API = mcim_config.modrinth_api


def submit_models(models: List[Union[Project, File, Version]]):
    if mcim_config.file_cdn:
        for model in models:
            if isinstance(model, File):
                if not model.file_cdn_cached:
                    if not os.path.exists(os.path.join(aria2_config.modrinth_download_path, model.hashes.sha512)):
                        file_cdn_cache_add_task.send(model)
                    else:
                        model.file_cdn_cached = True
                        mongodb_engine.save(model)
    mongodb_engine.save_all(models)


@actor
def check_alive():
    res = request_sync("https://api.modrinth.com")
    return res.json()


@actor
def sync_project_all_version(
    project_id: str,
    slug: Optional[str] = None,
) -> List[Union[Project, File, Version]]:
    models = []
    if not slug:
        project = mongodb_engine.find_one(Project, {"id": project_id})
        if project:
            slug = project.slug
        else:
            try:
                res = request_sync(f"{API}/project/{project_id}").json()
            except ResponseCodeException as e:
                if e.status_code == 404:
                    models.append(
                        Project(success=False, id=project_id, slug=project_id)
                    )
                    return
            slug = res["slug"]
    try:
        res = request_sync(f"{API}/project/{project_id}/version").json()
    except ResponseCodeException as e:
        if e.status_code == 404:
            models.append(Project(success=False, id=project_id, slug=project_id))
            return
    for version in res:
        for file in version["files"]:
            file["version_id"] = version["id"]
            models.append(File(found=True, slug=slug, **file))
        models.append(Version(found=True, slug=slug, **version))
    return models


def sync_multi_projects_all_version(
    project_ids: List[str],
    slugs: Optional[dict] = None,
) -> List[Union[Project, File, Version]]:
    models = []
    for project_id in project_ids:
        models.extend(
            sync_project_all_version(
                project_id, slug=slugs[project_id] if slugs else None
            )
        )
    return models


@actor
def sync_project(project_id: str):
    models = []
    try:
        res = request_sync(f"{API}/project/{project_id}").json()
        models.append(Project(found=True, **res))
    except ResponseCodeException as e:
        if e.status_code == 404:
            models = [Project(success=False, id=project_id, slug=project_id)]
            submit_models(models)
            return
    models.extend(sync_project_all_version(project_id, slug=res["slug"]))
    submit_models(models)


@actor
def sync_multi_projects(project_ids: List[str]):
    try:
        res = request_sync(f"{API}/projects", params={"ids": json.dumps(project_ids)}).json()
    except ResponseCodeException as e:
        if e.status_code == 404:
            models = []
            for project_id in project_ids:
                models.append(Project(success=False, id=project_id, slug=project_id))
            submit_models(models)
            return
    models = []
    slugs = {}
    for project in res:
        slugs[project["id"]] = project["slug"]
        models.append(Project(found=True, **project))
    models.extend(sync_multi_projects_all_version(project_ids, slugs=slugs))
    submit_models(models)


def process_version_resp(res: dict) -> List[Union[Project, File, Version]]:
    models = []
    for file in res["files"]:
        file["version_id"] = res["id"]
        models.append(File(found=True, **file))
    models.append(Version(found=True, **res))
    return models


@actor
def sync_version(version_id: str):
    try:
        res = request_sync(f"{API}/version/{version_id}").json()
    except ResponseCodeException as e:
        if e.status_code == 404:
            models = [Version(success=False, id=version_id)]
            submit_models(models)
            return

    models = []
    models.extend(process_version_resp(res, models))
    models.extend(sync_project_all_version(res["project_id"]))
    submit_models(models)


def process_multi_versions(res: List[dict]):
    models = []
    for version in res:
        for file in version["files"]:
            file["version_id"] = version["id"]
            models.append(File(found=True, **file))
        models.append(Version(found=True, **version))
    return models


@actor
def sync_multi_versions(version_ids: List[str]):
    try:
        res = request_sync(f"{API}/versions", params={"ids": json.dumps(version_ids)}).json()
    except ResponseCodeException as e:
        if e.status_code == 404:
            models = []
            for version_id in version_ids:
                models.append(Version(success=False, id=version_id))
            submit_models(models)
            return
    models = []
    models.extend(process_multi_versions(res))
    models.extend(
        sync_multi_projects_all_version([version["project_id"] for version in res])
    )
    submit_models(models)


@actor
def sync_hash(hash: str, algorithm: str):
    try:
        res = request_sync(
            f"{API}/version_file/{hash}", params={"algorithm": algorithm}
        ).json()
    except ResponseCodeException as e:
        if e.status_code == 404:
            models = [File(success=False, hash=hash)]
            submit_models(models)
            return
    models = []
    models.extend(process_version_resp(res))
    models.extend(sync_project_all_version(res["project_id"]))
    submit_models(models)


def process_multi_hashes(res: dict):
    models = []
    for version in res.values():
        for file in version["files"]:
            file["version_id"] = version["id"]
            models.append(File(found=True, **file))
        models.append(Version(found=True, **version))
    return models


@actor
def sync_multi_hashes(hashes: List[str], algorithm: str):
    try:
        res = request_sync(
            method="POST",
            url=f"{API}/version_files",
            json={"hashes": hashes, "algorithm": algorithm},
        ).json()
    except ResponseCodeException as e:
        if e.status_code == 404:
            models = []
            for hash in hashes:
                models.append(File(success=False, hash=hash))
            submit_models(models)
            return
    models = []
    models.extend(process_multi_hashes(res))
    models.extend(
        sync_multi_projects_all_version(
            [version["project_id"] for version in res.values()]
        )
    )
    submit_models(models)


@actor
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


# file cdn url cache
@actor
def file_cdn_url_cache(url: str, key: str):
    res = request_sync(method="HEAD", url=url, ignore_status_code=True)
    file_cdn_redis_sync_engine.hset("file_cdn_modrinth", key, res.headers["Location"])
    return res.headers["Location"]

@actor
def file_cdn_cache_add_task(file: File):
    sha1 = file.hashes.sha1
    download = add_http_task(url=file.url, name=sha1, dir=os.path.join(aria2_config.modrinth_download_path, sha1[:2]))
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
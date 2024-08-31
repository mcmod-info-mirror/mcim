from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from odmantic import query
from typing import Optional
import time
import httpx
from email.utils import formatdate

from app.models.database.curseforge import File as cfFile
from app.models.database.modrinth import File as mrFile
from app.config import MCIMConfig
from app.utils.loger import log
from app.utils.response_cache import cache
from app.utils.network import ResponseCodeException
from app.utils.network import request as request_async
from app.sync.modrinth import file_cdn_cache_add_task as mr_file_cdn_cache_add_task
from app.sync.curseforge import file_cdn_cache_add_task as cf_file_cdn_cache_add_task
from app.sync.curseforge import file_cdn_cache as cf_file_cdn_cache
from app.sync.modrinth import file_cdn_cache as mr_file_cdn_cache
from app.sync.modrinth import sync_project
from app.sync.curseforge import sync_mutil_files
from app.utils.metric import FILE_CDN_FORWARD_TO_ALIST_COUNT, FILE_CDN_FORWARD_TO_ORIGIN_COUNT


mcim_config = MCIMConfig.load()

# expire 3h
file_cdn_router = APIRouter()
ARIA2_ENABLED: bool = mcim_config.aria2
MAX_AGE = int(60 * 60 * 2.5)
CDN_MAX_AGE = int(60 * 60 * 2.8)
MAX_LENGTH = mcim_config.max_file_size
TIMEOUT = 2.5


def get_http_date(delay: int = CDN_MAX_AGE):
    # Get the current timestamp
    timestamp = time.time()
    timestamp += delay

    # Convert the timestamp to an HTTP date
    http_date = formatdate(timestamp, usegmt=True)
    return http_date


if mcim_config.file_cdn:
    # modrinth | example: https://cdn.modrinth.com/data/AANobbMI/versions/IZskON6d/sodium-fabric-0.5.8%2Bmc1.20.6.jar
    # WARNING: 直接查 version_id 忽略 project_id
    # WARNING: 必须文件名一致
    @file_cdn_router.get(
        "/data/{project_id}/versions/{version_id}/{file_name}", tags=["modrinth"]
    )
    @cache(expire=MAX_AGE)
    async def get_modrinth_file(
        project_id: str, version_id: str, file_name: str, request: Request
    ):
        file: Optional[mrFile] = await request.app.state.aio_mongo_engine.find_one(
            mrFile,
            query.and_(
                mrFile.project_id == project_id,
                mrFile.version_id == version_id,
                mrFile.filename == file_name,
                mrFile.found == True,
            ),
        )
        if file:
            if file.size <= MAX_LENGTH:
                sha1 = file.hashes.sha1
                alist_url = f"{mcim_config.alist_endpoint}/modrinth/{sha1[:2]}/{sha1}"
                if file.file_cdn_cached:
                    # 存在于网盘中
                    try:
                        alist_res = await request_async(
                            method="HEAD", url=alist_url, ignore_status_code=True, timeout=TIMEOUT
                        )
                        raw_url = alist_res.headers.get("Location")
                        if raw_url:
                            if 400 > alist_res.status_code > 200:
                                expires_date = get_http_date()
                                log.info(f"Redirect to {raw_url}")
                                FILE_CDN_FORWARD_TO_ALIST_COUNT.labels("modrinth").inc()
                                return RedirectResponse(
                                    url=raw_url,
                                    headers={
                                        "Cache-Control": "public",
                                        "Expires": expires_date,
                                    },
                                )
                    except (httpx.ConnectError, httpx.TimeoutException, ResponseCodeException) as e:
                        log.error(f"Failed: {alist_url} {e}")
                else:
                    # 文件不存在
                    if ARIA2_ENABLED:
                        mr_file_cdn_cache_add_task.send(file.model_dump())
                        log.debug(
                            f"file cache not found, {alist_url} send with aria2 mode."
                        )
                    else:
                        mr_file_cdn_cache.send(file.model_dump())
                        log.debug(
                            f"file cache not found, {alist_url} send with normal mode."
                        )
        else:
            # 文件信息不存在
            sync_project.send(project_id)
            log.debug(f"sync project {project_id} task send.")

        url = f"https://cdn.modrinth.com/data/{project_id}/versions/{version_id}/{file_name}"
        log.info(f"Redirect to {url}")
        FILE_CDN_FORWARD_TO_ORIGIN_COUNT.labels("modrinth").inc()
        return RedirectResponse(url=url, headers={"Cache-Control": "public, no-cache"})

    # curseforge | example: https://edge.forgecdn.net/files/3040/523/jei_1.12.2-4.16.1.301.jar
    @file_cdn_router.get("/files/{fileid1}/{fileid2}/{file_name}", tags=["curseforge"])
    @cache(expire=MAX_AGE)
    async def get_curseforge_file(
        fileid1: int, fileid2: int, file_name: str, request: Request
    ):
        fileid = int(f"{fileid1}{fileid2}")
        file: Optional[cfFile] = await request.app.state.aio_mongo_engine.find_one(
            cfFile,
            query.and_(
                cfFile.id == fileid, cfFile.fileName == file_name, cfFile.found == True
            ),
        )
        if file:  # 数据库中有文件
            if file.fileLength <= MAX_LENGTH:
                sha1 = (
                    file.hashes[0].value
                    if file.hashes[0].algo == 1
                    else file.hashes[1].value
                )
                alist_url = f"{mcim_config.alist_endpoint}/curseforge/{sha1[:2]}/{sha1}"
                if file.file_cdn_cached:
                    # 存在于网盘中
                    try:
                        alist_res = await request_async(
                            method="HEAD", url=alist_url, ignore_status_code=True, timeout=TIMEOUT
                        )
                        raw_url = alist_res.headers.get("Location")
                        if raw_url:
                            if 400 > alist_res.status_code > 200:
                                expires_date = get_http_date()
                                log.info(f"Redirect to {raw_url}")
                                FILE_CDN_FORWARD_TO_ALIST_COUNT.labels("curseforge").inc()
                                return RedirectResponse(
                                    url=raw_url,
                                    headers={
                                        "Cache-Control": "public",
                                        "Expires": expires_date,
                                    },
                                )
                            else:
                                log.debug(f"Failed: alist_res: {alist_res.__dict__}")
                    except (httpx.ConnectError, httpx.TimeoutException, ResponseCodeException) as e:
                        log.error(f"Failed: {alist_url} {e}")
                else:
                    # if not file.need_to_cache:
                    #     return RedirectResponse(
                    #         url=file.downloadUrl,
                    #         headers={
                    #             "Cache-Control": "public, max-age=31536000"
                    #         },  # 我就没打算存你
                    #     )
                    if ARIA2_ENABLED:
                        cf_file_cdn_cache_add_task.send(file.model_dump())
                        log.debug(
                            f"file cache not found, {alist_url} send with aria2 mode."
                        )
                    else:
                        cf_file_cdn_cache.send(file.model_dump())
                        log.debug(
                            f"file cache not found, {alist_url} send with normal mode."
                        )
            else:
                log.debug(f"File {fileid} is too large, {file.fileLength} > {MAX_LENGTH}")
        else:
            sync_mutil_files.send([fileid])
            log.debug(f"sync fileId {fileid} task send.")

        url = f"https://media.forgecdn.net/files/{fileid1}/{fileid2}/{file_name}"
        log.debug(f"Redirect to {url}")
        FILE_CDN_FORWARD_TO_ORIGIN_COUNT.labels("curseforge").inc()
        return RedirectResponse(url=url, headers={"Cache-Control": "public, no-cache"})

"""
与网络请求相关的模块
"""

import httpx
from tenacity import retry, stop_after_attempt
from typing import Optional, Union
from app.exceptions import ApiException, ResponseCodeException
from app.config.mcim import MCIMConfig
from app.utils.loger import log

mcim_config = MCIMConfig.load()


PROXY: Optional[str] = mcim_config.proxies

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.54",
}

TIMEOUT = 5
RETRY_TIMES = 3
REQUEST_LOG = True


httpx_async_client: httpx.AsyncClient = httpx.AsyncClient(proxies=PROXY)
httpx_sync_client: httpx.Client = httpx.Client(proxies=PROXY)


def get_session() -> httpx.Client:
    global httpx_sync_client
    if httpx_sync_client:
        return httpx_sync_client
    else:
        httpx_sync_client = httpx.Client()
        return httpx_sync_client


def get_async_session() -> httpx.AsyncClient:
    global httpx_async_client
    if httpx_async_client:
        return httpx_async_client
    else:
        httpx_async_client = httpx.AsyncClient()
        return httpx_async_client

@retry(stop=stop_after_attempt(RETRY_TIMES), reraise=True)
def request_sync(
    url: str,
    method: str = "GET",
    data: Optional[dict] = None,
    params: Optional[dict] = None,
    json: Optional[dict] = None,
    ignore_status_code: bool = False,
    **kwargs
) -> httpx.Response:
    """
    HTTPX 请求函数

    Args:
        url (str): 请求 URL

        method (str, optional): 请求方法 默认 GET

        **kwargs: 其他参数

    Returns:
        Any: 请求结果
    """
    # delete null query
    if params is not None:
        params = {k: v for k, v in params.items() if v is not None}

    session = get_session()

    if json is not None:
        res: httpx.Response = session.request(
            method, url, json=json, params=params, **kwargs
        )
    else:
        res: httpx.Response = session.request(
            method, url, data=data, params=params, **kwargs
        )
    if not ignore_status_code:
        if res.status_code != 200:
            raise ResponseCodeException(
                status_code=res.status_code,
                method=method,
                url=url,
                data=data if data is None else json,
                params=params,
                msg=res.text,
            )
    return res


@retry(stop=stop_after_attempt(RETRY_TIMES), reraise=True)
async def request(
    url: str,
    method: str = "GET",
    data: Optional[dict] = None,
    params: Optional[dict] = None,
    json: Optional[dict] = None,
    ignore_status_code: bool = False,
    **kwargs
) -> httpx.Response:
    """
    HTTPX 请求函数

    Args:
        url (str): 请求 URL

        method (str, optional): 请求方法 默认 GET

        **kwargs: 其他参数

    Returns:
        Any: 请求结果
    """
    # delete null query
    if params is not None:
        params = {k: v for k, v in params.items() if v is not None}

    session = get_async_session()

    if json is not None:
        res: httpx.Response = await session.request(
            method, url, json=json, params=params, **kwargs
        )
    else:
        res: httpx.Response = await session.request(
            method, url, data=data, params=params, **kwargs
        )
    if not ignore_status_code:
        if res.status_code != 200:
            raise ResponseCodeException(
                status_code=res.status_code,
                method=method,
                url=url,
                data=data if data is None else json,
                params=params,
                msg=res.text,
            )
    return res

@retry(stop=stop_after_attempt(RETRY_TIMES), reraise=True)
async def download_file(url: str, path: str):
    """
    下载文件

    Args:
        url (str): 下载链接

        path (str): 保存路径
    """
    log.debug(f"Downloading file from {url} to {path}")
    async with get_async_session() as client:
        async with client.stream("GET", url) as response:
            with open(path, "wb") as f:
                async for chunk in response.aiter_bytes():
                    f.write(chunk)
    log.debug(f"Downloaded file from {url} to {path}")

@retry(stop=stop_after_attempt(RETRY_TIMES), reraise=True)
def download_file_sync(url: str, path: str):
    """
    下载文件

    Args:
        url (str): 下载链接

        path (str): 保存路径
    """
    log.debug(f"Downloading file from {url} to {path}")
    with get_session() as client:
        with open(path, "wb") as f:
            with client.stream("GET", url, timeout=30) as response:
                for chunk in response.iter_bytes(1024):
                    f.write(chunk)
    log.debug(f"Downloaded file from {url} to {path}")
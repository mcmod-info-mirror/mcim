"""
与网络请求相关的模块
"""

import httpx
from tenacity import retry, stop_after_attempt

from app.exceptions import ApiException, ResponseCodeException
from app.config.mcim import MCIMConfig

mcim_config = MCIMConfig.load()


PROXY: str = mcim_config.proxies

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


# def retry_sync(times: int = RETRY_TIMES):
#     """
#     重试装饰器

#     Args:
#         times (int): 最大重试次数 默认 3 次 负数则一直重试直到成功

#     Returns:
#         Any: 原函数调用结果
#     """

#     def wrapper(func):
#         def inner(*args, **kwargs):
#             nonlocal times
#             loop = times
#             while loop != 0:
#                 loop -= 1
#                 try:
#                     return func(*args, **kwargs)
#                 except json.decoder.JSONDecodeError:
#                     continue
#                 except ResponseCodeException as e:
#                     raise e
#                 # TIMEOUT
#             raise ApiException("重试达到最大次数")

#         return inner

#     return wrapper


# def retry(times: int = RETRY_TIMES):
#     """
#     重试装饰器

#     Args:
#         times (int): 最大重试次数 默认 3 次 负数则一直重试直到成功

#     Returns:
#         Any: 原函数调用结果
#     """

#     def wrapper(func):
#         async def inner(*args, **kwargs):
#             nonlocal times
#             loop = times
#             while loop != 0:
#                 loop -= 1
#                 try:
#                     return await func(*args, **kwargs)
#                 except json.decoder.JSONDecodeError:
#                     continue
#                 except ResponseCodeException as e:
#                     raise e
#                 # TIMEOUT
#             raise ApiException("重试达到最大次数")

#         return inner

#     return wrapper


# @retry_sync()
@retry(stop=stop_after_attempt(RETRY_TIMES), reraise=True)
def request_sync(
    url: str,
    method: str = "GET",
    data: dict = None,
    params: dict = None,
    json: dict = None,
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
    data: dict = None,
    params: dict = None,
    json: dict = None,
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

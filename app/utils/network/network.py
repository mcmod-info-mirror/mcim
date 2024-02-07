"""
与网络请求相关的模块
"""

import json
import atexit
import asyncio
import httpx
from dataclasses import field, dataclass
from typing import Any, Dict, Union, Coroutine

from ..log import logger
from ...exceptions import ApiException, NetworkException, ResponseException
from ...config import MCIMConfig

mcim_config = MCIMConfig.load()


__httpx_session_pool = {}
PROXY: str = mcim_config.proxies

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.54",
}

TIMEOUT = 5
RETRY_TIMES = 3
REQUEST_LOG = True


def retry(times: int = 3):
    """
    重试装饰器

    Args:
        times (int): 最大重试次数 默认 3 次 负数则一直重试直到成功

    Returns:
        Any: 原函数调用结果
    """

    def wrapper(func: Coroutine):
        async def inner(*args, **kwargs):
            nonlocal times
            loop = times
            while loop != 0:
                if loop != times and REQUEST_LOG:
                    logger.info("第 %d 次重试", times - loop)
                loop -= 1
                try:
                    return await func(*args, **kwargs)
                except json.decoder.JSONDecodeError:
                    # json 解析错误 说明数据获取有误 再给次机会
                    continue
            raise ApiException("重试达到最大次数")

        return inner

    return wrapper


@dataclass
class Api:
    """
    用于请求的 Api 类

    Args:
        url (str): 请求地址

        method (str): 请求方法

        data (dict, optional): 请求载荷. Defaults to {}.

        params (dict, optional): 请求参数. Defaults to {}.
    """

    url: str
    method: str
    json_body: bool = False
    data: dict = field(default_factory=dict)
    params: dict = field(default_factory=dict)
    headers: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.method = self.method.upper()

    async def _prepare_request(self, **kwargs) -> dict:
        """
        准备请求的配置参数

        Args:
            **kwargs: 其他额外的请求配置参数

        Returns:
            dict: 包含请求的配置参数
        """
        # 去掉空的参数
        self.params = {k: v for k, v in self.params.items() if v}
        config = {
            "url": self.url,
            "method": self.method,
            "data": self.data,
            "params": self.params,
            "headers": HEADERS.copy() if len(self.headers) == 0 else self.headers,
            "timeout": TIMEOUT,
            
        }
        config.update(kwargs)

        if self.json_body:
            config["headers"]["Content-Type"] = "application/json"
            config["data"] = json.dumps(config["data"])

        return config

    async def _process_response(
        self,
        resp: httpx.Response,
        raw: bool = False,
    ) -> Union[int, str, dict]:
        """
        处理接口的响应数据
        """
        if raw:
            return resp.text()
        data = resp.json()
        return data

    @retry(times=RETRY_TIMES)
    async def request(self, raw: bool = False, **kwargs) -> Union[int, str, dict]:
        """
        向接口发送请求。

        Returns:
            接口未返回数据时，返回 None，否则返回该接口提供的 data 或 result 字段的数据。
        """
        config = await self._prepare_request(**kwargs)
        session: httpx.AsyncClient

        session = get_session()
        resp = await session.request(**config)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise NetworkException(resp.status_code, str(e) + f" {resp.url}")
        data = await self._process_response(resp, raw=raw)
        return data


def get_session() -> httpx.AsyncClient:
    """
    获取当前模块的 httpx.AsyncClient 对象，用于自定义请求

    Returns:
        httpx.AsyncClient
    """
    global __httpx_session_pool, last_proxy
    loop = asyncio.get_event_loop()
    session = __httpx_session_pool.get(loop, None)
    if session is None:
        if PROXY != "":
            proxies = {"all://": PROXY}
            session = httpx.AsyncClient(proxies=proxies)  # type: ignore
        else:
            last_proxy = ""
            session = httpx.AsyncClient()
        __httpx_session_pool[loop] = session

    return session


def set_session(session: httpx.AsyncClient) -> None:
    """
    用户手动设置 Session

    Args:
        session (httpx.AsyncClient):  httpx.AsyncClient 实例。
    """
    loop = asyncio.get_event_loop()
    __httpx_session_pool[loop] = session


@atexit.register
def __clean() -> None:
    """
    程序退出清理操作。
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        return

    async def __clean_task():
        s1 = __httpx_session_pool.get(loop, None)
        if s1 is not None:
            await s1.aclose()

    if loop.is_closed():
        loop.run_until_complete(__clean_task())
    else:
        loop.create_task(__clean_task())

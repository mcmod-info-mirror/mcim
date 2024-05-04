"""
与网络请求相关的模块
"""

import json
import httpx
from dataclasses import field, dataclass
from typing import Any, Dict, Union

from ..log import logger
from ...exceptions import ApiException, NetworkException, ResponseException
from ...config import MCIMConfig

mcim_config = MCIMConfig.load()


PROXY: str = mcim_config.proxies

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.54",
}

TIMEOUT = 5
RETRY_TIMES = 3
REQUEST_LOG = True

class ApiException(Exception):
    """
    API 基类异常。
    """

    def __init__(self, msg: str = "出现了错误，但是未说明具体原因。"):
        super().__init__(msg)
        self.msg = msg

    def __str__(self):
        return self.msg
    
class ResponseCodeException(ApiException):
    """
    API 返回 code 错误。
    """

    def __init__(self, status_code: int, msg: str):
        """

        Args:
            status_code (int):             错误代码。

            msg (str):              错误信息。
        """
        super().__init__(msg)
        self.msg = msg
        self.status_code = status_code

    def __str__(self):
        return f"HTTP {self.status_code}，信息：{self.msg}。"

def retry(times: int = RETRY_TIMES):
    """
    重试装饰器

    Args:
        times (int): 最大重试次数 默认 3 次 负数则一直重试直到成功

    Returns:
        Any: 原函数调用结果
    """

    def wrapper(func):
        def inner(*args, **kwargs):
            nonlocal times
            loop = times
            while loop != 0:
                loop -= 1
                try:
                    return func(*args, **kwargs)
                except json.decoder.JSONDecodeError:
                    continue
                except ResponseCodeException as e:
                    raise
                # TIMEOUT
            raise ApiException("重试达到最大次数")

        return inner

    return wrapper

@retry()
def request(url: str, method: str = "GET", **kwargs) -> httpx.Response:
    """
    HTTPX 请求函数

    Args:
        url (str): 请求 URL

        method (str, optional): 请求方法 默认 GET

        **kwargs: 其他参数

    Returns:
        Any: 请求结果
    """
    res = httpx.request(method, url, proxies=PROXY, **kwargs)
    if res.status_code != 200:
        raise ResponseCodeException(res.status_code, f'{res.url} {res.headers}')
    return res
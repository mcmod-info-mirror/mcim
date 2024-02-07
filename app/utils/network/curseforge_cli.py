from typing import Union
from datetime import datetime

from .network import Api

from ...config import MCIMConfig

MCIMConfig = MCIMConfig.load()

curseforge_api_key = MCIMConfig.curseforge_api_key

headers = {
    'Accept': 'application/json',
    "x-api-key": curseforge_api_key,
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
}

class CurseForgeCli(Api):
    def __init__(self, 
                    prefix: str = None, 
                    method: str = "GET", 
                    data: dict = {}, 
                    params: dict = {}, 
                    headers: dict = headers,
                    raw_url: str = None):
            url = MCIMConfig.curseforge_api + prefix if raw_url is None else raw_url
            if method == "GET":
                super().__init__(url=url, method=method, data=data, params=params, headers=headers)
            elif method == "POST":
                super().__init__(url=url, method=method, data=data, params=params, headers=headers, json_body=True)

    @property
    async def result(self, raw: bool = False, **kwargs) -> Union[int, str, dict]:
        """
        异步获取请求结果
        """
        data = self.request(raw=raw, **kwargs)
        return await data
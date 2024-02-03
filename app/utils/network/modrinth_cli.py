from typing import Union

from .network import Api

from app.config import MCIMConfig

MCIMConfig = MCIMConfig.load()

headers = {
    'Accept': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
}

def process_params(params: dict) -> dict:
    """
    处理参数
    """
    # 不考虑列表嵌套字典
    def convert_list_to_str(l: list) -> str:
        return f'[{",".join([f'"{i}"' for i in l])}]'
    r_params = {}
    for k, v in params.items():
        if isinstance(v, list):
            r_params[k] = convert_list_to_str(v)
        else:
            r_params[k] = v
    return r_params

def process_data(data: dict) -> dict:
    """
    处理数据
    """
    def clear_empty_dict(data: dict) -> dict:
        re_data = {}
        for k, v in data.items():
            if isinstance(v, list):
                if len([i for i in v if i is not None]) != 0:
                    re_data[k] = [i for i in v if i is not None]
            elif isinstance(v, dict):
                re_data[k] = clear_empty_dict(v)
            elif v is not None:
                re_data[k] = v
        return re_data
    return clear_empty_dict(data)

class ModrinthCli(Api):
    def __init__(self, 
                    prefix: str = None,
                    method: str = "GET", 
                    data: dict = {}, 
                    params: dict = {}, 
                    headers: dict = headers,
                    raw_url: str = None):
            url = MCIMConfig.modrinth_api + prefix if raw_url is None else raw_url
            params = process_params(params)
            data = process_data(data)
            if method == "GET":
                super().__init__(url=url, method=method, data=data, params=params, headers=headers)
            elif method == "POST":
                super().__init__(url=url, method=method, data=data, params=params, headers=headers, json_body=True)

    @property
    async def result(self, raw: bool = False, **kwargs) -> Union[int, str, dict]:
        """
        异步获取请求结果
        """
        return await self.request(raw=raw, **kwargs)
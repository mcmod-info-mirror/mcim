from typing import List
import json

from .base import *

__all__ = [
    'ModrinthApi'
]


class ModrinthApi:
    """
	Curseforge api 的包装，基于 asyncio 和 aiohttp

	函数只返回 api 原生数据，未处理

    用法: modapi = ModrinthApi("https://api.modrinth.com/v2")

    或者 modapi = ModrinthApi("https://staging-api.modrinth.com/v2")
    """

    def __init__(self, baseurl: str, proxies: str = None, acli=None, ua=None):
        self.baseurl = baseurl
        self.proxies = proxies
        if ua is None:
            self.headers = {
                "User-Agent": "github_org/mcim/1.0.0 (mcim.z0z0r4.top)",
                'Accept': 'application/json'
            }
        else:
            self.headers = {
                "User-Agent": ua,
                'Accept': 'application/json'
            }
        self.acli = acli

    async def end_point(self):
        async with self.acli:
            res, content = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,),
                                             "https://api.modrinth.com/", proxy=self.proxies, headers=self.headers)
            return json.loads(content)

    async def get_project(self, project_id: str = None, slug: str = None):
        '''
        获取 Mod 信息。

        使用中 `slug` 和 `modid` 可二选一使用，使用两个则优先使用 `slug` 。

        使用例子:

        - ` `
        '''
        if slug is not None:
            url = self.baseurl + "project/{slug}".format(slug=slug)
        elif project_id is not None:
            url = self.baseurl + "project/{modid}".format(modid=id)
        else:
            raise AssertionError("Neither slug and modid is not None")
        async with self.acli:
            res, content = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,), url,
                                             proxy=self.proxies, headers=self.headers)
            return json.loads(content)

    async def get_projects(self, ids: List[str]):  # 不支持 slug 查询差评
        url = self.baseurl + "projects"
        async with self.acli:
            res, content = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,), url,
                                             proxy=self.proxies, headers=self.headers, params={"ids": ids})
            return json.loads(content)

    async def check_project(self, project_id: str = None, slug: str = None):
        if slug is not None:
            url = self.baseurl + "project/{slug}/check".format(slug=slug)
        elif project_id is not None:
            url = self.baseurl + "project/{modid}/check".format(modid=id)
        else:
            raise AssertionError("Neither slug and modid is not None")
        async with self.acli:
            res, content = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,), url,
                                             proxy=self.proxies, headers=self.headers)
            if res.status == 200:
                return True
            else:
                return False

    async def get_project_dependencies(self, project_id: int):
        url = self.baseurl + "projects" + "/{id}/dependencies".format(id=project_id)
        async with self.acli:
            res, content = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,), url,
                                             proxy=self.proxies, headers=self.headers, params={"id": id})
            return json.loads(content)

    async def get_project_versions(self, slug=None, modid=None, game_versions=None, loaders=None, featured=None):
        '''
        获取 Mod 所有支持版本及相关信息。

        slug: ;

        modid: ;

        game_versions: 游戏版本号;

        loaders: 加载器名称;

        featured: ;

        使用中 `slug` 和 `modid` 可二选一使用，使用两个则优先使用 `slug` 。

        使用例子:

        - ``
        '''
        if slug is not None:
            url = self.baseurl + "project/{slug}/version".format(slug=slug)
        elif modid is not None:
            url = self.baseurl + "project/{modid}/version".format(modid=modid)
        else:
            raise AssertionError("Neither slug and modid is not None")
        async with self.acli:
            res, content = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,), url,
                                             proxy=self.proxies, headers=self.headers, params={
                    "game_versions": game_versions, "loaders": loaders, "featured": featured})
        return json.loads(content)

    async def get_project_version(self, project_id: str):
        '''
        根据提供的版本号获取信息。

        id: 版本号。

        使用例子:

        '''
        url = self.baseurl + "version/{version_id}".format(version_id=project_id)
        async with self.acli:
            res, content = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,), url,
                                             proxy=self.proxies, headers=self.headers)
            return json.loads(content)

    async def get_project_version_list(self, ids: str):
        '''
        根据提供的版本号列表获取信息。

        ids: 版本号列表。

        使用例子:

        '''
        url = self.baseurl + "version"
        async with self.acli:
            res, content = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,), url,
                                             proxy=self.proxies, headers=self.headers, params={"ids": ids})
            return json.loads(content)

    async def get_version_from_hash(self, hash: str, algorithm: str):
        '''
        根据提供的 Hash 查找 version 信息

        hash: 文件 Hash

        algorithm: 文件 Hash 算法
        '''
        url = self.baseurl + "version_file/{hash}".format(hash=hash)
        async with self.acli:
            res, content = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,), url,
                                             proxy=self.proxies, headers=self.headers, params={"algorithm": algorithm})
            return json.loads(content)

    async def search(self, query: str = None, limit: int = 20, offset: int = None, index: str = "relevance", facets: dict =None):
        '''
        搜索 Mod 。

        query: 搜索内容;

        offset: 从第几个开始;

        index
        '''
        if type(facets) == dict:
            facets_text = "["
            for a, b in facets.items():
                facets_text += '["{a}:{b}"],'.format(a=a, b=b)
            facets = facets_text[:-1] + "]"

        url = self.baseurl + "search"
        async with self.acli:
            res, content = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,), url,
                                             proxy=self.proxies, headers=self.headers, params={
                    "query": query, "limit": limit, "offset": offset, "index": index, "facets": facets
                })
        return json.loads(content)

    async def get_project_version_download_info(self, project_id: str):
        '''
        获取格式化后的文件信息
        用于下载Mod
        '''
        version_info = await self.get_project_version(project_id)
        info = {}
        if version_info is not None:
            info["type"] = "Modrinth"
            info["name"] = version_info["name"]
            info["date_published"] = version_info["date_published"]
            info["hash"] = version_info["files"][0]["hashes"]["sha1"]
            info["filename"] = version_info["files"][0]["filename"]
            info["url"] = version_info["files"][0]["url"]
            info["size"] = version_info["files"][0]["size"]
            return info
        return None

from typing import List
import json

from .base import *

__all__ = [
    'ModrinthApi'
]


class ModrinthApi:
    '''
	Modrinth Api 的包装，基于 Asyncio 和 AioHttp。

	函数只返回 api 原生数据，未处理。
    '''
    def __init__(self, baseurl: str, proxies: str = None, acli=None, ua=None):
        '''
        定义参数。
        
        参数:
        
        :param baseurl: API 地址
        
        :param proxies: 代理
        
        :param acli: 同步客户端
        
        :param ua: UA 标识
        
        用法: `<ModrinthApi>(baseurl, proxies, acli, ua)`
        '''
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
        '''
        测试是否可以链接到 API 。
        
        用法: `resp = <ModrinthApi>.end_point()`
        '''
        async with self.acli:
            res, content = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,),
                                             "https://api.modrinth.com/", proxy=self.proxies, headers=self.headers)
            return json.loads(content)

    async def get_project(self, project_id: str = None, slug: str = None):
        '''
        获取 Mod 信息。[🔗](https://docs.modrinth.com/api-spec/#tag/projects/operation/getProject)

        参数:

        :param project_id: Mod ID
        
        :param slug: Mod 项目 ID
        
        `project_id` 和 `slug` 可二选一使用，优先使用 `slug` 。
        
        用法: `resp = <ModrinthApi>.get_project(project_id, slug)`
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
        '''
        获取多个 Mod 信息。[🔗](https://docs.modrinth.com/api-spec/#tag/projects/operation/getProjects)
        
        参数:
        
        :param ids: 多个 Mod ID
        
        用法: `<ModrinthApi>.get_projects(ids)`
        '''
        url = self.baseurl + "projects"
        async with self.acli:
            res, content = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,), url,
                                             proxy=self.proxies, headers=self.headers, params={"ids": ids})
            return json.loads(content)

    async def check_project(self, project_id: str = None, slug: str = None):
        '''
        检查项目是否存在。[🔗](https://docs.modrinth.com/api-spec/#tag/projects/operation/checkProjectValidity)
        
        参数:
        
        :param project_id: Mod ID
        
        :param slug: Mod 项目 ID
        
        用法: `<ModrinthApi>.check_project(project_id, slug)`
        '''
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
        '''
        检查项目依赖。[🔗](https://docs.modrinth.com/api-spec/#tag/projects/operation/getDependencies)
        
        参数:
        
        :param project_id: Mod ID
        
        用法: `resp = <ModrinthApi>.get_project_dependencies(project_id)`
        '''
        url = self.baseurl + "projects" + "/{id}/dependencies".format(id=project_id)
        async with self.acli:
            res, content = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,), url,
                                             proxy=self.proxies, headers=self.headers, params={"id": id})
            return json.loads(content)

    async def get_project_versions(self, slug=None, modid=None, game_versions=None, loaders=None, featured=None):
        '''
        获取 Mod 所有支持版本及相关信息。[🔗](https://docs.modrinth.com/api-spec/#tag/versions/operation/getProjectVersions)
        
        参数:
        
        :param slug: Mod 项目 ID
        
        :param modid: Mod ID
        
        :param game_versions: 游戏版本
        
        :param loaders: 加载器
        
        :param featured: 允许仅筛选特色或非特色版本
        
        用法: `resp = <ModrinthApi>.get_project_versions(slug, modid, game_versions, loaders, featured)`
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
        根据版本 ID 获取信息。[🔗](https://docs.modrinth.com/api-spec/#tag/versions/operation/getVersion)
        
        参数:
        
        :param project_id: 版本 ID
        
        用法: `resp = <ModrinthApi>.get_project_version(project_id)`
        '''
        url = self.baseurl + "version/{version_id}".format(version_id=project_id)
        async with self.acli:
            res, content = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,), url,
                                             proxy=self.proxies, headers=self.headers)
            return json.loads(content)

    async def get_project_version_list(self, ids: str):
        '''
        根据多个版本 ID 获取多个版本信息。[🔗](https://docs.modrinth.com/api-spec/#tag/versions/operation/getVersion)
        
        参数:
        
        :param ids: 多个版本 ID
        
        用法: `resp = <ModrinthApi>.get_project_version_list(ids)`
        '''
        url = self.baseurl + "version"
        async with self.acli:
            res, content = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,), url,
                                             proxy=self.proxies, headers=self.headers, params={"ids": ids})
            return json.loads(content)

    async def get_version_from_hash(self, hash: str, algorithm: str):
        '''
        根据提供的 Hash 查找版本信息。[🔗](https://docs.modrinth.com/api-spec/#tag/version-files/operation/versionFromHash)

        参数:
        
        :param hash: 文件 Hash

        :param algorithm: 文件 Hash 算法
        
        用法: `resp = <ModrinthApi>.get_version_from_hash(hash, algorithm)`
        '''
        url = self.baseurl + "version_file/{hash}".format(hash=hash)
        async with self.acli:
            res, content = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,), url,
                                             proxy=self.proxies, headers=self.headers, params={"algorithm": algorithm})
            return json.loads(content)

    async def search(self, query: str = None, limit: int = 20, offset: int = None, index: str = "relevance", facets: dict =None):
        '''
        搜索 Mod 。[🔗](https://docs.modrinth.com/api-spec/#tag/projects/operation/searchProjects)

        参数:
        
        :param query: 搜索内容

        :param limit: 返回数量限制

        :param offset: 偏移量
        
        :param index: 排序方法
        
        :param facets: [筛选搜索结果](https://docs.modrinth.com/docs/tutorials/api_search)
        
        用法: `resp = <ModrinthApi>.search(query, limit, offset, index, facets)`
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
        获取经过格式化后的 Mod 下载信息。[🔗](https://docs.modrinth.com/api-spec/#tag/versions/operation/getVersion)
        
        参数:
        
        :param project_id: 项目 ID
        
        用法: `resp = <ModrinthApi>.get_project_version_download_info(project_id)`
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

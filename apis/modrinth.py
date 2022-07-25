
import requests

from .base import *

__all__ = [
    'ModrinthApi'
]

class ModrinthApi:
    '''
    用法: modapi = ModrinthApi("https://api.modrinth.com/")
    '''
    def __init__(self, baseurl: str, proxies: dict=None):
        self.baseurl = baseurl
        self.proxies = proxies

    def end_point(self):
        headers = {
            'Accept': 'application/json'
        }

        res = retry_req_get_mustok(3, url=self.baseurl, proxies=self.proxies, headers=headers)
        return res.json()

    def get_mod(self, slug=None, modid=None):
        '''
        获取 Mod 信息。

        使用中 `slug` 和 `modid` 可二选一使用，使用两个则优先使用 `slug` 。

        使用例子:

        - ` `
        '''
        if slug is not None:
            url = self.baseurl + "project/{slug}".format(slug=slug)
        elif modid is not None:
            url = self.baseurl + "project/{modid}".format(modid=modid)
        else:
            raise AssertionError("Neither slug and modid is not None")

        headers = {
            'Accept': 'application/json'
        }

        res = retry_req_get_mustok(3, url=url, proxies=self.proxies, headers=headers)
        return res.json()

    def get_mod_versions(self, slug=None, modid=None, game_versions=None, loaders=None, featured=None):
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

        headers = {
            'Accept': 'application/json'
        }

        res = retry_req_get_mustok(3, url=url, proxies=self.proxies, headers=headers, params={
            "game_versions": game_versions, "loaders": loaders, "featured": featured})
        return res.json()

    def get_mod_version(self, id: str):
        '''
        跟据提供的版本号获取信息。

        id: 版本号。

        使用例子:

        '''
        url = self.baseurl + "version/{version_id}".format(version_id=id)
        headers = {
            'Accept': 'application/json'
        }

        res = retry_req_get_mustok(3, url=url, proxies=self.proxies, headers=headers)
        return res.json()

    def search(self, query, limit=20, offset=None, index="relevance", facets=None):
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
        headers = {
            'Accept': 'application/json'
        }

        res = retry_req_get_mustok(3, url=url, proxies=self.proxies, headers=headers, params={
            "query": query, "limit": limit, "offset": offset, "index": index, "facets": facets
        })
        return res.json()

    def get_mod_version_download_info(self, id):
        '''
        获取格式化后的文件信息
        用于下载Mod
        '''
        version_info = self.get_mod_version(id)
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

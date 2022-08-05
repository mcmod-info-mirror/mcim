
import json
from .base import *


__all__ = [
    'CurseForgeApi'
]

HASHES_TYPE_ID = {
    1: "sha1",
    2: "md5"
}


class CurseForgeApi:
    '''
    Curseforge api 的包装，基于 asyncio 和 aiohttp

    函数只返回 api 原生数据，未处理 

    见 CFCore: https://docs.curseforge.com/
    '''

    def __init__(self, baseurl: str, api_key: str, proxies: dict = None, acli=None):
        self.baseurl = baseurl
        self.api_key = api_key
        self.proxies = proxies
        self.acli = acli

    async def end_point(self):
        headers = {
            'Accept': 'application/json'
            # 'x-api-key': self.api_key
        }
        async with self.acli:
            res, content = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,), "https://api.curseforge.com/", proxy=self.proxies, headers=headers)
            return content  # 这不是json

    async def get_all_games(self, index=1, pageSize=50):
        url = self.baseurl + \
            "games?index={index}&pageSize={pageSize}".format(
                index=index, pageSize=pageSize)
        headers = {
            'Accept': 'application/json',
            'x-api-key': self.api_key
        }
        async with self.acli:
            res, content = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,), url, proxy=self.proxies, headers=headers)
            return json.loads(content)

    async def get_game(self, gameid, index=1, pageSize=50):
        url = self.baseurl + "games/{gameid}?index={index}&pageSize={pageSize}".format(
            gameid=gameid, index=index, pageSize=pageSize)
        headers = {
            'Accept': 'application/json',
            'x-api-key': self.api_key
        }
        async with self.acli:
            res, content = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,), url, proxy=self.proxies, headers=headers)
            return json.loads(content)

    async def get_game_version(self, gameid, index=1, pageSize=50):
        url = self.baseurl + "games/{gameid}/versions?index={index}&pageSize={pageSize}".format(
            gameid=gameid, index=index, pageSize=pageSize)
        headers = {
            'Accept': 'application/json',
            'x-api-key': self.api_key
        }
        async with self.acli:
            res, content = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,), url, proxy=self.proxies, headers=headers)
            return json.loads(content)

    # classid 为主分类的有 main class [17,5,4546,4471,12,4559,6(Mods)]
    async def get_categories(self, gameid=432, classid=None):
        '''
        classid不是必须参数，无此参则为查询全部类别(Categories)
        '''
        url = self.baseurl + "categories"
        headers = {
            'Accept': 'application/json',
            'x-api-key': self.api_key
        }
        params = {
            'gameId': gameid
        }
        if classid is not None:
            params['classId'] = classid
        async with self.acli:
            res, content = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,), url, headers=headers, params=params, proxy=self.proxies)
            return json.loads(content)

    async def search(self, searchfilter=None, slug=None, gameid=432, classid=6, categoryid=None, modloadertype=None, sortfield="Featured", sortorder=None, gameversion=None, gameversiontypeid=None, index=None, pagesize=None):
        '''
        index: A zero based index of the first item to include in the response, the limit is: (index + pageSize <= 10,000).

        pageSize: The number of items to include in the response, the default/maximum value is 50.

        ---

        Enumerated Values

        Parameter	Value

        sortField	1

        sortField	2

        sortField	3

        sortField	4

        sortField	5

        sortField	6

        sortField	7

        sortField	8

        sortOrder	asc

        sortOrder	desc

        modLoaderType	0

        modLoaderType	1

        modLoaderType	2
		
        modLoaderType	3

        modLoaderType	4

        modLoaderType	5
        '''
        url = self.baseurl + "mods/search"
        headers = {
            'Accept': 'application/json',
            'x-api-key': self.api_key
        }


        params={
                "searchFilter": searchfilter, 'gameId': gameid, "classId": classid, "slug": slug, "categoryId": categoryid, "gameVersion": gameversion, "gameVersionTypeId": gameversiontypeid, "modLoaderType": modloadertype, "sortOrder": sortorder, "sortField": sortfield, "index": index, "pageSize": pagesize
            }
        # final_params = params.copy()
        # for param in params:
        #     if params[param] is None:
        #         del final_params[param]

        async with self.acli:
            res, content = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,), url, headers=headers, params=params, proxy=self.proxies)
            return json.loads(content)

    async def get_mod(self, modid):
        url = self.baseurl + "mods/{modid}".format(modid=modid)
        headers = {
            'Accept': 'application/json',
            'x-api-key': self.api_key
        }
        async with self.acli:
            res, content = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,), url, headers=headers, proxy=self.proxies)
            return json.loads(content)

    async def get_mods(self, modids) -> list:
        url = self.baseurl + "mods"
        body = {
            "modIds": modids
        }
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'x-api-key': self.api_key
        }
        async with self.acli:
            res, content = await self.acli.post(url, proxy=self.proxies, headers=headers, json=body)
            return json.loads(content)

    async def get_mod_description(self, modid):
        url = self.baseurl + "mods/{modid}/description".format(modid=modid)
        headers = {
            'Accept': 'application/json',
            'x-api-key': self.api_key
        }
        async with self.acli:
            res, content = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,), url, proxy=self.proxies, headers=headers)
            return json.loads(content)

    async def get_file(self, modid, fileid):
        url = self.baseurl + \
            "mods/{modid}/files/{fileid}".format(modid=modid, fileid=fileid)
        headers = {
            'Accept': 'application/json',
            'x-api-key': self.api_key
        }
        async with self.acli:
            res, content = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,), url, proxy=self.proxies, headers=headers)
            return json.loads(content)

    async def get_files(self, modid):
        url = self.baseurl + \
            "mods/{modid}/files".format(modid=modid)
        headers = {
            'Accept': 'application/json',
            'x-api-key': self.api_key
        }
        async with self.acli:
            res, content = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,), url, proxy=self.proxies, headers=headers)
            return json.loads(content)

    async def post_files(self, fileids, modid):
        url = self.baseurl + "mods/{modid}/files".format(modid=modid)
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'x-api-key': self.api_key
        }
        body = {
            "fileIds": fileids
        }
        async with self.acli:
            res, content = await res_mustok_async(self.acli.post)(url, proxy=self.proxies, headers=headers, json=body)
            return json.loads(content)

    async def get_mod_file_changelog(self, modid: int, fileid: int):
        url = self.baseurl + \
            "mods/{modid}/files/{fileid}/changelog".format(modid=modid, fileid=fileid)
        headers = {
            'Accept': 'application/json',
            'x-api-key': self.api_key
        }
        async with self.acli:
            res, content = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,), url, proxy=self.proxies, headers=headers)
            return json.loads(content)

    async def get_file_download_info(self, modid, fileid):
        '''
        获取格式化后的文件信息
        用于下载Mod
        '''
        version_info = await self.get_file(modid, fileid)["data"]
        if version_info is None:
            return None
        info = {
            "origin": "Curseforge",
            "name": version_info["displayName"],
            "date_published": version_info["fileDate"],
            "filename": version_info["fileName"],
            "url": version_info["downloadUrl"],
            "size": version_info["fileLength"],
        }
        info["hashes"] = [{
            "type": HASHES_TYPE_ID.get(hash["algo"], hash["algo"]),
            "value": hash["value"]
        } for hash in version_info["hashes"]]
        return info

    async def get_file_download_url(self, fileid, modid):
        url = self.baseurl + \
            "mods/{modid}/files/{fileid}/download-url".format(
                modid=modid, fileid=fileid)
        headers = {
            'Accept': 'application/json',
            'x-api-key': self.api_key
        }
        async with self.acli:
            res, content = await retry_async(self.acli.get, 3, (StatusCodeException,), url, proxy=self.proxies, headers=headers)
            return json.loads(content)


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
    Curseforge Api 的包装，基于 Asyncio 和 AioHttp

    函数只返回 Api 原生数据，未处理 

    见 CFCore: https://docs.curseforge.com/
    '''

    def __init__(self, baseurl: str, api_key: str, proxies: dict = None, acli=None):
        '''
        定义参数。
        
        参数:
        
        :param baseurl: API 主地址
        
        :param api_key: API 密钥
        
        :param proxies: 请求代理
        
        :param acli: 请求会话
        
        用法: `<CurseForgeApi>(baseurl, api_key, proxies, acli)`
        '''
        self.baseurl = baseurl
        self.api_key = api_key
        self.proxies = proxies
        self.acli = acli

    async def end_point(self):
        '''
        测试链接可用性。
        
        用法: `resp = <CurseForgeApi>.end_point()`
        '''
        headers = {
            'Accept': 'application/json'
            # 'x-api-key': self.api_key
        }
        async with self.acli:
            res, content = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,), "https://api.curseforge.com/", proxy=self.proxies, headers=headers)
            return content  # 这不是json

    async def get_all_games(self, index=1, pageSize=50):
        '''
        获取所有游戏 ID 。
        
        参数:
        
        :param index: 要包含在响应中的第一项的从零开始的索引
        
        :param pageSize: 要包含在响应中的项目数
        
        用法: `resp = <CurseForgeApi>.get_all_games(index, pageSize)`
        '''
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
        '''
        获取游戏信息。
        
        参数:
        
        :param gameid: 游戏 ID
        
        用法: `resp = <CurseForgeApi>.get_game(gameid)`
        '''
        url = self.baseurl + "games/{gameid}".format(
            gameid=gameid)
        headers = {
            'Accept': 'application/json',
            'x-api-key': self.api_key
        }
        async with self.acli:
            res, content = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,), url, proxy=self.proxies, headers=headers)
            return json.loads(content)

    async def get_game_version(self, gameid, index=1, pageSize=50):
        '''
        获取游戏版本。
        
        参数:
        
        :param gameid: 游戏 ID
        
        用法: `resp = <CurseForgeApi>.get_game_version(gameid)`
        '''
        url = self.baseurl + "games/{gameid}/versions".format(
            gameid=gameid)
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
        获取指定游戏的所有可用类和类别。
        
        参数:
        
        :param gameid: 游戏 ID
        
        :param classid: 类 ID
        
        注: `classid` 不是必须参数，无此参则为查询全部类别 `(Categories)`
        
        用法: `resp = <CurseForgeApi>.get_categories(gameid, classid)
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
        搜索 Mod 。
        
        参数:
        
        :param searchfilter: 搜索过滤器
        
        :param slug: Mod ID
        
        :param gameid: 游戏 ID
        
        :param classid: 类别 ID
        
        :param modloadertype: [加载器类型](https://docs.curseforge.com/#schemamodloadertype)
        
        :param sortfield: [排序字段](https://docs.curseforge.com/#tocS_ModsSearchSortField)
        
        :param sortorder: [排序顺序](https://docs.curseforge.com/#schemasortorder)
        
        :param gameversion: 游戏版本
        
        :param gameversiontype: 游戏版本类型
        
        :param index: 要包含在响应中的第一项的从零开始的索引
        
        :param pagesize: 要包含在响应中的项目数
        
        `gameid` 为 `必填项` , 其余为 `选填项` 。
        
        用法: `resp = <CurseForgeApi>.search(searchfilter, slug, gameid, classid categoryid, modloadertype, sortfield, sortorder, gameversion, gameversiontypeid, index, pagesize)`
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
        '''
        获取 Mod 信息。
        
        参数:
        
        :param modid: Mod ID
        
        用法: `resp = <CurseForgeApi>.get_mod(modid)`
        '''
        url = self.baseurl + "mods/{modid}".format(modid=modid)
        headers = {
            'Accept': 'application/json',
            'x-api-key': self.api_key
        }
        async with self.acli:
            res, content = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,), url, headers=headers, proxy=self.proxies)
            return json.loads(content)

    async def get_mods(self, modids) -> list:
        '''
        获取列表内的 Mod 信息。
        
        参数:
        
        :param modids: 多个 Mod ID
        
        用法: `<CurseForgeApi>.get_mods(modids)`
        '''
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
        '''
        获取 Mod 描述信息。
        
        参数:
        
        :param modid: Mod ID
        
        用法: `resp = <CurseForgeApi>.get_mod_description(modid)`
        '''
        url = self.baseurl + "mods/{modid}/description".format(modid=modid)
        headers = {
            'Accept': 'application/json',
            'x-api-key': self.api_key
        }
        async with self.acli:
            res, content = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,), url, proxy=self.proxies, headers=headers)
            return json.loads(content)

    async def get_file(self, modid, fileid):
        '''
        获取指定模组的单个文件。
        
        参数:
        
        :param modid: Mod ID
        
        :param fileid: 文件 ID
        
        用法: `resp = <CurseForgeApi>.get_file(modid, fileid)`
        '''
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
        '''
        获取指定模组的所有文件。
        
        参数:
        
        :param modid: Mod ID
        
        用法: resp = `<CurseForgeApi>.get_files(modid)`
        '''
        url = self.baseurl + \
            "mods/{modid}/files".format(modid=modid)
        headers = {
            'Accept': 'application/json',
            'x-api-key': self.api_key
        }
        async with self.acli:
            res, content = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,), url, proxy=self.proxies, headers=headers)
            return json.loads(content)

    async def post_files(self, fileids):
        '''
        获取所有文件。
        
        参数:
        
        :param fileids: 多个文件 ID
        
        用法: `resp = <CurseForgeApi>.post_files(fileids)`
        '''
        url = self.baseurl + "mods/files"
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
        '''
        获取模组更新日志。
        
        参数:
        
        :param modid: Mod ID
        
        :param fileid: 文件 ID
        
        用法: `resp = <CurseForgeApi>.get_mod_file_changelog(modid, fileid)`
        '''
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
        获取经过格式化的模组文件信息。
        
        参数:
        
        :param modid: Mod ID
        
        :param fileid: 文件 ID
        
        用法: `resp = <CurseForgeApi>.get_file_download_info(modid, fileid)
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
        '''
        获取指定模组的指定文件的下载链接。
        
        参数:
        
        :param fileid: 文件 ID
        
        :param modid: Mod ID
        
        用法: `<CurseForgeApi>.get_file_download_url(fileid, modid)`
        '''
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

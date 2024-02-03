from typing import List, Union
from enum import Enum

from app.utils.network.curseforge_cli import CurseForgeCli as cli
from app.config import MCIMConfig

MCIMConfig = MCIMConfig.load()

__all__ = ["CurseForgeApi"]


class SearchFilter:
    class SortField(Enum):
        FEATURED = 1
        POPULARITY = 2
        LASTUPDATED = 3
        NAME = 4
        AUTHOR = 5
        TOTALDOWNLOADS = 6
        CATEGORY = 7
        GAMEVERSION = 8
        EARLYACCESS = 9
        FEATUREDRELEASED = 10
        RELEASEDDATE = 11
        RATING = 12

    class SortOrder(Enum):
        ASC = "asc"
        DESC = "desc"

    class ModLoaderType(Enum):
        Any = 0
        Forge = 1
        Cauldron = 2
        LiteLoader = 3
        Fabric = 4
        Quilt = 5
        NeoForge = 6


HASHES_TYPE_ID = {1: "sha1", 2: "md5"}


class CurseForgeApi:
    """
    Curseforge Api 的包装，基于 HTTPX 的异步请求。

    函数只返回 Api 原生数据，未处理 。

    见 [CFCore](https://docs.curseforge.com/) 。
    """

    async def end_point(self):
        """
        测试链接可用性。

        用法: `resp = <CurseForgeApi>.end_point()`
        """
        return await cli("/").result(raw=True)

    async def get_all_games(self, index=1, pageSize=50):
        """
        获取所有游戏 ID 。[🔗](https://docs.curseforge.com/#get-games)

        参数:

        :param index: 要包含在响应中的第一项的从零开始的索引

        :param pageSize: 要包含在响应中的项目数

        用法: `resp = <CurseForgeApi>.get_all_games(index, pageSize)`
        """
        return await cli("/games", params={"index": index, "pageSize": pageSize}).result

    async def get_game(self, gameid: int = 432):
        """
        获取游戏信息。[🔗](https://docs.curseforge.com/#get-game)

        参数:

        :param gameid: 游戏 ID 432 为 Minecraft

        用法: `resp = <CurseForgeApi>.get_game(gameid)`
        """
        return await cli(f"/games/{gameid}").result

    async def get_game_version(self, gameid, index=1, pageSize=50):
        """
        获取游戏版本。[🔗](https://docs.curseforge.com/#get-versions)

        参数:

        :param gameid: 游戏 ID

        用法: `resp = <CurseForgeApi>.get_game_version(gameid)`
        """
        params = {"index": index, "pageSize": pageSize}
        return await cli(f"/games/{gameid}/versions", params=params).result

    # classid 为主分类的有 main class [17,5,4546,4471,12,4559,6(Mods)]
    async def get_categories(self, gameid=432, classid=None):
        """
        获取指定游戏的所有可用类和类别。[🔗](https://docs.curseforge.com/#get-categories)

        参数:

        :param gameid: 游戏 ID

        :param classid: 类 ID

        注: `classid` 不是必须参数，无此参则为查询全部类别 `(Categories)`

        用法: `resp = <CurseForgeApi>.get_categories(gameid, classid)
        """
        params = {"gameId": gameid}
        if classid is not None:
            params["classId"] = classid
        return await cli("/categories", params=params).result

    async def search(
        self,
        searchfilter: str = None,
        slug: str = None,
        gameid: int = 432,
        classid: int = 6,
        categoryid: int = None,
        modloader_type: Union[
            SearchFilter.ModLoaderType, str
        ] = SearchFilter.ModLoaderType.Any,
        sort_field: Union[
            SearchFilter.SortField, str
        ] = SearchFilter.SortField.POPULARITY,
        sort_order: Union[SearchFilter.SortOrder, str] = SearchFilter.SortOrder.DESC,
        game_version: str = None,
        game_version_typeid: str = None,
        index: int = None,
        pagesize: int = None,
    ) -> dict:
        """
        搜索 Mod 。[🔗](https://docs.curseforge.com/#search-mods)

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
        """
        params = {
            "searchFilter": searchfilter,
            "gameId": gameid,
            "classId": classid,
            "slug": slug,
            "categoryId": categoryid,
            "gameVersion": game_version,
            "gameVersionTypeId": game_version_typeid,
            "modLoaderType": (
                modloader_type.value
                if isinstance(modloader_type, Enum)
                else modloader_type
            ),
            "sortOrder": (
                sort_order.value if isinstance(sort_order, Enum) else sort_order
            ),
            "sortField": (
                sort_field.value if isinstance(sort_field, Enum) else sort_field
            ),
            "index": index,
            "pageSize": pagesize,
        }
        return await cli("/mods/search", params=params).result

    async def get_mod(self, modid: int):
        """
        获取 Mod 信息。[🔗](https://docs.curseforge.com/#get-mod)

        参数:

        :param modid: Mod ID

        用法: `resp = <CurseForgeApi>.get_mod(modid)`
        """
        return await cli(f"/mods/{modid}").result

    async def get_mods(self, modids: List[int]) -> list:
        """
        获取列表内的 Mod 信息。[🔗](https://docs.curseforge.com/#get-mods)

        参数:

        :param modids: 多个 Mod ID 列表

        用法: `<CurseForgeApi>.get_mods(modids)`
        """
        data = {"modIds": modids}
        return await cli("/mods", method="POST", data=data).result

    async def get_mod_description(self, modid: int):
        """
        获取 Mod 描述信息。[🔗](https://docs.curseforge.com/#get-mod-description)

        参数:

        :param modid: Mod ID

        用法: `resp = <CurseForgeApi>.get_mod_description(modid)`
        """
        return await cli(f"/mods/{modid}/description").result

    async def get_file(self, modid: int, fileid: int):
        """
        获取指定模组的单个文件。[🔗](https://docs.curseforge.com/#get-mod-file)

        参数:

        :param modid: Mod ID

        :param fileid: 文件 ID

        用法: `resp = <CurseForgeApi>.get_file(modid, fileid)`
        """
        return await cli(f"/mods/{modid}/files/{fileid}").result

    async def get_files(
        self,
        modid: int,
        game_version: str = None,
        modLoader_Type: int = None,
        game_version_typeid: int = None,
        index: int = 0,
        pageSize: int = 20,
    ):
        """
        获取指定模组的所有文件。[🔗](https://docs.curseforge.com/#get-mod-files)

        参数:

        :param modid: Mod ID

        :param gameVersion: 游戏版本

        :param modLoaderType: 模组加载器类型

        :param gameVersionTypeId: 游戏版本类型

        :param index: 页码

        :param pageSize: 每页数量

        用法: resp = `<CurseForgeApi>.get_files(modid)`
        """
        params = {
            "gameVersion": game_version,
            "modLoaderType": modLoader_Type,
            "gameVersionTypeId": game_version_typeid,
            "index": index,
            "pageSize": pageSize,
        }
        return await cli(f"/mods/{modid}/files", params=params).result

    async def post_files(self, fileids: List[int]):
        """
        获取所有文件。[🔗](https://docs.curseforge.com/#get-files)

        参数:

        :param fileids: 多个文件 ID

        用法: `resp = <CurseForgeApi>.post_files(fileids)`
        """
        data = {"fileIds": fileids}
        return await cli("/mods/files", method="POST", data=data).result

    async def get_file_download_url(self, fileid: int, modid: int):
        """
        获取指定模组的指定文件的下载链接。[🔗](https://docs.curseforge.com/#get-mod-file-download-url)

        参数:

        :param fileid: 文件 ID

        :param modid: Mod ID

        用法: `<CurseForgeApi>.get_file_download_url(fileid, modid)`
        """
        return await cli(f"/mods/{modid}/files/{fileid}/download-url").result

    async def get_fingerprint(self, fingerprints: List[int]):
        """
        Get mod files that match a list of fingerprints. [🔗](https://docs.curseforge.com/#get-fingerprints-matches)

        :param fingerprints: List of fingerprints
        """
        data = {"fingerprints": fingerprints}
        return await cli("/fingerprints/432", method="POST", data=data).result
    
async def test():
    cf = CurseForgeApi()
    # print(await cf.end_point())
    print(await cf.get_all_games())
    print(await cf.get_game(432))
    print(await cf.get_game_version(432))
    print(await cf.get_categories(432))
    print(await cf.search(gameid=432))
    print(await cf.get_mod(238222))
    print(await cf.get_mods([238222, 348521]))
    print(await cf.get_mod_description(348521))
    print(await cf.get_file(modid=348521, fileid=4973456))
    print(await cf.get_files(modid=348521))
    print(await cf.post_files([4973456, 4973457]))
    print(await cf.get_file_download_url(modid=348521, fileid=4973456))
    print(await cf.get_fingerprint([1667027305, 320753275]))
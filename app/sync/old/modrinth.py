from typing import List, Union
from enum import Enum

from app.utils.network.modrinth_cli import ModrinthCli as cli
from app.config import MCIMConfig

MCIMConfig = MCIMConfig.load()

__all__ = ["CurseForgeApi"]


class SortType(Enum):
    relevance = "relevance"
    downloads = "downloads"
    follows = "follows"
    newest = "newest"
    updated = "updated"


class ModrinthApi:
    """
    Modrinth Api 的包装，基于 HTTPX

    函数只返回 Api 原生数据，未处理。
    """

    async def end_point(self):
        """
        测试是否可以链接
        """
        return await cli(raw_url="https://api.modrinth.com/").result

    async def get_project(self, project_id: str = None, slug: str = None):
        """
        获取 Mod 信息。[🔗](https://docs.modrinth.com/api-spec/#tag/projects/operation/getProject)

        """
        if slug is not None:
            url = f"/project/{slug}"
        elif project_id is not None:
            url = f"/project/{project_id}"
        else:
            raise AssertionError("Neither slug and project_id is not None")
        return await cli(prefix=url).result

    async def get_projects(self, project_ids: List[str]):  # 不支持 slug 查询差评
        params = {"ids": project_ids}
        return await cli(prefix="/projects", params=params).result

    async def check_project(self, project_id: str = None, slug: str = None):
        """
        检查项目是否存在。[🔗](https://docs.modrinth.com/api-spec/#tag/projects/operation/checkProjectValidity)

        参数:

        :param project_id: Mod ID

        :param slug: Mod 项目 ID

        用法: `<ModrinthApi>.check_project(project_id, slug)`
        """
        if slug is not None:
            url = f"/project/{slug}/check"
        elif project_id is not None:
            url = f"/project/{project_id}/check"
        else:
            raise AssertionError("Neither slug and project_id is not None")
        return await cli(prefix=url).result

    async def get_project_dependencies(self, project_id: int):
        """
        检查项目依赖。[🔗](https://docs.modrinth.com/api-spec/#tag/projects/operation/getDependencies)

        参数:

        :param project_id: Mod ID

        用法: `resp = <ModrinthApi>.get_project_dependencies(project_id)`
        """
        url = f"/projects/{project_id}/dependencies"
        return await cli(prefix=url).result

    # TODO 构建器
    async def get_project_versions(
        self,
        slug: str = None,
        project_id: str = None,
        game_versions=None,
        loaders=None,
        featured=None,
    ):
        """
        获取 Mod 所有支持版本及相关信息。

        slug: ;

        project_id: ;

        game_versions: 游戏版本号;

        loaders: 加载器名称;

        featured: ;

        使用中 `slug` 和 `project_id` 可二选一使用，使用两个则优先使用 `slug` 。

        使用例子:

        - ``
        """
        if slug is not None:
            url = f"/project/{slug}/version"
        elif project_id is not None:
            url = f"/project/{project_id}/version"
        else:
            raise AssertionError("Neither slug and project_id is not None")
        params = {
            "game_versions": game_versions,
            "loaders": loaders,
            "featured": featured,
        }
        return await cli(prefix=url, params=params).result

    async def get_project_version(self, version_id: str):
        """
        根据版本 ID 获取信息。[🔗](https://docs.modrinth.com/api-spec/#tag/versions/operation/getVersion)

        参数:

        :param project_id: 版本 ID

        用法: `resp = <ModrinthApi>.get_project_version(project_id)`
        """
        url = f"/version/{version_id}"
        return await cli(prefix=url).result

    async def get_project_version_list(self, ids: str):
        """
        根据多个版本 ID 获取多个版本信息。[🔗](https://docs.modrinth.com/api-spec/#tag/versions/operation/getVersion)

        参数:

        :param ids: 多个版本 ID

        用法: `resp = <ModrinthApi>.get_project_version_list(ids)`
        """
        params = {"ids": ids}
        url = f"/versions"
        return await cli(prefix=url, params=params).result

    async def get_version_from_hash(self, hash: str, algorithm: str):
        """
        根据提供的 Hash 查找版本信息。[🔗](https://docs.modrinth.com/api-spec/#tag/version-files/operation/versionFromHash)

        参数:

        :param hash: 文件 Hash

        :param algorithm: 文件 Hash 算法

        用法: `resp = <ModrinthApi>.get_version_from_hash(hash, algorithm)`
        """
        params = {"algorithm": algorithm}
        url = f"/version_file/{hash}"
        return await cli(prefix=url, params=params).result

    async def get_latest_version_from_hash(
        self,
        hash: str,
        algorithm: str,
        loaders: List[str] = None,
        game_versions: List[str] = None,
    ):
        """
        根据提供的 Hash 查找版本信息。[🔗](https://docs.modrinth.com/#tag/version-files/operation/getLatestVersionFromHash)

        参数:

        :param hash: 文件 Hash

        :param algorithm: 文件 Hash 算法

        用法: `resp = <ModrinthApi>.get_version_from_hashes(hash, algorithm)`
        """
        params = {"algorithm": algorithm}
        url = f"/version_file/{hash}/update"
        data = {"loaders": [loaders], "game_versions": game_versions}
        return await cli(prefix=url, method="POST", params=params, data=data).result

    async def get_version_from_hashes(self, hashes: List[str], algorithm: str):
        """
        根据提供的 Hashes 查找版本信息。[🔗](https://docs.modrinth.com/#tag/version-files/operation/versionsFromHashes)

        参数:

        :param hashes: 文件 Hashes

        :param algorithm: 文件 Hash 算法

        用法: `resp = <ModrinthApi>.get_version_from_hashes(hashes, algorithm)`
        """
        url = f"/version_files"
        data = {"hashes": hashes, "algorithm": algorithm}
        return await cli(prefix=url, method="POST", data=data).result

    async def get_latest_version_from_hashes(
        self,
        hashes: List[str],
        algorithm: str,
        loaders: List[str] = None,
        game_versions: List[str] = None,
    ):
        """
        根据提供的 Hashes 查找版本信息。[🔗](https://docs.modrinth.com/#tag/version-files/operation/getLatestVersionFromHashes)

        参数:

        :param hashes: 文件 Hashes

        :param algorithm: 文件 Hash 算法

        用法: `resp = <ModrinthApi>.get_latest_version_from_hashes(hashes, algorithm)`
        """
        url = f"/version_files/update"
        data = {
            "hashes": hashes,
            "algorithm": algorithm,
            "loaders": loaders,
            "game_versions": game_versions,
        }
        return await cli(prefix=url, method="POST", data=data).result

    # TODO 这里需要一个 facets 构建器
    async def search(
        self,
        query: str = None,
        limit: int = 20,
        offset: int = None,
        index: Union[SortType, str] = SortType.relevance,
        facets: str = None,
    ):
        """
        搜索 Mod 。[🔗](https://docs.modrinth.com/api-spec/#tag/projects/operation/searchProjects)

        参数:

        :param query: 搜索内容

        :param limit: 返回数量限制

        :param offset: 偏移量

        :param index: 排序方法

        :param facets: [筛选搜索结果](https://docs.modrinth.com/docs/tutorials/api_search)

        用法: `resp = <ModrinthApi>.search(query, limit, offset, index, facets)`
        """

        if type(facets) == dict:
            facets_text = "["
            for a, b in facets.items():
                facets_text += '["{a}:{b}"],'.format(a=a, b=b)
            facets = facets_text[:-1] + "]"

        params = {
            "query": query,
            "limit": limit,
            "offset": offset,
            "index": index.value if isinstance(index, Enum) else index,
            "facets": facets,
        }
        url = "/search"
        return await cli(prefix=url, params=params).result

    async def get_categories(self):
        url = "/tag/category"
        return await cli(prefix=url).result

    async def get_loaders(self):
        url = f"/tag/loader"
        return await cli(prefix=url).result

    async def get_game_versions(self):
        url = f"/tag/game_version"
        return await cli(prefix=url).result

    async def get_licenses(self):
        url = f"/tag/license"
        return await cli(prefix=url).result

    async def get_project_dependencies(self, project_id: str, slug: str = None):
        if slug is not None:
            url = f"/project/{slug}/dependencies"
        elif project_id is not None:
            url = f"/project/{project_id}/dependencies"
        else:
            raise AssertionError("Neither slug and project_id is not None")
        return await cli(prefix=url).result

async def test():
    modrinth = ModrinthApi()
    example_hashes = ["7647a59c2b37c673948b0a35961eabac3a5eda96", "c4fcf9d92247c80149cee5ee2e3eff9819774042"]
    print(await modrinth.end_point())
    print(await modrinth.get_project("sodium"))
    print(await modrinth.get_projects(["sodium", "fabric-api"]))
    print(await modrinth.check_project(slug="fabric"))
    print(await modrinth.get_project_dependencies("sodium"))
    print(await modrinth.get_project_versions(slug="sodium"))
    print(await modrinth.get_project_version("pmgeU5yX"))
    print(await modrinth.get_project_version_list(["pmgeU5yX", "Wzzjm5lQ"]))
    print(await modrinth.get_version_from_hash(example_hashes[0], "sha1"))
    print(await modrinth.get_latest_version_from_hash(example_hashes[0], "sha1"))
    print(await modrinth.get_version_from_hashes(example_hashes, "sha1"))
    print(await modrinth.get_latest_version_from_hashes(example_hashes, "sha1"))
    print(await modrinth.search("sodium"))
    print(await modrinth.get_categories())
    print(await modrinth.get_loaders())
    print(await modrinth.get_game_versions())
    print(await modrinth.get_licenses())
    print(await modrinth.get_project_dependencies("sodium"))
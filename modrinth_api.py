import requests
import api_config

base_api_url = api_config.modrinth_base_api_url
proxies = api_config.proxies


def end_point():
    url = base_api_url

    headers = {
        'Accept': 'application/json'
    }

    res = requests.get(url=url, proxies=proxies, headers=headers)

    if res.status_code == 200:
        return res.text
    else:
        return res.status_code


class Mod:
    def __init__(self):
        pass

    def get_mod(self, slug=None, modid=None):
        '''
        获取 Mod 信息。

        使用中 `slug` 和 `modid` 可二选一使用，使用两个则优先使用 `slug` 。

        使用例子:

        - ``
        '''
        if slug is None and modid is None:
            return None
        else:
            if slug is not None:
                url = base_api_url + "project/{slug}".format(slug=slug)
            else:
                url = base_api_url + "project/{modid}".format(modid=modid)

            headers = {
                'Accept': 'application/json'
            }

            res = requests.get(url=url, proxies=proxies, headers=headers)
            if res.status_code == 200:
                return res.json()
            else:
                return res.status_code

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
        if slug is None and modid is None:
            return None
        else:
            if slug is not None:
                url = base_api_url + "project/{slug}/version".format(slug=slug)
            else:
                url = base_api_url + \
                    "project/{modid}/version".format(modid=modid)

            headers = {
                'Accept': 'application/json'
            }

            res = requests.get(url=url, proxies=proxies, headers=headers, params={
                               "game_versions": game_versions, "loaders": loaders, "featured": featured})
            if res.status_code == 200:
                return res.json()
            else:
                return res.status_code

    def get_mod_version(self, id: str):
        '''
        跟据提供的版本号获取信息。

        id: 版本号。

        使用例子:

        '''
        url = base_api_url + "version/{version_id}".format(version_id=id)
        headers = {
            'Accept': 'application/json'
        }

        res = requests.get(url=url, proxies=proxies, headers=headers)
        if res.status_code == 200:
            return res.json()
        else:
            return res.status_code

    def search(self, query, limit=20, offset=None, index="relevance", facets=None):
        '''
        搜索 Mod 。

        query: 搜索内容;

        offset: 从第几个开始;

        index
        '''
        if type(facets) == dict:
            facets_text = "["
            for facet in facets:
                facets_text = facets_text + \
                    '["{a}:{b}"]'.format(a=facet, b=facets[facet]) + ","
            facets = facets_text[:-1] + "]"

        url = base_api_url + "search"
        headers = {
            'Accept': 'application/json'
        }

        res = requests.get(url=url, proxies=proxies, headers=headers, params={
                           "query": query, "limit": limit, "offset": offset, "index": index, "facets": facets})
        if res.status_code == 200:
            return res.json()
        else:
            return res.status_code

    def get_mod_version_download_info(self, id):
        '''
        获取格式化后的文件信息
        用于下载Mod
        '''
        version_info = Mod().get_mod_version(id)
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
        else:
            return None

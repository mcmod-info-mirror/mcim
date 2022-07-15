
import requests

from .base import *

__all__ = [
    'CurseForgeApi'
]

class CurseForgeApi:
    def __init__(self, baseurl: str, api_key: str, proxies: dict=None):
        self.baseurl = baseurl
        self.api_key = api_key
        self.proxies = proxies

    def end_point(self):
        headers = {
            'Accept': 'application/json',
            'x-api-key': self.api_key
        }

        res = requests.get(url=self.baseurl, proxies=self.proxies, headers=headers)        
        if res.status_code != 200:
            raise StatusCodeException(res.status_code)
        return res.json()

    def get_all_games(self,index=1, pageSize=50):
        url = self.baseurl + "v1/games?index={index}&pageSize={pageSize}".format(index=index, pageSize=pageSize)
        headers = {
            'Accept': 'application/json',
            'x-api-key': self.api_key
        }
        res = requests.get(url=url, proxies=self.proxies, headers=headers)
        if res.status_code != 200:
            raise StatusCodeException(res.status_code)
        return res.json()

    def get_game(self,gameid,index=1, pageSize=50):
        url = self.baseurl + "v1/games/{gameid}?index={index}&pageSize={pageSize}".format(gameid=gameid,index=index, pageSize=pageSize)
        headers = {
            'Accept': 'application/json',
            'x-api-key': self.api_key
        }
        res = requests.get(url=url, proxies=self.proxies, headers=headers)
        if res.status_code != 200:
            raise StatusCodeException(res.status_code)
        return res.json()

    def get_game_version(self,gameid,index=1, pageSize=50):
        url = self.baseurl + "v1/games/{gameid}/versions?index={index}&pageSize={pageSize}".format(gameid=gameid,index=index, pageSize=pageSize)
        headers = {
            'Accept': 'application/json',
            'x-api-key': self.api_key
        }
        res = requests.get(url=url, proxies=self.proxies, headers=headers)
        if res.status_code != 200:
            raise StatusCodeException(res.status_code)
        return res.json()

    def get_all_categories(self, gameid=432): #id is class = [17,5,4546,4471,12,4559,6(Mods)]
        headers = {
            'Accept': 'application/json',
            'x-api-key': self.api_key
        }
        url = self.baseurl + "v1/categories"
        res = requests.get(url=url, headers=headers, params={'gameId': gameid}, proxies=self.proxies)
        if res.status_code != 200:
            raise StatusCodeException(res.status_code)
        return res.json()

    def search(self, text=None, slug=None, gameid=432, classid=6, ModLoaderType=0, gameversion=None, index=1, pageSize=50):
        #{"0":"Any","1":"Forge","2":"Cauldron","3":"LiteLoader","4":"Fabric","5":"Quilt"}
        #url = self.baseurl + "v1/mods/search?#gameId={gameid}&sortField=Featured&sortOrder=desc&pageSize={pageSize}&categoryId=0&classId={classid}&modLoaderType={modloadertype}&gameVersion={gameversion}&searchFilter={text}".format(classid=classid,text=text,gameid=gameid, pageSize=pageSize,modloadertype=ModLoaderType,gameversion=)
        url = self.baseurl + "v1/mods/search"
        headers = {
            'Accept': 'application/json',
            'x-api-key': self.api_key
        }
        res = requests.get(url=url, headers=headers, params={'gameId': gameid, "sortField": "Featured", "sortOrder": "desc", "pageSize": pageSize, "categoryId": "0", "classId": classid, "slug": slug, "modLoaderType": ModLoaderType, "gameVersion": gameversion, "searchFilter": text}, proxies=self.proxies)
        if res.status_code != 200:
            raise StatusCodeException(res.status_code)
        return res.json()

    def get_mod(self, modid):
        url = self.baseurl + "v1/mods/{modid}".format(modid=modid)
        headers = {
            'Accept': 'application/json',
            'x-api-key': self.api_key
        }
        res = requests.get(url=url, proxies=self.proxies, headers=headers)
        if res.status_code != 200:
            raise StatusCodeException(res.status_code)
        return res.json()
    
    def get_mods(self, modids) -> list:
        url = self.baseurl + "v1/mods"
        body = {
            "modIds":modids
        }
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'x-api-key': self.api_key
        }
        res = requests.post(url=url, proxies=self.proxies, headers=headers, json=body)
        if res.status_code != 200:
            raise StatusCodeException(res.status_code)
        return res.json()

    def get_mod_description(self, modid):
        url = self.baseurl + "v1/mods/{modid}/description".format(modid=modid)
        headers = {
            'Accept': 'application/json',
            'x-api-key': self.api_key
        }
        res = requests.get(url=url, proxies=self.proxies, headers=headers)
        if res.status_code != 200:
            raise StatusCodeException(res.status_code)
        return res.json()["data"]

    def get_file(self, modid, fileid):
        url = self.baseurl + "v1/mods/{modid}/files/{fileid}".format(modid=modid, fileid=fileid)
        headers = {
            'Accept': 'application/json',
            'x-api-key': self.api_key
        }
        res = requests.get(url=url, proxies=self.proxies, headers=headers)
        if res.status_code != 200:
            raise StatusCodeException(res.status_code)
        return res.json()

    def get_files(self, fileids, modid):
        url = self.baseurl + "v1/mods/{modid}/files".format(modid=modid)
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'x-api-key': self.api_key
        }
        body = {
            "fileIds": fileids
        }
        res = requests.post(url=url, proxies=self.proxies, headers=headers, json=body)
        if res.status_code != 200:
            raise StatusCodeException(res.status_code)
        return res.json()

    HASHES_TYPE_ID = {
        1: "sha1",
        2: "md5"
    }

    def get_file_download_info(self, modid, fileid):
        '''
        获取格式化后的文件信息
        用于下载Mod
        '''
        version_info = self.get_file(modid, fileid)["data"]
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
            "type": self.__class__.HASHES_TYPE_ID.get(hash["algo"], hash["algo"]),
            "value": hash["value"]
        } for hash in version_info["hashes"]]
        return info

    def get_file_download_url(self, fileid, modid):
        url = self.baseurl + "v1/mods/{modid}/files/{fileid}/download-url".format(modid=modid, fileid=fileid)
        headers = {
            'Accept': 'application/json',
            'x-api-key': self.api_key
        }
        res = requests.get(url=url, proxies=self.proxies, headers=headers)
        if res.status_code != 200:
            raise StatusCodeException(res.status_code)
        return res.json()["data"]

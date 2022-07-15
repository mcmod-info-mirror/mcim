import requests
import api_config

api_key = api_config.api_key
base_api_url = api_config.curseforge_base_api_url
proxies = api_config.proxies

def end_point():
        url = base_api_url
        
        headers = {
            'Accept': 'application/json',
            'x-api-key': api_key
        }
        
        res = requests.get(url=url,proxies=proxies,headers=headers)
        
        if res.status_code == 200:
            return res.text
        else:
            return res.status_code

class Games:
    def __init__(self):
        pass

    def get_all_games(self,index=1,pageSize=50):
        url = base_api_url + "v1/games?index={index}&pageSize={pageSize}".format(index=index,pageSize=pageSize)
        headers = {
            'Accept': 'application/json',
            'x-api-key': api_key
        }
        res = requests.get(url=url,proxies=proxies,headers=headers)
        if res.status_code == 200:
            return res.json()
        else:
            return res.status_code

    def get_game(self,gameid,index=1,pageSize=50):
        url = base_api_url + "v1/games/{gameid}?index={index}&pageSize={pageSize}".format(gameid=gameid,index=index,pageSize=pageSize)
        headers = {
            'Accept': 'application/json',
            'x-api-key': api_key
        }
        res = requests.get(url=url,proxies=proxies,headers=headers)
        if res.status_code == 200:
            return res.json()
        else:
            return res.status_code

    def get_game_version(self,gameid,index=1,pageSize=50):
        url = base_api_url + "v1/games/{gameid}/versions?index={index}&pageSize={pageSize}".format(gameid=gameid,index=index,pageSize=pageSize)
        headers = {
            'Accept': 'application/json',
            'x-api-key': api_key
        }
        res = requests.get(url=url,proxies=proxies,headers=headers)
        if res.status_code == 200:
            return res.json()
        else:
            return res.status_code

class Categories:
    def __init__(self):
        pass

    def get_all_categories(self,gameid=432): #id is class = [17,5,4546,4471,12,4559,6(Mods)]
        headers = {
            'Accept': 'application/json',
            'x-api-key': api_key
        }
        url = base_api_url + "v1/categories"
        res = requests.get(url=url,headers=headers,params={'gameId': gameid},proxies=proxies)
        if res.status_code == 200:
            return res.json()
        else:
            return res.status_code

class Mod:
    def __init__(self):
        pass

    def search(self,text=None,slug=None,gameid=432,classid=6,ModLoaderType=0,gameversion=None,index=1,pageSize=50):
        #{"0":"Any","1":"Forge","2":"Cauldron","3":"LiteLoader","4":"Fabric","5":"Quilt"}
        #url = base_api_url + "v1/mods/search?#gameId={gameid}&sortField=Featured&sortOrder=desc&pageSize={pageSize}&categoryId=0&classId={classid}&modLoaderType={modloadertype}&gameVersion={gameversion}&searchFilter={text}".format(classid=classid,text=text,gameid=gameid,pageSize=pageSize,modloadertype=ModLoaderType,gameversion=)
        url = base_api_url + "v1/mods/search"
        headers = {
            'Accept': 'application/json',
            'x-api-key': api_key
        }
        res = requests.get(url=url,headers=headers,params={'gameId': gameid,"sortField":"Featured","sortOrder": "desc", "pageSize":pageSize, "categoryId":"0", "classId":classid, "slug":slug, "modLoaderType":ModLoaderType, "gameVersion":gameversion, "searchFilter":text},proxies=proxies)
        if res.status_code == 200:
            return res.json()
        else:
            return res.status_code

    def get_mod(self,modid):
        url = base_api_url + "v1/mods/{modid}".format(modid=modid)
        headers = {
            'Accept': 'application/json',
            'x-api-key': api_key
        }
        res = requests.get(url=url,proxies=proxies,headers=headers)
        if res.status_code == 200:
            return res.json()
        else:
            return res.status_code
    
    def get_mods(self, modids) -> list:
        url = base_api_url + "v1/mods"
        body = {
            "modIds":modids
        }
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'x-api-key': api_key
        }
        res = requests.post(url=url,proxies=proxies,headers=headers,json=body)
        if res.status_code == 200:
            return res.json()
        else:
            return res.status_code

    def get_mod_description(self,modid):
        url = base_api_url + "v1/mods/{modid}/description".format(modid=modid)
        headers = {
            'Accept': 'application/json',
            'x-api-key': api_key
        }
        res = requests.get(url=url,proxies=proxies,headers=headers)
        if res.status_code == 200:
            return res.json()["data"]
        else:
            return res.status_code

class File:
    def __init__(self):
        pass

    def get_file(self,modid,fileid):
        url = base_api_url + "v1/mods/{modid}/files/{fileid}".format(modid=modid,fileid=fileid)
        headers = {
            'Accept': 'application/json',
            'x-api-key': api_key
        }
        res = requests.get(url=url,proxies=proxies,headers=headers)
        if res.status_code == 200:
            return res.json()
        else:
            return res.status_code

    def get_files(self,fileids,modid):
        url = base_api_url + "v1/mods/{modid}/files".format(modid=modid)
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'x-api-key': api_key
        }
        body = {
            "fileIds": fileids
        }
        res = requests.post(url=url,proxies=proxies,headers=headers,json=body)
        if res.status_code == 200:
            return res.json()
        else:
            return res.status_code

    def get_file_download_info(self,modid,fileid):
        '''
        获取格式化后的文件信息
        用于下载Mod
        '''
        version_info = File().get_file(modid,fileid)["data"]
        info = {}
        if version_info is not None:
            info["type"] = "Curseforge"
            info["name"] = version_info["displayName"]
            info["date_published"] = version_info["fileDate"]
            
            for hash in version_info["hashes"]:
                if hash["algo"] == 1: #sha1 == 1 | md5 == 2
                    info["hash"] = hash["value"]
                else:
                    info["hash"] = hash["value"]

            info["filename"] = version_info["fileName"]
            info["url"] = version_info["downloadUrl"]
            info["size"] = version_info["fileLength"]
            return info
        else:
            return None

    def get_file_download_url(self,fileid,modid):
        url = base_api_url + "v1/mods/{modid}/files/{fileid}/download-url".format(modid=modid,fileid=fileid)
        headers = {
            'Accept': 'application/json',
            'x-api-key': api_key
        }
        res = requests.get(url=url,proxies=proxies,headers=headers)
        if res.status_code == 200:
            return res.json()["data"]
        else:
            return res.status_code
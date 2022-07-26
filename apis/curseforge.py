
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
	def __init__(self, baseurl: str, api_key: str, proxies: dict = None, acli = None):
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
			res = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,), url=self.baseurl, proxy=self.proxies, headers=headers)
			return res.status_code # 这不是json

	async def get_all_games(self, index=1, pageSize=50):
		url = self.baseurl + "games?index={index}&pageSize={pageSize}".format(index=index, pageSize=pageSize)
		headers = {
			'Accept': 'application/json',
			'x-api-key': self.api_key
		}
		async with self.acli:
			res = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,), url, proxy=self.proxies, headers=headers)
			return res[1].decode('utf-8')

	async def get_game(self, gameid, index=1, pageSize=50):
		url = self.baseurl + "games/{gameid}?index={index}&pageSize={pageSize}".format(gameid=gameid,index=index, pageSize=pageSize)
		headers = {
			'Accept': 'application/json',
			'x-api-key': self.api_key
		}
		async with self.acli:
			res = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,), url, proxy=self.proxies, headers=headers)
			return res[1].decode('utf-8')

	async def get_game_version(self, gameid, index=1, pageSize=50):
		url = self.baseurl + "games/{gameid}/versions?index={index}&pageSize={pageSize}".format(gameid=gameid,index=index, pageSize=pageSize)
		headers = {
			'Accept': 'application/json',
			'x-api-key': self.api_key
		}
		async with self.acli:
			res = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,), url, proxy=self.proxies, headers=headers)
			return res[1].decode('utf-8')

	async def get_categories(self, gameid=432, classid=None): # classid 为主分类的有 main class [17,5,4546,4471,12,4559,6(Mods)]
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
			res = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,), url, headers=headers, params=params, proxy=self.proxies)
			return res[1].decode('utf-8')

	async def search(self, text=None, slug=None, gameid=432, classid=6, modLoaderType=None, sortField="Featured", categoryid=None, gameversion=None, index=None, pageSize=None):
		# ModLoaderType
		# {
		#   "0":"Any",
		#   "1":"Forge",
		#   "2":"Cauldron",
		#   "3":"LiteLoader",
		#   "4":"Fabric",
		#   "5":"Quilt"
		# }
		
		# sortField
		# 1=Featured
		# 2=Popularity
		# 3=LastUpdated
		# 4=Name
		# 5=Author
		# 6=TotalDownloads
		# 7=Category
		# 8=GameVersion
		
		#url = self.baseurl + "mods/search?#gameId={gameid}&sortField=Featured&sortOrder=desc&pageSize={pageSize}&categoryId=0&classId={classid}&modLoaderType={modloadertype}&gameVersion={gameversion}&searchFilter={text}".format(classid=classid,text=text,gameid=gameid, pageSize=pageSize,modloadertype=ModLoaderType,gameversion=gameversion)
		url = self.baseurl + "mods/search"
		headers = {
			'Accept': 'application/json',
			'x-api-key': self.api_key
		}
		async with self.acli:
			res = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,), url, headers=headers, params={'gameId': gameid, "sortField": sortField, "categoryId": categoryid, "sortOrder": "desc", "index": index, "pageSize": pageSize, "classId": classid, "slug": slug, "modLoaderType": modLoaderType, "gameVersion": gameversion, "searchFilter": text}, proxy=self.proxies)
			return res[1].decode('utf-8')

	async def get_mod(self, modid):
		url = self.baseurl + "mods/{modid}".format(modid=modid)
		headers = {
			'Accept': 'application/json',
			'x-api-key': self.api_key
		}
		async with self.acli:
			res = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,), url, headers=headers)
			return res[1].decode('utf-8')
			# 没有callback，返回数据只能在 content，不知道要不要传 callback for self.acli.get
			# 没想好怎么处理，作为 api 应该返回 dict 类型，对于 sync 来说就得再load一次; 先替换了

	async def get_mods(self, modids) -> list:
		url = self.baseurl + "mods"
		body = {
			"modIds":modids
		}
		headers = {
			'Content-Type': 'application/json',
			'Accept': 'application/json',
			'x-api-key': self.api_key
		}
		async with self.acli:
			res = await self.acli.post(url, proxy=self.proxies, headers=headers, json=body)
			return res[1].decode('utf-8')

	async def get_mod_description(self, modid):
		url = self.baseurl + "mods/{modid}/description".format(modid=modid)
		headers = {
			'Accept': 'application/json',
			'x-api-key': self.api_key
		}
		async with self.acli:
			res = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,), url, proxy=self.proxies, headers=headers)
			return res[1].decode('utf-8')

	async def get_file(self, modid, fileid):
		url = self.baseurl + "mods/{modid}/files/{fileid}".format(modid=modid, fileid=fileid)
		headers = {
			'Accept': 'application/json',
			'x-api-key': self.api_key
		}
		async with self.acli:
			res = await retry_async(res_mustok_async(self.acli.get), 3, (StatusCodeException,), url, proxy=self.proxies, headers=headers)
			return res[1].decode('utf-8')

	async def get_files(self, fileids, modid):
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
			res = await res_mustok_async(self.acli.post)(url, proxy=self.proxies, headers=headers, json=body)
			return res[1].decode('utf-8')

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
		url = self.baseurl + "mods/{modid}/files/{fileid}/download-url".format(modid=modid, fileid=fileid)
		headers = {
			'Accept': 'application/json',
			'x-api-key': self.api_key
		}
		async with self.acli:
			res = await retry_async(self.acli.get, 3, (StatusCodeException,), url, proxy=self.proxies, headers=headers)
			return res[1].decode('utf-8')

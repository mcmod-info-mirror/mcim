
import json
import os

__all__ = [
	'MysqlConfig',
	'MCIMConfig',
	'ClashConfig'
]

def checktyp(obj: object, typ: type):
	assert isinstance(obj, typ)
	return obj

class MysqlConfig:
	host: str = '127.0.0.1'
	port: int = 3306
	user: str = 'username'
	password: str = 'password'
	database: str = 'database'

	@classmethod
	def to_dict(cls):
		return {
			'host': cls.host,
			'port': cls.port,
			'user': cls.user,
			'password': cls.password,
			'database': cls.database
		}

	@classmethod
	def save(cls, target='./mysql.config.json'):
		with open(target, 'w') as fd:
			json.dump(cls.to_dict(), fd)

	@classmethod
	def load(cls, target='./mysql.config.json'):
		if not os.path.exists(target):
			cls.save(target=target)
			return
		data: dict
		with open(target, 'r') as fd:
			data = json.load(fd)
		cls.host = checktyp(data.get('host'), str)
		cls.port = checktyp(data.get('port'), int)
		cls.user = checktyp(data.get('user'), str)
		cls.password = checktyp(data.get('password'), str)
		cls.database = checktyp(data.get('database'), str)

class MCIMConfig:
	curseforge_api_key: str = '<api key>'
	curseforge_api: str = "https://api.curseforge.com/v1/" # 不然和api的拼接对不上
	modrinth_api: str = "https://api.modrinth.com/"
	proxies: str = None
	sync_interval: int = 3600 # seconds
	async_timeout: int = 60 # seconds

	# cqhttp
	cqhttp_type: str = "user"
	cqhttp_baseurl: str = "http://localhost:7777/"
	cqhttp_groupid: int = 316052940
	cqhttp_userid: int = 3531890582
	cqhttp_guild_id: int = 82563051659156519
	cqhttp_channel_id: int = 9409904

	@classmethod
	def to_dict(cls):
		return {
			'curseforge_api_key': cls.curseforge_api_key,
			'curseforge_api': cls.curseforge_api,
			'modrinth_api': cls.modrinth_api,
			'proxies': cls.proxies,
			'sync_interval': cls.sync_interval,
			'async_timeout': cls.async_timeout,
			'cqhttp_type': cls.cqhttp_type,
			'cqhttp_baseurl': cls.cqhttp_baseurl,
			'cqhttp_userid': cls.cqhttp_userid,
			'cqhttp_groupid': cls.cqhttp_groupid,
			'cqhttp_guild_id': cls.cqhttp_guild_id,
			'cqhttp_channel_id': cls.cqhttp_channel_id
		}

	@classmethod
	def save(cls, target='./config.json'):
		with open(target, 'w') as fd:
			json.dump(cls.to_dict(), fd)

	@classmethod
	def load(cls, target='./config.json'):
		if not os.path.exists(target):
			cls.save(target=target)
			return
		data: dict
		with open(target, 'r') as fd:
			data = json.load(fd)
		cls.curseforge_api_key = checktyp(data.get('curseforge_api_key'), str)
		cls.curseforge_api = checktyp(data.get('curseforge_api'), str)
		cls.modrinth_api = checktyp(data.get('modrinth_api'), str)
		cls.proxies = data.get('proxies')
		cls.sync_interval = checktyp(data.get('sync_interval'), int)
		cls.async_timeout = checktyp(data.get('async_timeout'), int)
		cls.cqhttp_type = checktyp(data.get('cqhttp_type'), str)
		cls.cqhttp_baseurl = checktyp(data.get('cqhttp_baseurl'), str)
		cls.cqhttp_userid = checktyp(data.get('cqhttp_userid'), int)
		cls.cqhttp_groupid = checktyp(data.get('cqhttp_groupid'), int)
		cls.cqhttp_guild_id = checktyp(data.get('cqhttp_guild_id'), int)
		cls.cqhttp_channel_id = checktyp(data.get('cqhttp_channel_id'), int)

class ClashConfig:
	api_url: str = "127.0.0.1"
	api_port: int = 9090
	api_secret: str = ""
	
	@classmethod
	def to_dict(cls):
		return {
			'clash_api_url': cls.api_url,
			'clash_api_port': cls.api_port,
			"clash_api_secret": cls.api_secret
		}

	@classmethod
	def save(cls, target='./clash.config.json'):
		with open(target, 'w') as fd:
			json.dump(cls.to_dict(), fd)

	@classmethod
	def load(cls, target='./clash.config.json'):
		if not os.path.exists(target):
			cls.save(target=target)
			return
		data: dict
		with open(target, 'r') as fd:
			data = json.load(fd)
		cls.api_url = checktyp(data.get('clash_api_url'), str)
		cls.api_port = checktyp(data.get('clash_api_port'), int)
		cls.api_secret =checktyp(data.get('clash_api_secret'), str)
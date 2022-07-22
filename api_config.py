
__all__ = [
	'Config'
]


class Config:
	api_key = "<api key>"
	curseforge_base_api_url = "https://api.curseforge.com/v1"
	modrinth_base_api_url = "https://api.modrinth.com/"
	proxies = {
		"http": "http://127.0.0.1:7890",
		"https": "http://127.0.0.1:7890"
	}
	sync_interval = 60 # minutes
	async_timeout = 60 # seconds
	mysql = {
		"pwd": "z0z0r4admin",
		"host": "127.0.0.1",
		"port": 3306,
		"user": "root"
	}

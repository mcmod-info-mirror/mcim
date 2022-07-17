
__all__ = [
	'Config'
]


class Config:
	api_key = "$2a$10$2DOXBr1x82Acn1A6GGw5b.psdLVOo29u5gEahTQSiGYmDOp2QXFSu"
	curseforge_base_api_url = "https://api.curseforge.com/"
	modrinth_base_api_url = "https://api.modrinth.com/"
	proxies = {
		"http": "http://127.0.0.1:7890",
		"https": "http://127.0.0.1:7890"
	}
	sync_interval = 60 # minutes
	async_timeout = 60 # seconds

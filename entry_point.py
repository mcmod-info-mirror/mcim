
import os
import json
from .apis import *
from .api_config import Config

def main():
    print('Welecome to MCIM')
    api = CurseForgeApi(Config.curseforge_base_api_url, Config.api_key, Config.proxies)
    res = api.get_categories(classid=6)
    print(json.dumps(res, indent=2))

# from app.service.curseforge import *
from app.sync.curseforge import CurseForgeApi
import json
from app.database.mongodb import start_async_mongodb

import asyncio

cf_api = CurseForgeApi

async def main():
    await start_async_mongodb()
    # info = await get_mod_files_info(348521)
    info = await cf_api.get_fingerprints([1667027305, 320753274, 114514])
    with open("info.json", "w") as f:
        f.write(json.dumps(info))
    pass

asyncio.run(main())
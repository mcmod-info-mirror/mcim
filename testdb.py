import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import Document, init_beanie, Indexed, Link, WriteRules
from typing import List
from app.sync.curseforge import CurseForgeApi


def alias_id(mod: dict) -> dict:
    mod["modId"] = mod["id"]
    del mod["id"]
    for file in mod["latestFiles"]:
        file["fileId"] = file["id"]
        del file["id"]
    return mod


async def main():
    # 连接到 MongoDB 数据库
    mongo_uri = "mongodb://z0z0r4:ZZR123zzr@localhost:27017"
    client = AsyncIOMotorClient(mongo_uri)
    database_name = "mcim"
    db = client[database_name]

    # 定义要插入的文档
    class FileInfo(Document):
        fileId: Indexed(int, unique=True)

        class Settings:
            name = "test_files"

    class ModInfo(Document):
        modId: Indexed(int, unique=True)
        # status: int
        files: Link[FileInfo]

        class Settings:
            name = "test_mods"

    # finfo = await CurseForgeApi.post_files([4973456, 4973457])

    f1 = {
        "fileId": 4973456,
        "modId": 348521,
    }

    f2 = {
        "fileId": 4973457,
        "modId": 348521,
    }
    mj = {"modId": 348521, 
        #   "status": 1
         "files": f1
         }
         
    await init_beanie(database=db, document_models=[FileInfo, ModInfo])
    m = await ModInfo.find_one(ModInfo.modId == 348521)
    await m.save(link_rule=WriteRules.WRITE)

if __name__ == "__main__":
    asyncio.run(main())

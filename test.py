# import os
# import json
# import sqlite3

# PATH = "E:/mcim_mount/modrinth"

# cached = set()

# ddata = {}

# dto_cache = {}


# # with open("cached.json") as f:
# #     cached = set(json.load(f))

# # with open("data.json") as f:
# #     data = json.load(f)
# #     for file in data:
# #         if data[file]["size"] < 1024*1024*50:
# #             if file not in cached:
# #                 dto_cache[file] = data[file]

# # with open("dto_cache.json", "w") as f:
# #     json.dump(dto_cache, f)

# # size = 0
# # count = 0
# # total_size = 0
# # with open("data.json") as f:
# #     data = json.load(f)
# #     total = len(data)
# #     for file in data:
# #         total_size += int(data[file]["size"])
# #         if int(data[file]["size"]) < 1024*1024*50:
# #             size += data[file]["size"]
# #             count += 1
# #         else:
# #             print(data[file])
# #     print(size/1024/1024/1024, count, total-count, total_size/1024/1024/1024 - size/1024/1024/1024, total)

# count = 0
# for i in range(255):
#     if os.path.exists(os.path.join(PATH, hex(i)[2:])):
#         for file in os.listdir(os.path.join(PATH, hex(i)[2:])):
#             # if os.path.getsize(os.path.join(PATH, hex(i)[2:], file)) == 0:
#             #     os.remove(os.path.join(PATH, hex(i)[2:], file))
#             #     print(f"Deleted {os.path.join(PATH, hex(i)[2:], file)}")
#             # cached.add(file)
#             count += 1
# print(count)

# # with open("cached.json", "w") as f:
# #     json.dump(list(cached), f)

# # with open("cached.json") as f:
# #     cached = set(json.load(f))
    


# # to_cache = sha1-cached


# # PATH = ""
# # for i in range(255):
# #     if os.path.exists(os.path.join(PATH, hex(i)[2:])):
# #         for file in os.listdir(os.path.join(PATH, hex(i)[2:])):
# #             if os.path.getsize(os.path.join(PATH, hex(i)[2:], file)) > 1024 * 1024 * 50:
# #                 os.rename(os.path.join(PATH, hex(i)[2:], file), os.path.join(PATH, hex(i)[2:], file+".ignore"))
#             # if os.path.getsize(os.path.join(PATH, hex(i)[2:], file)) == 0:
#             #     os.remove(os.path.join(PATH, hex(i)[2:], file))
#             #     print(f"Deleted {os.path.join(PATH, hex(i)[2:], file)}")


# # with open("to_cache.json", "w") as f:
# #     json.dump(, f)
# # size = 0
# # with open("dto_cache.json") as f:
# #     to_cache = json.load(f)
# #     print(len(to_cache))
# #     for cache in to_cache:
# #         size += to_cache[cache]["size"]
# #     print(size/1024/1024/1024)
# # dto_cache = {}


# # for sha1 in to_cache:
# #     dto_cache[sha1] = data[sha1]

# # with open("dto_cache.json", "w") as f:
# #     json.dump(dto_cache, f)

# # data1 = {}

# # with open("dto_cache.json") as f:
# #     dto_cache = json.load(f)
# #     i =0
# #     for item, file in dto_cache.items():
# #         # data1[file["sha1"]] = file
# #         i += 1
# #         if i >= 150000:
# #             data1[file["sha1"]] = file

# # with open("data150000-end.json", "w") as f:
# #     json.dump(data1, f)

import os

from app.config import MCIMConfig, Aria2Config

mcim_config = MCIMConfig.load()
aria2_config = Aria2Config.load()

if mcim_config.file_cdn:
    os.makedirs(aria2_config.modrinth_download_path, exist_ok=True)
    os.makedirs(aria2_config.curseforge_download_path, exist_ok=True)
    for i in range(256):
        os.makedirs(os.path.join(aria2_config.modrinth_download_path, format(i, '02x')), exist_ok=True)
        os.makedirs(os.path.join(aria2_config.curseforge_download_path, format(i, '02x')), exist_ok=True)
from app.sync.curseforge import file_cdn_cache_add_task
from app.models.database.curseforge import File
# file_cdn_url_cache(url="http://storage.yserver.ink:5244/d/modrinth/00/0000786b3e0ae9888efd51d460d130b0f7d71d7f", key="key")
file_info = {
  "dependencies": [],
  "displayName": "jei-1.20.4-forge-17.2.0.40.jar",
  "downloadCount": 0,
  "downloadUrl": "https://edge.forgecdn.net/files/5059/890/jei-1.20.4-forge-17.2.0.40.jar",
  "fileDate": "2024-01-26T00:39:03.153Z",
  "fileFingerprint": 1552132089,
  "fileLength": 1122171,
  "fileName": "jei-1.20.4-forge-17.2.0.40.jar",
  "fileStatus": 4,
  "found": True,
  "gameId": 432,
  "gameVersions": [
    "Forge",
    "1.20.4"
  ],
  "hashes": [
    {
      "value": "bcdba3c7c3bdc2c2934fc5f8b5048282b914b40d",
      "algo": 1
    },
    {
      "value": "13edd4668f68f0807efd3b379498de0a",
      "algo": 2
    }
  ],
  "modId": 238222,
  "releaseType": 2,
  "sortableGameVersions": [
    {
      "gameVersionName": "Forge",
      "gameVersionPadded": "0",
      "gameVersion": "",
      "gameVersionReleaseDate": "2022-10-01T00:00:00Z",
      "gameVersionTypeId": 68441
    },
    {
      "gameVersionName": "1.20.4",
      "gameVersionPadded": "0000000001.0000000020.0000000004",
      "gameVersion": "1.20.4",
      "gameVersionReleaseDate": "2023-12-07T15:17:47.907Z",
      "gameVersionTypeId": 75125
    }
  ],
  "sync_at": "2024-05-26T02:36:23Z"
}
file = File(id=5655655656, **file_info)
file_cdn_cache_add_task(file)

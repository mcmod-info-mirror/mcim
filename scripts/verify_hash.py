from webdav4.fsspec import WebdavFileSystem
from webdav4.client import Client
import os
import json
from pymongo import MongoClient



base_url = "http://127.0.0.1:5244/dav"

USERNAME = ""
PASSWORD = ""

fs = WebdavFileSystem(base_url, auth=(USERNAME, PASSWORD))
client = Client(base_url, auth=(USERNAME, PASSWORD))

fs.upload_fileobj(open("error_files.json"))

# 通过 fs 遍历 curseforge 和 modrinth 文件夹内的所有文件，输出 sha1 文件名对应 size 大小到 result.json
# /curseforge
#   00
#     00xxxxx (sha1)
# 根据这个规则遍历文件夹

result = []
os.makedirs("result", exist_ok=True)
for folder in ["curseforge", "modrinth"]:
    for i in range(256):
        folder_path = f"/{folder}/{i:02x}"
        for file in fs.ls(folder_path):
            sha1 = file.get("display_name")
            size = file.get("size")
            # path = file["name"]
            result.append({"sha1": sha1, "size": size})
        print(f"Folder {folder_path} done. Found {len(result)} files.")
        with open(os.path.join("result", f"{folder}_{i:02x}_result.json"), "w") as f:
            json.dump(result, f)
            result.clear()

import os
import json
from pymongo import MongoClient

client = MongoClient("mongodb://")
db = client["mcim_backend"]

mr_files = db["modrinth_files"]
cf_files = db["curseforge_files"]

error_files = []

for file in os.listdir("result"):
    print(f"Checking {file}")
    with open(os.path.join("result", file), "r") as f:
        data = json.load(f)
        formated_data = {x["sha1"]: x["size"] for x in data}
        if "modrinth" in file:
            find_result = mr_files.find({"_id.sha1": {"$in": [x["sha1"] for x in data]}}, {"_id.sha1": 1, "size": 1, "url": 1})
        else:
            find_result = cf_files.find({"hashes": {"elemMatch": {"algo": 1, "value": {"$in": [x["sha1"] for x in data]}}}}, {"hashes": 1, "fileLength": 1, "downloadUrl": 1})
        for item in find_result:
            if "modrinth" in file:
                sha1 = item["_id"]["sha1"]
                if item["size"] != formated_data[sha1]:
                    error_files.append({"sha1": sha1, "size": formated_data[sha1], "db_size": item["size"], "url": item["url"], "type": "mr"})
                    print(f'Error: {sha1} {formated_data[sha1]} {item["size"]}')
                    mr_files.update_one({"_id.sha1": sha1}, {"$set": {"file_cdn_cached": False}})
            else:
                for hash in item["hashes"]:
                    if hash["algo"] == 1 and hash["value"] in formated_data:
                        sha1 = hash["value"]
                        if item["fileLength"] != formated_data[sha1]:
                            error_files.append({"sha1": sha1, "size": formated_data[sha1], "db_size": item["fileLength"], "url": item["downloadUrl"], "type": "cf"})
                            print(f'Error: {sha1} {formated_data[sha1]} {item["fileLength"]}')
                            cf_files.update_one({"hashes": {"$elemMatch": {"algo": 1, "value": sha1}}}, {"$set": {"file_cdn_cached": False}})

        print(f"File {file} done, total {len(error_files)} errors.")

with open("error_files.json", "w") as f:
    json.dump(error_files, f)



import httpx, uuid,hashlib

hclient = httpx.Client()

def verify_sha1(path):
    with open(path, "rb") as f:
        content = f.read()
    return hashlib.sha1(content).hexdigest()


def upload_file(url, path, sha1):
    temp_path = os.path.join("result", str(uuid.uuid4()))
    with open(temp_path, "wb") as f:
        response = hclient.get(url)
        if response.status_code != 200:
            print(f"Failed to download {url}")
            return False
        f.write(response.content)
    check = verify_sha1(temp_path)
    if check != sha1:
        print(f"Failed to verify {url}")
        return False
    client.upload_file(temp_path, path, overwrite=True)
    os.remove(temp_path)
    print(f"Uploaded {url} to {path}, EST {count}")
    return True

flag = False
with open("error_files.json", "r") as f:
    error_files = json.load(f)
    count=len(error_files)
    for error in error_files:
        if error["sha1"] == "fe438eb2af2c31713d3b7df32c10be5359f44f17":
            flag = True
        if flag:
            if error["type"] == "mr":
                url = error["url"]
                path = f"/modrinth/{error['sha1'][0:2]}/{error['sha1']}"
            if error["type"] == "cf":
                url = error["url"]
                path = f"/curseforge/{error['sha1'][0:2]}/{error['sha1']}"
            i = 0
            while i < 3:
                try:
                    res = upload_file(url, path, sha1=error["sha1"])
                    if res:
                        break
                    i += 1
                except Exception as e:
                    print(f"Error: {e}")
                    i += 1
            else:
                print(f"Failed to upload {url} to {path}")
        count -= 1

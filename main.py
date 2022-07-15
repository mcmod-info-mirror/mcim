
import os
import json
import toml
import zipfile
from .apis import *

def check_jar(mods_path):
    jar_info_list = []
    for jar_path in os.listdir(mods_path):
        jar_path = os.path.join(mods_path,jar_path)
        pass
        if os.path.splitext(jar_path)[1] == ".jar":
            pass
            jar_info = {}
            if zipfile.is_zipfile(jar_path):
                pass
                with zipfile.ZipFile(jar_path, "r") as zipf:
                    if "fabric.mod.json" in zipf.namelist():
                        try:
                            with zipf.open("fabric.mod.json") as info:
                                info_json = json.loads(info.read().decode("utf-8"))
                                if info_json["contact"]:
                                    if info_json["contact"]["homepage"]:
                                        jar_info["url"] = info_json["contact"]["homepage"]
                                jar_info_list.append({jar_path:jar_info})
                        except:
                            pass
                    elif "META-INF/mods.toml" in zipf.namelist():
                        try:
                            with zipf.open("META-INF/mods.toml") as info:
                                info_toml = toml.loads(info.read().decode("utf-8"))
                                if info_toml["mods"][0]["displayURL"]:
                                    jar_info["url"] = info_toml[0]["mods"]["displayURL"]
                                jar_info_list.append({jar_path:jar_info})
                        except:
                            pass
                    else:
                        print(zipf.namelist())
            else:
                print(jar_path+" is "+zipfile.is_zipfile(jar_path))
        else:
            pass
    return jar_info_list


# gameId = 432
# mods_path = "D:/Minecraft/.minecraft/versions/1.18.2 PCLS/mods"
# mods = api.Parse().check_jar(mods_path)
# for mod in mods:
#     for path in mod:
#         try:
#             if "www.curseforge.com" in mod[path]["url"]:
#                 url = mod[path]["url"]
#                 mod_slug = url.split("/")[-1]
#                 with open("cache.json","w+") as f:
#                     json.dump(api.Mod().search(slug=mod_slug),f)
#                     f.write("\n")
#         except KeyError:
#             pass

def main():
    cf_api = CurseForgeApi(api_config.curseforge_base_api_url, api_config.api_key, proxies=api_config.proxies)
    with open("cf_cache.json","w") as f:
        json.dump(cf_api.end_point(), f)

    mod_api = ModrinthApi(api_config.modrinth_base_api_url, proxies=api_config.proxies)
    with open("cache.json","w") as f:
        #json.dump(api.Mod().search("Sodium",limit=5,facets={"categories":"fabric","versions":"1.18.1","project_type":"mod"}),f)
        json.dump(mod_api.get_mod_version_download_info("Yp8wLY1P"), f)

if __name__ == '__main__':
    main()

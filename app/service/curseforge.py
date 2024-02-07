from typing import List, Optional, Union
from beanie import BulkWriter

from app.sync.curseforge import CurseForgeApi
from app.models.database.curseforge import (
    ModInfo,
    FileInfo,
    ModFilesSyncInfo,
    PaginationInfo,
    FingerprintInfo,
)
from app.models.response.curseforge import FingerprintResp, FingerprintMatch


api = CurseForgeApi


async def _save_FileInfo(file: dict):
    find_result = await FileInfo.find_one(FileInfo.fileId == file["fileId"])
    if find_result:
        find_result = await find_result.delete()
    return await FileInfo(**file).insert()


async def _save_many_FileInfo(files: List[dict]):
    await FileInfo.find(
        {"fileId": {"$in": [file["fileId"] for file in files]}}
    ).delete()
    res = [FileInfo(**file) for file in files]
    await FileInfo.insert_many(res)


async def _save_ModInfo(mod: dict):
    find_result = await ModInfo.find_one(ModInfo.modId == mod["modId"])
    latestFiles = []
    for file in mod["latestFiles"]:
        latestFiles.append(await _save_FileInfo(file))
    mod_model = ModInfo(**mod)
    mod_model.latestFiles = latestFiles
    if find_result:
        find_result = find_result.delete()
    return await mod_model.insert()


def _alias_fileid(file: dict) -> dict:
    file["fileId"] = file["id"]
    del file["id"]
    return file


def _alias_modid(mod: dict) -> dict:
    mod["modId"] = mod["id"]
    del mod["id"]
    i = []
    for file in mod["latestFiles"]:
        i.append(_alias_fileid(file))
    i.reverse()
    mod["latestFiles"] = i
    return mod


async def get_mod_info(modid: int) -> dict:
    res = await ModInfo.find_one({"modId": modid}, fetch_links=True)
    if res:
        return res.model_dump()
    else:
        mod = await api.get_mod(modid)
        await _save_ModInfo(_alias_modid(mod["data"]))
        return ModInfo(**mod["data"]).model_dump()


async def get_mods_info(modids: List[int]) -> dict:
    db_results = await ModInfo.find(
        {"modId": {"$in": modids}}, fetch_links=True
    ).to_list()

    if len(db_results) == len(modids):
        return [mod.model_dump() for mod in db_results]
    else:
        mods = await api.get_mods(modids)
        for mod in mods["data"]:
            await _save_ModInfo(_alias_modid(mod))
        return mods["data"]


async def get_file_info(modid: int, fileid: int) -> dict:
    res = await FileInfo.find_one({"modId": modid, "fileId": fileid})
    if res:
        return res.model_dump()
    else:
        file = await api.get_file(modid, fileid)
        await _save_FileInfo(_alias_fileid(file["data"]))
        return file["data"]


async def get_files_info(fileids: List[int]) -> dict:
    db_results = await FileInfo.find({"fileId": {"$in": fileids}}).to_list()

    if len(db_results) == len(fileids):
        return [file.model_dump() for file in db_results]
    else:
        files = await api.post_files(fileids)
        for file in files["data"]:
            await _save_FileInfo(_alias_fileid(file))
        return files["data"]


async def _sync_mod_files(modid: int):
    async with BulkWriter() as bulk_writer:
        files = await api.get_files(modid, ps=50)
        page = PaginationInfo(**files["pagination"])
        # index 递增
        while page.index < page.totalCount - 1:
            info = await api.get_files(
                modid, ps=page.pageSize, index=page.index + page.pageSize
            )
            page = PaginationInfo(**info["pagination"])
            files["data"].extend(info["data"])
        files["data"].extend(
            (
                await api.get_files(
                    modid, ps=page.pageSize, index=page.index + page.pageSize
                )
            )["data"]
        )
        await _save_many_FileInfo([_alias_fileid(file) for file in files["data"]])
        await ModFilesSyncInfo(modId=modid).insert()
    return files["data"]


async def get_mod_files_info(modid: int) -> dict:
    # 这里需要一个 mod_files sync_at 记录上次所有文件的同步时间，初学 mongodb，我也不清楚应该咋做这个过期逻辑比较好...
    res = await ModFilesSyncInfo.find_one({"modId": modid})
    if res:
        res = await FileInfo.find({"modId": modid}).to_list()
        if res:
            return [file.model_dump() for file in res]
        else:
            return await _sync_mod_files(modid)
    else:
        return await _sync_mod_files(modid)


async def _sync_fingerprints(fingerprints: List[int]) -> dict:
    update_model = []
    info = await api.get_fingerprints(fingerprints)
    for fingerprint in set(fingerprints).difference(set(info["data"]["exactFingerprints"])):
        update_model.append(
            FingerprintInfo(
                fingerprint=fingerprint,
                exist=False,
            )
        )
    if info["data"]["exactFingerprints"]:
        for exactMatch in info["data"]["exactMatches"]:
            update_model.append(
                FingerprintInfo(
                    fingerprint=exactMatch["file"]["fileFingerprint"],
                    modId=exactMatch["id"],
                    fileId=exactMatch["file"]["id"],
                    exist=True,
                )
            )

    await FingerprintInfo.find(
        {"fingerprint": {"$in": fingerprints}}
    ).delete()

    await FingerprintInfo.insert_many(update_model)

    return info["data"]


async def get_fingerprints(fingerprints: List[int]) -> dict:
    find_result = await FingerprintInfo.find_many(
        {"fingerprint": {"$in": fingerprints}}
    ).to_list()

    exactMatches = []
    unmatchedFingerprints = []
    exactFingerprints = []

    # 是否有结果
    if find_result:
        if len(find_result) == len(fingerprints):  # 全匹配
            for fingerprint in find_result:
                if fingerprint.exist:
                    mod = await get_mod_info(modid=fingerprint.modId)
                    file = await get_file_info(fingerprint.modId, fingerprint.fileId)
                    exactMatches.append(
                        FingerprintMatch(
                            id=fingerprint.fingerprint,
                            file=file,
                            latestFiles=mod["latestFiles"],
                        )
                    )
                    exactFingerprints.append(fingerprint.fingerprint)
                else:
                    unmatchedFingerprints.append(fingerprint.fingerprint)
            return FingerprintResp(
                exactMatches=exactMatches,
                exactFingerprints=exactFingerprints,
                installedFingerprints=fingerprints,
                unmatchedFingerprints=unmatchedFingerprints,
            ).model_dump()

    return await _sync_fingerprints(fingerprints)

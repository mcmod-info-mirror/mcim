from pydantic import Field, BaseModel
from typing import List
from app.models.database.curseforge import Fingerprint


class Hash(BaseModel):
    value: str
    algo: int


class FileSortableGameVersions(BaseModel):
    gameVersionName: str = None
    gameVersionPadded: str = None
    gameVersion: str = None
    gameVersionReleaseDate: str = None
    gameVersionTypeId: int = None


class FileDependencies(BaseModel):
    modId: int
    relationType: int = None


{
    "id": 0,
    "gameId": 0,
    "modId": 0,
    "displayName": "string",
    "fileName": "string",
    "releaseType": 1,
    "fileStatus": 1,
    "hashes": [{"value": "string", "algo": 1}],
    "fileDate": "2019-08-24T14:15:22Z",
    "fileLength": 0,
    "downloadCount": 0,
    "downloadUrl": "string",
    "gameVersions": ["string"],
    "sortableGameVersions": [
        {
            "gameVersionName": "string",
            "gameVersionPadded": "string",
            "gameVersion": "string",
            "gameVersionReleaseDate": "2019-08-24T14:15:22Z",
            "gameVersionTypeId": 0,
        }
    ],
    "dependencies": [{"modId": 0, "relationType": 1}],
    "fileFingerprint": 0,
}


class FileInfo(BaseModel):
    fileId: int
    gameId: int
    modId: int
    displayName: str
    fileName: str
    releaseType: int = None
    fileStatus: int = None
    hashes: List[Hash]
    fileDate: str
    fileLength: int = None
    downloadCount: int = None
    downloadUrl: str
    gameVersions: List[str] = None
    sortableGameVersions: List[FileSortableGameVersions] = None
    dependencies: List[FileDependencies] = None
    fileFingerprint: int = None



class FingerprintResponse(BaseModel):
    isCacheBuilt: bool
    exactMatches: List[Fingerprint]
    exactFingerprints: List[int]
    installedFingerprints: List[int]
    unmatchedFingerprints: List[int]
from pydantic import BaseModel, Field, field_serializer
from typing import List, Optional, Annotated
from datetime import datetime
from pymongo import ASCENDING, IndexModel
from beanie import Link, Indexed, Document


expireAfterSeconds = 60

class FileDependencies(BaseModel):
    modId: int
    relationType: int = None


class FileSortableGameVersions(BaseModel):
    gameVersionName: str = None
    gameVersionPadded: str = None
    gameVersion: str = None
    gameVersionReleaseDate: str = None
    gameVersionTypeId: int = None


class Hash(BaseModel):
    value: str
    algo: int


{"id": 0, "name": "string", "url": "string"}


class AuthorInfo(BaseModel):
    id: int
    name: str
    url: str = None


{
    "id": 0,
    "modId": 0,
    "title": "string",
    "description": "string",
    "thumbnailUrl": "string",
    "url": "string",
}


class LogoInfo(BaseModel):
    id: int
    modId: int
    title: str = None
    description: str = None
    thumbnailUrl: str = None
    url: str = None


{
    "id": 0,
    "gameId": 0,
    "name": "string",
    "slug": "string",
    "url": "string",
    "iconUrl": "string",
    "dateModified": "2019-08-24T14:15:22Z",
    "isClass": True,
    "classId": 0,
    "parentCategoryId": 0,
    "displayIndex": 0,
}


class CategoryInfo(BaseModel):
    id: int
    gameId: int
    name: str
    slug: str
    url: str = None
    iconUrl: str = None
    dateModified: str = None
    isClass: bool = None
    classId: int = None
    parentCategoryId: int = None
    displayIndex: int = None


{
    "websiteUrl": "string",
    "wikiUrl": "string",
    "issuesUrl": "string",
    "sourceUrl": "string",
}


class LinksInfo(BaseModel):
    websiteUrl: str = None
    wikiUrl: str = None
    issuesUrl: str = None
    sourceUrl: str = None


{
    "id": 0,
    "modId": 0,
    "title": "string",
    "description": "string",
    "thumbnailUrl": "string",
    "url": "string",
}


class ScreenShotInfo(BaseModel):
    id: int
    modId: int
    title: str = None
    description: str = None
    thumbnailUrl: str = None
    url: str = None


{
    "id": 0,
    "gameId": 0,
    "modId": 0,
    "isAvailable": True,
    "displayName": "string",
    "fileName": "string",
    "releaseType": 1,
    "fileStatus": 1,
    "hashes": [{"value": "string", "algo": 1}],
    "fileDate": "2019-08-24T14:15:22Z",
    "fileLength": 0,
    "downloadCount": 0,
    "fileSizeOnDisk": 0,
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
    "exposeAsAlternative": True,
    "parentProjectFileId": 0,
    "alternateFileId": 0,
    "isSerlyAccessContent": True,
    "earlyAccessEndDate": "2019-08-24T14:15:22Z",
    "fileFingerprint": 0,
    "modules": [{"name": "string", "fingerprint": 0}],
}


class FileInfo(Document):
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

    sync_at: datetime = Field(default_factory=datetime.utcnow)

    @field_serializer("sync_at", when_used='json')
    def serialize_sync_Date(self, value: datetime, _info):
        return value.strftime("%Y-%m-%dT%H:%M:%SZ")

    class Settings:
        name = "files"
        indexes = [
            IndexModel([("fileId", 1)], unique=True),
            # IndexModel([("gameId", 1)], unique=False),
            # IndexModel([("modId", 1)], unique=False),
            IndexModel([("sync_at", ASCENDING)], expireAfterSeconds=expireAfterSeconds),  # auto expire
        ]


{
    "gameVersion": "string",
    "fileId": 0,
    "filename": "string",
    "releaseType": 1,
    "gameVersionTypeId": 0,
    "modLoader": 0,
}


class FileIndexInfo(BaseModel):
    gameVersion: str = None
    fileId: int
    filename: str = None
    releaseType: int = None
    gameVersionTypeId: int = None
    modLoader: Optional[int] = Field(default=None)


class ModInfo(Document):
    modId: int
    gameId: int
    name: str
    slug: str
    links: LinksInfo = None
    summary: str
    status: int = None
    downloadCount: int = None
    primaryCategoryId: int = None
    classId: int = None
    authors: List[AuthorInfo] = None
    logo: LogoInfo = None
    screenshots: List[ScreenShotInfo] = None
    latestFiles: List[Link[FileInfo]] = None
    latestFilesIndexes: List[FileIndexInfo] = None
    dateCreated: str = None
    dateModified: str = None
    dateReleased: str = None
    gamePopularityRank: int = None
    thumbsUpCount: int = None
    # rating: int

    sync_at: datetime = Field(default_factory=datetime.utcnow)

    @field_serializer("sync_at", when_used='json')
    def serialize_sync_Date(self, value: datetime, _info):
        return value.strftime("%Y-%m-%dT%H:%M:%SZ")

    class Settings:
        name = "mods"
        indexes = [
            IndexModel([("modId", 1)], unique=True),
            IndexModel([("gameId", 1)], unique=False),
            IndexModel([("slug", 1)], unique=True),
            IndexModel([("sync_at", ASCENDING)], expireAfterSeconds=expireAfterSeconds),  # auto expire
        ]

{"pagination": {"index": 0, "pageSize": 0, "resultCount": 0, "totalCount": 0}}


class PaginationInfo(BaseModel):
    index: int
    pageSize: int
    resultCount: int
    totalCount: int

class ModFilesSyncInfo(Document):
    modId: int
    
    sync_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "mod_files_sync"
        indexes = [
            IndexModel([("modId", 1)], unique=True),
            IndexModel([("sync_at", ASCENDING)], expireAfterSeconds=expireAfterSeconds),  # auto expire
        ]

class FingerprintInfo(Document):
    modId: Optional[int] = None
    fileId: Optional[int] = None
    fingerprint: int
    exist: bool = True

    class Settings:
        name = "fingerprints"
        indexes = [
            IndexModel([("fingerprint", 1)], unique=True),
            # 永不过期
        ]
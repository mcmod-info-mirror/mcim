from odmantic import Model, Field, EmbeddedModel
from pydantic import BaseModel, field_serializer, field_validator, model_validator

from typing import List, Optional, Union
from datetime import datetime

class DonationUrl(BaseModel):
    id: Optional[str] = None
    platform: Optional[str] = None
    url: Optional[str] = None

class License(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    url: Optional[str] = None

class GalleryItem(BaseModel):
    url: Optional[str] = None
    featured: Optional[bool] = None
    title: Optional[str] = None
    description: Optional[str] = None
    created: Optional[str] = None
    ordering: Optional[int] = None

class Project(Model):
    id: str = Field(primary_field=True, index=True)
    slug: str = Field(index=True)
    title: Optional[str] = None
    description: Optional[str] = None
    categories: Optional[List[str]] = None
    client_side: Optional[str] = None
    server_side: Optional[str] = None
    body: Optional[str] = None
    status: Optional[str] = None
    requested_status: Optional[str] = None
    additional_categories: Optional[List[str]] = None
    issues_url: Optional[str] = None
    source_url: Optional[str] = None
    wiki_url: Optional[str] = None
    discord_url: Optional[str] = None
    donation_urls: Optional[List[DonationUrl]] = None
    project_type: Optional[str] = None
    downloads: Optional[int] = None
    icon_url: Optional[str] = None
    color: Optional[int] = None
    thread_id: Optional[str] = None
    monetization_status: Optional[str] = None
    team: Optional[str] = None
    body_url: Optional[str] = None
    # moderator_message: Optional[str] = None Deprecated
    published: Optional[str] = None
    updated: Optional[str] = None
    approved: Optional[str] = None
    queued: Optional[str] = None
    followers: Optional[int] = None
    license: Optional[License] = None
    versions: Optional[List[str]] = None
    game_versions: Optional[List[str]] = None
    loaders: Optional[List[str]] = None
    gallery: Optional[List[GalleryItem]] = None

    translated_description: Optional[str] = None
    found: bool = Field(default=True)
    sync_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "collection": "modrinth_projects",
    }

    @field_serializer("sync_at")
    def serialize_sync_Date(self, value: datetime, _info):
        return value.strftime("%Y-%m-%dT%H:%M:%SZ")
    

class Dependencies(BaseModel):
    version_id: Optional[str] = None
    project_id: Optional[str] = None
    file_name: Optional[str] = None
    dependency_type: Optional[str] = None


class Hashes(EmbeddedModel):
    sha512: str
    sha1: str = Field(index=True)


# TODO: Add Version reference directly but not query File again
class File(Model):
    hashes: Hashes = Field(primary_field=True)
    url: Optional[str] = None
    filename: Optional[str] = None
    primary: Optional[bool] = None
    size: Optional[int] = None
    file_type: Optional[str] = None

    version_id: Optional[str] #  = Field(index=True)  # 有可能没有该 file...
    project_id: Optional[str] #  = Field(index=True)

    file_cdn_cached: Optional[bool] = False
    found: Optional[bool] = True
    sync_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"collection": "modrinth_files"}

    @field_serializer("sync_at")
    def serialize_sync_Date(self, value: datetime, _info):
        return value.strftime("%Y-%m-%dT%H:%M:%SZ")

class FileInfo(BaseModel):
    hashes: Hashes
    url: Optional[str] = None
    filename: Optional[str] = None
    primary: Optional[bool] = None
    size: Optional[int]
    file_type: Optional[str]

class Version(Model):
    id: str = Field(primary_field=True, index=True)
    project_id: Optional[str] = Field(index=True)
    slug: Optional[str] = None
    name: Optional[str] = None
    version_number: Optional[str] = None
    changelog: Optional[str] = None
    dependencies: Optional[List[Dependencies]] = None
    game_versions: Optional[List[str]] = None
    version_type: Optional[str] = None
    loaders: Optional[List[str]] = None
    featured: Optional[bool] = None
    status: Optional[str] = None
    requested_status: Optional[str] = None
    author_id: Optional[str] = None
    date_published: Optional[datetime] = None #  = Field(index=True)
    downloads: Optional[int] = None
    changelog_url: Optional[str] = None  # Deprecated
    files: Optional[List[FileInfo]] = None

    found: bool = True
    sync_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"collection": "modrinth_versions"}

    @field_serializer("sync_at", "date_published")
    def serialize_sync_date(self, value: datetime, _info):
        return value.strftime("%Y-%m-%dT%H:%M:%SZ")

    @field_validator("date_published")
    @classmethod
    def format_date(cls, v: Union[str, datetime]) -> datetime:
        if isinstance(v, str):
            return datetime.strptime(v, "%Y-%m-%dT%H:%M:%S.%fZ")
        return v

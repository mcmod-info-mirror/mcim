from odmantic import Model, Field, EmbeddedModel
from pydantic import BaseModel, field_serializer, model_serializer

from typing import List, Optional
from datetime import datetime

expireAfterSeconds: int = 60 * 60 * 24

class Gallery(BaseModel):
    url: Optional[str] = None
    featured: Optional[bool] = None
    title: Optional[str] = None
    description: Optional[str] = None
    created: Optional[str] = None
    ordering: Optional[int] = None

class Project(Model):
    id: str = Field(primary_field=True)
    slug: str
    title: Optional[str] = None
    description: Optional[str] = None
    categories: Optional[List[str]] = None
    client_side: Optional[str] = None
    server_side: Optional[str] = None
    status: Optional[str] = None
    additional_categories: Optional[List[str]] = None
    issues_url: Optional[str] = None
    source_url: Optional[str] = None
    wiki_url: Optional[str] = None
    project_type: Optional[str] = None
    downloads: Optional[int] = None
    icon_url: Optional[str] = None
    published: Optional[str] = None
    updated: Optional[str] = None
    approved: Optional[str] = None
    versions: Optional[List[str]] = None
    game_versions: Optional[List[str]] = None
    loaders: Optional[List[str]] = None
    gallery: Optional[List[Gallery]] = None

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
    sha1: str

# TODO: Add Version reference directly but not query File again
class File(Model):
    hashes: Hashes = Field(primary_field=True)
    version_id: str
    url: Optional[str] = None
    filename: Optional[str] = None
    primary: Optional[bool] = None
    size: Optional[int] = None
    file_type: Optional[Optional[str]] = None

    found: bool = True
    sync_at: datetime = Field(default_factory=datetime.utcnow)


    model_config = {
        "collection": "modrinth_files"
    }
        
    @field_serializer("sync_at")
    def serialize_sync_Date(self, value: datetime, _info):
        return value.strftime("%Y-%m-%dT%H:%M:%SZ")
    
class Version(Model):
    id: str = Field(primary_field=True)
    project_id: str
    slug: Optional[str] = None
    name: str
    version_number: str
    changelog: Optional[str] = None
    dependencies: Optional[List[Dependencies]] = None
    game_versions: List[str]
    version_type: str
    loaders: List[str]
    featured: bool
    status: Optional[str] = None
    requested_status: Optional[str] = None
    author_id: str
    date_published: str
    downloads: int
    changelog_url: Optional[str] = None # Deprecated
    files: List[File]

    found: bool = True
    sync_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "collection": "modrinth_versions"
    }

    @field_serializer("sync_at")
    def serialize_sync_Date(self, value: datetime, _info):
        return value.strftime("%Y-%m-%dT%H:%M:%SZ")

from pydantic import Field, BaseModel
from typing import List, Union, Optional
from app.models.database.curseforge import Mod, File, Pagination

class CurseforgeBaseResponse(BaseModel):
    data: Union[Mod, File, dict, List]

class CurseforgePageBaseResponse(BaseModel):
    data: Union[Mod, File, dict, List]
    pagination: Optional[Pagination] = Pagination()
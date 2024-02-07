from pydantic import Field, BaseModel
from typing import List

class Fingerprints(BaseModel):
    fingerprints: List[int]
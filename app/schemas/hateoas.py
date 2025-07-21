from pydantic import BaseModel
from typing import List, Dict, Any

class Link(BaseModel):
    rel: str
    href: str

class HypermediaModel(BaseModel):
    data: Any
    links: List[Link]
from pydantic import BaseModel
from datetime import datetime
from typing import Literal

class PartyBase(BaseModel):
    party_type: Literal['person', 'organisation']
    display_name: str

class PartyCreate(PartyBase):
    pass

class PartyRead(PartyBase):
    party_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
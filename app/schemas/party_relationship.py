from pydantic import BaseModel
from typing import Optional
from datetime import date

class PartyRelationshipBase(BaseModel):
    from_party_id: int
    to_party_id: int
    relationship_type: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = None

class PartyRelationshipCreate(PartyRelationshipBase):
    pass

class PartyRelationshipRead(PartyRelationshipBase):
    relationship_id: int

    class Config:
        from_attributes = True
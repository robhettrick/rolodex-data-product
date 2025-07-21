from datetime import datetime
from pydantic import ConfigDict
from pydantic import BaseModel

class ExternalIdentifierBase(BaseModel):
    party_id: int
    system_name: str
    external_id: str

class ExternalIdentifierCreate(ExternalIdentifierBase):
    pass

class ExternalIdentifierRead(ExternalIdentifierBase):
    model_config = ConfigDict(from_attributes=True)
    external_identifier_id: int
    party_id: int
    system_name: str
    external_id: str
    last_synced: datetime | None = None
    created_at: datetime

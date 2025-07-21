from pydantic import BaseModel

class PartyAddressBase(BaseModel):
    party_id: int
    address_id: int

class PartyAddressCreate(PartyAddressBase):
    pass

class PartyAddressRead(PartyAddressBase):

    class Config:
        from_attributes = True
from pydantic import BaseModel
from typing import Optional

class AddressBase(BaseModel):
    address_line_1: str
    address_line_2: Optional[str] = None
    city: str
    region: Optional[str] = None
    postal_code: str
    country: str
    address_type: str

class AddressCreate(AddressBase):
    pass

class AddressRead(AddressBase):
    address_id: int

    class Config:
        from_attributes = True
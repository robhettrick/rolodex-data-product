from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date

class PersonBase(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    email: EmailStr
    phone_primary: str
    phone_secondary: Optional[str] = None

class PersonCreate(PersonBase):
    pass

class PersonRead(PersonBase):
    party_id: int

    class Config:
        from_attributes = True
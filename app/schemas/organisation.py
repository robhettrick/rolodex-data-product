from pydantic import BaseModel, EmailStr
from typing import Optional

class OrganisationBase(BaseModel):
    organisation_name: str
    organisation_type: str
    registration_number: Optional[str] = None
    email: EmailStr
    phone_primary: str
    phone_secondary: Optional[str] = None

class OrganisationCreate(OrganisationBase):
    pass

class OrganisationRead(OrganisationBase):
    party_id: int

    class Config:
        from_attributes = True